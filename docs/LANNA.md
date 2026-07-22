# The Lanna face — where every fact comes from

This clock stands in a Lanna wat. Central Thai time is *national*; Lanna time is *local*,
and it is the reckoning a monk in San Sai actually keeps. So the Northern face is not a
translation of the Thai one — it is a different calendar, and it must be right.

This document records the provenance of every claim the face makes, because a sacred
object must not bluff and because whoever maintains this in 2050 deserves to know which
parts were verified and which were inherited.

## The corpus

Drawn from the project's own digitised Lanna manuscript corpus
(`manuscript-crawler/crawler/catalog.db`): **6,990 manuscripts, 388 of them astrology**,
including the day-quality genre this face's vocabulary comes from —

| ms | title | what it is |
|----|-------|-----------|
| 371 | มื้อวันสันเร้า | day-naming / day qualities |
| 445 | จัดหาวันดีวันร้าย | finding auspicious and inauspicious days |
| 356 | หนังสือหมอเมื่อ | the หมอเมื่อ reckoning tradition |
| 364 | โหฬาหลวง | *hora luang* — the greater astrology |

**What the corpus gave us:** proof that the Northern vocabulary on this face is *living
usage, not reconstruction*. The year-animal names appear directly in the manuscripts —
`ไจ้` on **34** pages, `เป้า` on **18**, alongside `เม็ง` and `มื้อ`.

**What the corpus did not give us:** a clean, machine-readable calendar. The OCR across
these leaves is fragmentary and interleaved with mantra and yantra material. It grounds
and corroborates; it does not compute. Saying otherwise would be the easiest lie in this
project to tell and the hardest to detect.

## The verified skeleton

| Fact | Value | Source |
|---|---|---|
| Chulasakarat era | **CS = CE − 638**, epoch 22 March 638 CE | Wikipedia, *Chula Sakarat*, retrieved 2026-07-20 |
| CS year boundary | turns at Songkran, mid-April | same |
| Month numbering | Lan Na numbers months **two ahead** of the central/Sukhothai reckoning | same (regional month table) |
| The lunar day itself | from the **published Thai calendar** authority table | Thai PBS — see `data/tables/thai_lunar_2569.csv` |

The lunar day is *not* recomputed for the North. Lanna and central Thai keep the same
waxing/waning day; they differ only in what they number the month. So `almanac/lanna.py`
wraps `almanac/thai.py` and inherits its authority — and its limits.

### The anchor that proves the offset

**Yi Peng is the full moon of เดือนยี่ — Lanna month 2.** That same full moon is central
Thai month 12 (Loy Krathong). A test asserts exactly this, and a second checks Visakha
Bucha lands on Lanna month 8 (เดือนแปดเป็ง), independently. If the offset is ever wrong,
both fail.

## What the face shows

**Zodiac band** — the twelve-year cycle in Northern forms (ไจ้ เป้า ยี เหม้า สี ไส้ สะง้า
เม็ด สัน เร้า เส็ด ไก๊), each house carrying a small stamp-style animal glyph with its name,
and the current year marked by a filled seal with the animal and name reversed out of it.
A *shape*, not a colour, so the mark survives a panel with no colour at all. Two glyphs
are deliberately Northern readings: **สี is drawn as the great serpent (naga)**, and
**ไก๊ is drawn as an elephant** — Northern iconography replaces the pig with the elephant. The cycle is cross-checked
against the central Thai animal in tests — they are the same cycle under two names, so a
drift would mean one is off by a year.

**Naga ring** (นาค) — the serpent that guards every wat stair, run as a scale-and-crest
border the way it edges a manuscript panel.

**Kanok spandrels** (ลายกนก) — the flame-tendril curl in each corner.

**Lotus hub** (บัว) — the seat, under the hands.

All of it is pure geometry in `faces/ornament.py`: no bitmaps, no external assets,
nothing that can fail to load. A stranger in 2096 can read that file and see exactly what
is drawn and why.

## Festivals

Anchored to the same authority table, so they inherit its trustworthiness:

