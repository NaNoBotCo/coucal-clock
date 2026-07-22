"""Unit tests for the golden harness itself — so the validation machinery is trusted."""

from tests.golden.harness import compare


def test_time_tolerance_pass_and_fail():
    assert compare({"t": "06:52"}, {"t": "06:54"}, {"t": "180s"}) == []
    problems = compare({"t": "06:52"}, {"t": "07:10"}, {"t": "180s"})
    assert problems and "t" in problems[0]


def test_numeric_tolerance():
    assert compare({"x": 100.0}, {"x": 100.4}, {"x": 0.5}) == []
    assert compare({"x": 100.0}, {"x": 101.0}, {"x": 0.5}) != []


def test_exact_match_when_no_tolerance():
    # Discrete values (a tithi number, a waxing/waning day) must match exactly.
    assert compare({"tithi": 5}, {"tithi": 5}, {}) == []
    assert compare({"tithi": 5}, {"tithi": 6}, {}) != []


def test_missing_computed_key_is_a_problem():
    assert compare({"a": 1}, {}, {"a": 1}) != []
