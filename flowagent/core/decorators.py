"""
Decorators - Utility decorators for FlowAgent.

This module provides decorators for common patterns like retry,
timeout, caching, rate limiting, and validation.
"""

from __future__ import annotations

import asyncio
import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from flowagent.core.logger import logger
from flowagent.core.exceptions import (
    FlowAgentTimeoutError,
    TimeoutError,
    ValidationError,
    RateLimitError,
)

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch

    Returns:
        Decorated function

    Example:
        >>> @retry(max_attempts=3, delay=1)
        ... async def fetch_data():
        ...     return await http_client.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}"
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: {e}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def timeout(seconds: float) -> Callable:
    """
    Timeout decorator.

    Args:
        seconds: Timeout in seconds

    Returns:
        Decorated function

    Example:
        >>> @timeout(30)
        ... async def long_operation():
        ...     await asyncio.sleep(100)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds,
                )
            except asyncio.TimeoutError:
                raise FlowAgentTimeoutError(
                    f"Function {func.__name__} timed out after {seconds}s"
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import signal

            def handler(signum, frame):
                raise FlowAgentTimeoutError(
                    f"Function {func.__name__} timed out after {seconds}s"
                )

            # Set alarm (Unix only)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, handler)
                signal.alarm(int(seconds))
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
                return result
            else:
                # Windows - no native timeout support
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def cache(
    ttl: Optional[float] = None,
    max_size: int = 128,
) -> Callable:
    """
    Caching decorator.

    Args:
        ttl: Time-to-live in seconds, or None for no expiration
        max_size: Maximum cache size

    Returns:
        Decorated function

    Example:
        >>> @cache(ttl=60)
        ... async def expensive_operation(x):
        ...     return await compute(x)
    """
    def decorator(func: Callable) -> Callable:
        cache_store: Dict[str, Any] = {}
        timestamps: Dict[str, float] = {}

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))

            # Check cache
            if key in cache_store:
                if ttl is None or time.time() - timestamps[key] < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache_store[key]

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            if len(cache_store) >= max_size:
                # Remove oldest entry
                oldest_key = min(timestamps, key=timestamps.get)
                del cache_store[oldest_key]
                del timestamps[oldest_key]

            cache_store[key] = result
            timestamps[key] = time.time()

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))

            # Check cache
            if key in cache_store:
                if ttl is None or time.time() - timestamps[key] < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache_store[key]

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            if len(cache_store) >= max_size:
                oldest_key = min(timestamps, key=timestamps.get)
                del cache_store[oldest_key]
                del timestamps[oldest_key]

            cache_store[key] = result
            timestamps[key] = time.time()

            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def rate_limit(
    calls: int,
    period: float,
) -> Callable:
    """
    Rate limiting decorator.

    Args:
        calls: Number of calls allowed
        period: Time period in seconds

    Returns:
        Decorated function

    Example:
        >>> @rate_limit(calls=10, period=60)
        ... async def api_call():
        ...     return await client.request()
    """
    def decorator(func: Callable) -> Callable:
        call_times: list = []
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            now = time.time()

            # Remove old calls
            while call_times and call_times[0] < now - period:
                call_times.pop(0)

            # Check rate limit
            if len(call_times) >= calls:
                wait_time = call_times[0] + period - now
                if wait_time > 0:
                    raise RateLimitError(
                        f"Rate limit exceeded for {func.__name__}. "
                        f"Wait {wait_time:.1f}s"
                    )

            call_times.append(now)
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            now = time.time()

            while call_times and call_times[0] < now - period:
                call_times.pop(0)

            if len(call_times) >= calls:
                wait_time = call_times[0] + period - now
                if wait_time > 0:
                    raise RateLimitError(
                        f"Rate limit exceeded for {func.__name__}. "
                        f"Wait {wait_time:.1f}s"
                    )

            call_times.append(now)
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def validate(**validators: Callable) -> Callable:
    """
    Validation decorator.

    Args:
        **validators: Keyword arguments mapping parameter names to validation functions

    Returns:
        Decorated function

    Example:
        >>> @validate(age=lambda x: x >= 0, name=lambda x: len(x) > 0)
        ... def create_user(name: str, age: int):
        ...     return {"name": name, "age": age}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValidationError(
                            f"Validation failed for parameter '{param_name}': "
                            f"value {value!r} is invalid"
                        )

            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            import inspect

            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for param_name, validator in validators.items():
                if param_name in bound.arguments:
                    value = bound.arguments[param_name]
                    if not validator(value):
                        raise ValidationError(
                            f"Validation failed for parameter '{param_name}': "
                            f"value {value!r} is invalid"
                        )

            return await func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


def memoize(func: Callable) -> Callable:
    """
    Simple memoization decorator.

    Args:
        func: Function to memoize

    Returns:
        Decorated function
    """
    cache: Dict[str, Any] = {}

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(sorted(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]

    return wrapper
