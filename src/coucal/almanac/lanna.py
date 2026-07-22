"""The Lanna (Tai Yuan / ล้านนา) reckoning — for the wat this clock actually stands in.

Central Thai time is national; Lanna time is *local*. A monk in San Sai keeps the
Northern reckoning, and this module is what lets the clock speak it: the Chulasakarat
era, the Northern month names, the twelve-year animal cycle in its Lanna forms, and the
Northern festivals — ปี๋ใหม่เมือง, ยี่เป็ง, เข้าอินทขีล.

## Where each fact comes from — stated, because a sacred object must not bluff

* **The lunar day** (ขึ้น/แรม ค่ำ) is reused from :mod:`coucal.almanac.thai`, which reads a
  published authority table. Lanna and central Thai keep the *same* waxing/waning day;
  they differ only in what they *number the month*. So the day itself stays authority-
  backed, and this module never re-derives it.

* **The month offset.** Lan Na numbers its lunar months **two ahead** of the central
  reckoning — central เดือน ๑๒ (the Loy Krathong full moon) is Northern เดือนยี่ (month 2).
  Verified against Wikipedia, *Chula Sakarat* (regional month tables), 2026-07-20.

* **The Chulasakarat year.** CS = CE − 638, the year turning at Songkran in mid-April
  (epoch: 22 March 638 CE). Same source. Before Songkran a Gregorian year still belongs
  to the previous CS year, which is handled below.

* **The twelve animals** in their Lanna forms — ไจ้, เป้า, ยี, เหม้า … — are standard
  Northern calendrical usage. The corpus corroborates the living forms directly:
  ``ไจ้`` appears on 34 manuscript pages and ``เป้า`` on 18 in the digitised Lanna
  astrology manuscripts (crawler ``catalog.db``, genre = astrology). The full ordered
  list is documented tradition, marked as such.

## Honest limits

The lunar reckoning is only as wide as the Thai authority table (2026 for now); outside
it, ``lanna_day`` returns ``known=False`` and the face says so in Kam Mueang rather than
inventing a Northern month. The **sixty-name mื้อ day-cycle** (กาบไจ้ …) is deliberately
*not* computed here: it needs a verified epoch anchor we do not yet have, and a wrong
sexagenary name on a temple clock is worse than an absent one. It is an open door
(``docs/GROWING.md``), not a silent guess.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .thai import ThaiDay, thai_day, thai_numerals

# Chulasakarat: CS = CE - 638, turning at Songkran. Wikipedia, Chula Sakarat.
CS_OFFSET = 638
# Songkran — the solar new year and the CS year-boundary — falls 13-15 April; the CS
# year and the animal year turn with it. Approximated at 16 April; refining this to the
# astronomically-computed สังกรานต์ is a noted follow-up.
SONGKRAN_MONTH, SONGKRAN_DAY = 4, 16

# Lan Na is two lunar months ahead of the central Thai numbering.
LANNA_MONTH_OFFSET = 2

# Northern lunar month names (เดือน ... เหนือ). Month 1 is เจียง, month 2 ยี่ — after which
# Lanna, like the South, simply numbers them.
LANNA_MONTH_NAMES = {
    1: "เดือนเจียง",
    2: "เดือนยี่",
    3: "เดือนสาม",
    4: "เดือนสี่",
    5: "เดือนห้า",
    6: "เดือนหก",
    7: "เดือนเจ็ด",
    8: "เดือนแปด",
    9: "เดือนเก้า",
    10: "เดือนสิบ",
    11: "เดือนสิบเอ็ด",
    12: "เดือนสิบสอง",
}

# The twelve-year cycle in its Lanna (Tai) forms, with the central Thai equivalent.
# Order is canonical; ไจ้ and เป้า are directly attested in the manuscript corpus.
LANNA_ANIMALS = (
    ("ไจ้", "ชวด", "rat"),
    ("เป้า", "ฉลู", "ox"),
    ("ยี", "ขาล", "tiger"),
    ("เหม้า", "เถาะ", "rabbit"),
    ("สี", "มะโรง", "dragon"),
    ("ไส้", "มะเส็ง", "snake"),
    ("สะง้า", "มะเมีย", "horse"),
    ("เม็ด", "มะแม", "goat"),
    ("สัน", "วอก", "monkey"),
    ("เร้า", "ระกา", "rooster"),
    ("เส็ด", "จอ", "dog"),
    ("ไก๊", "กุน", "pig"),
)


def chulasakarat_year(day: date) -> int:
    """The Chulasakarat year, turning at Songkran (mid-April)."""
    cs = day.year - CS_OFFSET
    if (day.month, day.day) < (SONGKRAN_MONTH, SONGKRAN_DAY):
        cs -= 1
    return cs


def _animal_index(day: date) -> int:
    """Index into the twelve-year cycle, turning at Songkran.

    Cross-check: this is the same cycle central Thai keeps, so the Lanna animal must
    line up with :func:`coucal.almanac.thai.animal_year`. 2026 is ปีสะง้า / ปีมะเมีย.
    """
    year = day.year if (day.month, day.day) >= (SONGKRAN_MONTH, SONGKRAN_DAY) else day.year - 1
    return (year + 543 + 4) % 12


def lanna_animal(day: date) -> tuple[str, str, str]:
    """(Lanna name, central Thai name, English) for the year's animal."""
    return LANNA_ANIMALS[_animal_index(day)]


