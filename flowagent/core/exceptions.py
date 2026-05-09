"""
Exceptions - Custom exceptions for FlowAgent.

This module provides all custom exceptions used in FlowAgent.
"""


class FlowAgentError(Exception):
    """Base exception for FlowAgent."""
    pass


class TaskError(FlowAgentError):
    """Exception raised when a task fails."""
    pass


class WorkflowError(FlowAgentError):
    """Exception raised when a workflow fails."""
    pass


class AgentError(FlowAgentError):
    """Exception raised when an agent fails."""
    pass


class FlowAgentTimeoutError(FlowAgentError):
    """Exception raised when a task or workflow times out."""
    pass


# Backward-compatible alias
TimeoutError = FlowAgentTimeoutError


class ValidationError(FlowAgentError):
    """Exception raised when validation fails."""
    pass


class ConfigurationError(FlowAgentError):
    """Exception raised when configuration is invalid."""
    pass


class IntegrationError(FlowAgentError):
    """Exception raised when an integration fails."""
    pass


class StateError(FlowAgentError):
    """Exception raised when state operations fail."""
    pass


class DependencyError(FlowAgentError):
    """Exception raised when dependencies are not met."""
    pass


class RetryExhaustedError(TaskError):
    """Exception raised when all retries are exhausted."""
    pass


class ToolError(AgentError):
    """Exception raised when a tool execution fails."""
    pass


class MemoryError(AgentError):
    """Exception raised when memory operations fail."""
    pass


class RateLimitError(IntegrationError):
    """Exception raised when rate limit is exceeded."""
    pass


class AuthenticationError(IntegrationError):
    """Exception raised when authentication fails."""
    pass


class FlowAgentConnectionError(IntegrationError):
    """Exception raised when connection fails."""
    pass


# Backward-compatible alias
ConnectionError = FlowAgentConnectionError
