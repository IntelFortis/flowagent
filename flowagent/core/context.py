"""
Context - Execution context for FlowAgent tasks.

This module provides the Context class that carries state and configuration
throughout task execution.
"""

from __future__ import annotations

import asyncio
import copy
import threading
from typing import Any, Dict, Optional, TypeVar, Generic, List, Set
from datetime import datetime, timedelta

from flowagent.core.logger import logger

T = TypeVar("T")


class Context:
    """
    Execution context for FlowAgent tasks.

    The Context provides a thread-safe container for passing data between
    tasks, managing configuration, and tracking execution state.

    Example:
        >>> ctx = Context()
        >>> ctx.set("user_id", "123")
        >>> user_id = ctx.get("user_id")
    """

    def __init__(self, parent: Optional["Context"] = None, max_log_size: int = 1000):
        self._data: Dict[str, Any] = {}
        self._parent = parent
        self._lock = threading.Lock()
        self._metadata: Dict[str, Any] = {}
        self._created_at = datetime.now()
        self._access_log: List[Dict[str, Any]] = []
        self._max_log_size = max_log_size

    @property
    def created_at(self) -> datetime:
        """Get the context creation time."""
        return self._created_at

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the context.

        Args:
            key: The key to look up
            default: Default value if key not found

        Returns:
            The value, or default if not found
        """
        with self._lock:
            # Check local data first
            if key in self._data:
                self._log_access(key, "get")
                return self._data[key]

            # Check parent context
            if self._parent:
                return self._parent.get(key, default)

            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the context.

        Args:
            key: The key to set
            value: The value to set
        """
        with self._lock:
            self._data[key] = value
            self._log_access(key, "set")
            logger.debug(f"Context: set '{key}'")

    def delete(self, key: str) -> bool:
        """
        Delete a value from the context.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted, False if not found
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._log_access(key, "delete")
                logger.debug(f"Context: deleted '{key}'")
                return True
            return False

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if the key exists
        """
        with self._lock:
            if key in self._data:
                return True
            if self._parent:
                return self._parent.has(key)
            return False

    def keys(self) -> Set[str]:
        """Get all keys in the context."""
        with self._lock:
            keys = set(self._data.keys())
            if self._parent:
                keys.update(self._parent.keys())
            return keys

    def values(self) -> Dict[str, Any]:
        """Get all key-value pairs in the context."""
        with self._lock:
            result = {}
            if self._parent:
                result.update(self._parent.values())
            result.update(self._data)
            return result

    def items(self) -> Dict[str, Any]:
        """Get all key-value pairs (alias for values)."""
        return self.values()

    def update(self, data: Dict[str, Any]) -> None:
        """
        Update context with multiple key-value pairs.

        Args:
            data: Dictionary of key-value pairs to add
        """
        with self._lock:
            self._data.update(data)
            logger.debug(f"Context: updated with {len(data)} keys")

    def clear(self) -> None:
        """Clear all data in the context."""
        with self._lock:
            self._data.clear()
            logger.debug("Context: cleared")

    def clone(self) -> "Context":
        """
        Create a shallow clone of the context.

        Returns:
            New Context with copied data
        """
        with self._lock:
            new_ctx = Context(parent=self._parent)
            new_ctx._data = copy.copy(self._data)
            new_ctx._metadata = copy.copy(self._metadata)
            return new_ctx

    def merge(self, other: "Context") -> "Context":
        """
        Merge another context into this one.

        Args:
            other: Context to merge from

        Returns:
            Self for chaining
        """
        with self._lock:
            self._data.update(other._data)
            self._metadata.update(other._metadata)
            return self

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        with self._lock:
            self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value.

        Args:
            key: Metadata key
            default: Default value if not found

        Returns:
            Metadata value
        """
        with self._lock:
            return self._metadata.get(key, default)

    def _log_access(self, key: str, operation: str) -> None:
        """Log context access for debugging."""
        self._access_log.append({
            "key": key,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
        })
        if len(self._access_log) > self._max_log_size:
            self._access_log = self._access_log[-self._max_log_size:]

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get the context access log."""
        return self._access_log

    def __getitem__(self, key: str) -> Any:
        """Get item using bracket notation."""
        result = self.get(key)
        if result is None and not self.has(key):
            raise KeyError(key)
        return result

    def __setitem__(self, key: str, value: Any) -> None:
        """Set item using bracket notation."""
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        """Delete item using bracket notation."""
        if not self.delete(key):
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Check if key exists using 'in' operator."""
        return self.has(key)

    def __len__(self) -> int:
        """Get the number of items in the context."""
        return len(self.keys())

    def __repr__(self) -> str:
        return f"Context(keys={len(self)}, metadata={len(self._metadata)})"

    def __str__(self) -> str:
        return f"Context({len(self)} items)"


class AsyncContext(Context):
    """
    Async-safe context for FlowAgent tasks.

    This context uses asyncio locks for thread-safety in async environments.
    """

    def __init__(self, parent: Optional["AsyncContext"] = None):
        super().__init__(parent)
        self._async_lock = asyncio.Lock()

    async def async_get(self, key: str, default: Any = None) -> Any:
        """Async version of get."""
        async with self._async_lock:
            return self.get(key, default)

    async def async_set(self, key: str, value: Any) -> None:
        """Async version of set."""
        async with self._async_lock:
            self.set(key, value)

    async def async_delete(self, key: str) -> bool:
        """Async version of delete."""
        async with self._async_lock:
            return self.delete(key)
