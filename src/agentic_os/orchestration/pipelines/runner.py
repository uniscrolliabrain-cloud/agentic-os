"""PipelineRunner - motor canonico, tenant-agnostico.

Pipeline -> MicroAction (`runner.tool()`) -> Executor (Policy + audit)
-> Tool -> EventLog.

Cada tenant declara sus pipelines como modelos Pydantic en
`domains/<tenant>/pipelines.py` y sus handlers en `domains/<tenant>/handlers.py`.
El runner resuelve `(tenant_slug, pipeline_id) -> handler` via DomainRegistry.
NO conoce pipeline alguno de forma hardcodeada.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from typing import Any, Callable, Dict, Optional

from ...domains import DomainRegistry
from ...infrastructure.idempotency import IdempotencyStore
from ...kernel.world.events import Event


class PipelineStepError(Exception):
    def __init__(self, tool_name: str, error: str):
        super().__init__(f"[pipeline] tool '{tool_name}' fallo: {error}")
        self.tool_name = tool_name
        self.error = error


class UnknownPipelineError(Exception):
    def __init__(self, pipeline_id: str, tenant_slug: str = ""):
        self.pipeline_id = pipeline_id
        self.tenant_slug = tenant_slug
        msg = f"pipeline desconocido: {pipeline_id!r}"
        if tenant_slug:
            msg += f" (tenant={tenant_slug!r})"
        super().__init__(msg)


def get_tenant_pipelines(tenant_slug: str) -> Dict[str, Any]:
    pack = DomainRegistry().get(tenant_slug)
    return dict(pack.pipelines) if pack else {}


def get_tenant_handlers(tenant_slug: str) -> Dict[str, Callable[..., Dict[str, Any]]]:
    pack = DomainRegistry().get(tenant_slug)
    return dict(pack.handlers) if pack else {}


def list_registered_tenants() -> list[str]:
    return DomainRegistry().all_slugs()


class PipelineRunner:
    def __init__(self, executor: Any, llm: Any = None,
                 tenant_slug: Optional[str] = None):
        self.executor = executor
        self.idempotency = IdempotencyStore()
        self.llm = llm
        self.tenant_slug = tenant_slug

    def tool(self, name: str, params: Dict[str, Any], tenant_id: str,
             correlation_id: Optional[str] = None,
             command_id: Optional[str] = None,
             retry_policy: Optional[Dict[str, Any]] = None,
             output_schema: Optional[Dict[str, Any]] = None,
             timeout_seconds: Optional[int] = None) -> Dict[str, Any]:
        """Ejecuta una microaccion con observabilidad (spec 17).

        - Emite MicroActionStarted/Completed/Failed.
        - Aplica retry_policy (spec 12) a fallos retryables.
        - Aplica timeout_seconds (spec 12).
        - Valida output contra output_schema (spec 16).
        """
        run_params = dict(params or {})
        if tenant_id:
            run_params.setdefault("tenant_id", tenant_id)

        policy = retry_policy or {}
        max_retries = int(policy.get("max_retries", 0) or 0)
        backoff = float(policy.get("backoff", 1.5) or 1.5)
        attempts = max_retries + 1

        last_error: Optional[str] = None
        for attempt in range(1, attempts + 1):
            self._audit("MicroActionStarted", name, tenant_id,
                        correlation_id, command_id,
                        {"tool": name, "attempt": attempt})
            started = time.perf_counter()
            try:
                if timeout_seconds:
                    pool = ThreadPoolExecutor(max_workers=1)
                    try:
                        fut = pool.submit(
                            self.executor.execute,
                            action=name, params=run_params,
                            tenant_id=tenant_id,
                            correlation_id=correlation_id,
                            command_id=command_id,
                        )
                        try:
                            result = fut.result(timeout=timeout_seconds)
                        except FuturesTimeoutError:
                            raise _TimeoutError(name, timeout_seconds)
                    finally:
                        pool.shutdown(wait=False)
                else:
                    result = self.executor.execute(
                        action=name, params=run_params, tenant_id=tenant_id,
                        correlation_id=correlation_id, command_id=command_id,
                    )

                if not result.get("success"):
                    raise PipelineStepError(
                        name, result.get("error", "error desconocido")
                    )

                output = result.get("output")
                if not isinstance(output, dict):
                    output = {"data": output}

                if output_schema:
                    _validate_output_schema(name, output, output_schema)

                elapsed_ms = int((time.perf_counter() - started) * 1000)
                self._audit("MicroActionCompleted", name, tenant_id,
                            correlation_id, command_id,
                            {"tool": name, "attempt": attempt,
                             "elapsed_ms": elapsed_ms,
                             "output_keys": sorted(output.keys())})
                return output

            except _TimeoutError as exc:
                self._audit("MicroActionFailed", name, tenant_id,
                            correlation_id, command_id,
                            {"tool": name, "attempt": attempt,
                             "error": str(exc)})
                raise PipelineStepError(name, str(exc))
            except PipelineStepError as exc:
                last_error = str(exc)[:300]
                if attempt < attempts:
                    time.sleep(backoff ** (attempt - 1) * 0.05)
                    continue
                self._audit("MicroActionFailed", name, tenant_id,
                            correlation_id, command_id,
                            {"tool": name, "attempt": attempt,
                             "error": last_error})
                raise
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)[:300]
                if attempt < attempts:
                    time.sleep(backoff ** (attempt - 1) * 0.05)
                    continue
                self._audit("MicroActionFailed", name, tenant_id,
                            correlation_id, command_id,
                            {"tool": name, "attempt": attempt,
                             "error": last_error})
                raise PipelineStepError(name, last_error or "error")

        raise PipelineStepError(name, last_error or "sin intentos")

    def run(self, pipeline_id: str, tenant_id: str,
            params: Optional[Dict[str, Any]] = None,
            correlation_id: Optional[str] = None,
            command_id: Optional[str] = None,
            tenant_slug: Optional[str] = None) -> Dict[str, Any]:
        slug = tenant_slug or self.tenant_slug
        if not slug:
            raise UnknownPipelineError(pipeline_id, tenant_slug="<no especificado>")

        tid = tenant_id or "system"

        if command_id:
            try:
                cached = self.idempotency.get(tid, f"pipeline:{slug}:{command_id}")
                if cached is not None:
                    return cached
            except Exception:
                pass

        return self._run_impl(
            pipeline_id=pipeline_id, tenant_slug=slug, tenant_id=tid,
            params=params or {}, correlation_id=correlation_id,
            command_id=command_id,
        )

    def _run_impl(self, pipeline_id: str, tenant_slug: str, tenant_id: str,
                  params: Dict[str, Any], correlation_id: Optional[str],
                  command_id: Optional[str]) -> Dict[str, Any]:
        pipelines = get_tenant_pipelines(tenant_slug)
        handlers = get_tenant_handlers(tenant_slug)

        pipeline = pipelines.get(pipeline_id)
        if pipeline is None:
            raise UnknownPipelineError(pipeline_id, tenant_slug)

        if not getattr(pipeline, "enabled", True):
            raise PipelineStepError(
                pipeline_id,
                f"pipeline deshabilitado para tenant '{tenant_slug}'",
            )

        handler = handlers.get(pipeline_id)
        if handler is None:
            raise PipelineStepError(
                pipeline_id,
                f"pipeline '{pipeline_id}' sin handler registrado en '{tenant_slug}'",
            )

        self._audit("PipelineStarted", pipeline_id, tenant_id,
                    correlation_id, command_id,
                    {"pipeline_id": pipeline_id, "tenant_slug": tenant_slug})
        try:
            result = handler(self, tenant_id, params, correlation_id)
            self._audit("PipelineCompleted", pipeline_id, tenant_id,
                        correlation_id, command_id,
                        {"pipeline_id": pipeline_id, "status": result.get("status")})
            if command_id:
                try:
                    self.idempotency.save(
                        tenant_id, f"pipeline:{tenant_slug}:{command_id}", result
                    )
                except Exception:
                    pass
            return result
        except Exception as error:
            self._audit("PipelineFailed", pipeline_id, tenant_id,
                        correlation_id, command_id,
                        {"pipeline_id": pipeline_id, "error": str(error)[:300]})
            raise

    def emit_event(self, kind: str, entity_id: str, tenant_id: str,
                   payload: Dict[str, Any],
                   correlation_id: Optional[str] = None,
                   command_id: Optional[str] = None) -> None:
        event_log = getattr(self.executor, "event_log", None)
        if event_log is None:
            return
        event_log.append(Event(
            kind=kind, entity_id=entity_id, tenant_id=tenant_id,
            actor_id="pipeline_runner", payload=payload,
            correlation_id=correlation_id, command_id=command_id,
        ))

    def _audit(self, kind: str, entity_id: str, tenant_id: str,
               correlation_id: Optional[str], command_id: Optional[str],
               payload: Dict[str, Any]) -> None:
        event_log = getattr(self.executor, "event_log", None)
        if event_log is None:
            return
        event_log.append(Event(
            kind=kind, entity_id=entity_id, tenant_id=tenant_id,
            actor_id="pipeline_runner", payload=payload,
            correlation_id=correlation_id, command_id=command_id,
        ))


def _validate_output_schema(tool_name: str, output: Dict[str, Any],
                             schema: Dict[str, Any]) -> None:
    """Validacion minima (spec 16): required keys + tipo si se declara."""
    if not isinstance(schema, dict):
        return
    required = schema.get("required") or []
    missing = [k for k in required if k not in output]
    if missing:
        raise PipelineStepError(
            tool_name, f"output_schema: faltan claves requeridas {missing}"
        )
    props = schema.get("properties") or {}
    type_map = {
        "string": str, "integer": int, "number": (int, float),
        "boolean": bool, "array": list, "object": dict,
    }
    for key, spec in props.items():
        if key not in output or not isinstance(spec, dict):
            continue
        expected = spec.get("type")
        if expected not in type_map:
            continue
        value = output[key]
        py_type = type_map[expected]
        if expected == "integer" and isinstance(value, bool):
            raise PipelineStepError(
                tool_name, f"output_schema: {key} debe ser integer"
            )
        if not isinstance(value, py_type):
            raise PipelineStepError(
                tool_name, f"output_schema: {key} debe ser {expected}"
            )

class _TimeoutError(Exception):
    """Timeout de un step de pipeline (terminal, no retryable)."""

    def __init__(self, tool_name: str, seconds: int):
        super().__init__(f"timeout de {seconds}s en tool {tool_name!r}")


__all__ = [
    "PipelineRunner",
    "PipelineStepError",
    "UnknownPipelineError",
    "get_tenant_pipelines",
    "get_tenant_handlers",
    "list_registered_tenants",
]
