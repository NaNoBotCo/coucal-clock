"""Knowing what time it is, and how much to trust that.

Sits directly above the HAL's ``TimeSource``. The hardware layer reports *what it can
see* (a GPS fix, or the holdover RTC); this service decides what the clock should
*believe*, keeps civil time moving forwards, disciplines the RTC while a fix is
available, and — most importantly — says out loud when it is no longer sure.

The governing principle: **a confident wrong time is the worst failure this clock can
have.** A monk planning wan phra from a display that silently drifted is worse served
than one told plainly that the clock has been running blind for eight months. So
uncertainty is surfaced, never smoothed over.

Holdover: the DS3231 drifts roughly 2 minutes per year. That is excellent — good enough
that the clock stays useful for years without a satellite — but it is not nothing, and
the estimate below is what the time-confidence glyph is drawn from.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..hal.interfaces import TimeQuality, TimeReading, TimeSource

# DS3231 datasheet accuracy is ±2 ppm over the temple's temperature range, which works
# out near 2 minutes per year. Stated as seconds/day so the estimate is obvious.
DS3231_DRIFT_SECONDS_PER_DAY = 120.0 / 365.0

# Re-set the RTC from GPS at most this often — writes are cheap but not free, and a
# daily discipline is far more than enough for a 2 min/year part.
DISCIPLINE_INTERVAL = timedelta(hours=24)

# Confidence vocabulary. These names appear in the maintenance manual, so they are part
# of the clock's contract with whoever cares for it — do not rename casually.
EXACT = "exact"  # live satellite fix
GOOD = "good"  # holdover, within the configured horizon
DRIFTING = "drifting"  # holdover, beyond the horizon — believable but ageing
UNKNOWN = "unknown"  # no trustworthy source at all


@dataclass(frozen=True)
class TimeStatus:
    """What the clock believes, and how firmly."""

    utc: datetime
    confidence: str
    holdover_days: float
    estimated_drift_seconds: float
    went_backwards: bool = False  # a source handed us an earlier time than last read

    @property
    def is_trustworthy(self) -> bool:
        """Whether to show ordinary time, as opposed to admitting ignorance."""
        return self.confidence in (EXACT, GOOD, DRIFTING)

    @property
    def estimated_drift(self) -> timedelta:
        return timedelta(seconds=self.estimated_drift_seconds)


class Timebase:
    def __init__(self, source: TimeSource, holdover_warn_days: int = 30) -> None:
        self._source = source
        self._holdover_warn_days = holdover_warn_days
        self._last_utc: datetime | None = None
        self._last_disciplined: datetime | None = None

    # --- reading -----------------------------------------------------------
    def read(self) -> TimeStatus:
        reading = self._source.now()
        went_backwards = self._last_utc is not None and reading.utc < self._last_utc

        # Civil time must not run backwards between wakes: the voice scheduler would
        # re-fire a call it already made, and the heartbeat would appear to stall. If a
        # source hands us an earlier instant we hold the previous one and say so.
        utc = self._last_utc if (went_backwards and self._last_utc) else reading.utc
        self._last_utc = utc

        return TimeStatus(
            utc=utc,
            confidence=self._confidence(reading),
            holdover_days=reading.holdover_days,
            estimated_drift_seconds=reading.holdover_days * DS3231_DRIFT_SECONDS_PER_DAY,
            went_backwards=went_backwards,
        )

    def _confidence(self, reading: TimeReading) -> str:
        if reading.quality is TimeQuality.GPS:
            return EXACT
        if reading.quality is TimeQuality.UNKNOWN:
            return UNKNOWN
        if reading.holdover_days > self._holdover_warn_days:
            return DRIFTING
        return GOOD

    # --- disciplining ------------------------------------------------------
    def discipline_if_due(self) -> bool:
        """Push satellite time into the holdover RTC. Returns True if it did.

        Only ever while a fix is live — writing a drifting time back into the RTC would
        launder a guess into something that looks authoritative.
        """
        reading = self._source.now()
        if reading.quality is not TimeQuality.GPS:
            return False
        if (
            self._last_disciplined is not None
            and reading.utc - self._last_disciplined < DISCIPLINE_INTERVAL
        ):
            return False
        self._source.discipline_rtc(reading.utc)
        self._last_disciplined = reading.utc
        return True
