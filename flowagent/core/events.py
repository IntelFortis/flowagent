"""
Events - Event system for FlowAgent.

This module provides the event system for workflow and task lifecycle events.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

from flowagent.core.logger import logger


class EventType(Enum):
    """Types of events in FlowAgent."""
    # Workflow events
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    WORKFLOW_CANCELLED = "workflow_cancelled"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"

    # Task events
    TASK_START = "task_start"
    TASK_COMPLETE = "task_complete"
    TASK_ERROR = "task_error"
    TASK_RETRY = "task_retry"

    # Agent events
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"
    AGENT_ERROR = "agent_error"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTING = "agent_acting"

    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """Represents an event in the system."""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    timestamp: Optional[float] = None

    def __post_init__(self):
        import time
        if self.timestamp is None:
            self.timestamp = time.time()


class EventEmitter:
    """
    Event emitter for FlowAgent.

    Provides pub/sub functionality for workflow and task events.

    Example:
        >>> emitter = EventEmitter()
        >>> emitter.on("task_complete", lambda data: print(data))
        >>> emitter.emit(EventType.TASK_COMPLETE, {"task": "my-task"})
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._once_listeners: Dict[str, List[Callable]] = {}

    def on(self, event: str, callback: Callable) -> "EventEmitter":
        """
        Register an event listener.

        Args:
            event: Event name
            callback: Callback function

        Returns:
            Self for chaining
        """
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)
        return self

    def once(self, event: str, callback: Callable) -> "EventEmitter":
        """
        Register a one-time event listener.

        Args:
            event: Event name
            callback: Callback function

        Returns:
            Self for chaining
        """
        if event not in self._once_listeners:
            self._once_listeners[event] = []
        self._once_listeners[event].append(callback)
        return self

    def off(self, event: str, callback: Optional[Callable] = None) -> "EventEmitter":
        """
        Remove an event listener.

        Args:
            event: Event name
            callback: Specific callback to remove, or None to remove all

        Returns:
            Self for chaining
        """
        if callback is None:
            self._listeners.pop(event, None)
            self._once_listeners.pop(event, None)
        else:
            if event in self._listeners:
                self._listeners[event] = [
                    cb for cb in self._listeners[event]
                    if cb != callback
                ]
            if event in self._once_listeners:
                self._once_listeners[event] = [
                    cb for cb in self._once_listeners[event]
                    if cb != callback
                ]
        return self

    def emit(self, event: Union[str, EventType], data: Optional[Dict[str, Any]] = None) -> None:
        """
        Emit an event.

        Args:
            event: Event name or type
            data: Event data
        """
        event_name = event.value if isinstance(event, EventType) else event
        event_data = data or {}

        logger.debug(f"Event emitted: {event_name}")

        # Call regular listeners
        for callback in self._listeners.get(event_name, []):
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

        # Call once listeners
        for callback in self._once_listeners.get(event_name, []):
            try:
                callback(event_data)
            except Exception as e:
                logger.error(f"Event listener error: {e}")

        # Clear once listeners
        self._once_listeners.pop(event_name, None)

    def listeners(self, event: str) -> List[Callable]:
        """Get all listeners for an event."""
        return self._listeners.get(event, []).copy()

    def listener_count(self, event: str) -> int:
        """Get the number of listeners for an event."""
        return len(self._listeners.get(event, []))

    def event_names(self) -> List[str]:
        """Get all registered event names."""
        return list(self._listeners.keys())


