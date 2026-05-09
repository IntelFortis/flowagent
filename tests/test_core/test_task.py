"""
Tests for FlowAgent Task.
"""

import asyncio
import pytest
from flowagent import task, Task, Context


def test_task_decorator():
    """Test task decorator."""
    @task
    def hello():
        return "Hello"

    assert isinstance(hello, Task)
    assert hello.name == "hello"


def test_task_with_name():
    """Test task with custom name."""
    @task(name="custom_name")
    def hello():
        return "Hello"

    assert hello.name == "custom_name"


def test_task_execution():
    """Test task execution."""
    @task
    def add(a, b):
        return a + b

    ctx = Context()
    result = asyncio.run(add.execute(ctx, 1, 2))
    assert result == 3


def test_task_with_kwargs():
    """Test task with keyword arguments."""
    @task
    def greet(name, greeting="Hello"):
        return f"{greeting}, {name}!"

    ctx = Context()
    result = asyncio.run(greet.execute(ctx, "World"))
    assert result == "Hello, World!"


def test_task_retries():
    """Test task retries."""
    call_count = 0

    @task(retries=2, retry_delay=0.01)
    def flaky_task():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Flaky!")
        return "Success"

    ctx = Context()
    result = asyncio.run(flaky_task.execute(ctx))

    assert result == "Success"
    assert call_count == 3
    assert flaky_task.attempts == 3


def test_task_retry_exhausted():
    """Test task when retries are exhausted."""
    @task(retries=1, retry_delay=0.01)
    def always_fails():
        raise ValueError("Always fails")

    ctx = Context()

    with pytest.raises(Exception):
        asyncio.run(always_fails.execute(ctx))

    assert always_fails.status.value == "failed"


def test_task_caching():
    """Test task result caching."""
    call_count = 0

    @task(cache_result=True)
    def cached_task(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    ctx = Context()

    # First call
    result1 = asyncio.run(cached_task.execute(ctx, 5))
    assert result1 == 10
    assert call_count == 1

    # Second call (should use cache)
    result2 = asyncio.run(cached_task.execute(ctx, 5))
    assert result2 == 10
    assert call_count == 1  # Not called again


def test_task_status():
    """Test task status tracking."""
    @task
    def hello():
        return "Hello"

    assert hello.status.value == "pending"

    ctx = Context()
    asyncio.run(hello.execute(ctx))

    assert hello.status.value == "completed"


def test_task_duration():
    """Test task duration tracking."""
    @task
    def slow_task():
        import time
        time.sleep(0.05)
        return "done"

    ctx = Context()
    asyncio.run(slow_task.execute(ctx))

    assert slow_task.duration is not None
    assert slow_task.duration >= 0.05


def test_task_reset():
    """Test task reset."""
    @task
    def hello():
        return "Hello"

    ctx = Context()
    asyncio.run(hello.execute(ctx))

    assert hello.status.value == "completed"
    assert hello.result == "Hello"

    hello.reset()

    assert hello.status.value == "pending"
    assert hello.result is None
    assert hello.attempts == 0


def test_task_cancel():
    """Test task cancellation."""
    @task
    def hello():
        return "Hello"

    hello.cancel()
    assert hello.status.value == "cancelled"


def test_task_to_dict():
    """Test task serialization."""
    @task(retries=2)
    def hello():
        return "Hello"

    data = hello.to_dict()

    assert data["name"] == "hello"
    assert data["status"] == "pending"
    assert data["config"]["retries"] == 2


def test_task_callable():
    """Test task is callable."""
    @task
    def add(a, b):
        return a + b

    result = add(1, 2)
    assert result == 3


@pytest.mark.asyncio
async def test_async_task():
    """Test async task execution."""
    @task
    async def async_add(a, b):
        await asyncio.sleep(0.01)
        return a + b

    ctx = Context()
    result = await async_add.execute(ctx, 1, 2)
    assert result == 3


def test_task_tags():
    """Test task tags."""
    @task(tags=["data", "processing"])
    def process_data():
        return "processed"

    assert "data" in process_data.config.tags
    assert "processing" in process_data.config.tags


def test_task_priority():
    """Test task priority."""
    @task(priority=10)
    def important_task():
        return "important"

    assert important_task.config.priority == 10
