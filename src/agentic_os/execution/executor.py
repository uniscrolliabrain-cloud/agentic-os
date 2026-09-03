from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from .action import Action
from .result import ExecutionResult
from .tools.registry import ToolRegistry
from ..kernel.policy.engine import PolicyEngine
from ..kernel.policy.evaluator import Decision
from ..kernel.world.events import Event


_SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9\-_]{20,}",
    r"ya29\.[a-zA-Z0-9\-_]+",
    r"Bearer\s+[a-zA-Z0-9\.\-_]+",
    r"api_key[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"token[=:]\s*[a-zA-Z0-9\-_]{10,}",
    r"xox[bprs]-[a-zA-Z0-9\-]+",
]


def _safe_error(error: Exception) -> str:

    message = str(error)

    for pattern in _SECRET_PATTERNS:
        message = re.sub(
            pattern,
            "[REDACTED_SECRET]",
            message,
            flags=re.IGNORECASE,
        )

    if len(message) > 300:
        message = message[:300] + " [truncated]"

    sensitive = {
        "authorization",
        "credential",
        "secret",
        "private_key",
        "password",
        "api key",
    }

    if any(
        item in message.lower()
        for item in sensitive
    ):
        return (
            "execution failed: "
            "provider error "
            "(details redacted)"
        )

    return message


class Executor:

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        policy_engine: Optional[PolicyEngine] = None,
        event_log: Any = None,
    ):
        self.registry = registry or ToolRegistry()
        self.policy = policy_engine or PolicyEngine()
        self.event_log = event_log

    def _audit(
        self,
        kind: str,
        capability: str,
        tenant_id: str,
        payload: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
    ) -> None:

        if self.event_log is None:
            return

        event = Event(
            kind=kind,
            entity_id=capability,
            tenant_id=tenant_id or "system",
            actor_id=actor_id or "executor",
            payload=payload or {},
            correlation_id=correlation_id,
            command_id=command_id,
        )

        self.event_log.append(event)

    @staticmethod
    def _tenant_from_context(
        context: Any,
    ) -> Optional[str]:

        if context is None:
            return None

        if hasattr(context, "tenant"):
            return getattr(
                context.tenant,
                "id",
                None,
            )

        if isinstance(context, dict):
            tenant = context.get("tenant")

            if isinstance(tenant, dict):
                return tenant.get("id")

            return getattr(
                tenant,
                "id",
                None,
            )

        return None

    @staticmethod
    def _params_summary(
        params: Dict[str, Any],
    ) -> Dict[str, str]:

        return {
            key: f"<{type(value).__name__}>"
            for key, value in sorted(
                params.items()
            )
        }

    def _decision(
        self,
        action: str,
        tenant_id: str,
        roles: Optional[List[str]],
        context: Any,
    ) -> Decision:

        if not tenant_id:
            if self.policy is not None and getattr(
                self.policy, "_has_explicit_policy", False
            ):
                # Path legacy/tests (ConnectorBridgeTool, mocks): policy
                # explícita inyectada se evalúa sin tenant (default-deny del
                # evaluador gobierna la resolución).
                return self.policy.decide(
                    tenant_id=None,
                    capability=action,
                    resource_kind=(
                        context
                        if isinstance(context, str)
                        else None
                    ),
                    roles=roles or [],
                )
            return Decision(
                effect="deny",
                reason="tenant_id obligatorio",
            )

        return self.policy.decide(
            tenant_id=tenant_id,
            capability=action,
            resource_kind=(
                context
                if isinstance(context, str)
                else None
            ),
            roles=roles or [],
        )

    def execute(
        self,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        context: Any = None,
        roles: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        command_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:

        params = params or {}

        tid = (
            tenant_id
            or self._tenant_from_context(context)
        )

        actor = (
            actor_id
            or (roles[0] if roles else "executor")
        )

        # ------------------------------------------------ POLICY

        decision = self._decision(
            action=action,
            tenant_id=tid,
            roles=roles,
            context=context,
        )

        if decision.effect == "deny":

            self._audit(
                "ActionDenied",
                action,
                tid or "system",
                {
                    "reason": decision.reason,
                    "params": self._params_summary(params),
                },
                actor,
                correlation_id,
                command_id,
            )

            return {
                "success": False,
                "error": decision.reason,
                "decision": decision.model_dump(),
            }

        # ------------------------------------------ APPROVAL

        if decision.effect == "require_approval":

            self._audit(
                "ApprovalRequired",
                action,
                tid,
                {
                    "reason": decision.reason,
                    "params": self._params_summary(params),
                },
                actor,
                correlation_id,
                command_id,
            )

            return {
                "success": False,
                "error": "approval required",
                "decision": decision.model_dump(),
            }

        # ---------------------------------------------- TOOL

        tool = self.registry.get(action)

        if tool is None:

            self._audit(
                "ToolFailed",
                action,
                tid,
                {
                    "error": (
                        f"tool '{action}' "
                        "no encontrada"
                    )
                },
                actor,
                correlation_id,
                command_id,
            )

            return {
                "success": False,
                "error": (
                    f"tool '{action}' "
                    "no encontrada"
                ),
            }

        if tid:
            # Aislamiento de tenant: el tenant del contexto SIEMPRE gana.
            # Un caller no puede sobreescribir tenant_id con un valor distinto
            # del confirmado por policy/autenticación (fail-closed).
            supplied_tenant = params.get("tenant_id")
            if supplied_tenant is not None and supplied_tenant != tid:
                self._audit(
                    "ActionDenied",
                    action,
                    tid,
                    {
                        "reason": "tenant_id no puede ser sobreescrito",
                        "params": self._params_summary(params),
                    },
                    actor,
                    correlation_id,
                    command_id,
                )
                return {
                    "success": False,
                    "error": "tenant_id no puede ser sobreescrito",
                }

        self._audit(
            "ActionStarted",
            action,
            tid,
            {
                "status": "started",
                "params": self._params_summary(params),
            },
            actor,
            correlation_id,
            command_id,
        )

        try:

            run_params = dict(params)
            if tid:
                # El tenant autenticado se inyecta SIEMPRE: las tools nunca
                # confían en un tenant_id libre aportado por el caller.
                run_params["tenant_id"] = tid

            output = tool.run(run_params)

            self._audit(
                "ToolCompleted",
                action,
                tid,
                {
                    "status": "ok",
                    "output_keys": (
                        sorted(output.keys())
                        if isinstance(output, dict)
                        else []
                    ),
                },
                actor,
                correlation_id,
                command_id,
            )

            return {
                "success": True,
                "output": output,
            }

        except Exception as error:

            safe = _safe_error(error)

            self._audit(
                "ToolFailed",
                action,
                tid,
                {
                    "status": "error",
                    "error": safe,
                },
                actor,
                correlation_id,
                command_id,
            )

            return {
                "success": False,
                "error": safe,
            }

    def execute_action(
        self,
        action,
        roles=None,
    ):

        value = (
            action.value
            if hasattr(action, "value")
            else action
        )

        result = self.execute(
            action=value,
            roles=roles,
            tenant_id="system",
        )

        return ExecutionResult(
            action=action,
            success=result.get(
                "success",
                False,
            ),
            output=result.get("output"),
            error=result.get("error"),
        )
