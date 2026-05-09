"""
Agent - High-level agent abstraction for FlowAgent.

This module provides the Agent class for creating intelligent agents
that can orchestrate complex workflows with LLM capabilities.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    Awaitable,
)

from flowagent.core.workflow import Workflow
from flowagent.core.task import Task, task
from flowagent.core.context import Context
from flowagent.core.state import State
from flowagent.core.logger import logger
from flowagent.core.exceptions import AgentError

T = TypeVar("T")


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    name: str
    description: str = ""
    model: str = "gpt-5.5"
    temperature: float = 0.7
    max_iterations: int = 10
    max_tokens: int = 4096
    system_prompt: str = ""
    tools: List[Dict[str, Any]] = field(default_factory=list)
    memory_enabled: bool = True
    memory_size: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
    """A message in the agent conversation."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Agent:
    """
    High-level agent abstraction for FlowAgent.

    The Agent class provides an intelligent agent that can orchestrate
    complex workflows using LLM capabilities, tool calling, and memory.

    Accepts ANY model name. The model is passed directly to the LLM provider.
    Use ModelRegistry to create custom aliases for frequently used models.

    Example:
        >>> agent = Agent(
        ...     name="research-agent",
        ...     model="gpt-5.5",
        ...     system_prompt="You are a research assistant."
        ... )
        >>>
        >>> @agent.tool
        ... async def search(query: str) -> str:
        ...     return await web_search(query)
        >>>
        >>> result = await agent.run("Find information about AI agents")
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        model: str = "gpt-5.5",
        temperature: float = 0.7,
        max_iterations: int = 10,
        max_tokens: int = 4096,
        system_prompt: str = "",
        tools: Optional[List[Dict[str, Any]]] = None,
        memory_enabled: bool = True,
        memory_size: int = 100,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.config = AgentConfig(
            name=name,
            description=description,
            model=model,
            temperature=temperature,
            max_iterations=max_iterations,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            tools=tools or [],
            memory_enabled=memory_enabled,
            memory_size=memory_size,
            metadata=metadata or {},
        )
        self._status = AgentStatus.IDLE
        self._messages: List[AgentMessage] = []
        self._tools: Dict[str, Callable] = {}
        self._context = Context()
        self._state = State()
        self._workflow: Optional[Workflow] = None
        self._iteration: int = 0
        self._total_tokens: int = 0

        # Initialize system message
        if system_prompt:
            self._messages.append(AgentMessage(
                role="system",
                content=system_prompt,
            ))

        logger.info(f"Agent '{name}' created with model '{model}'")

    @property
    def name(self) -> str:
        """Get the agent name."""
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        """Get the current agent status."""
        return self._status

    @property
    def messages(self) -> List[AgentMessage]:
        """Get the conversation messages."""
        return self._messages.copy()

    @property
    def context(self) -> Context:
        """Get the agent context."""
        return self._context

    @property
    def state(self) -> State:
        """Get the agent state."""
        return self._state

    @property
    def tools(self) -> Dict[str, Callable]:
        """Get the registered tools."""
        return self._tools.copy()

    def tool(
        self,
        func: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        description: str = "",
    ) -> Union[Callable, Callable[..., Callable]]:
        """
        Register a tool for the agent.

        Can be used as a decorator or function.

        Args:
            func: The function to register
            name: Tool name (defaults to function name)
            description: Tool description

        Returns:
            The original function or decorator

        Example:
            >>> @agent.tool
            ... async def search(query: str) -> str:
            ...     return await web_search(query)
        """
        def decorator(f: Callable) -> Callable:
            tool_name = name or f.__name__
            tool_desc = description or f.__doc__ or ""

            self._tools[tool_name] = f
            self.config.tools.append({
                "name": tool_name,
                "description": tool_desc,
                "parameters": self._extract_parameters(f),
            })

            logger.debug(f"Agent '{self.name}': tool '{tool_name}' registered")
            return f

        if func is not None:
            return decorator(func)
        return decorator

    def _extract_parameters(self, func: Callable) -> Dict[str, Any]:
        """Extract function parameters for tool definition."""
        import inspect

        sig = inspect.signature(func)
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }

        for name, param in sig.parameters.items():
            if name in ("self", "cls", "ctx", "context"):
                continue

            param_info: Dict[str, Any] = {}

            # Get type annotation
            if param.annotation != inspect.Parameter.empty:
                type_map = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                param_info["type"] = type_map.get(param.annotation, "string")

            # Get description from docstring or default
            param_info["description"] = f"Parameter: {name}"

            parameters["properties"][name] = param_info

            # Check if required
            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)

        return parameters

    async def run(
        self,
        prompt: str,
        context: Optional[Context] = None,
        **kwargs,
    ) -> str:
        """
        Run the agent with a prompt.

        Args:
            prompt: The user prompt
            context: Optional execution context
            **kwargs: Additional arguments

        Returns:
            Agent response

        Raises:
            AgentError: If agent execution fails
        """
        self._status = AgentStatus.THINKING
        self._iteration = 0

        # Add user message
        self._messages.append(AgentMessage(
            role="user",
            content=prompt,
        ))

        # Merge context
        if context:
            self._context.merge(context)

        logger.info(f"Agent '{self.name}': processing prompt")

        try:
            # Main agent loop
            while self._iteration < self.config.max_iterations:
                self._iteration += 1

                # Generate response
                response = await self._generate_response()

                # Check for tool calls
                if response.tool_calls:
                    self._status = AgentStatus.ACTING

                    # Execute tools
                    tool_results = await self._execute_tools(response.tool_calls)

                    # Add tool results to messages
                    for result in tool_results:
                        self._messages.append(AgentMessage(
                            role="tool",
                            content=result["result"],
                            tool_call_id=result["tool_call_id"],
                        ))

                    self._status = AgentStatus.THINKING
                    continue

                # No tool calls, return response
                self._messages.append(response)
                self._status = AgentStatus.COMPLETED

                logger.info(
                    f"Agent '{self.name}': completed in {self._iteration} iterations"
                )
                return response.content

            # Max iterations reached
            raise AgentError(
                f"Agent '{self.name}' reached max iterations "
                f"({self.config.max_iterations})"
            )

        except Exception as e:
            self._status = AgentStatus.FAILED
            logger.error(f"Agent '{self.name}' failed: {e}")
            raise AgentError(f"Agent execution failed: {e}") from e

    async def _generate_response(self) -> AgentMessage:
        """
        Generate a response using the LLM.

        This is a placeholder that should be overridden by specific LLM integrations.
        """
        # This would be implemented by specific LLM integrations
        # For now, return a placeholder
        raise NotImplementedError(
            "LLM integration not configured. "
            "Use flowagent.integrations.OpenAI, Anthropic, etc."
        )

    async def _execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Execute tool calls.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of tool results
        """
        results = []

        for call in tool_calls:
            tool_name = call["function"]["name"]
            tool_args = call["function"]["arguments"]
            tool_call_id = call["id"]

            if tool_name not in self._tools:
                result = f"Error: Tool '{tool_name}' not found"
            else:
                try:
                    # Parse arguments
                    import json
                    args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args

                    # Execute tool
                    tool_func = self._tools[tool_name]
                    if asyncio.iscoroutinefunction(tool_func):
                        result = await tool_func(**args)
                    else:
                        result = tool_func(**args)

                    result = str(result)

                except Exception as e:
                    result = f"Error executing tool '{tool_name}': {e}"
                    logger.error(f"Agent '{self.name}': tool error: {e}")

            results.append({
                "tool_call_id": tool_call_id,
                "result": result,
            })

        return results

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """Add a message to the conversation."""
        self._messages.append(AgentMessage(
            role=role,
            content=content,
            **kwargs,
        ))

    def clear_messages(self) -> None:
        """Clear all messages except system message."""
        self._messages = [
            msg for msg in self._messages
            if msg.role == "system"
        ]

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions for LLM API."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                },
            }
            for tool in self.config.tools
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary."""
        return {
            "name": self.name,
            "description": self.config.description,
            "model": self.config.model,
            "status": self._status.value,
            "iteration": self._iteration,
            "message_count": len(self._messages),
            "tool_count": len(self._tools),
        }

    def __repr__(self) -> str:
        return (
            f"Agent(name='{self.name}', model='{self.config.model}', "
            f"status={self._status.value})"
        )


class ReActAgent(Agent):
    """
    ReAct (Reasoning + Acting) Agent.

    Implements the ReAct pattern for more structured reasoning
    and action taking.

    Example:
        >>> agent = ReActAgent(
        ...     name="research-agent",
        ...     model="gpt-4",
        ... )
        >>> result = await agent.run("What is the capital of France?")
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._thoughts: List[str] = []
        self._actions: List[Dict[str, Any]] = []
        self._observations: List[str] = []

    async def run(self, prompt: str, **kwargs) -> str:
        """
        Run the agent using ReAct pattern.

        Args:
            prompt: The user prompt

        Returns:
            Final answer
        """
        # Override to implement ReAct logic
        return await super().run(prompt, **kwargs)


