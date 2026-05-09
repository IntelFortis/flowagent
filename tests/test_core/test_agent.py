"""
Tests for FlowAgent Agent.
"""

import pytest
from flowagent import Agent


def test_agent_creation():
    """Test agent creation."""
    agent = Agent(name="test-agent")
    assert agent.name == "test-agent"


def test_agent_with_model():
    """Test agent with model configuration."""
    agent = Agent(name="test", model="gpt-4")
    assert agent.config.model == "gpt-4"


def test_agent_with_system_prompt():
    """Test agent with system prompt."""
    agent = Agent(
        name="test",
        system_prompt="You are a helpful assistant."
    )
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "system"


def test_agent_register_tool():
    """Test registering a tool."""
    agent = Agent(name="test")

    @agent.tool
    def my_tool(param: str) -> str:
        return f"Result: {param}"

    assert "my_tool" in agent.tools


def test_agent_tool_with_name():
    """Test registering a tool with custom name."""
    agent = Agent(name="test")

    @agent.tool(name="custom_tool")
    def my_tool():
        return "result"

    assert "custom_tool" in agent.tools


def test_agent_tool_definitions():
    """Test getting tool definitions."""
    agent = Agent(name="test")

    @agent.tool
    def search(query: str) -> str:
        """Search for information."""
        return "result"

    definitions = agent.get_tool_definitions()

    assert len(definitions) == 1
    assert definitions[0]["function"]["name"] == "search"
    assert definitions[0]["function"]["description"] == "Search for information."


def test_agent_status():
    """Test agent status."""
    agent = Agent(name="test")
    assert agent.status.value == "idle"


def test_agent_context():
    """Test agent context."""
    agent = Agent(name="test")
    agent.context.set("key", "value")
    assert agent.context.get("key") == "value"


def test_agent_state():
    """Test agent state."""
    agent = Agent(name="test")
    agent.state.set("counter", 0)
    assert agent.state.get("counter") == 0


def test_agent_add_message():
    """Test adding messages."""
    agent = Agent(name="test")

    agent.add_message("user", "Hello")
    agent.add_message("assistant", "Hi there!")

    assert len(agent.messages) == 2
    assert agent.messages[0].content == "Hello"
    assert agent.messages[1].content == "Hi there!"


def test_agent_clear_messages():
    """Test clearing messages."""
    agent = Agent(name="test", system_prompt="System")

    agent.add_message("user", "Hello")
    agent.add_message("assistant", "Hi!")

    agent.clear_messages()

    # Only system message remains
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "system"


def test_agent_to_dict():
    """Test agent serialization."""
    agent = Agent(name="test", model="gpt-4")

    data = agent.to_dict()

    assert data["name"] == "test"
    assert data["model"] == "gpt-4"
    assert data["status"] == "idle"


def test_agent_repr():
    """Test agent repr."""
    agent = Agent(name="test", model="gpt-4")

    assert "test" in repr(agent)
    assert "gpt-4" in repr(agent)
