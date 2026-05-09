"""Tests for event system."""

from unittest.mock import MagicMock

from flowagent.core.events import EventEmitter, Event, EventType


class TestEventType:
    def test_workflow_events(self):
        assert EventType.WORKFLOW_START.value == "workflow_start"
        assert EventType.WORKFLOW_COMPLETE.value == "workflow_complete"
        assert EventType.WORKFLOW_ERROR.value == "workflow_error"

    def test_task_events(self):
        assert EventType.TASK_START.value == "task_start"
        assert EventType.TASK_COMPLETE.value == "task_complete"
        assert EventType.TASK_ERROR.value == "task_error"

    def test_agent_events(self):
        assert EventType.AGENT_START.value == "agent_start"
        assert EventType.AGENT_COMPLETE.value == "agent_complete"


class TestEvent:
    def test_create_event(self):
        event = Event(type=EventType.TASK_START, data={"task": "test"})
        assert event.type == EventType.TASK_START
        assert event.data == {"task": "test"}
        assert event.timestamp is not None

    def test_event_auto_timestamp(self):
        event = Event(type=EventType.CUSTOM)
        assert event.timestamp is not None


class TestEventEmitter:
    def test_on_and_emit(self):
        emitter = EventEmitter()
        callback = MagicMock()
        emitter.on("test", callback)
        emitter.emit("test", {"key": "value"})
        callback.assert_called_once_with({"key": "value"})

    def test_once(self):
        emitter = EventEmitter()
        callback = MagicMock()
        emitter.once("test", callback)
        emitter.emit("test", {})
        emitter.emit("test", {})
        assert callback.call_count == 1

    def test_off_specific(self):
        emitter = EventEmitter()
        callback = MagicMock()
        emitter.on("test", callback)
        emitter.off("test", callback)
        emitter.emit("test", {})
        callback.assert_not_called()

    def test_off_all(self):
        emitter = EventEmitter()
        cb1 = MagicMock()
        cb2 = MagicMock()
        emitter.on("test", cb1)
        emitter.on("test", cb2)
        emitter.off("test")
        emitter.emit("test", {})
        cb1.assert_not_called()
        cb2.assert_not_called()

    def test_emit_with_event_type(self):
        emitter = EventEmitter()
        callback = MagicMock()
        emitter.on("task_start", callback)
        emitter.emit(EventType.TASK_START, {"task": "test"})
        callback.assert_called_once()

    def test_listeners(self):
        emitter = EventEmitter()
        cb = MagicMock()
        emitter.on("test", cb)
        assert len(emitter.listeners("test")) == 1

    def test_listener_count(self):
        emitter = EventEmitter()
        emitter.on("test", lambda: None)
        emitter.on("test", lambda: None)
        assert emitter.listener_count("test") == 2

    def test_event_names(self):
        emitter = EventEmitter()
        emitter.on("a", lambda: None)
        emitter.on("b", lambda: None)
        names = emitter.event_names()
        assert "a" in names
        assert "b" in names

    def test_chaining(self):
        emitter = EventEmitter()
        result = emitter.on("a", lambda: None)
        assert result is emitter
        result = emitter.off("a")
        assert result is emitter

    def test_callback_error_doesnt_propagate(self):
        emitter = EventEmitter()
        def bad_callback(data):
            raise ValueError("oops")
        emitter.on("test", bad_callback)
        # Should not raise
        emitter.emit("test", {})

    def test_emit_no_listeners(self):
        emitter = EventEmitter()
        # Should not raise
        emitter.emit("nonexistent", {})
