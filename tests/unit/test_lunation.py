"""Tests for the lunation gear — the monthly reset that keeps the moon dial honest."""

import math
from datetime import UTC, datetime, timedelta

import pytest

from coucal.almanac.ephemeris import Observer, get_sky
from coucal.almanac.lunation import (
    MEAN_SYNODIC_DAYS,
    disc_angle_for_phase,
    lunation_at,
)

TEMPLE = Observer(18.85, 99.05, 320.0, "Asia/Bangkok")


@pytest.fixture(scope="module")
def sky():
    return get_sky(TEMPLE)


def test_the_gear_resets_exactly_at_every_new_moon(sky):
    """THE point of the module: once a month the gear re-datums against the sky, so
    nothing accumulates and nothing drifts."""
    when = datetime(2026, 6, 1, tzinfo=UTC)
    for _ in range(6):
        lun = lunation_at(sky, when)
        just_after_new = lunation_at(sky, lun.next_new + timedelta(seconds=1))
        assert just_after_new.fraction == pytest.approx(0.0, abs=1e-5), (
            "the gear did not return to its datum at the new moon"
        )
        when = lun.next_new + timedelta(days=5)


def test_a_full_turn_takes_two_lunations(sky):
    """Two moons on one disc means 180 deg a month — a whole turn every two."""
    when = datetime(2026, 6, 1, tzinfo=UTC)
    first = lunation_at(sky, when)
    # Sample just after two successive new moons: the gear must have advanced 360 deg.
    second = lunation_at(sky, first.next_new + timedelta(days=1))
    third = lunation_at(sky, second.next_new + timedelta(days=1))
    assert second.number == first.number + 1
    assert third.number == first.number + 2
    assert third.parity == first.parity, "parity must return after two lunations"
    assert second.parity != first.parity, "and alternate between them"


def test_the_two_moons_take_alternate_months(sky):
    """Which moon is in the window flips every lunation, exactly as on a real disc."""
    from coucal.faces.ornament import crossing_index

    when = datetime(2026, 3, 10, tzinfo=UTC)
    seen = []
    for _ in range(6):
        lun = lunation_at(sky, when)
        seen.append(crossing_index(lun.disc_angle_deg))
        when = lun.next_new + timedelta(days=8)
    for a, b in zip(seen, seen[1:], strict=False):
        assert a != b, f"the same moon crossed twice running: {seen}"


def test_the_lunation_number_is_stable_within_a_month(sky):
    """It must increment once per month, not wobble as the clock ticks."""
    lun = lunation_at(sky, datetime(2026, 7, 1, tzinfo=UTC))
    when = lun.last_new + timedelta(hours=6)
    numbers = set()
    while when < lun.next_new - timedelta(hours=6):
        numbers.add(lunation_at(sky, when).number)
        when += timedelta(days=3)
    assert len(numbers) == 1, f"the count changed mid-month: {numbers}"


def test_the_synodic_month_really_does_vary(sky):
    """The reason the gear is driven by elongation rather than elapsed time."""
    when = datetime(2026, 1, 15, tzinfo=UTC)
    lengths = []
    for _ in range(12):
        lun = lunation_at(sky, when)
        lengths.append(lun.length_days)
        when = lun.next_new + timedelta(days=2)
    assert max(lengths) - min(lengths) > 0.3, (
        "expected real variation in the synodic month; a constant-rate time gear "
        "would drift by hours against it"
    )
    assert all(29.0 < length < 30.1 for length in lengths)


def test_a_time_gear_would_be_the_dominant_error(sky):
    """Documents the measurement that shaped the design: a constant-rate gear synced
    only at new moon is far worse than the dial's own geometry (about 1 point)."""
    lun = lunation_at(sky, datetime(2026, 2, 1, tzinfo=UTC))
    span = lun.next_new - lun.last_new
    worst = 0.0
    for k in range(1, 60):
        f = k / 60.0
        at = lunation_at(sky, lun.last_new + span * f)
        true_k = (1 - math.cos(math.radians(at.phase_angle_deg))) / 2
        gear_k = (1 - math.cos(math.radians(360.0 * f))) / 2
        worst = max(worst, abs(true_k - gear_k))
    assert worst > 0.02, (
        "a pure time gear looked accurate here — re-check before simplifying the module"
    )


def test_disc_angle_helper_matches_the_gear(sky):
    lun = lunation_at(sky, datetime(2026, 9, 20, tzinfo=UTC))
    assert disc_angle_for_phase(lun.phase_angle_deg, lun.parity) == pytest.approx(
        lun.disc_angle_deg, abs=1e-9
    )


def test_age_and_length_are_sane(sky):
    lun = lunation_at(sky, datetime(2026, 5, 5, tzinfo=UTC))
    assert 0.0 <= lun.age_days <= lun.length_days
    assert lun.length_days == pytest.approx(MEAN_SYNODIC_DAYS, abs=0.6)
    assert lun.last_new < lun.next_new


def test_naive_datetime_is_refused(sky):
    with pytest.raises(ValueError):
        lunation_at(sky, datetime(2026, 5, 5))
