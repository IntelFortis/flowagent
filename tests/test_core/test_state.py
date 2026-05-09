"""
Tests for FlowAgent State.
"""

import pytest
from flowagent import State


def test_state_creation():
    """Test state creation."""
    state = State()
    assert len(state) == 0
    assert state.version == 0


def test_state_with_initial_data():
    """Test state with initial data."""
    state = State(initial_data={"a": 1, "b": 2})
    assert len(state) == 2
    assert state.get("a") == 1


def test_state_set_get():
    """Test setting and getting values."""
    state = State()
    state.set("key", "value")
    assert state.get("key") == "value"


def test_state_default_value():
    """Test getting with default value."""
    state = State()
    assert state.get("missing", "default") == "default"


def test_state_has():
    """Test checking key existence."""
    state = State()
    assert state.has("key") is False

    state.set("key", "value")
    assert state.has("key") is True


def test_state_delete():
    """Test deleting values."""
    state = State()
    state.set("key", "value")

    assert state.delete("key") is True
    assert state.has("key") is False


def test_state_version_increment():
    """Test version increments on changes."""
    state = State()
    assert state.version == 0

    state.set("a", 1)
    assert state.version == 1

    state.set("b", 2)
    assert state.version == 2

    state.delete("a")
    assert state.version == 3


def test_state_update():
    """Test updating value with function."""
    state = State()
    state.set("counter", 0)

    state.update("counter", lambda x: x + 1)
    assert state.get("counter") == 1

    state.update("counter", lambda x: x + 1)
    assert state.get("counter") == 2


def test_state_history():
    """Test state history tracking."""
    state = State()

    state.set("a", 1)
    state.set("b", 2)
    state.set("a", 3)

    history = state.history
    assert len(history) == 4  # Initial + 3 changes


def test_state_snapshot():
    """Test state snapshots."""
    state = State()

    state.set("a", 1)
    snapshot = state.get_snapshot()

    assert snapshot is not None
    assert snapshot.data["a"] == 1


def test_state_snapshot_version():
    """Test getting snapshot by version."""
    state = State()

    state.set("a", 1)  # v1
    state.set("b", 2)  # v2
    state.set("c", 3)  # v3

    snapshot = state.get_snapshot(version=2)
    assert snapshot is not None
    assert snapshot.version == 2


def test_state_rollback():
    """Test state rollback."""
    state = State()

    state.set("a", 1)  # v1
    state.set("b", 2)  # v2
    state.set("c", 3)  # v3

    assert state.rollback(1) is True
    assert state.get("a") == 1
    assert state.has("b") is False


def test_state_on_change():
    """Test change listener."""
    changes = []

    def listener(key, old_value, new_value):
        changes.append((key, old_value, new_value))

    state = State()
    state.on_change(listener)

    state.set("a", 1)
    state.set("a", 2)
    state.delete("a")

    assert len(changes) == 3
    assert changes[0] == ("a", None, 1)
    assert changes[1] == ("a", 1, 2)
    assert changes[2] == ("a", 2, None)


def test_state_clear():
    """Test clearing state."""
    state = State()
    state.set("a", 1)
    state.set("b", 2)

    state.clear()
    assert len(state) == 0


def test_state_keys():
    """Test getting all keys."""
    state = State()
    state.set("a", 1)
    state.set("b", 2)
    state.set("c", 3)

    keys = state.keys()
    assert len(keys) == 3
    assert "a" in keys
    assert "b" in keys
    assert "c" in keys


def test_state_values():
    """Test getting all values."""
    state = State()
    state.set("a", 1)
    state.set("b", 2)

    values = state.values()
    assert values == {"a": 1, "b": 2}


def test_state_update_many():
    """Test updating multiple values."""
    state = State()
    state.update_many({"a": 1, "b": 2, "c": 3})

    assert state.get("a") == 1
    assert state.get("b") == 2
    assert state.get("c") == 3


def test_state_bracket_access():
    """Test bracket notation access."""
    state = State()
    state["key"] = "value"

    assert state["key"] == "value"
    assert "key" in state


def test_state_bracket_missing():
    """Test bracket access for missing key."""
    state = State()

    with pytest.raises(KeyError):
        _ = state["missing"]


def test_state_delete_bracket():
    """Test deleting with bracket notation."""
    state = State()
    state["key"] = "value"

    del state["key"]
    assert "key" not in state


def test_state_to_dict():
    """Test state serialization."""
    state = State()
    state.set("a", 1)
    state.set("b", 2)

    data = state.to_dict()

    assert data["version"] == 2
    assert data["data"] == {"a": 1, "b": 2}


def test_state_to_json():
    """Test state JSON serialization."""
    state = State()
    state.set("a", 1)

    json_str = state.to_json()

    assert '"a": 1' in json_str
    assert '"version": 1' in json_str


def test_state_repr():
    """Test state repr."""
    state = State()
    state.set("a", 1)

    assert "State" in repr(state)
    assert "version=1" in repr(state)
