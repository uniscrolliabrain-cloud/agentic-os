from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel

from ...infrastructure.config.settings import Settings

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers in Agentic OS."""

    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generates a text response from the model."""
        pass

    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
    ) -> T:
        """Generates a structured response adhering to a Pydantic schema."""
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
            # Client can still initialize with GEMINI_API_KEY environment variable if present
            self.client = genai.Client()
        else:
            self.client = genai.Client(api_key=self.api_key)

        self._types = types

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        config = self._types.GenerateContentConfig(
            temperature=self.temperature,
            system_instruction=system_instruction,
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
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
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        if not response.text:
            raise ValueError("Gemini returned empty response")

        # Parse and validate with Pydantic
        return response_schema.model_validate_json(response.text)


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


# Backwards compatibility alias
LLMProvider = BaseLLMProvider
