"""The Lanna face — the clock as a Northern cosmologist would lay it out.

Composition follows a Lanna cosmological diagram rather than a dashboard: one centre,
concentric rings, and the year's twelve animals turning around the outside like the
zodiac band on a temple mural. Read from the outside in —

    outer band   the twelve-year cycle (ปีไจ้ … ปีไก๊), this year's animal marked
    naga ring    the serpent border that edges a manuscript panel
    hour ring    twelve Northern hours in Thai numerals
    the hands    hour and minute, over a lotus hub
    the centre   the lunar day — ขึ้น / แฮม ค่ำ — the reason anyone looks

To the right, a plate of Northern readings: the Chulasakarat year, the month, the
sabbath (วันศีล), the coming festival, the sun and the bird.

Everything is line and repetition, drawn in semantic inks — no bitmaps, no colour
dependency, nothing that fails to load. It is designed to survive 16 greys and to be
legible across a courtyard.
"""

from __future__ import annotations

from ..almanac.thai import thai_numerals
from ..hal.interfaces import TimeQuality
from .base import (
    FONT_SERIF_THAI,
    PANEL_H,
    PANEL_W,
    W_BOLD,
    W_LIGHT,
    W_MEDIUM,
    W_SEMIBOLD,
    Canvas,
    RenderState,
)
from .ornament import (
    guilloche_rosette,
    kanok_corner,
    lotus_hub,
    moon_complication,
    naga_ring,
    polar,
    rays,
    sri_yantra_field,
    zodiac_glyph,
)
from .palette import Ink, Palette

# The dial is the left two-thirds; the reading plate is the right third.
CX, CY = 620, 700
R_ZODIAC_OUT = 590
R_ZODIAC_IN = 478
R_NAGA = 470
R_HOURS = 400
R_DIAL = 355

PLATE_X = 1230

HEARTBEAT_STEPS = 12

# The twelve animals, in cycle order, as short Northern labels for the outer band.
ZODIAC_LABELS = (
    "ไจ้",
    "เป้า",
    "ยี",
    "เหม้า",
    "สี",
    "ไส้",
    "สะง้า",
    "เม็ด",
    "สัน",
    "เร้า",
    "เส็ด",
    "ไก๊",
)


def _hm(value) -> str:
    return thai_numerals(value.strftime("%H:%M")) if value is not None else "—"


def _draw_zodiac_band(c: Canvas, state: RenderState) -> None:
    """The twelve-year cycle as an outer band, with this year's animal marked.

    A Lanna almanac places the animal cycle on the outside of the diagram; the current
    year is the one the reader is standing in, so it is given a filled cartouche rather
    than a colour — the mark survives a panel with no colour at all.
    """
    lan = state.lanna
    current = None
    if lan is not None:
        try:
            current = ZODIAC_LABELS.index(lan.animal_lanna)
        except ValueError:
            current = None

    c.ellipse(
        [CX - R_ZODIAC_OUT, CY - R_ZODIAC_OUT, CX + R_ZODIAC_OUT, CY + R_ZODIAC_OUT],
        outline=Ink.FAINT,
        width=3,
    )
    c.ellipse(
        [CX - R_ZODIAC_IN, CY - R_ZODIAC_IN, CX + R_ZODIAC_IN, CY + R_ZODIAC_IN],
        outline=Ink.FAINT,
        width=2,
    )
    # Divide the band into twelve houses.
    rays(c, CX, CY, R_ZODIAC_IN, R_ZODIAC_OUT, count=12, offset_deg=15.0, ink=Ink.FAINT, width=2)

    r_glyph = 538.0
    r_name = 494.0
    for i, label in enumerate(ZODIAC_LABELS):
        ang = i * 30.0
        gx, gy = polar(CX, CY, r_glyph, ang)
        nx, ny = polar(CX, CY, r_name, ang)
        if i == current:
            # The year we are standing in: a filled seal with the animal AND its name
            # reversed out of it — a self-contained stamp, so nothing collides with
            # the house label. Shape carries the meaning; no colour needed, so the
            # mark survives any panel.
            c.ellipse([gx - 48, gy - 48, gx + 48, gy + 48], fill=Ink.PRIMARY)
            zodiac_glyph(c, gx, gy - 10, 52, i, ink=Ink.PAPER)
            c.text(
                (gx, gy + 28),
                label,
                21,
                fill=Ink.PAPER,
                anchor="mm",
                family=FONT_SERIF_THAI,
                weight=W_SEMIBOLD,
            )
        else:
            zodiac_glyph(c, gx, gy, 60, i, ink=Ink.SECONDARY)
            c.text(
                (nx, ny),
                label,
                26,
                fill=Ink.SECONDARY,
                anchor="mm",
                family=FONT_SERIF_THAI,
                weight=W_LIGHT,
            )


def _draw_ground(c: Canvas) -> None:
    """The engine-turned ground: guilloche rosette over a twelve-sided yantra.

    Drawn first, faintly, so every reading sits on it. Guilloche is felt before it
    is seen — at two metres this should read as a tone on the dial, never as pattern
    competing with the numerals.
    """
    guilloche_rosette(c, CX, CY, R_DIAL - 18, petals=12, depth=0.14, passes=4, ink=Ink.ENGRAVING)
    sri_yantra_field(c, CX, CY, R_DIAL - 68, sides=12, ink=Ink.ENGRAVING)


