"""Phase 0 diagnostic face.

Not one of the eight instrument faces — a deliberately plain screen that proves the
whole pipeline (HAL time/power -> state -> Pillow -> framebuffer -> panel) and, above
all, demonstrates the **heartbeat**: a dot that steps one position every wake cycle.

A frozen screen is e-ink's dangerous failure mode (frozen-but-plausible). Anyone told
"the dot should step every few minutes" can detect death at a glance. The maintenance
manual will point at exactly this element.
"""

from __future__ import annotations

import math

from ..hal.interfaces import TimeQuality
from .base import PANEL_H, PANEL_W, Canvas, RenderState
from .palette import Ink, Palette

_QUALITY_LABEL = {
    TimeQuality.GPS: "GPS",
    TimeQuality.RTC: "RTC holdover",
    TimeQuality.RTC_STALE: "RTC (stale)",
    TimeQuality.UNKNOWN: "no time source",
}

HEARTBEAT_STEPS = 12


def _draw_heartbeat(c: Canvas, cx: int, cy: int, tick: int) -> None:
    """A ring of ticks with one filled dot that advances each wake."""
    r = 70
    active = tick % HEARTBEAT_STEPS
    for i in range(HEARTBEAT_STEPS):
        angle = -math.pi / 2 + (2 * math.pi * i / HEARTBEAT_STEPS)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == active:
            c.ellipse([x - 12, y - 12, x + 12, y + 12], fill=Ink.PRIMARY)
        else:
            c.ellipse([x - 5, y - 5, x + 5, y + 5], fill=Ink.FAINT)
    c.text((cx, cy + r + 34), "heartbeat", 26, fill=Ink.SECONDARY, anchor="mm")


def _draw_battery(c: Canvas, x: int, y: int, volts: float, state: str) -> None:
    # WARNING ink only *reinforces* what the words already say — the state is spelled
    # out in text beside it, so nothing is lost on a panel with no colour.
    tone = Ink.PRIMARY if state == "normal" else Ink.WARNING

    w, h = 96, 44
    c.rectangle([x, y, x + w, y + h], outline=tone, width=3)
    c.rectangle([x + w, y + 12, x + w + 8, y + h - 12], fill=tone)
    # Fill proportional to a 12.0–13.2 V LiFePO4 working band.
    frac = max(0.0, min(1.0, (volts - 12.0) / 1.2))
    fill_w = int((w - 8) * frac)
    if fill_w > 0:
        c.rectangle([x + 4, y + 4, x + 4 + fill_w, y + h - 4], fill=Ink.SECONDARY)
    c.text((x + w + 24, y + h // 2), f"{volts:.1f} V · {state}", 28, fill=tone, anchor="lm")


def _hm(value) -> str:
    return value.strftime("%H:%M") if value is not None else "—"


def _draw_almanac(c: Canvas, state: RenderState) -> None:
    """Three columns: the sun's day, the moon's state, and the bird's next two calls."""
    y = 960
    if state.sun is None and state.moon is None:
        c.text(
            (PANEL_W // 2, y + 60),
            "no ephemeris — the clock keeps time but cannot place the sun",
            30,
            fill=Ink.FAINT,
            anchor="mm",
        )
        return

    c.line([(140, y - 30), (PANEL_W - 140, y - 30)], fill=Ink.FAINT, width=2)
    col = PANEL_W // 3
    label, value = 26, 34

    if state.sun is not None:
        c.text((col * 0 + 200, y), "SUN", label, fill=Ink.FAINT)
        c.text((col * 0 + 200, y + 40), f"rise   {_hm(state.sun.sunrise)}", value, fill=Ink.PRIMARY)
        c.text((col * 0 + 200, y + 84), f"set    {_hm(state.sun.sunset)}", value, fill=Ink.PRIMARY)
        length = state.sun.day_length
        if length is not None:
            hours, rem = divmod(int(length.total_seconds()), 3600)
            c.text(
                (col * 0 + 200, y + 128),
                f"day    {hours}h {rem // 60:02d}m",
                value,
                fill=Ink.SECONDARY,
            )

    if state.moon is not None:
        c.text((col * 1 + 120, y), "MOON", label, fill=Ink.FAINT)
        c.text((col * 1 + 120, y + 40), state.moon.phase_name, value, fill=Ink.PRIMARY)
        c.text(
            (col * 1 + 120, y + 84),
            f"{state.moon.illumination * 100:.0f}% lit",
            value,
            fill=Ink.PRIMARY,
        )
        c.text(
            (col * 1 + 120, y + 128),
            f"rise {_hm(state.moon.moonrise)}  set {_hm(state.moon.moonset)}",
            value - 6,
            fill=Ink.SECONDARY,
        )

    c.text((col * 2 + 60, y), "COUCAL", label, fill=Ink.FAINT)
    c.text((col * 2 + 60, y + 40), f"dawn   {_hm(state.next_dawn)}", value, fill=Ink.PRIMARY)
    c.text((col * 2 + 60, y + 84), f"dusk   {_hm(state.next_dusk)}", value, fill=Ink.PRIMARY)
    c.text((col * 2 + 60, y + 128), "civil twilight", value - 6, fill=Ink.SECONDARY)


def render(state: RenderState, palette: Palette | None = None) -> bytes:
    """Draw the face. ``palette`` decides how the inks look on the fitted panel;
    omitting it gives the mono floor, which is always a complete clock."""
    c = Canvas(palette)

    # Header
    c.text((90, 70), "COUCAL CLOCK", 40, fill=Ink.PRIMARY)
    c.text((90, 128), "Phase 0 · pipeline self-test", 28, fill=Ink.SECONDARY)
    if state.unit_label:
        c.text((PANEL_W - 90, 70), state.unit_label, 30, fill=Ink.SECONDARY, anchor="ra")

    # Big civil time
    hhmm = state.local_time.strftime("%H:%M")
    c.text((PANEL_W // 2, 560), hhmm, 360, fill=Ink.PRIMARY, anchor="mm")
    c.text(
        (PANEL_W // 2, 800),
        state.local_time.strftime("%A  %d %B %Y"),
        48,
        fill=Ink.SECONDARY,
        anchor="mm",
    )

    # Heartbeat (top-right quadrant)
    _draw_heartbeat(c, PANEL_W - 240, 320, state.tick)

    # Astronomy (Phase 1). Absent if the ephemeris is missing or the moment is beyond
    # its span — in which case the clock says nothing rather than guessing.
    _draw_almanac(c, state)

    # Status strip
    _draw_battery(c, 90, PANEL_H - 150, state.power.battery_volts, state.power_state)
    q = _QUALITY_LABEL.get(state.time.quality, "?")
    if state.time.quality in (TimeQuality.RTC, TimeQuality.RTC_STALE):
        q += f"  ({state.time.holdover_days:.0f} d)"
    stale = state.time.quality in (TimeQuality.RTC_STALE, TimeQuality.UNKNOWN)
    c.text(
        (PANEL_W - 90, PANEL_H - 128),
        f"time: {q}",
        30,
        fill=Ink.WARNING if stale else Ink.PRIMARY,
        anchor="ra",
    )

    # A frame line so the panel edges and any ghosting are obvious in the sim.
    c.rectangle([40, 40, PANEL_W - 40, PANEL_H - 40], outline=Ink.FAINT, width=2)
    return c.to_framebuffer()
