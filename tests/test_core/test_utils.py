"""Tests for utility helpers."""

import pytest

from flowagent.utils.helpers import (
    generate_id,
    format_duration,
    truncate_string,
    flatten_dict,
    unflatten_dict,
    merge_dicts,
    deep_merge,
    chunks,
    hash_string,
    retry,
)


class TestGenerateId:
    def test_default_prefix(self):
        id1 = generate_id()
        assert id1.startswith("fa_")
        assert len(id1) == 11  # "fa_" + 8 hex chars

    def test_custom_prefix(self):
        id1 = generate_id("task")
        assert id1.startswith("task_")

    def test_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100


class TestFormatDuration:
    def test_microseconds(self):
        assert format_duration(0.0005) == "500us"

    def test_milliseconds(self):
        assert format_duration(0.5) == "500ms"

    def test_seconds(self):
        assert format_duration(5.5) == "5.5s"

    def test_minutes(self):
        assert format_duration(65) == "1m 5s"

    def test_hours(self):
        assert format_duration(3661) == "1h 1m 1s"


class TestTruncateString:
    def test_short_string(self):
        assert truncate_string("hello", 10) == "hello"

    def test_long_string(self):
        assert truncate_string("hello world", 8) == "hello..."

    def test_custom_suffix(self):
        assert truncate_string("hello world", 8, "~") == "hello w~"


class TestFlattenDict:
    def test_flat(self):
        assert flatten_dict({"a": 1}) == {"a": 1}

    def test_nested(self):
        assert flatten_dict({"a": {"b": 1, "c": 2}}) == {"a.b": 1, "a.c": 2}

    def test_deep_nested(self):
        result = flatten_dict({"a": {"b": {"c": 1}}})
        assert result == {"a.b.c": 1}

    def test_custom_separator(self):
        result = flatten_dict({"a": {"b": 1}}, sep="/")
        assert result == {"a/b": 1}


class TestUnflattenDict:
    def test_flat(self):
        assert unflatten_dict({"a": 1}) == {"a": 1}

    def test_nested(self):
        assert unflatten_dict({"a.b": 1, "a.c": 2}) == {"a": {"b": 1, "c": 2}}

    def test_roundtrip(self):
        original = {"a": {"b": 1, "c": {"d": 2}}}
        assert unflatten_dict(flatten_dict(original)) == original


class TestMergeDicts:
    def test_merge(self):
        assert merge_dicts({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_override(self):
        assert merge_dicts({"a": 1}, {"a": 2}) == {"a": 2}


class TestDeepMerge:
    def test_deep(self):
        base = {"a": {"b": 1, "c": 2}}
        override = {"a": {"c": 3, "d": 4}}
        result = deep_merge(base, override)
        assert result == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_non_dict_override(self):
        assert deep_merge({"a": 1}, {"a": {"b": 2}}) == {"a": {"b": 2}}


class TestChunks:
    def test_even(self):
        assert chunks([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]

    def test_uneven(self):
        assert chunks([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]

    def test_single_chunk(self):
        assert chunks([1, 2, 3], 10) == [[1, 2, 3]]


class TestHashString:
    def test_sha256(self):
        h = hash_string("hello")
        assert len(h) == 64

    def test_deterministic(self):
        assert hash_string("hello") == hash_string("hello")

    def test_different_inputs(self):
        assert hash_string("hello") != hash_string("world")


class TestRetry:
    def test_success_first_try(self):
        call_count = 0
        def func():
            nonlocal call_count
            call_count += 1
            return "ok"
        assert retry(func) == "ok"
        assert call_count == 1

    def test_success_after_retry(self):
        call_count = 0
        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"
        assert retry(func, max_attempts=3, delay=0.01) == "ok"
        assert call_count == 3

    def test_exhausted(self):
        def func():
            raise ValueError("always fail")
        with pytest.raises(ValueError):
            retry(func, max_attempts=2, delay=0.01)
