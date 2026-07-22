"""Tests for the Thai reckoning.

The load-bearing one is ``test_every_published_anchor_is_reproduced``: the day-by-day
calendar is *derived* by counting between anchors, so if the derivation and the published
Thai calendar ever disagree, that test fails loudly. Wan phra is when people come to the
temple; a silent off-by-one here is the worst bug this project could ship.
"""

from datetime import date, timedelta

import pytest

from coucal.almanac.thai import (
    WANING,
    WAXING,
    _load_anchors,
    buddhist_year,
    is_wan_phra,
    next_wan_phra,
    table_span,
    thai_day,
    thai_numerals,
)

# --- the Buddhist year -----------------------------------------------------


def test_buddhist_year():
    assert buddhist_year(date(2026, 7, 20)) == 2569
    assert buddhist_year(date(2026, 1, 1)) == 2569
    assert buddhist_year(date(2027, 1, 1)) == 2570


def test_thai_numerals():
    assert thai_numerals(15) == "๑๕"
    assert thai_numerals(2569) == "๒๕๖๙"
    assert thai_numerals(8) == "๘"


# --- the authority table ---------------------------------------------------


def test_anchors_load():
    anchors = _load_anchors()
    assert len(anchors) == 50, "expected the full published 2569 table"


def test_every_published_anchor_is_reproduced():
    """THE test. Each anchor is a published fact; the calendar between anchors is
    derived by counting. If counting drifts, this catches it at the next anchor."""
    problems = []
    for anchor_date, phase, day, month in _load_anchors():
        got = thai_day(anchor_date)
        if not got.known:
            problems.append(f"{anchor_date}: not in derived calendar")
        elif (got.phase, got.day, got.month) != (phase, day, month):
            problems.append(
                f"{anchor_date}: published {phase} {day} month {month}, "
                f"derived {got.phase} {got.day} month {got.month}"
            )
    assert not problems, "derivation disagrees with the published calendar:\n  " + "\n  ".join(
        problems
    )


def test_intercalary_eighth_month_is_present():
    """2569 is an adhikamasa year — the eighth month is doubled. This is exactly the
    case a naive algorithm gets wrong, which is why the table is the authority."""
    asalha = thai_day(date(2026, 7, 29))
    assert asalha.known
    assert asalha.month == "8b"
    assert asalha.phase == WAXING and asalha.day == 15
    assert "เดือนแปดสอง" in asalha.lunar_text

    # Khao Phansa, the start of Vassa, is the following day.
    khao_phansa = thai_day(date(2026, 7, 30))
    assert khao_phansa.phase == WANING and khao_phansa.day == 1


# --- wan phra --------------------------------------------------------------


def test_wan_phra_rule():
    # Waxing 8 and 15 are always wan phra.
    assert is_wan_phra(WAXING, 8, 15)
    assert is_wan_phra(WAXING, 15, 15)
    assert not is_wan_phra(WAXING, 14, 15)
    # Waning 8 always; and the last day, which depends on the month's length.
    assert is_wan_phra(WANING, 8, 15)
    assert is_wan_phra(WANING, 15, 15)
    assert not is_wan_phra(WANING, 14, 15)
    # In a short month the last waning day is the 14th.
    assert is_wan_phra(WANING, 14, 14)


def test_published_wan_phra_days_are_detected():
    """Spot-check against dates the published calendar lists as wan phra."""
    for d in (date(2026, 1, 3), date(2026, 2, 16), date(2026, 7, 29), date(2026, 12, 24)):
        assert thai_day(d).is_wan_phra, f"{d} should be wan phra"


def test_khao_phansa_is_not_a_wan_phra():
    """แรม ๑ ค่ำ is a major religious day but not a sabbath — the distinction matters."""
    assert not thai_day(date(2026, 7, 30)).is_wan_phra


def test_wan_phra_recur_roughly_weekly():
    """Consecutive wan phra sit 6-9 days apart: waxing 8 -> 15 is seven days, 15 ->
    waning 8 is eight, and the last two gaps vary with the month's waning length.

    Measured between actual wan phra, not from an arbitrary start date — the first
    interval from a random day is meaninglessly short.
    """
    first = next_wan_phra(date(2026, 2, 1))
    assert first is not None
    d = first.gregorian
    gaps = []
    for _ in range(10):
        nxt = next_wan_phra(d)
        assert nxt is not None
        gaps.append((nxt.gregorian - d).days)
        d = nxt.gregorian
    assert all(6 <= g <= 9 for g in gaps), f"implausible wan phra spacing: {gaps}"


# --- honest limits ---------------------------------------------------------


def test_dates_outside_the_table_are_admitted_not_guessed():
    """The clock must never invent a lunar day. Outside the table it says so — while
    still giving the Buddhist year, which is always computable."""
    far = thai_day(date(2040, 5, 1))
    assert not far.known
    assert far.day is None and far.phase is None
    assert far.buddhist_year == 2583
    assert far.lunar_text == "ไม่ทราบข้างขึ้นข้างแรม"


def test_table_span_is_reported():
    """The span covers 2026. It reaches slightly back into December 2025 because the
    first anchor is ขึ้น ๑๕ ค่ำ, and the waxing half it belongs to began in the previous
    month — backfilling within one half-month is plain counting, not extrapolation."""
    span = table_span()
    assert span is not None
    start, end = span
    assert start <= date(2026, 1, 1)
    assert end.year == 2026 and end.month == 12


def test_next_wan_phra_returns_none_past_the_table():
    assert next_wan_phra(date(2040, 1, 1)) is None


# --- Thai rendering --------------------------------------------------------


def test_lunar_text_reads_as_thai():
    d = thai_day(date(2026, 1, 3))
    assert d.lunar_text.startswith("ขึ้น ๑๕ ค่ำ")
    assert d.weekday_text.startswith("วัน")
    assert "๒๕๖๙" in d.solar_text


@pytest.mark.parametrize("offset", range(0, 360, 17))
def test_calendar_is_continuous_across_the_year(offset):
    """No gaps: every day inside the table's span must resolve."""
    span = table_span()
    day = span[0] + timedelta(days=offset)
    if day <= span[1]:
        assert thai_day(day).known, f"{day} fell into a hole in the derived calendar"
