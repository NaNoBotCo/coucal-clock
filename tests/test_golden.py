"""Discover every golden fixture and validate it against its module's evaluator.

A fixture whose module is not yet implemented is *skipped* with a clear reason, so
fixtures may be written ahead of the code. Once an evaluator is registered in
``tests.golden.harness.EVALUATORS``, its fixtures become live pass/fail gates —
and per the project rule, a failing golden test blocks advancing to the next phase.
"""

from __future__ import annotations

import pytest

from tests.golden.harness import EVALUATORS, compare, load_fixtures

_FIXTURES = load_fixtures()


@pytest.mark.golden
@pytest.mark.parametrize("fx", _FIXTURES, ids=[f.name for f in _FIXTURES])
def test_golden(fx) -> None:
    evaluator = EVALUATORS.get(fx.module)
    if evaluator is None:
        pytest.skip(f"module {fx.module!r} not implemented yet — fixture parked for its phase")
    computed = evaluator(fx.inputs)
    problems = compare(fx.expected, computed, fx.tolerance)
    assert not problems, f"{fx.name} ({fx.source}):\n  " + "\n  ".join(problems)


def test_at_least_one_fixture_present() -> None:
    assert _FIXTURES, "no golden fixtures found under tests/golden/fixtures/"
