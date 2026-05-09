"""
Tests for FlowAgent Context.
"""

import pytest
from flowagent import Context


def test_context_creation():
    """Test context creation."""
    ctx = Context()
    assert len(ctx) == 0


def test_context_set_get():
    """Test setting and getting values."""
    ctx = Context()
    ctx.set("key", "value")
    assert ctx.get("key") == "value"


def test_context_default_value():
    """Test getting with default value."""
    ctx = Context()
    assert ctx.get("missing", "default") == "default"


def test_context_has():
    """Test checking key existence."""
    ctx = Context()
    assert ctx.has("key") is False

    ctx.set("key", "value")
    assert ctx.has("key") is True


def test_context_delete():
    """Test deleting values."""
    ctx = Context()
    ctx.set("key", "value")

    assert ctx.delete("key") is True
    assert ctx.has("key") is False


def test_context_delete_missing():
    """Test deleting missing key."""
    ctx = Context()
    assert ctx.delete("missing") is False


def test_context_keys():
    """Test getting all keys."""
    ctx = Context()
    ctx.set("a", 1)
    ctx.set("b", 2)
    ctx.set("c", 3)

    keys = ctx.keys()
    assert len(keys) == 3
    assert "a" in keys
    assert "b" in keys
    assert "c" in keys


def test_context_values():
    """Test getting all values."""
    ctx = Context()
    ctx.set("a", 1)
    ctx.set("b", 2)

    values = ctx.values()
    assert values == {"a": 1, "b": 2}


def test_context_update():
    """Test updating multiple values."""
    ctx = Context()
    ctx.update({"a": 1, "b": 2, "c": 3})

    assert ctx.get("a") == 1
    assert ctx.get("b") == 2
    assert ctx.get("c") == 3


def test_context_clear():
    """Test clearing context."""
    ctx = Context()
    ctx.set("a", 1)
    ctx.set("b", 2)

    ctx.clear()
    assert len(ctx) == 0


def test_context_clone():
    """Test cloning context."""
    ctx = Context()
    ctx.set("a", 1)
    ctx.set("b", 2)

    clone = ctx.clone()
    clone.set("c", 3)

    assert clone.get("a") == 1
    assert clone.get("b") == 2
    assert clone.get("c") == 3
    assert ctx.has("c") is False


def test_context_parent():
    """Test parent context."""
    parent = Context()
    parent.set("parent_key", "parent_value")

    child = Context(parent=parent)
    child.set("child_key", "child_value")

    assert child.get("parent_key") == "parent_value"
    assert child.get("child_key") == "child_value"


def test_context_parent_override():
    """Test child overriding parent values."""
    parent = Context()
    parent.set("key", "parent_value")

    child = Context(parent=parent)
    child.set("key", "child_value")

    assert parent.get("key") == "parent_value"
    assert child.get("key") == "child_value"


def test_context_bracket_access():
    """Test bracket notation access."""
    ctx = Context()
    ctx["key"] = "value"

    assert ctx["key"] == "value"
    assert "key" in ctx


def test_context_bracket_missing():
    """Test bracket access for missing key."""
    ctx = Context()

    with pytest.raises(KeyError):
        _ = ctx["missing"]


def test_context_delete_bracket():
    """Test deleting with bracket notation."""
    ctx = Context()
    ctx["key"] = "value"

    del ctx["key"]
    assert "key" not in ctx


def test_context_len():
    """Test context length."""
    ctx = Context()
    assert len(ctx) == 0

    ctx.set("a", 1)
    assert len(ctx) == 1

    ctx.set("b", 2)
    assert len(ctx) == 2


def test_context_repr():
    """Test context repr."""
    ctx = Context()
    ctx.set("a", 1)

    assert "Context" in repr(ctx)


def test_context_metadata():
    """Test context metadata."""
    ctx = Context()
    ctx.set_metadata("source", "test")
    ctx.set_metadata("version", 1)

    assert ctx.get_metadata("source") == "test"
    assert ctx.get_metadata("version") == 1
    assert ctx.get_metadata("missing", "default") == "default"


def test_context_merge():
    """Test merging contexts."""
    ctx1 = Context()
    ctx1.set("a", 1)

    ctx2 = Context()
    ctx2.set("b", 2)

    ctx1.merge(ctx2)

    assert ctx1.get("a") == 1
    assert ctx1.get("b") == 2
