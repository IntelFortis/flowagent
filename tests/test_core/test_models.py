"""Tests for ModelRegistry."""

import json
import tempfile
from pathlib import Path

from flowagent.core.models import ModelRegistry, get_registry, set_registry


class TestModelRegistry:
    def test_create_registry(self):
        registry = ModelRegistry()
        assert len(registry.list_aliases()) == 0
        assert len(registry.list_defaults()) == 0

    def test_register_alias(self):
        registry = ModelRegistry()
        registry.register_alias("my-gpt", "gpt-5.5", provider="openai")
        assert registry.has_alias("my-gpt")
        assert registry.get_model("my-gpt") == "gpt-5.5"

    def test_resolve_alias(self):
        registry = ModelRegistry()
        registry.register_alias("my-gpt", "gpt-5.5", provider="openai")
        result = registry.resolve("my-gpt")
        assert result["model"] == "gpt-5.5"
        assert result["provider"] == "openai"

    def test_resolve_unknown_passthrough(self):
        registry = ModelRegistry()
        result = registry.resolve("gpt-5.5")
        assert result == {"model": "gpt-5.5"}

    def test_get_model_unknown_passthrough(self):
        registry = ModelRegistry()
        assert registry.get_model("gpt-5.5") == "gpt-5.5"
        assert registry.get_model("some-random-model") == "some-random-model"

    def test_unregister_alias(self):
        registry = ModelRegistry()
        registry.register_alias("my-gpt", "gpt-5.5")
        assert registry.unregister_alias("my-gpt") is True
        assert not registry.has_alias("my-gpt")

    def test_unregister_nonexistent(self):
        registry = ModelRegistry()
        assert registry.unregister_alias("nonexistent") is False

    def test_set_default(self):
        registry = ModelRegistry()
        registry.set_default("openai", "gpt-5.5")
        assert registry.get_default("openai") == "gpt-5.5"

    def test_get_default_none(self):
        registry = ModelRegistry()
        assert registry.get_default("openai") is None

    def test_register_with_extra_kwargs(self):
        registry = ModelRegistry()
        registry.register_alias(
            "local-llama",
            "meta-llama/Llama-3-70B",
            provider="openai",
            api_base="http://localhost:8000/v1",
        )
        result = registry.resolve("local-llama")
        assert result["model"] == "meta-llama/Llama-3-70B"
        assert result["api_base"] == "http://localhost:8000/v1"

    def test_save_and_load_config(self, tmp_path):
        config_path = tmp_path / "models.json"

        # Save
        registry = ModelRegistry(config_path=config_path)
        registry.register_alias("my-gpt", "gpt-5.5", provider="openai")
        registry.set_default("openai", "gpt-5.5")
        assert config_path.exists()

        # Load in new registry
        registry2 = ModelRegistry(config_path=config_path)
        assert registry2.has_alias("my-gpt")
        assert registry2.get_model("my-gpt") == "gpt-5.5"
        assert registry2.get_default("openai") == "gpt-5.5"

    def test_auto_save_on_register(self, tmp_path):
        config_path = tmp_path / "models.json"
        registry = ModelRegistry(config_path=config_path)
        registry.register_alias("test", "gpt-5.5")
        data = json.loads(config_path.read_text())
        assert "test" in data["aliases"]

    def test_auto_save_on_set_default(self, tmp_path):
        config_path = tmp_path / "models.json"
        registry = ModelRegistry(config_path=config_path)
        registry.set_default("openai", "gpt-5.5")
        data = json.loads(config_path.read_text())
        assert data["defaults"]["openai"] == "gpt-5.5"

    def test_auto_save_on_unregister(self, tmp_path):
        config_path = tmp_path / "models.json"
        registry = ModelRegistry(config_path=config_path)
        registry.register_alias("test", "gpt-5.5")
        registry.unregister_alias("test")
        data = json.loads(config_path.read_text())
        assert "test" not in data["aliases"]

    def test_repr(self):
        registry = ModelRegistry()
        registry.register_alias("a", "b")
        registry.set_default("c", "d")
        r = repr(registry)
        assert "aliases=1" in r
        assert "defaults=1" in r


class TestGlobalRegistry:
    def test_get_registry_singleton(self):
        # Reset global
        set_registry(None)
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_set_registry(self):
        custom = ModelRegistry()
        custom.register_alias("test", "model")
        set_registry(custom)
        assert get_registry().has_alias("test")
        # Reset
        set_registry(None)
