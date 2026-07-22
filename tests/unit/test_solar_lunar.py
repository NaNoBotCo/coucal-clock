"""Unit tests for the sun/moon core.

The golden fixtures check us against published USNO values. These check the properties
*no* published table can: internal consistency, correct behaviour at the edges, and
that the module tells the truth about its own limits.
"""

from datetime import date, datetime, timedelta

import pytest

from coucal.almanac.ephemeris import Observer, ephemeris_span, get_sky
from coucal.almanac.solar_lunar import moon_state, next_coucal_calls, sun_day

TEMPLE = Observer(18.85, 99.05, 320.0, "Asia/Bangkok")


@pytest.fixture(scope="module")
def sky():
    return get_sky(TEMPLE)


# --- the sun ---------------------------------------------------------------


def test_twilights_nest_in_the_correct_order(sky):
    """Astronomical dawn precedes nautical precedes civil precedes sunrise, and the
    evening mirrors it. If this ever inverts, a depression angle has the wrong sign."""
    d = sun_day(sky, date(2026, 3, 21))
    assert (
        d.astronomical_dawn
        < d.nautical_dawn
        < d.civil_dawn
        < d.sunrise
        < d.solar_noon
        < d.sunset
        < d.civil_dusk
        < d.nautical_dusk
        < d.astronomical_dusk
    )


def test_solar_noon_sits_between_sunrise_and_sunset(sky):
    for month in (1, 4, 7, 10):
        d = sun_day(sky, date(2026, month, 15))
        assert d.sunrise < d.solar_noon < d.sunset


def test_day_length_is_longest_near_the_june_solstice(sky):
    june = sun_day(sky, date(2026, 6, 21)).day_length
    december = sun_day(sky, date(2026, 12, 21)).day_length
    march = sun_day(sky, date(2026, 3, 21)).day_length
    assert june > march > december
    # At 18.85 N the swing is real but modest — roughly 13h05m to 11h10m.
    assert timedelta(hours=12, minutes=30) < june < timedelta(hours=13, minutes=30)
    assert timedelta(hours=10, minutes=30) < december < timedelta(hours=11, minutes=30)


def test_equinox_day_is_close_to_twelve_hours(sky):
    """Refraction and the upper-limb convention make it slightly longer than 12h."""
    length = sun_day(sky, date(2026, 3, 20)).day_length
    assert timedelta(hours=11, minutes=55) < length < timedelta(hours=12, minutes=15)


def test_every_day_of_a_year_has_a_sunrise_and_sunset(sky):
    """At this latitude the sun always rises. A None here means the finder failed."""
    day = date(2026, 1, 1)
    while day.year == 2026:
        s = sun_day(sky, day)
        assert s.sunrise is not None and s.sunset is not None, f"no sun on {day}"
        day += timedelta(days=40)  # sample the year rather than all 365


# --- the moon --------------------------------------------------------------


def test_illumination_is_near_zero_at_new_moon_and_full_at_full(sky):
    """Checked at the exact phase instants the module itself predicts — so this also
    verifies that the phase-event finder and the illumination agree with each other."""
    m = moon_state(sky, datetime(2026, 1, 1, 12, 0, tzinfo=TEMPLE.tz))

    at_new = moon_state(sky, m.next_new_moon)
    assert at_new.illumination < 0.01
    assert at_new.phase_name == "New Moon"

    at_full = moon_state(sky, m.next_full_moon)
    assert at_full.illumination > 0.99
    assert at_full.phase_name == "Full Moon"


def test_next_new_and_full_are_within_a_synodic_month(sky):
    when = datetime(2026, 5, 5, 12, 0, tzinfo=TEMPLE.tz)
    m = moon_state(sky, when)
    for event in (m.next_new_moon, m.next_full_moon):
        assert when <= event <= when + timedelta(days=30)


def test_waxing_flag_matches_the_phase_angle(sky):
    for month in range(1, 13):
        m = moon_state(sky, datetime(2026, month, 10, 12, 0, tzinfo=TEMPLE.tz))
        assert m.is_waxing == (m.phase_angle_deg < 180.0)


def test_moon_may_legitimately_skip_a_rise_or_set(sky):
    """The moon rises ~50 min later each day, so some local days genuinely have no
    moonrise. The module must return None rather than inventing one."""
    missing = 0
    day = date(2026, 1, 1)
    for _ in range(60):
        m = moon_state(sky, datetime(day.year, day.month, day.day, 12, 0, tzinfo=TEMPLE.tz))
        if m.moonrise is None or m.moonset is None:
            missing += 1
        day += timedelta(days=1)
    assert missing > 0, "expected at least one day in two months with no moonrise or moonset"


# --- the coucal ------------------------------------------------------------


def test_coucal_calls_are_in_the_future_and_drift_through_the_year(sky):
    midday = datetime(2026, 7, 20, 10, 0, tzinfo=TEMPLE.tz)
    dawn, dusk = next_coucal_calls(sky, midday)
    assert dawn >= midday and dusk >= midday

    # The whole point of computing the call: it must not be a fixed clock time.
    january = next_coucal_calls(sky, datetime(2026, 1, 20, 0, 1, tzinfo=TEMPLE.tz))[0]
    july = next_coucal_calls(sky, datetime(2026, 7, 20, 0, 1, tzinfo=TEMPLE.tz))[0]
    assert january.time() != july.time()
    assert abs((january.hour * 60 + january.minute) - (july.hour * 60 + july.minute)) > 30, (
        "dawn should shift by more than half an hour between January and July"
    )


# --- honest limits ---------------------------------------------------------


def test_ephemeris_covers_the_span_the_brief_asked_for():
    """The brief named a 1550-2650 horizon. Verify the bundled kernel truly has it —
    de440s, the short variant, only reaches 2150 and would silently fall short."""
    start, end = ephemeris_span()
    assert start.year <= 1550
    assert end.year >= 2650


def test_sky_reports_whether_it_covers_a_moment(sky):
    assert sky.covers(datetime(2026, 7, 20, 12, 0, tzinfo=TEMPLE.tz))
    assert not sky.covers(datetime(3000, 1, 1, 12, 0, tzinfo=TEMPLE.tz))
