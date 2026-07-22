"""Tests for the timebase service — what the clock believes, and how firmly."""

from datetime import UTC, datetime, timedelta

from coucal.hal.interfaces import TimeQuality, TimeReading
from coucal.services.timebase import (
    DRIFTING,
    EXACT,
    GOOD,
    UNKNOWN,
    Timebase,
)


class FakeSource:
    """A TimeSource we can drive precisely."""

    def __init__(self, utc, quality=TimeQuality.GPS, holdover_days=0.0):
        self.reading = TimeReading(utc, quality, holdover_days)
        self.disciplined: list[datetime] = []

    def set(self, utc=None, quality=None, holdover_days=None):
        self.reading = TimeReading(
            utc if utc is not None else self.reading.utc,
            quality if quality is not None else self.reading.quality,
            holdover_days if holdover_days is not None else self.reading.holdover_days,
        )

    def now(self):
        return self.reading

    def discipline_rtc(self, utc):
        self.disciplined.append(utc)


T0 = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def test_confidence_vocabulary():
    src = FakeSource(T0)
    tb = Timebase(src, holdover_warn_days=30)
    assert tb.read().confidence == EXACT

    src.set(quality=TimeQuality.RTC, holdover_days=5)
    assert tb.read().confidence == GOOD

    src.set(quality=TimeQuality.RTC_STALE, holdover_days=200)
    assert tb.read().confidence == DRIFTING

    src.set(quality=TimeQuality.UNKNOWN)
    assert tb.read().confidence == UNKNOWN


def test_unknown_time_is_not_trustworthy():
    src = FakeSource(T0, quality=TimeQuality.UNKNOWN)
    assert not Timebase(src).read().is_trustworthy


def test_drift_estimate_grows_with_holdover():
    src = FakeSource(T0, quality=TimeQuality.RTC, holdover_days=365)
    status = Timebase(src).read()
    # DS3231 is about 2 minutes per year.
    assert timedelta(seconds=100) < status.estimated_drift < timedelta(seconds=140)


def test_civil_time_never_runs_backwards():
    """A glitching source must not rewind the clock: the voice scheduler would re-fire
    a call it already made, and the heartbeat would appear to stall."""
    src = FakeSource(T0)
    tb = Timebase(src)
    first = tb.read()

    src.set(utc=T0 - timedelta(hours=3))
    second = tb.read()

    assert second.utc == first.utc
    assert second.went_backwards


def test_forward_time_advances_normally():
    src = FakeSource(T0)
    tb = Timebase(src)
    tb.read()
    src.set(utc=T0 + timedelta(minutes=5))
    status = tb.read()
    assert status.utc == T0 + timedelta(minutes=5)
    assert not status.went_backwards


def test_rtc_is_disciplined_from_gps_but_only_once_a_day():
    src = FakeSource(T0)
    tb = Timebase(src)

    assert tb.discipline_if_due() is True
    assert src.disciplined == [T0]

    # Too soon.
    src.set(utc=T0 + timedelta(hours=1))
    assert tb.discipline_if_due() is False

    # A day later.
    src.set(utc=T0 + timedelta(hours=25))
    assert tb.discipline_if_due() is True
    assert len(src.disciplined) == 2


def test_rtc_is_never_disciplined_from_a_holdover_reading():
    """Writing a drifting time back into the RTC would launder a guess into something
    that looks authoritative."""
    src = FakeSource(T0, quality=TimeQuality.RTC, holdover_days=90)
    tb = Timebase(src)
    assert tb.discipline_if_due() is False
    assert src.disciplined == []
