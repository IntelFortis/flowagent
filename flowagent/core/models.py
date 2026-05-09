"""
Models - Model registry and configuration for FlowAgent.

This module provides a flexible model registry that allows users to:
1. Use any model name directly (pass-through to API)
2. Register custom model aliases
3. Persist model configurations via config files
4. Share model configs across workflows
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from flowagent.core.logger import logger


class ModelRegistry:
    """
    Global model registry for managing model aliases and configurations.

    The registry does NOT restrict which models can be used. Any model name
    is passed through to the API directly. The registry only provides
    convenience aliases and default configurations.

    Example:
        >>> registry = ModelRegistry()
        >>>
        >>> # Register a custom alias
        >>> registry.register_alias("my-gpt", "gpt-5.5", provider="openai")
        >>>
        >>> # Use it
        >>> resolved = registry.resolve("my-gpt")
        >>> # -> {"model": "gpt-5.5", "provider": "openai"}
        >>>
        >>> # Register a self-hosted model
        >>> registry.register_alias(
        ...     "local-llama",
        ...     "meta-llama/Llama-3-70B",
        ...     provider="openai",
        ...     api_base="http://localhost:8000/v1",
        ... )
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the model registry.

        Args:
            config_path: Optional path to a JSON config file for persistence
        """
        self._aliases: Dict[str, Dict[str, Any]] = {}
        self._defaults: Dict[str, str] = {}  # provider -> default model
        self._config_path = config_path

        # Load config if exists
        if config_path and config_path.exists():
            self._load_config()

        logger.debug("Model registry initialized")

    def register_alias(
        self,
        alias: str,
        model: str,
        provider: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Register a model alias.

        Args:
            alias: The alias name (e.g., "my-gpt", "local-llama")
            model: The actual model name to use (e.g., "gpt-5.5")
            provider: Optional provider name (e.g., "openai", "anthropic")
            **kwargs: Additional configuration (api_base, api_key, etc.)
        """
        self._aliases[alias] = {
            "model": model,
            "provider": provider,
            **kwargs,
        }
        logger.info(f"Registered model alias: {alias} -> {model}")

        # Auto-save if config path is set
        if self._config_path:
            self._save_config()

    def unregister_alias(self, alias: str) -> bool:
        """
        Remove a model alias.

        Args:
            alias: The alias to remove

        Returns:
            True if removed, False if not found
        """
        if alias in self._aliases:
            del self._aliases[alias]
            logger.info(f"Unregistered model alias: {alias}")

            if self._config_path:
                self._save_config()
            return True
        return False

    def resolve(self, name: str) -> Dict[str, Any]:
        """
        Resolve a model name or alias.

        If the name is a registered alias, returns the alias configuration.
        Otherwise, returns the name as-is (pass-through).

        Args:
            name: Model name or alias

        Returns:
            Dictionary with "model" key and optional additional config
        """
        if name in self._aliases:
            return self._aliases[name].copy()

        # Pass-through: use the name directly
        return {"model": name}

    def get_model(self, name: str) -> str:
        """
        Get the actual model name for a given name or alias.

        Args:
            name: Model name or alias

        Returns:
            Actual model name
        """
        return self.resolve(name).get("model", name)

    def set_default(self, provider: str, model: str) -> None:
        """
        Set the default model for a provider.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            model: Default model name
        """
        self._defaults[provider] = model
        logger.info(f"Default model for {provider}: {model}")

        if self._config_path:
            self._save_config()

    def get_default(self, provider: str) -> Optional[str]:
        """
        Get the default model for a provider.

        Args:
            provider: Provider name

        Returns:
            Default model name, or None if not set
        """
        return self._defaults.get(provider)

    def list_aliases(self) -> Dict[str, Dict[str, Any]]:
        """List all registered aliases."""
        return self._aliases.copy()

    def list_defaults(self) -> Dict[str, str]:
        """List all provider defaults."""
        return self._defaults.copy()

    def has_alias(self, alias: str) -> bool:
        """Check if an alias exists."""
        return alias in self._aliases

    def _save_config(self) -> None:
        """Save configuration to file."""
        if not self._config_path:
            return

        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                "aliases": self._aliases,
                "defaults": self._defaults,
            }
            self._config_path.write_text(
                json.dumps(config, indent=2, ensure_ascii=False)
            )
            logger.debug(f"Model config saved to {self._config_path}")
        except Exception as e:
            logger.error(f"Failed to save model config: {e}")

    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self._config_path:
            return

        try:
            config = json.loads(self._config_path.read_text())
            self._aliases = config.get("aliases", {})
            self._defaults = config.get("defaults", {})
            logger.debug(
                f"Model config loaded: {len(self._aliases)} aliases, "
                f"{len(self._defaults)} defaults"
            )
        except Exception as e:
            logger.error(f"Failed to load model config: {e}")

    def __repr__(self) -> str:
        return (
            f"ModelRegistry(aliases={len(self._aliases)}, "
            f"defaults={len(self._defaults)})"
        )


# Global registry instance
_global_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """
    Get the global model registry.

    Returns:
        Global ModelRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        # Try to load from default config path
        default_path = Path.home() / ".flowagent" / "models.json"
        _global_registry = ModelRegistry(config_path=default_path)
    return _global_registry


def set_registry(registry: ModelRegistry) -> None:
    """
    Set the global model registry.

    Args:
        registry: ModelRegistry instance to use globally
    """
    global _global_registry
    _global_registry = registry
