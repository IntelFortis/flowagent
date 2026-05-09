"""
Workflow - The core orchestration engine for FlowAgent.

This module provides the Workflow class that orchestrates task execution
using a DAG (Directed Acyclic Graph) structure with event-driven capabilities.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Generic,
    Union,
    Awaitable,
)

from flowagent.core.task import Task, TaskStatus
from flowagent.core.context import Context
from flowagent.core.state import State
from flowagent.core.exceptions import WorkflowError, TaskError
from flowagent.core.logger import logger
from flowagent.core.events import EventEmitter, Event, EventType

T = TypeVar("T")


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowConfig:
    """Configuration for a workflow."""
    name: str
    description: str = ""
    max_parallel_tasks: int = 10
    timeout: Optional[float] = None
    retry_policy: Optional[Dict[str, Any]] = None
    on_start: Optional[Callable] = None
    on_complete: Optional[Callable] = None
    on_error: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Workflow:
    """
    Core workflow orchestration engine.

    The Workflow class manages the execution of tasks in a DAG structure,
    handling dependencies, parallel execution, error recovery, and state management.

    Example:
        >>> from flowagent import Workflow, task
        >>>
        >>> @task
        ... def hello():
        ...     return "Hello!"
        >>>
        >>> workflow = Workflow("my-workflow")
        >>> workflow.add(hello)
        >>> result = workflow.run()
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        max_parallel_tasks: int = 10,
        timeout: Optional[float] = None,
    ):
        self.config = WorkflowConfig(
            name=name,
            description=description,
            max_parallel_tasks=max_parallel_tasks,
            timeout=timeout,
        )
        self._tasks: Dict[str, Task] = {}
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}
        self._status = WorkflowStatus.PENDING
        self._context = Context()
        self._state = State()
        self._events = EventEmitter()
        self._results: Dict[str, Any] = {}
        self._errors: Dict[str, Exception] = {}
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._execution_order: List[str] = []

        logger.info(f"Workflow '{name}' created")

    @property
    def name(self) -> str:
        """Get the workflow name."""
        return self.config.name

    @property
    def status(self) -> WorkflowStatus:
        """Get the current workflow status."""
        return self._status

    @property
    def context(self) -> Context:
        """Get the workflow context."""
        return self._context

    @property
    def state(self) -> State:
        """Get the workflow state."""
        return self._state

    @property
    def results(self) -> Dict[str, Any]:
        """Get the task results."""
        return self._results

    @property
    def errors(self) -> Dict[str, Exception]:
        """Get the task errors."""
        return self._errors

    @property
    def duration(self) -> Optional[float]:
        """Get the workflow execution duration in seconds."""
        if self._start_time is None:
            return None
        end_time = self._end_time or time.time()
        return end_time - self._start_time

    def add(
        self,
        task: Union[Task, Callable],
        depends_on: Optional[List[Union[Task, str]]] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> "Workflow":
        """
        Add a task to the workflow.

        Args:
            task: The task or callable to add
            depends_on: List of tasks or task names this task depends on
            name: Optional name for the task
            **kwargs: Additional task configuration

        Returns:
            Self for method chaining

        Example:
            >>> workflow.add(my_task, depends_on=[other_task])
        """
        # Convert callable to Task if needed
        if callable(task) and not isinstance(task, Task):
            task = Task(task, name=name, **kwargs)

        task_name = task.name

        # Check for duplicate tasks
        if task_name in self._tasks:
            raise WorkflowError(f"Task '{task_name}' already exists in workflow")

        # Add task
        self._tasks[task_name] = task
        self._dependencies[task_name] = set()
        self._dependents[task_name] = self._dependents.get(task_name, set())

        # Process dependencies
        if depends_on:
            for dep in depends_on:
                dep_name = dep.name if isinstance(dep, Task) else dep
                if dep_name not in self._tasks:
                    raise WorkflowError(
                        f"Dependency '{dep_name}' not found. "
                        f"Add it before adding '{task_name}'"
                    )
                self._dependencies[task_name].add(dep_name)
                self._dependents.setdefault(dep_name, set()).add(task_name)

        logger.debug(f"Task '{task_name}' added to workflow '{self.name}'")
        return self

    def chain(self, *tasks: Union[Task, Callable]) -> "Workflow":
        """
        Chain tasks in sequence.

        Each task depends on the previous one.

        Args:
            *tasks: Tasks to chain together

        Returns:
            Self for method chaining

        Example:
            >>> workflow.chain(extract, transform, load)
        """
        for i, task in enumerate(tasks):
            if i == 0:
                self.add(task)
            else:
                prev_task = tasks[i - 1]
                self.add(task, depends_on=[prev_task])
        return self

    def parallel(self, *tasks: Union[Task, Callable]) -> "Workflow":
        """
        Add tasks to run in parallel.

        These tasks will all execute simultaneously.

        Args:
            *tasks: Tasks to run in parallel

        Returns:
            Self for method chaining

        Example:
            >>> workflow.parallel(task1, task2, task3)
        """
        for task in tasks:
            self.add(task)
        return self

    def on(self, event: str, callback: Callable) -> "Workflow":
        """
        Register an event handler.

        Args:
            event: Event name (start, complete, error, task_complete, etc.)
            callback: Callback function

        Returns:
            Self for method chaining
        """
        self._events.on(event, callback)
        return self

    def _validate_dag(self) -> None:
        """
        Validate the workflow DAG for cycles.

        Raises:
            WorkflowError: If a cycle is detected
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self._dependencies.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.discard(node)
            return False

        for task_name in self._tasks:
            if task_name not in visited:
                if dfs(task_name):
                    raise WorkflowError(
                        f"Cycle detected in workflow '{self.name}'. "
                        f"Check dependencies for task '{task_name}'"
                    )

    def _get_execution_order(self) -> List[List[str]]:
        """
        Get the execution order using topological sort.

        Returns:
            List of levels, where each level contains tasks that can run in parallel
        """
        self._validate_dag()

        # Calculate in-degree for each task
        in_degree: Dict[str, int] = {name: 0 for name in self._tasks}
        for task_name, deps in self._dependencies.items():
            in_degree[task_name] = len(deps)

        # Find tasks with no dependencies (first level)
        queue: List[str] = [
            name for name, degree in in_degree.items() if degree == 0
        ]

        levels: List[List[str]] = []
        while queue:
            levels.append(queue)
            next_queue: List[str] = []

            for task_name in queue:
                for dependent in self._dependents.get(task_name, set()):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_queue.append(dependent)

            queue = next_queue

        return levels

    async def _execute_task(self, task: Task) -> Any:
        """
        Execute a single task.

        Args:
            task: The task to execute

        Returns:
            Task result
        """
        task_name = task.name

        # Prepare context with dependency results
        task_context = self._context.clone()
        for dep_name in self._dependencies.get(task_name, set()):
            if dep_name in self._results:
                task_context.set(f"dep:{dep_name}", self._results[dep_name])

        # Execute task
        try:
            task.status = TaskStatus.RUNNING
            self._events.emit(EventType.TASK_START, {"task": task_name})

            start_time = time.time()
            result = await task.execute(task_context)
            duration = time.time() - start_time

            task.status = TaskStatus.COMPLETED
            self._results[task_name] = result
            self._execution_order.append(task_name)

            self._events.emit(EventType.TASK_COMPLETE, {
                "task": task_name,
                "result": result,
                "duration": duration,
            })

            logger.info(f"Task '{task_name}' completed in {duration:.2f}s")
            return result

        except Exception as e:
            task.status = TaskStatus.FAILED
            self._errors[task_name] = e

            self._events.emit(EventType.TASK_ERROR, {
                "task": task_name,
                "error": e,
            })

            logger.error(f"Task '{task_name}' failed: {e}")
            raise TaskError(f"Task '{task_name}' failed: {e}") from e

    async def run_async(self) -> Dict[str, Any]:
        """
        Execute the workflow asynchronously.

        Returns:
            Dictionary of task results

        Raises:
            WorkflowError: If workflow execution fails
        """
        self._status = WorkflowStatus.RUNNING
        self._start_time = time.time()

        self._events.emit(EventType.WORKFLOW_START, {"workflow": self.name})
        logger.info(f"Workflow '{self.name}' started")

        try:
            # Get execution order
            levels = self._get_execution_order()

            # Execute tasks level by level
            for level in levels:
                # Create tasks for this level
                tasks = [self._tasks[name] for name in level]

                # Execute in parallel with semaphore for concurrency control
                semaphore = asyncio.Semaphore(self.config.max_parallel_tasks)

                async def run_with_semaphore(task: Task):
                    async with semaphore:
                        return await self._execute_task(task)

                # Run all tasks in this level
                await asyncio.gather(
                    *[run_with_semaphore(task) for task in tasks],
                    return_exceptions=True,
                )

                # Check for errors
                for task_name in level:
                    if task_name in self._errors:
                        raise self._errors[task_name]

            self._status = WorkflowStatus.COMPLETED
            self._end_time = time.time()

            self._events.emit(EventType.WORKFLOW_COMPLETE, {
                "workflow": self.name,
                "results": self._results,
                "duration": self.duration,
            })

            logger.info(
                f"Workflow '{self.name}' completed in {self.duration:.2f}s"
            )
            return self._results

        except Exception as e:
            self._status = WorkflowStatus.FAILED
            self._end_time = time.time()

            self._events.emit(EventType.WORKFLOW_ERROR, {
                "workflow": self.name,
                "error": e,
            })

            logger.error(f"Workflow '{self.name}' failed: {e}")
            raise WorkflowError(f"Workflow '{self.name}' failed: {e}") from e

    def run(self) -> Dict[str, Any]:
        """
        Execute the workflow synchronously.

        Returns:
            Dictionary of task results
        """
        return asyncio.run(self.run_async())

    def cancel(self) -> None:
        """Cancel the workflow execution."""
        self._status = WorkflowStatus.CANCELLED
        self._events.emit(EventType.WORKFLOW_CANCELLED, {"workflow": self.name})
        logger.info(f"Workflow '{self.name}' cancelled")

    def pause(self) -> None:
        """Pause the workflow execution."""
        self._status = WorkflowStatus.PAUSED
        self._events.emit(EventType.WORKFLOW_PAUSED, {"workflow": self.name})
        logger.info(f"Workflow '{self.name}' paused")

    def resume(self) -> None:
        """Resume the workflow execution."""
        self._status = WorkflowStatus.RUNNING
        self._events.emit(EventType.WORKFLOW_RESUMED, {"workflow": self.name})
        logger.info(f"Workflow '{self.name}' resumed")

    def get_task(self, name: str) -> Optional[Task]:
        """Get a task by name."""
        return self._tasks.get(name)

    def get_dependencies(self, task_name: str) -> Set[str]:
        """Get the dependencies of a task."""
        return self._dependencies.get(task_name, set())

    def get_dependents(self, task_name: str) -> Set[str]:
        """Get the tasks that depend on this task."""
        return self._dependents.get(task_name, set())

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary representation."""
        return {
            "name": self.name,
            "description": self.config.description,
            "status": self._status.value,
            "tasks": {
                name: {
                    "name": task.name,
                    "status": task.status.value,
                    "dependencies": list(self._dependencies.get(name, set())),
                }
                for name, task in self._tasks.items()
            },
            "results": self._results,
            "errors": {k: str(v) for k, v in self._errors.items()},
            "duration": self.duration,
        }

    def visualize(self) -> str:
        """
        Generate a text visualization of the workflow DAG.

        Returns:
            ASCII art representation of the workflow
        """
        lines = [f"Workflow: {self.name}", "=" * 40, ""]

        levels = self._get_execution_order()
        for i, level in enumerate(levels):
            lines.append(f"Level {i + 1}:")
            for task_name in level:
                deps = self._dependencies.get(task_name, set())
                if deps:
                    deps_str = ", ".join(deps)
                    lines.append(f"  [{task_name}] -> depends on: {deps_str}")
                else:
                    lines.append(f"  [{task_name}] (no dependencies)")
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"Workflow(name='{self.name}', tasks={len(self._tasks)}, status={self._status.value})"

    def __len__(self) -> int:
        return len(self._tasks)

    def __contains__(self, task_name: str) -> bool:
        return task_name in self._tasks
