"""
Helpers - Utility helper functions for FlowAgent.

This module provides common utility functions used throughout FlowAgent.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Awaitable

T = TypeVar("T")


def generate_id(prefix: str = "fa") -> str:
    """
    Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string

    Example:
        >>> generate_id("task")
        'task_a1b2c3d4'
    """
    unique = uuid.uuid4().hex[:8]
    return f"{prefix}_{unique}"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string

    Example:
        >>> format_duration(3661)
        '1h 1m 1s'
        >>> format_duration(65)
        '1m 5s'
        >>> format_duration(0.5)
        '500ms'
    """
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f}us"
    elif seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def truncate_string(s: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    sep: str = ".",
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key for nested items
        sep: Separator for keys

    Returns:
        Flattened dictionary

    Example:
        >>> flatten_dict({"a": {"b": 1, "c": 2}})
        {'a.b': 1, 'a.c': 2}
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(
    d: Dict[str, Any],
    sep: str = ".",
) -> Dict[str, Any]:
    """
    Unflatten a dictionary with dot-separated keys.

    Args:
        d: Dictionary to unflatten
        sep: Separator used in keys

    Returns:
        Nested dictionary

    Example:
        >>> unflatten_dict({"a.b": 1, "a.c": 2})
        {'a': {'b': 1, 'c': 2}}
    """
    result: Dict[str, Any] = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries (shallow).

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result: Dict[str, Any] = {}
    for d in dicts:
        result.update(d)
    return result


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Override dictionary

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def chunks(lst: List[T], size: int) -> List[List[T]]:
    """
    Split a list into chunks of a given size.

    Args:
        lst: List to split
        size: Chunk size

    Returns:
        List of chunks

    Example:
        >>> chunks([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def hash_string(s: str, algorithm: str = "sha256") -> str:
    """
    Hash a string using the specified algorithm.

    Args:
        s: String to hash
        algorithm: Hash algorithm

    Returns:
        Hex digest of the hash
    """
    return hashlib.new(algorithm, s.encode()).hexdigest()


def retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """
    Retry a synchronous function.

    Args:
        func: Function to retry
        max_attempts: Maximum attempts
        delay: Initial delay
        backoff: Backoff multiplier
        exceptions: Exceptions to catch

    Returns:
        Function result
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                time.sleep(current_delay)
                current_delay *= backoff

    raise last_exception


async def async_retry(
    func: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> T:
    """
    Retry an async function.

    Args:
        func: Async function to retry
        max_attempts: Maximum attempts
        delay: Initial delay
        backoff: Backoff multiplier
        exceptions: Exceptions to catch

    Returns:
        Function result
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_attempts):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:
                await asyncio.sleep(current_delay)
                current_delay *= backoff

    raise last_exception