def _lanna_month(thai_month: int | str) -> tuple[int | str, str]:
    """Translate a central-Thai lunar month to its Northern number and name.

    The doubled eighth month of an adhikamasa year (``"8b"``) maps to a doubled tenth
    month in the North; it is given its own label so the face can show it honestly.
    """
    if thai_month == "8b":
        # Central second-eighth month -> Northern second-tenth month (เดือนสิบ, doubled).
        return "10b", "เดือนสิบ (สอง)"
    n = ((int(thai_month) - 1 + LANNA_MONTH_OFFSET) % 12) + 1
    return n, LANNA_MONTH_NAMES[n]


@dataclass(frozen=True)
class LannaDay:
    """The Northern reckoning of one day. Wraps the authority-backed Thai lunar day."""

    gregorian: date
    cs_year: int
    animal_lanna: str
    animal_thai: str
    known: bool
    phase: str | None = None
    day: int | None = None
    month: int | str | None = None
    month_name: str = ""
    is_wan_sin: bool = False  # วันศีล — the Northern name for the sabbath (wan phra)

    @property
    def lunar_text(self) -> str:
        """e.g. 'ขึ้น ๑๕ ค่ำ เดือนยี่' in the Northern month naming."""
        if not self.known:
            return "บ่ฮู้ข้างขึ้นข้างแฮม"  # Kam Mueang: "the lunar day is not known"
        word = "ขึ้น" if self.phase == "waxing" else "แฮม"  # Northern แฮม for แรม
        return f"{word} {thai_numerals(self.day)} ค่ำ {self.month_name}".strip()

    @property
    def year_text(self) -> str:
        """e.g. 'ปีสะง้า จ.ศ. ๑๓๘๘'."""
        return f"ปี{self.animal_lanna} จ.ศ. {thai_numerals(self.cs_year)}"


def lanna_day(day: date) -> LannaDay:
    """The Northern reckoning of a Gregorian date, built on the Thai authority table."""
    t: ThaiDay = thai_day(day)
    animal_lanna, animal_thai, _ = lanna_animal(day)
    cs = chulasakarat_year(day)

    if not t.known:
        return LannaDay(
            gregorian=day,
            cs_year=cs,
            animal_lanna=animal_lanna,
            animal_thai=animal_thai,
            known=False,
        )

    month_num, month_name = _lanna_month(t.month)
    return LannaDay(
        gregorian=day,
        cs_year=cs,
        animal_lanna=animal_lanna,
        animal_thai=animal_thai,
        known=True,
        phase=t.phase,
        day=t.day,
        month=month_num,
        month_name=month_name,
        is_wan_sin=t.is_wan_phra,  # the sabbath is the same day; the North calls it วันศีล
    )


