"""Face 0 — the main dial. Thai first, and analog.

This is the face a monk or a visitor actually reads, so it is built for them rather than
for whoever maintains it:

* **Thai leads.** The lunar day — ขึ้น/แรม ค่ำ and the month — is set larger than
  anything except the clock itself, because that is how one knows when to come to the
  temple. The Buddhist year is the year. Gregorian appears small, once, as a courtesy.
* **Analog leads.** A drawn dial with Thai numerals, read at a glance across a courtyard.
  The digital time sits underneath it, small, for when a precise minute is wanted.
* **Wan phra announces itself.** On a sabbath the day is named plainly rather than
  hidden in a glyph, and the next one is always shown.

Everything here is drawn in semantic inks, so a colour panel would deepen it without a
line of this file changing. Nothing carries meaning by colour alone.
"""

from __future__ import annotations

import math

from ..almanac.thai import thai_numerals
from ..hal.interfaces import TimeQuality
from .base import (
    FONT_SERIF_THAI,
    PANEL_H,
    PANEL_W,
    Canvas,
    RenderState,
)
from .palette import Ink, Palette

# The dial sits left of centre; the reading column runs down the right.
DIAL_CX, DIAL_CY, DIAL_R = 520, 660, 400
TEXT_X = 1030

HEARTBEAT_STEPS = 12


def _polar(cx: float, cy: float, r: float, degrees_from_12: float) -> tuple[float, float]:
    a = math.radians(degrees_from_12 - 90.0)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _draw_dial(c: Canvas, state: RenderState) -> None:
    cx, cy, r = DIAL_CX, DIAL_CY, DIAL_R

    # Rim: two rules with air between them, the way an instrument bezel reads.
    c.ellipse([cx - r, cy - r, cx + r, cy + r], outline=Ink.PRIMARY, width=5)
    c.ellipse([cx - r + 22, cy - r + 22, cx + r - 22, cy + r - 22], outline=Ink.FAINT, width=2)

    # Minute ticks, with the hours struck longer and heavier.
    for minute in range(60):
        angle = minute * 6.0
        is_hour = minute % 5 == 0
        outer = r - 30
        inner = outer - (34 if is_hour else 14)
        x1, y1 = _polar(cx, cy, inner, angle)
        x2, y2 = _polar(cx, cy, outer, angle)
        c.line(
            [(x1, y1), (x2, y2)],
            fill=Ink.PRIMARY if is_hour else Ink.FAINT,
            width=6 if is_hour else 2,
        )

    # Thai hour numerals — ๑ to ๑๒.
    for hour in range(1, 13):
        x, y = _polar(cx, cy, r - 112, hour * 30.0)
        c.text(
            (x, y), thai_numerals(hour), 62, fill=Ink.PRIMARY, anchor="mm", family=FONT_SERIF_THAI
        )

    # Hands. The hour hand carries the reading; the minute hand is finer and longer.
    hour24 = state.local_time.hour
    minute = state.local_time.minute
    hour_angle = (hour24 % 12) * 30.0 + minute * 0.5
    minute_angle = minute * 6.0

    hx, hy = _polar(cx, cy, r * 0.52, hour_angle)
    c.line([(cx, cy), (hx, hy)], fill=Ink.PRIMARY, width=18)
    mx, my = _polar(cx, cy, r * 0.76, minute_angle)
    c.line([(cx, cy), (mx, my)], fill=Ink.PRIMARY, width=9)

    # Hub
    c.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=Ink.PRIMARY)
    c.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=Ink.PAPER)

    # Digital time beneath the dial, small — the dial is the reading, this is the check.
    c.text(
        (cx, cy + r + 86),
        thai_numerals(state.local_time.strftime("%H:%M")),
        76,
        fill=Ink.SECONDARY,
        anchor="mm",
        family=FONT_SERIF_THAI,
    )


def _draw_moon(c: Canvas, cx: int, cy: int, r: int, state: RenderState) -> None:
    """The moon as it actually looks tonight — lit fraction and which limb."""
    if state.moon is None:
        return
    k = max(0.0, min(1.0, state.moon.illumination))
    waxing = state.moon.is_waxing

    # Unlit disc, then the lit half, then the terminator ellipse either carved out of
    # the lit half (crescent) or added to it (gibbous).
    c.ellipse([cx - r, cy - r, cx + r, cy + r], fill=Ink.FAINT, outline=Ink.PRIMARY, width=3)
    start, end = (-90, 90) if waxing else (90, 270)
    c.draw.pieslice([cx - r, cy - r, cx + r, cy + r], start, end, fill=c.ink(Ink.PAPER))

    half_width = r * abs(1.0 - 2.0 * k)
    if half_width > 1:
        terminator_is_dark = k < 0.5
        c.ellipse(
            [cx - half_width, cy - r, cx + half_width, cy + r],
            fill=Ink.FAINT if terminator_is_dark else Ink.PAPER,
        )
    c.ellipse([cx - r, cy - r, cx + r, cy + r], outline=Ink.PRIMARY, width=3)


