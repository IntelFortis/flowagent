"""
Task - Core task abstraction for FlowAgent.

This module provides the Task class and @task decorator for defining
individual units of work in a workflow.
"""

from __future__ import annotations

import asyncio
import functools
import inspect
import time
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
    Generic,
)

from flowagent.core.context import Context
from flowagent.core.exceptions import TaskError, FlowAgentTimeoutError, TimeoutError
from flowagent.core.logger import logger

T = TypeVar("T")
R = TypeVar("R")


class TaskStatus(Enum):
    """Status of a task execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass
class TaskConfig:
    """Configuration for a task."""
    name: str
    description: str = ""
    retries: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    cache_result: bool = False
    cache_ttl: Optional[float] = None
    priority: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Task(Generic[R]):
    """
    Core task abstraction for FlowAgent.

    A Task represents a single unit of work in a workflow. It can be
    a sync or async function with optional configuration for retries,
    timeouts, caching, and more.

    Example:
        >>> @task(retries=3, timeout=30)
        ... async def fetch_data(url: str) -> dict:
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get(url)
        ...         return response.json()
    """

    def __init__(
        self,
        func: Callable[..., Union[R, Awaitable[R]]],
        name: Optional[str] = None,
        description: str = "",
        retries: int = 0,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        cache_result: bool = False,
        cache_ttl: Optional[float] = None,
        priority: int = 0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self._func = func
        self._config = TaskConfig(
            name=name or func.__name__,
            description=description or func.__doc__ or "",
            retries=retries,
            retry_delay=retry_delay,
            timeout=timeout,
            cache_result=cache_result,
            cache_ttl=cache_ttl,
            priority=priority,
            tags=tags or [],
            metadata=metadata or {},
        )
        self._status = TaskStatus.PENDING
        self._result: Optional[R] = None
        self._error: Optional[Exception] = None
        self._attempts: int = 0
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._cache: Dict[str, Any] = {}

        # Inspect function signature
        self._sig = inspect.signature(func)
        self._is_async = asyncio.iscoroutinefunction(func)

        logger.debug(f"Task '{self.name}' created")

    @property
    def name(self) -> str:
        """Get the task name."""
        return self._config.name

    @property
    def status(self) -> TaskStatus:
        """Get the current task status."""
        return self._status

    @status.setter
    def status(self, value: TaskStatus) -> None:
        """Set the task status."""
        self._status = value

    @property
    def result(self) -> Optional[R]:
        """Get the task result."""
        return self._result

    @property
    def error(self) -> Optional[Exception]:
        """Get the task error."""
        return self._error

    @property
    def attempts(self) -> int:
        """Get the number of execution attempts."""
        return self._attempts

    @property
    def duration(self) -> Optional[float]:
        """Get the task execution duration in seconds."""
        if self._start_time is None:
            return None
        end_time = self._end_time or time.time()
        return end_time - self._start_time

    @property
    def config(self) -> TaskConfig:
        """Get the task configuration."""
        return self._config

    @property
    def is_async(self) -> bool:
        """Check if the task is async."""
        return self._is_async

    def _get_cache_key(self, args: tuple, kwargs: dict) -> str:
        """Generate a cache key from function arguments."""
        key_parts = [self.name]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return ":".join(key_parts)

    async def execute(self, context: Context, *args: Any, **kwargs: Any) -> R:
        """
        Execute the task.

        Args:
            context: The execution context
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Task result

        Raises:
            TaskError: If task execution fails
            TimeoutError: If task execution times out
        """
        self._status = TaskStatus.RUNNING
        self._start_time = time.time()

        # Check cache
        if self._config.cache_result:
            cache_key = self._get_cache_key(args, kwargs)
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if cached["expires"] is None or time.time() < cached["expires"]:
                    logger.debug(f"Task '{self.name}' cache hit")
                    return cached["result"]

        # Execute with retries
        last_error = None
        for attempt in range(self._config.retries + 1):
            self._attempts += 1
            try:
                # Add context to kwargs if function expects it
                sig = inspect.signature(self._func)
                if "ctx" in sig.parameters:
                    kwargs["ctx"] = context
                elif "context" in sig.parameters:
                    kwargs["context"] = context

                # Execute function
                if self._is_async:
                    result = await self._func(*args, **kwargs)
                else:
                    result = self._func(*args, **kwargs)

                # Handle coroutines
                if asyncio.iscoroutine(result):
                    result = await result

                # Cache result
                if self._config.cache_result:
                    cache_key = self._get_cache_key(args, kwargs)
                    expires = None
                    if self._config.cache_ttl:
                        expires = time.time() + self._config.cache_ttl
                    self._cache[cache_key] = {
                        "result": result,
                        "expires": expires,
                    }

                self._result = result
                self._status = TaskStatus.COMPLETED
                self._end_time = time.time()

                logger.info(
                    f"Task '{self.name}' completed successfully "
                    f"(attempt {attempt + 1})"
                )
                return result

            except Exception as e:
                last_error = e
                self._error = e

                if attempt < self._config.retries:
                    self._status = TaskStatus.RETRYING
                    delay = self._config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Task '{self.name}' failed (attempt {attempt + 1}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    self._status = TaskStatus.FAILED
                    self._end_time = time.time()

                    logger.error(
                        f"Task '{self.name}' failed after "
                        f"{self._config.retries + 1} attempts: {e}"
                    )
                    raise TaskError(
                        f"Task '{self.name}' failed after "
                        f"{self._config.retries + 1} attempts: {e}"
                    ) from e

        # This should never be reached, but just in case
        raise TaskError(f"Task '{self.name}' failed: {last_error}")

    def cancel(self) -> None:
        """Cancel the task."""
        self._status = TaskStatus.CANCELLED
        logger.info(f"Task '{self.name}' cancelled")

    def reset(self) -> None:
        """Reset the task state."""
        self._status = TaskStatus.PENDING
        self._result = None
        self._error = None
        self._attempts = 0
        self._start_time = None
        self._end_time = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "name": self.name,
            "description": self._config.description,
            "status": self._status.value,
            "attempts": self._attempts,
            "duration": self.duration,
            "error": str(self._error) if self._error else None,
            "config": {
                "retries": self._config.retries,
                "timeout": self._config.timeout,
                "cache_result": self._config.cache_result,
                "priority": self._config.priority,
                "tags": self._config.tags,
            },
        }

    def __repr__(self) -> str:
        return (
            f"Task(name='{self.name}', status={self._status.value}, "
            f"attempts={self._attempts})"
        )

    def __call__(self, *args: Any, **kwargs: Any) -> R:
        """Make task callable for direct execution."""
        if self._is_async:
            return self.execute(Context(), *args, **kwargs)  # type: ignore
        return self._func(*args, **kwargs)


def task(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    description: str = "",
    retries: int = 0,
    retry_delay: float = 1.0,
    timeout: Optional[float] = None,
    cache_result: bool = False,
    cache_ttl: Optional[float] = None,
    priority: int = 0,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Union[Task, Callable[..., Task]]:
    """
    Decorator to create a FlowAgent task.

    Can be used as a bare decorator or with arguments.

    Args:
        func: The function to decorate
        name: Task name (defaults to function name)
        description: Task description
        retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Task timeout in seconds
        cache_result: Whether to cache the result
        cache_ttl: Cache time-to-live in seconds
        priority: Task priority (higher = more important)
        tags: Task tags for categorization
        metadata: Additional metadata

    Returns:
        Task instance or decorator

    Example:
        >>> @task(retries=3, timeout=30)
        ... async def fetch_data(url: str) -> dict:
        ...     async with httpx.AsyncClient() as client:
        ...         return await client.get(url)

        >>> @task
        ... def simple_task():
        ...     return "Hello"
    """
    def decorator(func: Callable) -> Task:
        return Task(
            func,
            name=name,
            description=description,
            retries=retries,
            retry_delay=retry_delay,
            timeout=timeout,
            cache_result=cache_result,
            cache_ttl=cache_ttl,
            priority=priority,
            tags=tags,
            metadata=metadata,
        )

    if func is not None:
        # Used as @task without arguments
        return decorator(func)

    # Used as @task(...) with arguments
    return decorator


class TaskGroup:
    """
    A group of tasks that can be executed together.

    Example:
        >>> group = TaskGroup("data-processing")
        >>> group.add(task1)
        >>> group.add(task2)
        >>> await group.execute_all()
    """

    def __init__(self, name: str, max_parallel: int = 10):
        self.name = name
        self.max_parallel = max_parallel
        self._tasks: List[Task] = []
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, Exception] = {}

    def add(self, task: Task) -> "TaskGroup":
        """Add a task to the group."""
        self._tasks.append(task)
        return self

    async def execute_all(self, context: Optional[Context] = None) -> Dict[str, Any]:
        """
        Execute all tasks in parallel.

        Args:
            context: Optional execution context

        Returns:
            Dictionary of task results
        """
        ctx = context or Context()
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def run_task(task: Task):
            async with semaphore:
                try:
                    result = await task.execute(ctx)
                    self._results[task.name] = result
                except Exception as e:
                    self._errors[task.name] = e

        await asyncio.gather(*[run_task(task) for task in self._tasks])

        if self._errors:
            raise TaskError(
                f"TaskGroup '{self.name}' had {len(self._errors)} failures: "
                f"{list(self._errors.keys())}"
            )

        return self._results

    @property
    def results(self) -> Dict[str, Any]:
        """Get the task results."""
        return self._results

    @property
    def errors(self) -> Dict[str, Exception]:
        """Get the task errors."""
        return self._errors