def _draw_dial(c: Canvas, state: RenderState) -> None:
    """The hour ring and the hands."""
    naga_ring(c, CX, CY, R_NAGA, scales=84, depth=15, ink=Ink.FAINT)

    # Hour ring: twelve Northern hours, with minute ticks between.
    c.ellipse([CX - R_DIAL, CY - R_DIAL, CX + R_DIAL, CY + R_DIAL], outline=Ink.PRIMARY, width=4)
    for minute in range(60):
        ang = minute * 6.0
        is_hour = minute % 5 == 0
        outer = R_DIAL
        inner = outer - (30 if is_hour else 13)
        c.line(
            [polar(CX, CY, inner, ang), polar(CX, CY, outer, ang)],
            fill=Ink.PRIMARY if is_hour else Ink.FAINT,
            width=5 if is_hour else 2,
        )
    for hour in range(1, 13):
        x, y = polar(CX, CY, R_DIAL - 78, hour * 30.0)
        c.text(
            (x, y),
            thai_numerals(hour),
            54,
            fill=Ink.PRIMARY,
            anchor="mm",
            family=FONT_SERIF_THAI,
            weight=W_MEDIUM,
        )

    # Hands, then the lotus hub over their pivot.
    minute = state.local_time.minute
    hour_ang = (state.local_time.hour % 12) * 30.0 + minute * 0.5
    c.line([(CX, CY), polar(CX, CY, R_DIAL * 0.52, hour_ang)], fill=Ink.PRIMARY, width=16)
    c.line([(CX, CY), polar(CX, CY, R_DIAL * 0.72, minute * 6.0)], fill=Ink.PRIMARY, width=8)
    lotus_hub(c, CX, CY, 34, petals=8)


def _draw_plate(c: Canvas, state: RenderState) -> None:
    """The reading plate: era, sabbath, festival, sun, bird."""
    x, y = PLATE_X, 132
    lan = state.lanna

    # THE LUNAR DAY — the hero of the panel. It sits here rather than at the dial's
    # centre because the hands sweep that centre and would cross it twice an hour.
    if lan is not None:
        if lan.known:
            # Laid out from measured widths: "ขึ้น ๑๕ ค่ำ" on one baseline, the numeral
            # oversized between two smaller words. Guessed offsets collided as soon as
            # the numeral changed width (๖ vs ๑๕).
            word = "ขึ้น" if lan.phase == "waxing" else "แฮม"
            numeral = thai_numerals(lan.day)
            gap = 26
            w_word, _ = c.measure(word, 62, FONT_SERIF_THAI)
            w_num, _ = c.measure(numeral, 150, FONT_SERIF_THAI)

            c.text(
                (x, y + 62),
                word,
                62,
                fill=Ink.SECONDARY,
                family=FONT_SERIF_THAI,
                anchor="ls",
                weight=W_LIGHT,
            )
            c.text(
                (x + w_word + gap, y + 62),
                numeral,
                150,
                fill=Ink.PRIMARY,
                family=FONT_SERIF_THAI,
                anchor="ls",
                weight=W_BOLD,
            )
            c.text(
                (x + w_word + gap + w_num + gap, y + 62),
                "ค่ำ",
                62,
                fill=Ink.SECONDARY,
                family=FONT_SERIF_THAI,
                anchor="ls",
            )
            y += 128
            c.text(
                (x, y),
                lan.month_name,
                60,
                fill=Ink.PRIMARY,
                family=FONT_SERIF_THAI,
                weight=W_LIGHT,
            )
            y += 92
        else:
            c.text((x, y), lan.lunar_text, 46, fill=Ink.WARNING, family=FONT_SERIF_THAI)
            y += 92

    c.line([(x, y), (PANEL_W - 90, y)], fill=Ink.FAINT, width=2)
    y += 30

    if lan is not None:
        # The year, in the Northern era, with the animal named.
        c.text(
            (x, y),
            f"ปี{lan.animal_lanna}",
            76,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
            weight=W_SEMIBOLD,
        )
        c.text(
            (x + 250, y + 22),
            f"จ.ศ. {thai_numerals(lan.cs_year)}",
            50,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
        )
        y += 96
        if state.thai is not None:
            c.text(
                (x, y),
                f"พ.ศ. {thai_numerals(state.thai.buddhist_year)}",
                42,
                fill=Ink.SECONDARY,
                family=FONT_SERIF_THAI,
            )
            y += 74

    c.line([(x, y), (PANEL_W - 90, y)], fill=Ink.FAINT, width=2)
    y += 30

    # วันศีล — the Northern name for the sabbath.
    if lan is not None and lan.is_wan_sin:
        c.rectangle([x - 14, y - 10, x + 330, y + 78], outline=Ink.SACRED, width=4)
        c.text((x + 14, y + 8), "วันศีล", 60, fill=Ink.SACRED, family=FONT_SERIF_THAI)
        y += 116
    elif state.next_wan_phra is not None:
        days = (state.next_wan_phra.gregorian - state.local_time.date()).days
        c.text(
            (x, y),
            f"วันศีลหน้า  อีก {thai_numerals(days)} วัน",
            44,
            fill=Ink.SECONDARY,
            family=FONT_SERIF_THAI,
        )
        y += 76

    # The coming Northern festival.
    festival = state.festival
    if festival is not None:
        c.rectangle([x - 14, y - 10, x + 430, y + 78], outline=Ink.SACRED, width=4)
        c.text((x + 14, y + 8), festival.name_lanna, 56, fill=Ink.SACRED, family=FONT_SERIF_THAI)
        y += 112
    elif state.next_festival is not None:
        nxt = state.next_festival
        days = (nxt.gregorian - state.local_time.date()).days
        c.text((x, y), nxt.name_lanna, 50, fill=Ink.PRIMARY, family=FONT_SERIF_THAI)
        y += 62
        c.text(
            (x, y),
            f"อีก {thai_numerals(days)} วัน",
            40,
            fill=Ink.SECONDARY,
            family=FONT_SERIF_THAI,
        )
        y += 72

    c.line([(x, y), (PANEL_W - 90, y)], fill=Ink.FAINT, width=2)
    y += 34

    if state.sun is not None:
        c.text(
            (x, y),
            f"ตะวันขึ้น {_hm(state.sun.sunrise)}",
            42,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
        )
        y += 58
        c.text(
            (x, y),
            f"ตะวันตก  {_hm(state.sun.sunset)}",
            42,
            fill=Ink.PRIMARY,
            family=FONT_SERIF_THAI,
        )
        y += 66
    if state.next_dawn is not None:
        c.text(
            (x, y),
            f"นกกระปูด {_hm(state.next_dawn)} · {_hm(state.next_dusk)}",
            40,
            fill=Ink.SECONDARY,
            family=FONT_SERIF_THAI,
        )
        y += 62


