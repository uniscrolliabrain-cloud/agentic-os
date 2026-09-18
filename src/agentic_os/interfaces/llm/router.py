"""Model Router (BUILD_PLAN bloque 0).

Enruta peticiones LLM a multiples proveedores con:
- Preferencia declarada (skill / agente / paso).
- Fallback en cascada cuando un proveedor falla.
- Cache en memoria de prompts identicos.
- Tracking de tokens, latencia y coste.

No toca FallbackLLMProvider existente. Es una pieza nueva.
"""
from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ModelRequest(BaseModel):
    """Peticion a cualquier proveedor LLM."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    prompt: str
    system_instruction: Optional[str] = None
    response_schema: Optional[Dict[str, Any]] = None
    preferred_model: Optional[str] = None
    tenant_id: Optional[str] = None
    correlation_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.2
    cost_hint: Optional[str] = None  # "cheap" | "medium" | "expensive"


class ModelResponse(BaseModel):
    """Respuesta normalizada de cualquier proveedor."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str
    structured: Optional[Dict[str, Any]] = None
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    fallback_used: bool = False
    cache_hit: bool = False


# ---------------------------------------------------------------------------
# ProviderAdapter: interfaz comun
# ---------------------------------------------------------------------------


class ProviderAdapter(ABC):
    """Adapter de un proveedor LLM. Contrato minimo."""

    name: str = ""
    default_model: str = ""
    cost_class: str = "medium"  # "cheap" | "medium" | "expensive"

    @abstractmethod
    def is_available(self) -> bool:
        """True si tiene credenciales / esta operativo."""

    @abstractmethod
    def generate(self, req: ModelRequest) -> ModelResponse:
        """Ejecuta la peticion y devuelve respuesta normalizada."""


# ---------------------------------------------------------------------------
# Adapters reales (envuelven providers existentes o nuevos)
# ---------------------------------------------------------------------------


class MockAdapter(ProviderAdapter):
    """Adapter de test. Respuestas deterministas."""

    name = "mock"
    default_model = "mock-model"
    cost_class = "cheap"

    def __init__(self, response_text: str = "ok", fail: bool = False) -> None:
        self._response_text = response_text
        self._fail = fail

    def is_available(self) -> bool:
        return True

    def generate(self, req: ModelRequest) -> ModelResponse:
        if self._fail:
            raise RuntimeError(f"{self.name} forced failure")
        return ModelResponse(
            text=self._response_text,
            provider=self.name,
            model=req.preferred_model or self.default_model,
        )


class GeminiAdapter(ProviderAdapter):
    """Envuelve GeminiProvider existente."""

    name = "gemini"
    cost_class = "cheap"

    def __init__(self) -> None:
        from .provider import GeminiProvider
        from ...infrastructure.config.settings import settings

        self.default_model = settings.gemini_model
        self._provider = None
        try:
            self._provider = GeminiProvider()
        except Exception:
            self._provider = None

    def is_available(self) -> bool:
        return self._provider is not None

    def generate(self, req: ModelRequest) -> ModelResponse:
        if self._provider is None:
            raise RuntimeError("gemini no disponible (falta API key)")
        t0 = time.perf_counter()
        if req.response_schema:
            from pydantic import create_model
            schema = req.response_schema
            # Construye modelo dinamico minimo a partir del schema
            fields = {k: (Any, None) for k in schema.get("properties", {})} or {"result": (Any, None)}
            Dyn = create_model("DynLLMOutput", **fields)
            parsed = self._provider.generate_structured(req.prompt, Dyn, req.system_instruction)
            text = parsed.model_dump_json()
            structured = parsed.model_dump()
        else:
            text = self._provider.generate(req.prompt, req.system_instruction)
            structured = None
        elapsed = int((time.perf_counter() - t0) * 1000)
        return ModelResponse(
            text=text,
            structured=structured,
            provider=self.name,
            model=req.preferred_model or self.default_model,
            latency_ms=elapsed,
        )


class GroqAdapter(ProviderAdapter):
    """Envuelve GroqProvider existente."""

    name = "groq"
    cost_class = "cheap"

    def __init__(self) -> None:
        from .provider import GroqProvider
        from ...infrastructure.config.settings import settings

        self.default_model = settings.groq_model
        self._provider = None
        try:
            self._provider = GroqProvider()
        except Exception:
            self._provider = None

    def is_available(self) -> bool:
        return self._provider is not None

    def generate(self, req: ModelRequest) -> ModelResponse:
        if self._provider is None:
            raise RuntimeError("groq no disponible (falta API key)")
        t0 = time.perf_counter()
        if req.response_schema:
            from pydantic import create_model
            schema = req.response_schema
            fields = {k: (Any, None) for k in schema.get("properties", {})} or {"result": (Any, None)}
            Dyn = create_model("DynLLMOutput", **fields)
            parsed = self._provider.generate_structured(req.prompt, Dyn, req.system_instruction)
            text = parsed.model_dump_json()
            structured = parsed.model_dump()
        else:
            text = self._provider.generate(req.prompt, req.system_instruction)
            structured = None
        elapsed = int((time.perf_counter() - t0) * 1000)
        return ModelResponse(
            text=text,
            structured=structured,
            provider=self.name,
            model=req.preferred_model or self.default_model,
            latency_ms=elapsed,
        )


