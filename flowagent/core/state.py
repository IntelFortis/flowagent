"""
State - State management for FlowAgent workflows.

This module provides the State class for managing workflow state,
including persistence, serialization, and history tracking.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic, Union
from pathlib import Path

from flowagent.core.logger import logger

T = TypeVar("T")


class StateStatus(Enum):
    """Status of the state manager."""
    IDLE = "idle"
    UPDATING = "updating"
    PERSISTING = "persisting"
    ERROR = "error"


@dataclass
class StateSnapshot:
    """A snapshot of state at a point in time."""
    timestamp: float
    data: Dict[str, Any]
    version: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class State:
    """
    State management for FlowAgent workflows.

    The State class provides a thread-safe, versioned state store with
    support for persistence, history, and change notifications.

    Example:
        >>> state = State()
        >>> state.set("counter", 0)
        >>> state.update("counter", lambda x: x + 1)
        >>> print(state.get("counter"))  # 1
    """

    def __init__(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        max_history: int = 100,
        auto_persist: bool = False,
        persist_path: Optional[Path] = None,
        snapshot_interval: int = 1,
    ):
        self._data: Dict[str, Any] = initial_data or {}
        self._version: int = 0
        self._max_history = max_history
        self._history: List[StateSnapshot] = []
        self._status = StateStatus.IDLE
        self._auto_persist = auto_persist
        self._persist_path = persist_path
        self._snapshot_interval = max(1, snapshot_interval)
        self._listeners: List[Callable[[str, Any, Any], None]] = []
        self._created_at = time.time()
        self._updated_at = time.time()

        # Save initial state
        self._save_snapshot()

        logger.debug("State manager initialized")

    @property
    def version(self) -> int:
        """Get the current state version."""
        return self._version

    @property
    def status(self) -> StateStatus:
        """Get the current state status."""
        return self._status

    @property
    def data(self) -> Dict[str, Any]:
        """Get a copy of the current state data."""
        return self._data.copy()

    @property
    def history(self) -> List[StateSnapshot]:
        """Get the state history."""
        return self._history.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the state.

        Args:
            key: The key to look up
            default: Default value if key not found

        Returns:
            The value, or default if not found
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the state.

        Args:
            key: The key to set
            value: The value to set
        """
        old_value = self._data.get(key)
        self._data[key] = value
        self._version += 1
        self._updated_at = time.time()

        # Notify listeners
        self._notify_listeners(key, old_value, value)

        # Save snapshot
        self._save_snapshot()

        # Auto-persist if enabled
        if self._auto_persist:
            self.persist()

        logger.debug(f"State: set '{key}' (version {self._version})")

    def update(self, key: str, updater: Callable[[Any], Any]) -> None:
        """
        Update a value using a function.

        Args:
            key: The key to update
            updater: Function that takes current value and returns new value
        """
        current = self.get(key)
        new_value = updater(current)
        self.set(key, new_value)

    def delete(self, key: str) -> bool:
        """
        Delete a value from the state.

        Args:
            key: The key to delete

        Returns:
            True if the key was deleted
        """
        if key in self._data:
            old_value = self._data[key]
            del self._data[key]
            self._version += 1
            self._updated_at = time.time()

            # Notify listeners
            self._notify_listeners(key, old_value, None)

            # Save snapshot
            self._save_snapshot()

            logger.debug(f"State: deleted '{key}' (version {self._version})")
            return True
        return False

    def has(self, key: str) -> bool:
        """Check if a key exists in the state."""
        return key in self._data

    def keys(self) -> List[str]:
        """Get all keys in the state."""
        return list(self._data.keys())

    def values(self) -> Dict[str, Any]:
        """Get all key-value pairs in the state."""
        return self._data.copy()

    def update_many(self, data: Dict[str, Any]) -> None:
        """
        Update multiple values at once.

        Args:
            data: Dictionary of key-value pairs to update
        """
        for key, value in data.items():
            self.set(key, value)

    def clear(self) -> None:
        """Clear all data in the state."""
        self._data.clear()
        self._version += 1
        self._updated_at = time.time()
        self._save_snapshot(force=True)
        logger.debug("State: cleared")

    def on_change(self, listener: Callable[[str, Any, Any], None]) -> None:
        """
        Register a change listener.

        Args:
            listener: Function(key, old_value, new_value)
        """
        self._listeners.append(listener)

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify all listeners of a change."""
        for listener in self._listeners:
            try:
                listener(key, old_value, new_value)
            except Exception as e:
                logger.error(f"State listener error: {e}")

    def _save_snapshot(self, force: bool = False) -> None:
        """Save a snapshot of the current state.

        Args:
            force: If True, save regardless of interval
        """
        if not force and self._version % self._snapshot_interval != 0:
            return

        snapshot = StateSnapshot(
            timestamp=time.time(),
            data=self._data.copy(),
            version=self._version,
        )
        self._history.append(snapshot)

        # Trim history if needed
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_snapshot(self, version: Optional[int] = None) -> Optional[StateSnapshot]:
        """
        Get a state snapshot.

        Args:
            version: Specific version to get, or None for latest

        Returns:
            StateSnapshot or None if not found
        """
        if version is None:
            return self._history[-1] if self._history else None

        for snapshot in self._history:
            if snapshot.version == version:
                return snapshot
        return None

    def rollback(self, version: int) -> bool:
        """
        Rollback to a specific version.

        Args:
            version: Version to rollback to

        Returns:
            True if rollback was successful
        """
        snapshot = self.get_snapshot(version)
        if snapshot:
            self._data = snapshot.data.copy()
            self._version = version
            self._updated_at = time.time()
            self._save_snapshot(force=True)
            logger.info(f"State: rolled back to version {version}")
            return True
        return False

    def persist(self, path: Optional[Path] = None) -> None:
        """
        Persist state to disk.

        Args:
            path: Path to persist to, or None to use default
        """
        persist_path = path or self._persist_path
        if not persist_path:
            logger.warning("State: no persist path configured")
            return

        self._status = StateStatus.PERSISTING

        try:
            persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "version": self._version,
                "data": self._data,
                "updated_at": self._updated_at,
                "metadata": {
                    "created_at": self._created_at,
                    "snapshot_count": len(self._history),
                },
            }
            persist_path.write_text(json.dumps(data, indent=2, default=str))
            logger.debug(f"State: persisted to {persist_path}")

        except Exception as e:
            self._status = StateStatus.ERROR
            logger.error(f"State: persist failed: {e}")
            raise

        finally:
            self._status = StateStatus.IDLE

    @classmethod
    def load(cls, path: Path) -> "State":
        """
        Load state from disk.

        Args:
            path: Path to load from

        Returns:
            State instance
        """
        try:
            data = json.loads(path.read_text())
            state = cls(
                initial_data=data.get("data", {}),
                persist_path=path,
            )
            state._version = data.get("version", 0)
            state._updated_at = data.get("updated_at", time.time())
            logger.debug(f"State: loaded from {path}")
            return state

        except Exception as e:
            logger.error(f"State: load failed: {e}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "version": self._version,
            "data": self._data,
            "updated_at": self._updated_at,
            "snapshot_count": len(self._history),
        }

    def to_json(self) -> str:
        """Convert state to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def __repr__(self) -> str:
        return f"State(version={self._version}, keys={len(self._data)})"

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(key)
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        if not self.delete(key):
            raise KeyError(key)