# --------------------------------------------------------------------------- #
# Northern festivals (ประเพณีเมือง)
#
# Each is anchored either to a fixed solar date or to a lunar full moon already present
# in the Thai authority table — so the festivals inherit the table's authority and its
# limits. Only festivals we can anchor with confidence are listed; more can be added as
# the table grows. Full-moon observances (Makha/Visakha/Asalha) are pan-Thai but kept
# in the North, so they belong on a Northern face too.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Festival:
    name_lanna: str  # the Northern name, shown first
    name_thai: str  # central Thai name
    gregorian: date
    note: str = ""


# Fixed solar festivals (month, day) -> names. Songkran's public days are 13-15 April;
# the 13th (มหาสงกรานต์) is the anchor shown.
_SOLAR_FESTIVALS = {
    (4, 13): ("ปี๋ใหม่เมือง", "สงกรานต์", "Northern New Year — the water festival"),
}

# Lunar full-moon festivals, keyed by the *central Thai* month whose ขึ้น ๑๕ ค่ำ they
# fall on. The North reads the same full moon under its own month number, so the Northern
# name (เดือน...เป็ง / ยี่เป็ง) is *derived* from that number rather than hand-written —
# hand-written names had already drifted twice. เป็ง = the full moon.
_FULL_MOON_FESTIVALS = {
    3: ("มาฆบูชา", "Makha Bucha"),
    6: ("วิสาขบูชา", "Visakha Bucha"),
    8: ("อาสาฬหบูชา", "Asalha Bucha — eve of Vassa"),
    "8b": ("อาสาฬหบูชา", "Asalha Bucha — eve of Vassa"),
    12: ("ลอยกระทง", "Yi Peng — the lantern festival"),
}


def _peng_name(lanna_month: int | str) -> str:
    """The Northern full-moon festival name for a Lanna month: 'เดือนสิบเป็ง' etc."""
    n = 10 if lanna_month == "10b" else int(lanna_month)
    if n == 2:
        return "ยี่เป็ง"  # the one everyone knows by name, not by number
    return f"{LANNA_MONTH_NAMES[n]}เป็ง"


def _year_has_second_eighth(year: int) -> bool:
    """Whether this year is adhikamasa (อธิกมาส) — the eighth month doubled."""
    from .thai import _load_anchors

    return any(m == "8b" and d.year == year for d, _, _, m in _load_anchors())


def festival_on(day: date) -> Festival | None:
    """The Northern festival falling on this day, if any."""
    solar = _SOLAR_FESTIVALS.get((day.month, day.day))
    if solar is not None:
        return Festival(solar[0], solar[1], day, solar[2])

    t = thai_day(day)
    if not (t.known and t.phase == "waxing" and t.day == 15):
        return None
    if t.month not in _FULL_MOON_FESTIVALS:
        return None

    # In an adhikamasa year Asalha Bucha — and so Vassa — is kept on the *second*
    # eighth month's full moon, not the first. Observing it twice would send the whole
    # temple into the rains retreat a month early.
    if t.month == 8 and _year_has_second_eighth(day.year):
        return None

    name_thai, note = _FULL_MOON_FESTIVALS[t.month]
    lanna_month, _ = _lanna_month(t.month)
    return Festival(_peng_name(lanna_month), name_thai, day, note)


def next_festival(after: date, limit_days: int = 200) -> Festival | None:
    """The next Northern festival strictly after ``after``, within the table's reach."""
    for offset in range(1, limit_days + 1):
        f = festival_on(after + timedelta(days=offset))
        if f is not None:
            return f
    return None