def _draw_heartbeat(c: Canvas, cx: int, cy: int, tick: int) -> None:
    r = 38
    active = tick % HEARTBEAT_STEPS
    for i in range(HEARTBEAT_STEPS):
        x, y = polar(cx, cy, r, i * (360.0 / HEARTBEAT_STEPS))
        size = 8 if i == active else 4
        c.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=Ink.PRIMARY if i == active else Ink.FAINT,
        )


def _draw_status(c: Canvas, state: RenderState) -> None:
    y = PANEL_H - 72
    stale = state.time.quality in (TimeQuality.RTC_STALE, TimeQuality.UNKNOWN)
    notes = []
    if stale:
        notes.append("เวลาอาจคลาดเคลื่อน")
    if state.power_state != "normal":
        notes.append("ไฟสำรองต่ำ")
    if notes:
        c.text((110, y), "   ".join(notes), 34, fill=Ink.WARNING, family=FONT_SERIF_THAI)
    c.text(
        (PANEL_W - 90, y),
        state.local_time.strftime("%d %b %Y"),
        28,
        fill=Ink.FAINT,
        anchor="ra",
    )


def render(state: RenderState, palette: Palette | None = None) -> bytes:
    c = Canvas(palette)

    # A framing rule with kanok spandrels — the panel edge of a manuscript leaf.
    inset = 34
    c.rectangle([inset, inset, PANEL_W - inset, PANEL_H - inset], outline=Ink.FAINT, width=3)
    corner = 108
    kanok_corner(c, inset + 8, inset + 8, corner, quadrant=0)
    kanok_corner(c, PANEL_W - inset - 8, inset + 8, corner, quadrant=1)
    kanok_corner(c, PANEL_W - inset - 8, PANEL_H - inset - 8, corner, quadrant=2)
    kanok_corner(c, inset + 8, PANEL_H - inset - 8, corner, quadrant=3)

    _draw_ground(c)
    _draw_zodiac_band(c, state)
    _draw_dial(c, state)
    _draw_plate(c, state)

    # Moon and heartbeat sit in the clear zone below the plate — off the zodiac band
    # and clear of the corner ornament.
    if state.moon is not None:
        # Driven by the LUNATION GEAR — the disc's own angle, re-datumed at every new
        # moon. Falls back to a parity-0 gear angle if the lunation is unavailable.
        from ..almanac.lunation import disc_angle_for_phase

        gear = (
            state.lunation.disc_angle_deg
            if state.lunation is not None
            else disc_angle_for_phase(state.moon.phase_angle_deg)
        )
        moon_complication(c, PLATE_X + 110, PANEL_H - 250, 96, gear)
        c.text(
            (PLATE_X + 110, PANEL_H - 118),
            f"{state.moon.illumination * 100:.0f}%",
            34,
            fill=Ink.SECONDARY,
            anchor="mm",
            family=FONT_SERIF_THAI,
            weight=W_LIGHT,
        )
    _draw_heartbeat(c, PLATE_X + 360, PANEL_H - 250, state.tick)
    _draw_status(c, state)

    return c.to_framebuffer()