class MultiAgentOrchestrator:
    """
    Orchestrator for multiple agents.

    Coordinates multiple agents to work together on complex tasks.

    Example:
        >>> orchestrator = MultiAgentOrchestrator()
        >>> orchestrator.add_agent(research_agent)
        >>> orchestrator.add_agent(writer_agent)
        >>> result = await orchestrator.run("Write a research paper")
    """

    def __init__(self, name: str = "orchestrator"):
        self.name = name
        self._agents: Dict[str, Agent] = {}
        self._context = Context()
        self._state = State()

    def add_agent(self, agent: Agent) -> "MultiAgentOrchestrator":
        """Add an agent to the orchestrator."""
        self._agents[agent.name] = agent
        logger.info(f"Orchestrator '{self.name}': agent '{agent.name}' added")
        return self

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self._agents.get(name)

    async def run(
        self,
        prompt: str,
        agent_name: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        Run the orchestrator.

        Args:
            prompt: The task prompt
            agent_name: Specific agent to use, or None for automatic selection

        Returns:
            Result from the agent
        """
        if agent_name:
            agent = self._agents.get(agent_name)
            if not agent:
                raise AgentError(f"Agent '{agent_name}' not found")
            return await agent.run(prompt, context=self._context, **kwargs)

        # Automatic agent selection (simple: use first agent)
        if not self._agents:
            raise AgentError("No agents registered")

        agent = next(iter(self._agents.values()))
        return await agent.run(prompt, context=self._context, **kwargs)

    async def run_parallel(
        self,
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, str]:
        """
        Run multiple tasks in parallel across agents.

        Args:
            tasks: List of tasks with agent_name and prompt

        Returns:
            Dictionary of agent_name -> result
        """
        results = {}

        async def run_task(agent_name: str, prompt: str):
            agent = self._agents.get(agent_name)
            if agent:
                results[agent_name] = await agent.run(prompt)

        await asyncio.gather(*[
            run_task(task["agent_name"], task["prompt"])
            for task in tasks
        ])

        return results

    def to_dict(self) -> Dict[str, Any]:
        """Convert orchestrator to dictionary."""
        return {
            "name": self.name,
            "agents": {
                name: agent.to_dict()
                for name, agent in self._agents.items()
            },
        }
