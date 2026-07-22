"""Screenshot regression for faces.

Renders a face at a fixed instant and compares against a committed baseline PNG.
On first run (no baseline) it writes the baseline and skips — so adopting a new face
is a deliberate, reviewable commit of its baseline image. Later runs fail if the mean
pixel difference exceeds a small threshold, catching accidental visual drift.

Phase 3 extends this to all eight instrument faces.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from coucal.faces import phase0
from coucal.faces.base import PANEL_H, PANEL_W, RenderState
from coucal.hal.interfaces import Position, PowerReading, TimeQuality, TimeReading

BASELINE_DIR = Path(__file__).parent / "screenshots"
MAX_MEAN_DIFF = 1.0  # average per-pixel greyscale difference allowed (0..255)


def _fixed_state() -> RenderState:
    """A fully-populated state at one fixed instant.

    Real almanac values are computed, not stubbed, so the baseline exercises the sun /
    moon / coucal block too — a regression in the astronomy shows up as a visual diff.
    """
    from coucal.almanac.ephemeris import Observer, get_sky
    from coucal.almanac.solar_lunar import moon_state, next_coucal_calls, sun_day

    observer = Observer(18.85, 99.05, 320.0, "Asia/Bangkok")
    local = datetime(2026, 7, 19, 7, 30, tzinfo=observer.tz)
    utc = local.astimezone(UTC)

    sky = get_sky(observer)
    dawn, dusk = next_coucal_calls(sky, local)

    return RenderState(
        time=TimeReading(utc=utc, quality=TimeQuality.GPS),
        position=Position(18.85, 99.05, 320.0),
        power=PowerReading(13.0, 0.4, 18.0, 1.1),
        local_time=local,
        tick=3,
        unit_label="COUCAL-01",
        sun=sun_day(sky, local.date()),
        moon=moon_state(sky, local),
        next_dawn=dawn,
        next_dusk=dusk,
    )


def _image_from(fb: bytes) -> Image.Image:
    return Image.frombytes("L", (PANEL_W, PANEL_H), fb)


def _mean_diff(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a, b)
    hist = diff.histogram()
    total = sum(i * n for i, n in enumerate(hist))
    return total / (a.width * a.height)


def _check_baseline(name: str, framebuffer: bytes):
    img = _image_from(framebuffer)
    baseline_path = BASELINE_DIR / f"{name}.png"

    if not baseline_path.exists():
        BASELINE_DIR.mkdir(parents=True, exist_ok=True)
        img.save(baseline_path)
        pytest.skip(f"baseline written: {baseline_path.name} — review and commit it")

    baseline = Image.open(baseline_path).convert("L")
    assert img.size == baseline.size
    diff = _mean_diff(img, baseline)
    assert diff <= MAX_MEAN_DIFF, f"{name} face drifted (mean diff {diff:.3f} > {MAX_MEAN_DIFF})"


def test_phase0_face_matches_baseline():
    _check_baseline("phase0", phase0.render(_fixed_state()))


def test_main_face_matches_baseline():
    """The face people actually read — Thai, analog, Buddhist year."""
    from coucal.faces import main

    _check_baseline("main", main.render(_fixed_state()))


def test_main_face_on_a_wan_phra():
    """Wan phra changes the composition, so it gets its own baseline."""
    from datetime import date

    from coucal.almanac.thai import next_wan_phra, thai_day
    from coucal.faces import main

    state = _fixed_state()
    holy = date(2026, 7, 29)  # Asalha Bucha; ขึ้น ๑๕ ค่ำ เดือนแปดสอง
    on_holy_day = replace(
        state,
        local_time=state.local_time.replace(year=2026, month=7, day=29),
        thai=thai_day(holy),
        next_wan_phra=next_wan_phra(holy),
    )
    assert on_holy_day.thai.is_wan_phra
    _check_baseline("main_wan_phra", main.render(on_holy_day))


def test_lanna_face_matches_baseline():
    """The Northern face — zodiac band, naga ring, Lanna lunar day."""
    from datetime import date

    from coucal.almanac.lanna import festival_on, lanna_day, next_festival
    from coucal.faces import lanna

    state = _fixed_state()
    when = date(2026, 11, 24)  # Yi Peng — the fullest composition
    on_yi_peng = replace(
        state,
        local_time=state.local_time.replace(year=2026, month=11, day=24),
        lanna=lanna_day(when),
        festival=festival_on(when),
        next_festival=next_festival(when),
    )
    _check_baseline("lanna", lanna.render(on_yi_peng))
