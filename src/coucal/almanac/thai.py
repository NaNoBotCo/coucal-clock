"""The Thai reckoning — Buddhist Era, the lunar month, and wan phra.

This is the module that matters most to the people the clock is actually for. A visitor
to the wat does not need to know the Gregorian date; they need to know **what lunar day
it is** and **when the next wan phra falls**, because that is when one comes to make
merit. Getting it wrong would send someone to the temple on the wrong morning, so this
module never guesses.

## Where the truth comes from

Per the design brief, the **published Thai calendar is the authority**. Its intercalation
is decided by human authority, not derived from the sky, so an astronomical calculation
can legitimately disagree with it — and when it does, the calendar wins.

So the bundled table in ``data/tables/`` is the source of truth. Each row fixes the
lunar designation of one Gregorian date; days between anchors are derived by simple
counting, and every anchor is re-verified against that derivation in the tests.

## Honest limits

The table currently covers **2569 BE (2026 CE) only**. Outside it, ``thai_day`` returns
a record with ``known=False`` rather than extrapolating. The clock then shows the
Buddhist year — which is always computable — and says plainly that it does not know the
lunar day. Before donation this table must be extended and Eade's arithmetic rules
implemented, with the table kept as the cross-check.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

_TABLE_DIR = Path(__file__).resolve().parents[3] / "data" / "tables"

# Buddhist Era is ahead of the Common Era by this much. Thailand has begun the BE year
# on 1 January since 1941, so for any date after that the offset is a constant.
BE_OFFSET = 543

WAXING = "waxing"  # ขึ้น — the moon growing toward full
WANING = "waning"  # แรม — the moon shrinking toward dark

# --- Thai words, for a face that speaks Thai first -------------------------

THAI_DIGITS = "๐๑๒๓๔๕๖๗๘๙"

# Lunar month names. Month 1 is เดือนอ้าย, month 2 เดือนยี่, then plain numbers.
THAI_MONTH_NAMES = {
    1: "เดือนอ้าย",
    2: "เดือนยี่",
    3: "เดือนสาม",
    4: "เดือนสี่",
    5: "เดือนห้า",
    6: "เดือนหก",
    7: "เดือนเจ็ด",
    8: "เดือนแปด",
    "8b": "เดือนแปดสอง",  # the intercalary eighth month of an adhikamasa year
    9: "เดือนเก้า",
    10: "เดือนสิบ",
    11: "เดือนสิบเอ็ด",
    12: "เดือนสิบสอง",
}

THAI_WEEKDAYS = (
    "วันจันทร์",  # Monday — Python's weekday() starts here
    "วันอังคาร",
    "วันพุธ",
    "วันพฤหัสบดี",
    "วันศุกร์",
    "วันเสาร์",
    "วันอาทิตย์",
)

THAI_SOLAR_MONTHS = (
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
)

# The 12-year animal cycle (นักษัตร).
THAI_ANIMALS = (
    "ชวด",  # rat
    "ฉลู",  # ox
    "ขาล",  # tiger
    "เถาะ",  # rabbit
    "มะโรง",  # dragon
    "มะเส็ง",  # snake
    "มะเมีย",  # horse
    "มะแม",  # goat
    "วอก",  # monkey
    "ระกา",  # rooster
    "จอ",  # dog
    "กุน",  # pig
)


def thai_numerals(value: int | str) -> str:
    """Render digits as Thai numerals — ๑๕ rather than 15."""
    return "".join(THAI_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(value))


def buddhist_year(day: date) -> int:
    """พ.ศ. for a Gregorian date. Always computable, table or no table."""
    return day.year + BE_OFFSET


def animal_year(day: date) -> str:
    """The นักษัตร animal for the year.

    Approximate at the year boundary: the animal year properly turns with the lunar
    new year, not 1 January. Flagged rather than hidden — refining it belongs with the
    full algorithm.
    """
    return THAI_ANIMALS[(day.year + 543 + 5) % 12]


@dataclass(frozen=True)
class ThaiDay:
    """The Thai reckoning of one day."""

    gregorian: date
    buddhist_year: int
    known: bool  # False when the date falls outside the authority table
    phase: str | None = None  # WAXING (ขึ้น) or WANING (แรม)
    day: int | None = None  # ค่ำ, 1..15
    month: int | str | None = None  # 1..12, or "8b" for the intercalary eighth
    is_wan_phra: bool = False
    waning_length: int | None = None  # 14 or 15 — the month's short or full waning half

    # --- Thai renderings ---------------------------------------------------
    @property
    def lunar_text(self) -> str:
        """e.g. 'ขึ้น ๑๕ ค่ำ เดือนแปดสอง' — how the day is actually spoken."""
        if not self.known:
            return "ไม่ทราบข้างขึ้นข้างแรม"  # "the lunar day is not known"
        word = "ขึ้น" if self.phase == WAXING else "แรม"
        month_name = THAI_MONTH_NAMES.get(self.month, "")
        return f"{word} {thai_numerals(self.day)} ค่ำ {month_name}".strip()

    @property
    def weekday_text(self) -> str:
        return THAI_WEEKDAYS[self.gregorian.weekday()]

    @property
    def solar_text(self) -> str:
        """e.g. '๒๐ กรกฎาคม ๒๕๖๙' — Gregorian day and month, Buddhist year."""
        d = thai_numerals(self.gregorian.day)
        m = THAI_SOLAR_MONTHS[self.gregorian.month - 1]
        y = thai_numerals(self.buddhist_year)
        return f"{d} {m} {y}"


# --------------------------------------------------------------------------- #
# The authority table
# --------------------------------------------------------------------------- #


def _parse_month(raw: str) -> int | str:
    return raw if raw.endswith("b") else int(raw)


@lru_cache(maxsize=4)
def _load_anchors(path: str | None = None) -> tuple[tuple[date, str, int, int | str], ...]:
    table = Path(path) if path else _TABLE_DIR / "thai_lunar_2569.csv"
    if not table.exists():
        return ()
    rows: list[tuple[date, str, int, int | str]] = []
    with table.open(encoding="utf-8") as fh:
        for row in csv.reader(line for line in fh if not line.startswith("#")):
            if not row or len(row) < 4:
                continue
            rows.append((date.fromisoformat(row[0]), row[1], int(row[2]), _parse_month(row[3])))
    return tuple(sorted(rows))


def _waning_lengths(anchors) -> dict[int | str, int]:
    """How long each month's waning half runs — 14 (short) or 15 (full).

    Read from the published anchors rather than assumed, because this is precisely what
    decides whether the month's last wan phra falls on แรม ๑๔ or แรม ๑๕ ค่ำ.
    """
    lengths: dict[int | str, int] = {}
    for _, phase, day, month in anchors:
        if phase == WANING and day in (14, 15):
            lengths[month] = day
    return lengths


def _step(phase: str, day: int, month, waning_length: int, next_month):
    """Advance one day, rolling over the half-month and the month."""
    day += 1
    if phase == WAXING and day > 15:
        return WANING, 1, month
    if phase == WANING and day > waning_length:
        # A new month opens with ขึ้น ๑ ค่ำ. Its identity comes from the anchor we are
        # walking towards — the published calendar names the month, we only count days.
        return WAXING, 1, next_month
    return phase, day, month


@lru_cache(maxsize=4)
def _build_calendar(path: str | None = None) -> dict[date, tuple[str, int, int | str, int]]:
    """Expand the anchors into a day-by-day map.

    Between each pair of consecutive anchors we simply count, rolling over half-months
    and months as we go — then assert we land exactly on the next published anchor. That
    assertion is the whole safety argument: the published calendar supplies the truth at
    ~50 points in the year, and counting cannot drift more than a few days before being
    caught.
    """
    anchors = _load_anchors(path)
    if not anchors:
        return {}

    lengths = _waning_lengths(anchors)
    calendar: dict[date, tuple[str, int, int | str, int]] = {}

    def waning_len(month) -> int:
        return lengths.get(month, 15)

    for (a_date, a_phase, a_day, a_month), (b_date, b_phase, b_day, b_month) in zip(
        anchors, anchors[1:], strict=False
    ):
        cursor, phase, day, month = a_date, a_phase, a_day, a_month
        while cursor < b_date:
            calendar[cursor] = (phase, day, month, waning_len(month))
            phase, day, month = _step(phase, day, month, waning_len(month), b_month)
            cursor += timedelta(days=1)
        if (phase, day, month) != (b_phase, b_day, b_month):  # pragma: no cover
            raise ValueError(
                f"Thai calendar derivation drifted: counting from {a_date} reached "
                f"{phase} {day} month {month} at {b_date}, but the published calendar "
                f"says {b_phase} {b_day} month {b_month}. Check the table."
            )

    # The final anchor's own day, and a backfill to the start of the first anchor's
    # half-month so the table does not begin mid-air.
    last_date, last_phase, last_day, last_month = anchors[-1]
    calendar[last_date] = (last_phase, last_day, last_month, waning_len(last_month))

    first_date, first_phase, first_day, first_month = anchors[0]
    for back in range(1, first_day):
        calendar[first_date - timedelta(days=back)] = (
            first_phase,
            first_day - back,
            first_month,
            waning_len(first_month),
        )

    return calendar


def is_wan_phra(phase: str, day: int, waning_length: int) -> bool:
    """The rule, stated plainly.

    Wan phra (วันพระ, the Buddhist sabbath) falls on ขึ้น ๘ ค่ำ, ขึ้น ๑๕ ค่ำ, แรม ๘ ค่ำ,
    and the last day of the waning half — which is แรม ๑๕ ค่ำ in a full month but
    แรม ๑๔ ค่ำ in a short one.
    """
    if phase == WAXING:
        return day in (8, 15)
    return day == 8 or day == waning_length


def thai_day(day: date, table_path: str | None = None) -> ThaiDay:
    """The Thai reckoning of a Gregorian date.

    Outside the bundled table this returns ``known=False`` rather than extrapolating.
    The Buddhist year is still given, because it is always computable.
    """
    calendar = _build_calendar(table_path)
    entry = calendar.get(day)
    if entry is None:
        return ThaiDay(gregorian=day, buddhist_year=buddhist_year(day), known=False)

    phase, lunar_day, month, waning_length = entry
    return ThaiDay(
        gregorian=day,
        buddhist_year=buddhist_year(day),
        known=True,
        phase=phase,
        day=lunar_day,
        month=month,
        is_wan_phra=is_wan_phra(phase, lunar_day, waning_length),
        waning_length=waning_length,
    )


def next_wan_phra(
    after: date, limit_days: int = 40, table_path: str | None = None
) -> ThaiDay | None:
    """The next wan phra strictly after ``after``, or None if beyond the table."""
    for offset in range(1, limit_days + 1):
        candidate = thai_day(after + timedelta(days=offset), table_path)
        if candidate.known and candidate.is_wan_phra:
            return candidate
    return None


def table_span(table_path: str | None = None) -> tuple[date, date] | None:
    """What the authority table actually covers — for the clock's honest limits."""
    calendar = _build_calendar(table_path)
    if not calendar:
        return None
    days = sorted(calendar)
    return days[0], days[-1]
