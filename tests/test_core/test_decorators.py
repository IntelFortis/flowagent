"""
Tests for FlowAgent Decorators.
"""

import asyncio
import pytest
from flowagent.core.decorators import retry, timeout, cache, rate_limit, validate


def test_retry_decorator():
    """Test retry decorator."""
    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "Success"

    result = flaky()
    assert result == "Success"
    assert call_count == 3


def test_retry_exhausted():
    """Test retry when all attempts fail."""
    @retry(max_attempts=2, delay=0.01)
    def always_fails():
        raise ValueError("Always fails")

    with pytest.raises(ValueError):
        always_fails()


@pytest.mark.asyncio
async def test_async_retry():
    """Test async retry decorator."""
    call_count = 0

    @retry(max_attempts=3, delay=0.01)
    async def flaky_async():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Not yet")
        return "Success"

    result = await flaky_async()
    assert result == "Success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_timeout_decorator():
    """Test timeout decorator."""
    @timeout(0.1)
    async def slow():
        await asyncio.sleep(1)
        return "Done"

    with pytest.raises(Exception):
        await slow()


def test_cache_decorator():
    """Test cache decorator."""
    call_count = 0

    @cache()
    def expensive(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    result1 = expensive(5)
    assert result1 == 10
    assert call_count == 1

    result2 = expensive(5)
    assert result2 == 10
    assert call_count == 1  # Not called again


def test_cache_different_args():
    """Test cache with different arguments."""
    call_count = 0

    @cache()
    def expensive(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    expensive(5)
    expensive(10)

    assert call_count == 2


def test_rate_limit_decorator():
    """Test rate limit decorator."""
    @rate_limit(calls=2, period=1.0)
    def api_call():
        return "Success"

    # First two calls should succeed
    assert api_call() == "Success"
    assert api_call() == "Success"

    # Third call should fail
    with pytest.raises(Exception):
        api_call()


def test_validate_decorator():
    """Test validate decorator."""
    @validate(age=lambda x: x >= 0, name=lambda x: len(x) > 0)
    def create_user(name: str, age: int):
        return {"name": name, "age": age}

    # Valid input
    result = create_user("Alice", 30)
    assert result == {"name": "Alice", "age": 30}

    # Invalid age
    with pytest.raises(Exception):
        create_user("Alice", -1)

    # Invalid name
    with pytest.raises(Exception):
        create_user("", 30)
