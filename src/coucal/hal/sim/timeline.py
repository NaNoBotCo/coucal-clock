"""A controllable virtual clock — the engine behind "test years in minutes".

The device's almanac and faces are pure functions of civil time, so aging the
whole system is just a matter of advancing this one object. The simulator GUI
scrubs it; the fake ``PowerController`` fast-forwards it across a sleep; tests set
it to an exact instant.

There is no real wall-clock coupling unless ``rate`` is set and ``tick`` is called
by an animation loop — deterministic tests use ``set`` / ``advance`` only.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta


class SimTimeline:
    def __init__(self, start_utc: datetime, rate: float = 0.0) -> None:
        if start_utc.tzinfo is None:
            raise ValueError("start_utc must be timezone-aware (use UTC)")
        self._now = start_utc.astimezone(UTC)
        self.rate = rate  # virtual seconds advanced per wall second when ticking; 0 = paused
        # Holdover simulation: pretend GPS was last seen this many days ago.
        self.holdover_days = 0.0
        self.gps_available = True

    # --- reading -----------------------------------------------------------
    def now(self) -> datetime:
        return self._now

    # --- explicit control (deterministic; used by tests and GUI buttons) ---
    def set(self, utc: datetime) -> None:
        if utc.tzinfo is None:
            raise ValueError("utc must be timezone-aware")
        self._now = utc.astimezone(UTC)

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)

    def jump(self, delta: timedelta) -> None:
        self._now += delta

    # --- wall-driven animation (interactive simulator only) ----------------
    def tick(self, wall_elapsed_s: float) -> None:
        """Advance virtual time by ``rate * wall_elapsed_s`` (no-op when paused)."""
        if self.rate:
            self._now += timedelta(seconds=self.rate * wall_elapsed_s)
