import pytest
from pydantic import BaseModel
from agentic_os.interfaces.llm.provider import MockLLMProvider, BaseLLMProvider


class SampleSchema(BaseModel):
    name: str
    score: int


def test_mock_llm_provider_text_generation():
    provider = MockLLMProvider(default_response="Hello, world!")
    response = provider.generate("Test prompt", system_instruction="Be helpful")
    assert response == "Hello, world!"
    assert provider.last_prompt == "Test prompt"
    assert provider.last_system_instruction == "Be helpful"


def test_mock_llm_provider_structured_generation():
    provider = MockLLMProvider(default_response='{"name": "test_agent", "score": 100}')
    result = provider.generate_structured("Generate sample", SampleSchema)
    assert isinstance(result, SampleSchema)
    assert result.name == "test_agent"
    assert result.score == 100


def test_mock_llm_provider_with_explicit_structured_response():
    expected = SampleSchema(name="explicit_agent", score=42)
    provider = MockLLMProvider(structured_response=expected)
    result = provider.generate_structured("Generate sample", SampleSchema)
    assert result == expected
