from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel

from ...infrastructure.config.settings import Settings

T = TypeVar("T", bound=BaseModel)
log = logging.getLogger("agentic_os.llm")


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in Agentic OS."""

    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        pass


class GeminiProvider(BaseLLMProvider):
    """Gemini LLM provider using the modern google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        from google import genai
        from google.genai import types

        settings = Settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model or settings.gemini_model
        self.temperature = (
            temperature if temperature is not None else settings.gemini_temperature
        )

        if not self.api_key:
            self.client = genai.Client(http_options=types.HttpOptions(timeout=45_000))
        else:
            self.client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=45_000),
            )

        self._types = types

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        config = self._types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
        )
        response = self._call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        )
        return response.text or ""

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        config = self._types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
        response = self._call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        )
        if not response.text:
            raise ValueError("Gemini returned empty response")
        return response_schema.model_validate_json(response.text)

    def _call_with_retry(self, fn, attempts: int = 2) -> Any:
        last_exc: Optional[Exception] = None
        for i in range(attempts):
            try:
                return fn()
            except Exception as e:
                last_exc = e
                message = str(e).lower()
                transient = any(
                    token in message
                    for token in (
                        "timeout",
                        "timed out",
                        "429",
                        "rate limit",
                        "resource_exhausted",
                        "unavailable",
                        "502",
                        "503",
                        "504",
                        "internal error",
                        "connection",
                    )
                )
                if not transient or i == attempts - 1:
                    break
                import time
                time.sleep(1.5)
        raise RuntimeError(
            f"Gemini no respondió correctamente ({self.model_name}): {last_exc}"
        ) from last_exc


class GroqProvider(BaseLLMProvider):
    """Groq fallback provider - OpenAI compatible, muy rápido y barato."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        settings = Settings()
        # Usa tu Settings (añade GROQ_API_KEY en settings.py)
        self.api_key = api_key or getattr(settings, 'groq_api_key', None) or getattr(settings, 'GROQ_API_KEY', None)
        self.model_name = model or getattr(settings, 'groq_model', 'llama-3.3-70b-versatile')
        self.temperature = temperature if temperature is not None else settings.gemini_temperature

        if not self.api_key:
            raise ValueError("GROQ_API_KEY no configurada. Ponla en .env")

        # Groq es OpenAI-compatible
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        except ImportError:
            raise ImportError("Falta 'groq'. Haz pip install groq")

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
        )
        return resp.choices[0].message.content or ""

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        # Forzamos JSON con system prompt
        schema_json = response_schema.model_json_schema()
        json_instruction = f"\n\nDebes responder SOLO con JSON válido que cumpla este schema: {json.dumps(schema_json)}"

        full_system = (system_instruction or "") + json_instruction

        messages = []
        if full_system:
            messages.append({"role": "system", "content": full_system})
        messages.append({"role": "user", "content": prompt})

        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        text = resp.choices[0].message.content or "{}"
        try:
            return response_schema.model_validate_json(text)
        except Exception:
            # Intenta limpiar markdown ```json
            cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return response_schema.model_validate_json(cleaned)


class FallbackLLMProvider(BaseLLMProvider):
    """Intenta Gemini, si falla usa Groq. Mantiene invariantes."""

    def __init__(
        self,
        primary: Optional[BaseLLMProvider] = None,
        fallback: Optional[BaseLLMProvider] = None,
    ):
        settings = Settings()
        # Primary = Gemini
        if primary:
            self.primary = primary
        else:
            try:
                self.primary = GeminiProvider()
            except Exception as e:
                log.warning(f"No se pudo inicializar Gemini: {e}")
                self.primary = None

        # Fallback = Groq
        if fallback:
            self.fallback = fallback
        else:
            try:
                self.fallback = GroqProvider()
                log.info(f"Groq fallback inicializado: {settings.groq_model if hasattr(settings,'groq_model') else 'llama-3.3-70b'}")
            except Exception as e:
                log.warning(f"No se pudo inicializar Groq fallback: {e}")
                self.fallback = None

        if not self.primary and not self.fallback:
            raise RuntimeError("Ni Gemini ni Groq disponibles. Configura al menos uno.")

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        # 1. Intenta primary (Gemini)
        if self.primary:
            try:
                return self.primary.generate(prompt, system_instruction)
            except Exception as e:
                log.warning(f"Gemini falló en generate, usando Groq: {e}")
                # Si no hay fallback, relanza
                if not self.fallback:
                    raise

        # 2. Fallback Groq
        if self.fallback:
            return self.fallback.generate(prompt, system_instruction)

        raise RuntimeError("No hay provider disponible")

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        if self.primary:
            try:
                return self.primary.generate_structured(prompt, response_schema, system_instruction)
            except Exception as e:
                log.warning(f"Gemini falló en structured, usando Groq: {e}")
                if not self.fallback:
                    raise

        if self.fallback:
            return self.fallback.generate_structured(prompt, response_schema, system_instruction)

        raise RuntimeError("No hay provider disponible")


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for offline development and testing."""

    def __init__(self, default_response: str = "{}", structured_response: Optional[BaseModel] = None):
        self.default_response = default_response
        self.structured_response = structured_response
        self.last_prompt: Optional[str] = None
        self.last_system_instruction: Optional[str] = None

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction
        return self.default_response

    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction
        if self.structured_response is not None and isinstance(self.structured_response, response_schema):
            return self.structured_response
        
        try:
            return response_schema.model_validate_json(self.default_response)
        except Exception:
            return response_schema.model_validate({})


# Aliases
LLMProvider = BaseLLMProvider
# Para que tu rest.py y streamlit_app.py no cambien nada, este será el default ahora:
DefaultLLMProvider = FallbackLLMProvider
