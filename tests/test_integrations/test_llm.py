"""Tests for LLM integrations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from flowagent.integrations.llm import (
    LLMConfig,
    LLMMessage,
    LLMResponse,
    OpenAI,
    Anthropic,
    OpenAICompatible,
    _resolve_model,
)
from flowagent.core.models import ModelRegistry, set_registry, get_registry


class TestLLMConfig:
    def test_default_config(self):
        config = LLMConfig(model="test-model")
        assert config.model == "test-model"
        assert config.temperature == 0.7
        assert config.max_tokens == 4096
        assert config.api_key is None
        assert config.api_base is None

    def test_custom_config(self):
        config = LLMConfig(
            model="gpt-5.5",
            temperature=0.5,
            max_tokens=8192,
            api_key="sk-test",
            api_base="http://localhost:8000/v1",
        )
        assert config.model == "gpt-5.5"
        assert config.temperature == 0.5
        assert config.max_tokens == 8192
        assert config.api_key == "sk-test"
        assert config.api_base == "http://localhost:8000/v1"


class TestLLMMessage:
    def test_create_message(self):
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None
        assert msg.tool_call_id is None

    def test_create_system_message(self):
        msg = LLMMessage(role="system", content="You are helpful")
        assert msg.role == "system"


class TestLLMResponse:
    def test_create_response(self):
        resp = LLMResponse(content="Hi", model="test")
        assert resp.content == "Hi"
        assert resp.model == "test"
        assert resp.usage == {}
        assert resp.tool_calls is None

    def test_response_with_usage(self):
        resp = LLMResponse(
            content="Hi",
            model="test",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert resp.usage["total_tokens"] == 15


class TestResolveModel:
    def test_passthrough_unknown(self):
        result = _resolve_model("gpt-5.5")
        assert result == "gpt-5.5"

    def test_resolve_alias(self):
        registry = ModelRegistry()
        registry.register_alias("my-gpt", "gpt-5.5")
        set_registry(registry)
        result = _resolve_model("my-gpt")
        assert result == "gpt-5.5"
        set_registry(None)

    def test_passthrough_on_registry_error(self):
        set_registry(None)
        result = _resolve_model("any-model")
        assert result == "any-model"


class TestOpenAIProvider:
    def test_init_requires_openai_package(self):
        with patch.dict("sys.modules", {"openai": None}):
            with pytest.raises(Exception, match="not installed"):
                OpenAI(model="gpt-5.5")

    def test_model_resolution(self):
        registry = ModelRegistry()
        registry.register_alias("fast", "gpt-4o")
        set_registry(registry)
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import openai
            openai.AsyncOpenAI = MagicMock()
            llm = OpenAI(model="fast")
            assert llm.config.model == "gpt-4o"
        set_registry(None)


class TestOpenAICompatibleProvider:
    def test_requires_api_base(self):
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import openai
            openai.AsyncOpenAI = MagicMock()
            with pytest.raises(Exception, match="api_base is required"):
                OpenAICompatible(model="test")

    def test_init_with_api_base(self):
        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import openai
            mock_client = MagicMock()
            openai.AsyncOpenAI = MagicMock(return_value=mock_client)
            llm = OpenAICompatible(
                model="test-model",
                api_base="http://localhost:8000/v1",
            )
            assert llm.config.model == "test-model"
            assert llm.config.api_base == "http://localhost:8000/v1"
