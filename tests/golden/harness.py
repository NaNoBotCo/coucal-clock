"""Golden-fixture loader and comparison helpers.

Kept separate from the test module so evaluators for each almanac module can be
registered here as they are built (Phase 1+). Until a module has an evaluator, its
fixtures are reported as ``skipped`` with the reason, never as failures.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"

# module name -> function(inputs: dict) -> dict of computed values.
# Populated by each phase as its module lands.
EVALUATORS: dict[str, Callable[[dict], dict]] = {}


def _evaluate_solar_lunar(inputs: dict) -> dict:
    """Phase 1: sun and moon for one local day at the observer's position.

    Imports live inside the function so that collecting the test suite does not
    require the astronomy stack to be installed.
    """
    from datetime import date as _date
    from datetime import datetime as _datetime

    from coucal.almanac.ephemeris import Observer, get_sky
    from coucal.almanac.solar_lunar import moon_state, sun_day

    observer = Observer(
        latitude=inputs["lat"],
        longitude=inputs["lon"],
        elevation_m=inputs.get("elev_m", 0.0),
        timezone_name=inputs.get("tz", "Asia/Bangkok"),
    )
    sky = get_sky(observer)
    day = _date.fromisoformat(inputs["date"])
    solar = sun_day(sky, day)

    # Phase is read at local noon: a single, stated instant, so the comparison is
    # reproducible rather than depending on when in the day it happens to be asked.
    noon = _datetime(day.year, day.month, day.day, 12, 0, tzinfo=observer.tz)
    moon = moon_state(sky, noon)

    def hhmm(value):
        return value.strftime("%H:%M") if value is not None else None

    return {
        "civil_dawn_local": hhmm(solar.civil_dawn),
        "sunrise_local": hhmm(solar.sunrise),
        "solar_noon_local": hhmm(solar.solar_noon),
        "sunset_local": hhmm(solar.sunset),
        "civil_dusk_local": hhmm(solar.civil_dusk),
        "moonrise_local": hhmm(moon.moonrise),
        "moonset_local": hhmm(moon.moonset),
        "moon_phase_name": moon.phase_name,
    }


EVALUATORS["solar_lunar"] = _evaluate_solar_lunar


@dataclass(frozen=True)
class Fixture:
    path: Path
    module: str
    description: str
    source: str
    inputs: dict
    expected: dict
    tolerance: dict

    @property
    def name(self) -> str:
        return self.path.stem


def load_fixtures() -> list[Fixture]:
    fixtures = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        fixtures.append(
            Fixture(
                path=path,
                module=raw["module"],
                description=raw.get("description", ""),
                source=raw.get("source", ""),
                inputs=raw["inputs"],
                expected=raw["expected"],
                tolerance=raw.get("tolerance", {}),
            )
        )
    return fixtures


def _parse_tolerance(spec) -> float:
    """Return a numeric tolerance. '120s' -> 120.0 seconds; a bare number -> itself."""
    if isinstance(spec, (int, float)):
        return float(spec)
    s = str(spec).strip()
    if s.endswith("s"):
        return float(s[:-1])
    return float(s)


def compare(expected: dict, computed: dict, tolerance: dict) -> list[str]:
    """Return a list of human-readable mismatch messages (empty == pass)."""
    problems = []
    for key, exp in expected.items():
        if key not in computed:
            problems.append(f"{key}: not computed")
            continue
        got = computed[key]
        tol = tolerance.get(key)
        if tol is None:
            if got != exp:
                problems.append(f"{key}: expected {exp!r}, got {got!r} (exact match required)")
            continue
        # Numeric / time tolerance.
        allowed = _parse_tolerance(tol)
        diff = _delta(exp, got)
        if diff is None:
            problems.append(f"{key}: cannot compare {exp!r} vs {got!r} with tolerance")
        elif diff > allowed:
            problems.append(f"{key}: expected {exp!r}, got {got!r} (Δ{diff:.1f} > {allowed})")
    return problems


def _delta(a, b) -> float | None:
    """Absolute difference in comparable units (seconds for HH:MM, else numeric)."""
    for parser in (_as_seconds, _as_float):
        pa, pb = parser(a), parser(b)
        if pa is not None and pb is not None:
            return abs(pa - pb)
    return None


def _as_seconds(v) -> float | None:
    if isinstance(v, str) and ":" in v:
        try:
            t = datetime.strptime(v, "%H:%M")
        except ValueError:
            return None
        return t.hour * 3600 + t.minute * 60
    return None


def _as_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None
