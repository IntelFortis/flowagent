"""
FlowAgent Performance Benchmarks

This module contains performance benchmarks for FlowAgent.
"""

import asyncio
import time
from typing import List

from flowagent import Workflow, task, Context


def benchmark_task_creation(num_tasks: int = 1000) -> float:
    """Benchmark task creation performance."""
    start = time.perf_counter()

    tasks = []
    for i in range(num_tasks):
        @task(name=f"task_{i}")
        def my_task():
            return i

        tasks.append(my_task)

    duration = time.perf_counter() - start
    return duration


def benchmark_workflow_creation(num_tasks: int = 100) -> float:
    """Benchmark workflow creation performance."""
    start = time.perf_counter()

    workflow = Workflow("benchmark")

    for i in range(num_tasks):
        @task(name=f"task_{i}")
        def my_task():
            return i

        workflow.add(my_task)

    duration = time.perf_counter() - start
    return duration


async def benchmark_workflow_execution(num_tasks: int = 50) -> float:
    """Benchmark workflow execution performance."""
    workflow = Workflow("benchmark")

    async def fast_task():
        await asyncio.sleep(0.001)  # 1ms
        return "done"

    for i in range(num_tasks):
        workflow.add(fast_task, name=f"task_{i}")

    start = time.perf_counter()
    await workflow.run_async()
    duration = time.perf_counter() - start

    return duration


async def benchmark_parallel_execution(num_tasks: int = 100) -> float:
    """Benchmark parallel task execution."""
    workflow = Workflow("parallel-benchmark")

    async def parallel_task():
        await asyncio.sleep(0.01)  # 10ms
        return "done"

    # Add all tasks without dependencies (parallel)
    for i in range(num_tasks):
        workflow.add(parallel_task, name=f"task_{i}")

    start = time.perf_counter()
    await workflow.run_async()
    duration = time.perf_counter() - start

    return duration


async def benchmark_context_operations(num_operations: int = 10000) -> float:
    """Benchmark context operations."""
    ctx = Context()

    start = time.perf_counter()

    for i in range(num_operations):
        ctx.set(f"key_{i}", f"value_{i}")

    for i in range(num_operations):
        ctx.get(f"key_{i}")

    duration = time.perf_counter() - start
    return duration


async def benchmark_state_operations(num_operations: int = 10000) -> float:
    """Benchmark state operations."""
    from flowagent.core.state import State

    state = State()

    start = time.perf_counter()

    for i in range(num_operations):
        state.set(f"key_{i}", f"value_{i}")

    for i in range(num_operations):
        state.get(f"key_{i}")

    duration = time.perf_counter() - start
    return duration


def run_benchmarks():
    """Run all benchmarks."""
    print("FlowAgent Performance Benchmarks")
    print("=" * 50)

    # Task creation
    duration = benchmark_task_creation(1000)
    print(f"Task Creation (1000 tasks): {duration:.3f}s ({duration/1000*1000:.3f}ms per task)")

    # Workflow creation
    duration = benchmark_workflow_creation(100)
    print(f"Workflow Creation (100 tasks): {duration:.3f}s")

    # Workflow execution
    duration = asyncio.run(benchmark_workflow_execution(50))
    print(f"Workflow Execution (50 tasks): {duration:.3f}s")

    # Parallel execution
    duration = asyncio.run(benchmark_parallel_execution(100))
    print(f"Parallel Execution (100 tasks): {duration:.3f}s")

    # Context operations
    duration = asyncio.run(benchmark_context_operations(10000))
    print(f"Context Operations (10000 ops): {duration:.3f}s")

    # State operations
    duration = asyncio.run(benchmark_state_operations(10000))
    print(f"State Operations (10000 ops): {duration:.3f}s")

    print("=" * 50)
    print("Benchmarks complete!")


if __name__ == "__main__":
    run_benchmarks()
