"""
FlowAgent - A small personal workflow automation experiment.

Create and run simple Python workflows with optional visual editing tools.
"""

__version__ = "0.1.0"
__author__ = "IntelFortis"
__email__ = ""

from flowagent.core.workflow import Workflow
from flowagent.core.task import task, Task
from flowagent.core.context import Context
from flowagent.core.state import State
from flowagent.core.agent import Agent
from flowagent.core.decorators import (
    retry,
    timeout,
    cache,
    rate_limit,
    validate,
)
from flowagent.core.models import ModelRegistry, get_registry, set_registry
from flowagent.core.exceptions import (
    FlowAgentError,
    TaskError,
    WorkflowError,
    AgentError,
    FlowAgentTimeoutError,
    TimeoutError,
    ValidationError,
)

__all__ = [
    # Core
    "Workflow",
    "task",
    "Task",
    "Context",
    "State",
    "Agent",
    # Decorators
    "retry",
    "timeout",
    "cache",
    "rate_limit",
    "validate",
    # Models
    "ModelRegistry",
    "get_registry",
    "set_registry",
    # Exceptions
    "FlowAgentError",
    "TaskError",
    "WorkflowError",
    "AgentError",
    "FlowAgentTimeoutError",
    "TimeoutError",
    "ValidationError",
]

# Version info
VERSION_INFO = {
    "major": 0,
    "minor": 1,
    "patch": 0,
    "release": "alpha",
}

def get_version() -> str:
    """Get the current version string."""
    return __version__

def get_version_info() -> dict:
    """Get detailed version information."""
    return {
        **VERSION_INFO,
        "version": __version__,
    }
