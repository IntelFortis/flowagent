"""
Tests for FlowAgent Workflow.
"""

import asyncio
import pytest
from flowagent import Workflow, task, Context


def test_workflow_creation():
    """Test workflow creation."""
    workflow = Workflow("test-workflow")
    assert workflow.name == "test-workflow"
    assert len(workflow) == 0


def test_workflow_add_task():
    """Test adding tasks to workflow."""
    workflow = Workflow("test")

    @task
    def hello():
        return "Hello"

    workflow.add(hello)
    assert len(workflow) == 1
    assert "hello" in workflow


def test_workflow_add_callable():
    """Test adding callable to workflow."""
    workflow = Workflow("test")

    def my_task():
        return 42

    workflow.add(my_task)
    assert len(workflow) == 1


def test_workflow_chain():
    """Test chaining tasks."""
    workflow = Workflow("test")

    @task
    def step1():
        return 1

    @task
    def step2():
        return 2

    @task
    def step3():
        return 3

    workflow.chain(step1, step2, step3)
    assert len(workflow) == 3

    # Check dependencies
    assert len(workflow.get_dependencies("step2")) == 1
    assert len(workflow.get_dependencies("step3")) == 1


def test_workflow_parallel():
    """Test parallel tasks."""
    workflow = Workflow("test")

    @task
    def task1():
        return 1

    @task
    def task2():
        return 2

    @task
    def task3():
        return 3

    workflow.parallel(task1, task2, task3)
    assert len(workflow) == 3

    # No dependencies
    for name in ["task1", "task2", "task3"]:
        assert len(workflow.get_dependencies(name)) == 0


def test_workflow_execution():
    """Test workflow execution."""
    workflow = Workflow("test")

    @task
    def hello():
        return "Hello, World!"

    workflow.add(hello)
    results = workflow.run()

    assert "hello" in results
    assert results["hello"] == "Hello, World!"


def test_workflow_with_dependencies():
    """Test workflow with task dependencies."""
    workflow = Workflow("test")

    @task
    def first():
        return 10

    @task
    def second(ctx):
        value = ctx.get("dep:first")
        return value * 2

    workflow.add(first)
    workflow.add(second, depends_on=[first])

    results = workflow.run()

    assert results["first"] == 10
    assert results["second"] == 20


def test_workflow_multiple_dependencies():
    """Test workflow with multiple dependencies."""
    workflow = Workflow("test")

    @task
    def a():
        return 1

    @task
    def b():
        return 2

    @task
    def sum_task(ctx):
        a_val = ctx.get("dep:a")
        b_val = ctx.get("dep:b")
        return a_val + b_val

    workflow.add(a)
    workflow.add(b)
    workflow.add(sum_task, depends_on=[a, b])

    results = workflow.run()

    assert results["sum_task"] == 3


def test_workflow_status():
    """Test workflow status tracking."""
    workflow = Workflow("test")

    @task
    def hello():
        return "Hello"

    workflow.add(hello)

    assert workflow.status.value == "pending"

    results = workflow.run()

    assert workflow.status.value == "completed"


def test_workflow_duration():
    """Test workflow duration tracking."""
    workflow = Workflow("test")

    @task
    def slow_task():
        import time
        time.sleep(0.1)
        return "done"

    workflow.add(slow_task)

    results = workflow.run()

    assert workflow.duration is not None
    assert workflow.duration >= 0.1


def test_workflow_retries():
    """Test task retries."""
    call_count = 0

    @task(retries=2, retry_delay=0.01)
    def failing_task():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet!")
        return "Success"

    workflow = Workflow("test")
    workflow.add(failing_task)

    results = workflow.run()

    assert results["failing_task"] == "Success"
    assert call_count == 3


def test_workflow_error_handling():
    """Test workflow error handling."""
    @task(retries=0)
    def failing_task():
        raise ValueError("Task failed!")

    workflow = Workflow("test")
    workflow.add(failing_task)

    with pytest.raises(Exception):
        workflow.run()

    assert workflow.status.value == "failed"


def test_workflow_visualize():
    """Test workflow visualization."""
    workflow = Workflow("test")

    @task
    def a():
        return 1

    @task
    def b():
        return 2

    workflow.chain(a, b)

    viz = workflow.visualize()
    assert "test" in viz
    assert "a" in viz
    assert "b" in viz


def test_workflow_to_dict():
    """Test workflow serialization."""
    workflow = Workflow("test")

    @task
    def hello():
        return "Hello"

    workflow.add(hello)
    workflow.run()

    data = workflow.to_dict()

    assert data["name"] == "test"
    assert data["status"] == "completed"
    assert "hello" in data["tasks"]
    assert data["results"]["hello"] == "Hello"


@pytest.mark.asyncio
async def test_workflow_async():
    """Test async workflow execution."""
    workflow = Workflow("test")

    @task
    async def async_task():
        await asyncio.sleep(0.01)
        return "Async result"

    workflow.add(async_task)

    results = await workflow.run_async()

    assert results["async_task"] == "Async result"


@pytest.mark.asyncio
async def test_workflow_parallel_execution():
    """Test parallel task execution."""
    execution_order = []

    @task
    async def task_a():
        execution_order.append("a_start")
        await asyncio.sleep(0.05)
        execution_order.append("a_end")
        return "A"

    @task
    async def task_b():
        execution_order.append("b_start")
        await asyncio.sleep(0.05)
        execution_order.append("b_end")
        return "B"

    workflow = Workflow("test")
    workflow.add(task_a)
    workflow.add(task_b)

    results = await workflow.run_async()

    assert results["task_a"] == "A"
    assert results["task_b"] == "B"

    # Both should start before either ends (parallel)
    assert execution_order.index("a_start") < execution_order.index("a_end")
    assert execution_order.index("b_start") < execution_order.index("b_end")


def test_workflow_duplicate_task():
    """Test adding duplicate task."""
    workflow = Workflow("test")

    @task
    def hello():
        return "Hello"

    workflow.add(hello)

    with pytest.raises(Exception):
        workflow.add(hello)


def test_workflow_missing_dependency():
    """Test adding task with missing dependency."""
    workflow = Workflow("test")

    @task
    def hello():
        return "Hello"

    with pytest.raises(Exception):
        workflow.add(hello, depends_on=["nonexistent"])