class _OpenAICompatibleAdapter(ProviderAdapter):
    """Adapter generico para APIs OpenAI-compatible (XAI, OpenRouter, HF).

    No realiza llamadas reales todavia. Falla con mensaje claro si no
    hay credenciales. Cuando se active, se rellena el metodo _call.
    """

    def __init__(self, name: str, api_key: Optional[str], base_url: str, model: str, cost_class: str = "medium") -> None:
        self.name = name
        self._api_key = api_key
        self._base_url = base_url
        self.default_model = model
        self.cost_class = cost_class

    def is_available(self) -> bool:
        return bool(self._api_key)

    def generate(self, req: ModelRequest) -> ModelResponse:
        if not self._api_key:
            raise RuntimeError(f"{self.name} sin API key configurada")
        raise NotImplementedError(
            f"Adapter {self.name}: implementacion HTTP pendiente (bloque 0.3)"
        )


def build_default_adapters() -> List[ProviderAdapter]:
    """Construye los adapters por defecto desde settings."""
    from ...infrastructure.config.settings import settings

    return [
        GeminiAdapter(),
        GroqAdapter(),
        _OpenAICompatibleAdapter(
            name="xai",
            api_key=settings.xai_api_key,
            base_url=settings.xai_base_url,
            model=settings.xai_model,
            cost_class="medium",
        ),
        _OpenAICompatibleAdapter(
            name="openrouter",
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=settings.openrouter_model,
            cost_class="medium",
        ),
        _OpenAICompatibleAdapter(
            name="huggingface",
            api_key=settings.hf_api_key,
            base_url=settings.hf_base_url,
            model=settings.hf_model,
            cost_class="cheap",
        ),
    ]


# ---------------------------------------------------------------------------
# ModelRouter
# ---------------------------------------------------------------------------


class ModelRouter:
    """Enruta a multiples proveedores con fallback y cache."""

    def __init__(self, adapters: Optional[List[ProviderAdapter]] = None, cache_size: int = 256) -> None:
        self._adapters: List[ProviderAdapter] = list(adapters) if adapters is not None else build_default_adapters()
        self._cache_size = cache_size
        self._cache: Dict[str, ModelResponse] = {}

    def register(self, adapter: ProviderAdapter) -> None:
        """Anade un adapter al final del orden de fallback."""
        self._adapters.append(adapter)

    def available(self) -> List[str]:
        return [a.name for a in self._adapters if a.is_available()]

    @staticmethod
    def _cache_key(req: ModelRequest) -> str:
        raw = "|".join([
            req.prompt or "",
            req.system_instruction or "",
            str(req.response_schema or ""),
            str(req.temperature),
            req.preferred_model or "",
        ])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _ordered(self, req: ModelRequest) -> List[ProviderAdapter]:
        """Ordena adapters: preferencia > cost_hint > orden natural."""
        disponibles = [a for a in self._adapters if a.is_available()]
        if req.preferred_model:
            matches = [a for a in disponibles if a.default_model == req.preferred_model or req.preferred_model == a.name]
            others = [a for a in disponibles if a not in matches]
            return matches + others
        if req.cost_hint in ("cheap", "medium", "expensive"):
            return sorted(disponibles, key=lambda a: abs(self._rank(a.cost_class) - self._rank(req.cost_hint)))
        return disponibles

    @staticmethod
    def _rank(cost_class: str) -> int:
        return {"cheap": 0, "medium": 1, "expensive": 2}.get(cost_class, 1)

    def generate(self, req: ModelRequest) -> ModelResponse:
        key = self._cache_key(req)
        if key in self._cache:
            hit = self._cache[key]
            return hit.model_copy(update={"cache_hit": True})

        ordered = self._ordered(req)
        if not ordered:
            raise RuntimeError("ModelRouter: ningun proveedor disponible")

        last_error: Optional[Exception] = None
        for idx, adapter in enumerate(ordered):
            try:
                resp = adapter.generate(req)
                if idx > 0:
                    resp = resp.model_copy(update={"fallback_used": True})
                self._cache[key] = resp
                if len(self._cache) > self._cache_size:
                    self._cache.pop(next(iter(self._cache)))
                return resp
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue

        raise RuntimeError(f"ModelRouter: todos los proveedores fallaron ({last_error})")


_singleton: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Singleton por proceso."""
    global _singleton
    if _singleton is None:
        _singleton = ModelRouter()
    return _singleton


__all__ = [
    "ModelRequest", "ModelResponse", "ProviderAdapter",
    "MockAdapter", "GeminiAdapter", "GroqAdapter",
    "build_default_adapters", "ModelRouter", "get_model_router",
]