def _draw_heartbeat(c: Canvas, cx: int, cy: int, tick: int) -> None:
    r = 42
    active = tick % HEARTBEAT_STEPS
    for i in range(HEARTBEAT_STEPS):
        x, y = _polar(cx, cy, r, i * (360.0 / HEARTBEAT_STEPS))
        size = 9 if i == active else 4
        c.ellipse(
            [x - size, y - size, x + size, y + size], fill=Ink.PRIMARY if i == active else Ink.FAINT
        )


def _hm(value) -> str:
    """HH:MM in Thai numerals — ๐๕:๕๙. The face does not change numeral system
    partway down; the dial, the date and the times all read the same way."""
    return thai_numerals(value.strftime("%H:%M")) if value is not None else "—"


def _draw_reading(c: Canvas, state: RenderState) -> None:
    """The Thai reading column — the reason the clock is on the wall."""
    x = TEXT_X
    y = 150
    thai = state.thai

    # Weekday, in Thai.
    if thai is not None:
        c.text((x, y), thai.weekday_text, 66, fill=Ink.PRIMARY, family=FONT_SERIF_THAI)
        y += 96

    # THE LUNAR DAY — the largest thing on this column by intent.
    if thai is not None:
        if thai.known:
            word = "ขึ้น" if thai.phase == "waxing" else "แรม"
            c.text(
                (x, y),
                f"{word} {thai_numerals(thai.day)} ค่ำ",
                118,
                fill=Ink.PRIMARY,
                family=FONT_SERIF_THAI,
            )
            y += 138
            from ..almanac.thai import THAI_MONTH_NAMES

            c.text(
                (x, y),
                THAI_MONTH_NAMES.get(thai.month, ""),
                64,
                fill=Ink.SECONDARY,
                family=FONT_SERIF_THAI,
            )
            y += 96
        else:
            # Never invent a lunar day. Say so, in Thai.
            c.text((x, y), thai.lunar_text, 54, fill=Ink.WARNING, family=FONT_SERIF_THAI)
            y += 92

    # Wan phra, named plainly rather than coded into a glyph.
    if thai is not None and thai.is_wan_phra:
        c.rectangle([x - 16, y - 12, x + 430, y + 76], outline=Ink.SACRED, width=4)
        c.text((x + 12, y + 8), "วันพระ", 62, fill=Ink.SACRED, family=FONT_SERIF_THAI)
        y += 116
    elif state.next_wan_phra is not None:
        nxt = state.next_wan_phra
        days = (nxt.gregorian - state.local_time.date()).days
        c.text(
            (x, y),
            f"วันพระถัดไป  อีก {thai_numerals(days)} วัน",
            44,
            fill=Ink.SECONDARY,
            family=FONT_SERIF_THAI,
        )
        y += 78

    # Day and month, then the Buddhist year on its own line and labelled. Split so the
    # year is not printed twice — `solar_text` already carries it, which would read as
    # "20 July 2569 / B.E. 2569".
    if thai is not None:
        from ..almanac.thai import THAI_SOLAR_MONTHS

        day_month = (
            f"{thai_numerals(thai.gregorian.day)} {THAI_SOLAR_MONTHS[thai.gregorian.month - 1]}"
        )
        c.text((x, y), day_month, 58, fill=Ink.PRIMARY, family=FONT_SERIF_THAI)
        y += 82
        c.text(
            (x, y),
            f"พ.ศ. {thai_numerals(thai.buddhist_year)}",
            50,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
        )
        y += 82

    # Sun and the bird, in Thai.
    c.line([(x, y), (PANEL_W - 90, y)], fill=Ink.FAINT, width=2)
    y += 28
    if state.sun is not None:
        c.text(
            (x, y),
            f"อาทิตย์ขึ้น {_hm(state.sun.sunrise)}   ตก {_hm(state.sun.sunset)}",
            42,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
        )
        y += 62
    if state.next_dawn is not None or state.next_dusk is not None:
        c.text(
            (x, y),
            f"นกกระปูด  เช้า {_hm(state.next_dawn)}   เย็น {_hm(state.next_dusk)}",
            42,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
        )
        y += 62


def _draw_status(c: Canvas, state: RenderState) -> None:
    """Small, low, and out of the way — but never dishonest."""
    y = PANEL_H - 82
    stale = state.time.quality in (TimeQuality.RTC_STALE, TimeQuality.UNKNOWN)
    if stale or state.power_state != "normal":
        parts = []
        if stale:
            parts.append("เวลาอาจคลาดเคลื่อน")  # "the time may be inaccurate"
        if state.power_state != "normal":
            parts.append("ไฟสำรองต่ำ")  # "reserve power low"
        c.text((90, y), "   ".join(parts), 34, fill=Ink.WARNING, family=FONT_SERIF_THAI)

    # A single courtesy line of Gregorian/English, small, at the foot.
    c.text(
        (PANEL_W - 90, y), state.local_time.strftime("%d %b %Y"), 30, fill=Ink.FAINT, anchor="ra"
    )


def render(state: RenderState, palette: Palette | None = None) -> bytes:
    c = Canvas(palette)

    _draw_dial(c, state)
    _draw_moon(c, PANEL_W - 190, 130, 68, state)
    _draw_heartbeat(c, PANEL_W - 190, 300, state.tick)
    _draw_reading(c, state)
    _draw_status(c, state)

    return c.to_framebuffer()