| Northern name | Central | 2026 | Anchor |
|---|---|---|---|
| ปี๋ใหม่เมือง | สงกรานต์ | 13 Apr | solar |
| เดือนห้าเป็ง | มาฆบูชา | 2 Feb | full moon, Lanna month 5 |
| เดือนแปดเป็ง | วิสาขบูชา | 1 May | full moon, Lanna month 8 |
| เดือนสิบเป็ง | อาสาฬหบูชา | 29 Jul | full moon, Lanna month 10 (second) |
| **ยี่เป็ง** | ลอยกระทง | 24 Nov | full moon, Lanna month 2 |

The เป็ง names are **derived** from the Lanna month number, not hand-written — hand-written
names drifted twice during development before the derivation replaced them.

**2569 is adhikamasa** (อธิกมาส): the eighth month is doubled. Asalha Bucha, and so the
start of Vassa, is kept on the **second** eighth month — 29 July, matching the published
calendar. Observing it on both would send the whole temple into the rains retreat a month
early, so there is a test for exactly that.

## Honest limits — what this face does *not* claim

1. **The lunar reckoning reaches only as far as the Thai table** (2026 today). Beyond it
   the face says `บ่ฮู้ข้างขึ้นข้างแฮม` — "the lunar day is not known" — in Kam Mueang,
   rather than inventing a Northern month. The era and the animal still show; both are
   computable without the table.

2. **The sixty-name มื้อ day-cycle (กาบไจ้ …) is deliberately absent.** It needs a verified
   epoch anchor we do not have. A wrong sexagenary name on a temple clock is worse than
   an absent one, so it is an open door in `GROWING.md`, not a silent guess.

3. **Songkran is approximated at 16 April** for the era boundary. The true สังกรานต์ is
   computed, and moves. Refining it is a noted follow-up.

4. **The Tai Tham script is bundled but not yet used on this face.** `NotoSansTaiTham` is
   in `data/fonts/` and verified rendering, but the face is set in Thai script, which is
   what most readers at the wat read today. Setting the month names in Tua Mueang is an
   obvious next step and needs someone who reads it to check the orthography — not me.

5. **เข้าอินทขีล** (the Inthakhin city-pillar festival, distinctively Chiang Mai) is not
   yet included; its anchoring rule needs a source we can cite.

6. **The zodiac glyphs are modern stamp-drawings, not copies of manuscript art** — and
   the two Northern readings (naga for สี, elephant for ไก๊) are documented tradition but
   should be verified against the corpus and a native reader before donation.

7. **The moon complication is a gear, re-datumed monthly against the sky.**

   *The movement.* One disc carries **two moons** 180° apart and makes one full 360°
   turn per **two** lunations — 180° a month, the only rate consistent with two moons.
   One crosses the aperture this month; its partner takes the next. At new moon one is
   setting behind the right hump as the other rises behind the left, and both are hidden.

   *The monthly reset.* `almanac/lunation.py` counts new moons from the ephemeris. At
   every true new moon the count increments and the gear's fraction returns to exactly
   zero — the datum is re-established once a month, so nothing accumulates and nothing
   drifts. A clock dark for a year wakes knowing which moon belongs in the window.

   *Why not a pure time gear.* Measured, not assumed: across 25 lunations of 2026–27 the
   synodic month runs from **29.284 to 29.814 days**, and a constant-rate gear synced
   only at new moon lands up to **10.65° out — 8.4 points of illumination, ~21 hours of
   phase**. The dial's geometry is good to about 1 point, so a time gear would have been
   the dominant error eightfold. Within the month the fraction therefore comes from the
   true elongation, which is exact and free.

   *The proportions*, fitted against real illumination with the design requirements as
   hard constraints — moon slightly smaller than the cloud (**0.82**), plate covering
   **71%** of the frame, a visible notch between the humps, the humps clipping the moon
   and the rim never touching it (0.00%), the partner never showing (0.00%):

   **RMS 0.0037, worst 1.1 percentage points.** The larger moon proved *more* accurate
   as well as more legible, so there was no trade between the two.

---

**Sources:** the project's Lanna manuscript corpus (`catalog.db`) ·
[Wikipedia, *Chula Sakarat*](https://en.wikipedia.org/wiki/Chula_Sakarat) ·
[Thai PBS, ปฏิทินวันพระ 2569](https://www.thaipbs.or.th/now/content/3498) ·
[Noto Sans Tai Tham](https://fonts.google.com/noto/specimen/Noto+Sans+Tai+Tham) (SIL OFL)
