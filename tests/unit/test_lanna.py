"""Tests for the Lanna (Northern) reckoning.

The month offset is the whole point of this module and the easiest thing to get subtly
wrong — hand-written festival names drifted twice during development before these tests
existed. The anchor that catches it: **Yi Peng is the full moon of เดือนยี่**, Lanna month
2, which is central Thai month 12. If the offset is wrong, that check fails.
"""

from datetime import date, timedelta

from coucal.almanac.lanna import (
    LANNA_ANIMALS,
    _lanna_month,
    chulasakarat_year,
    festival_on,
    lanna_animal,
    lanna_day,
    next_festival,
)
from coucal.almanac.thai import animal_year, thai_day

# --- the era ---------------------------------------------------------------


def test_chulasakarat_year_turns_at_songkran():
    """CS = CE - 638, but the year turns in mid-April, not on 1 January."""
    assert chulasakarat_year(date(2026, 1, 1)) == 1387
    assert chulasakarat_year(date(2026, 7, 20)) == 1388
    assert chulasakarat_year(date(2026, 12, 31)) == 1388


# --- the month offset ------------------------------------------------------


def test_lanna_runs_two_months_ahead():
    assert _lanna_month(1)[0] == 3
    assert _lanna_month(8)[0] == 10
    assert _lanna_month(10)[0] == 12
    # ...and wraps.
    assert _lanna_month(11)[0] == 1
    assert _lanna_month(12)[0] == 2


def test_month_one_is_chiang_and_two_is_yi():
    """The North names its first two months rather than numbering them."""
    assert _lanna_month(11)[1] == "เดือนเจียง"
    assert _lanna_month(12)[1] == "เดือนยี่"


def test_doubled_eighth_becomes_doubled_tenth():
    number, name = _lanna_month("8b")
    assert number == "10b"
    assert "สิบ" in name and "สอง" in name  # เดือนสิบ (สอง)


def test_yi_peng_is_the_full_moon_of_lanna_month_two():
    """THE anchor test for the offset. Yi Peng — the Chiang Mai lantern festival — is
    ขึ้น ๑๕ ค่ำ เดือนยี่. That same full moon is central Thai month 12 (Loy Krathong)."""
    yi_peng = date(2026, 11, 24)
    t = thai_day(yi_peng)
    assert t.month == 12 and t.phase == "waxing" and t.day == 15

    lan = lanna_day(yi_peng)
    assert lan.month == 2
    assert lan.month_name == "เดือนยี่"

    f = festival_on(yi_peng)
    assert f is not None and f.name_lanna == "ยี่เป็ง"


def test_visakha_falls_on_lanna_month_eight():
    """Cross-check on a second, independently-known Northern name: Visakha Bucha is
    kept as เดือนแปดเป็ง in the North — Lanna month 8, central Thai month 6."""
    f = festival_on(date(2026, 5, 1))
    assert f is not None
    assert f.name_lanna == "เดือนแปดเป็ง"
    assert lanna_day(date(2026, 5, 1)).month == 8


# --- the zodiac ------------------------------------------------------------


def test_twelve_animals_and_no_duplicates():
    assert len(LANNA_ANIMALS) == 12
    assert len({a[0] for a in LANNA_ANIMALS}) == 12


def test_lanna_animal_agrees_with_the_central_thai_cycle():
    """Lanna and central Thai keep the *same* twelve-year cycle under different names,
    so the pairing must line up — a drift here would mean one of them is off by a year."""
    for probe in (date(2026, 7, 20), date(2027, 6, 1), date(2030, 9, 9)):
        lanna_name, thai_name, _ = lanna_animal(probe)
        assert thai_name == animal_year(probe), f"{probe}: {lanna_name}/{thai_name} mismatch"


def test_animal_turns_at_songkran_not_new_year():
    before = lanna_animal(date(2026, 1, 1))[0]
    after = lanna_animal(date(2026, 7, 1))[0]
    assert before != after


# --- festivals -------------------------------------------------------------


def test_asalha_is_kept_once_on_the_second_eighth_month():
    """2569 is adhikamasa. Observing Asalha on both eighth months would start the rains
    retreat a month early for the whole temple."""
    asalha_days = [
        d
        for d in (date(2026, 1, 1) + timedelta(days=i) for i in range(360))
        if (f := festival_on(d)) is not None and f.name_thai == "อาสาฬหบูชา"
    ]
    assert asalha_days == [date(2026, 7, 29)], f"expected one Asalha, got {asalha_days}"


def test_the_expected_northern_festivals_are_found():
    found = {}
    for i in range(360):
        d = date(2026, 1, 1) + timedelta(days=i)
        f = festival_on(d)
        if f:
            found[f.name_thai] = d
    for expected in ("มาฆบูชา", "สงกรานต์", "วิสาขบูชา", "อาสาฬหบูชา", "ลอยกระทง"):
        assert expected in found, f"{expected} not found in 2026"


def test_songkran_is_the_northern_new_year():
    f = festival_on(date(2026, 4, 13))
    assert f is not None and f.name_lanna == "ปี๋ใหม่เมือง"


def test_next_festival_looks_forward():
    f = next_festival(date(2026, 7, 20))
    assert f is not None and f.gregorian == date(2026, 7, 29)


# --- honest limits ---------------------------------------------------------


def test_outside_the_table_the_north_says_so_in_kam_mueang():
    """Never invent a Northern month. The era and the animal are still computable."""
    far = lanna_day(date(2040, 5, 1))
    assert not far.known
    assert far.month is None
    assert far.cs_year == 1402
    assert far.lunar_text == "บ่ฮู้ข้างขึ้นข้างแฮม"


def test_northern_wording_uses_haem_not_ram():
    """The North says แฮม where the centre says แรม."""
    waning = lanna_day(date(2026, 8, 6))  # แรม ๘ ค่ำ in the central reckoning
    assert waning.known and waning.phase == "waning"
    assert waning.lunar_text.startswith("แฮม")
