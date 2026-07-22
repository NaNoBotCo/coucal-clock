"""Tests for semantic inks and the colour-to-mono fallback.

The promise these guard: **black is the floor.** Whatever panel is fitted, every face
renders legibly, and nothing that carries meaning is lost when colour disappears.
"""

import pytest

from coucal.faces import palette as palette_module
from coucal.faces.base import Canvas
from coucal.faces.palette import MONO16, PALETTES, SPECTRA6, Ink, Palette


@pytest.mark.parametrize("pal", list(PALETTES.values()), ids=list(PALETTES))
def test_every_ink_resolves_in_every_palette(pal: Palette):
    """A palette missing an ink would crash a face at render time on real hardware."""
    for ink in Ink:
        assert isinstance(pal.value(ink), int)
        r, g, b = pal.as_rgb(ink)
        assert all(0 <= channel <= 255 for channel in (r, g, b))


def test_mono_is_the_default():
    """Black is the fallback: no configuration, no colour panel, still a whole clock."""
    assert palette_module.DEFAULT is MONO16
    assert not MONO16.is_colour
    assert Canvas().palette is MONO16


def test_reading_text_is_legible_against_paper_in_every_palette():
    """Primary marks must contrast strongly with the background, or the dial is unreadable."""
    for pal in PALETTES.values():
        paper = pal.as_rgb(Ink.PAPER)
        primary = pal.as_rgb(Ink.PRIMARY)
        # Crude luminance difference is enough to catch an inverted or washed-out palette.
        lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]  # noqa: E731
        assert abs(lum(paper) - lum(primary)) > 120, f"{pal.name}: primary is not legible"


def test_mono_keeps_its_greys_distinct():
    """The hierarchy — primary, secondary, faint, paper — must stay visually separable
    on a greyscale panel, or the composition collapses into one flat tone."""
    steps = [MONO16.value(i) for i in (Ink.PRIMARY, Ink.SECONDARY, Ink.FAINT, Ink.PAPER)]
    assert steps == sorted(steps), "expected primary darkest through paper lightest"
    for a, b in zip(steps, steps[1:], strict=False):
        assert b - a >= 60, "grey steps too close to tell apart at two metres"


def test_colour_only_meaning_is_not_relied_upon():
    """WARNING and SACRED collapse onto ordinary ink in mono — by design.

    That is exactly why the rule exists: colour reinforces, it never carries meaning by
    itself. If this ever stops being true, the mono panel silently loses information.
    """
    assert MONO16.value(Ink.WARNING) == MONO16.value(Ink.PRIMARY)
    assert MONO16.value(Ink.SACRED) == MONO16.value(Ink.PRIMARY)
    # ...whereas a colour panel distinguishes them.
    assert SPECTRA6.value(Ink.WARNING) != SPECTRA6.value(Ink.PRIMARY)
    assert SPECTRA6.value(Ink.SACRED) != SPECTRA6.value(Ink.PRIMARY)


def test_palette_records_the_panel_it_describes():
    """Capabilities travel with the palette, so the compositor can adapt rather than
    assume — Spectra 6 has no partial refresh, and pretending otherwise would ghost."""
    assert MONO16.supports_partial_refresh
    assert not SPECTRA6.supports_partial_refresh
    assert MONO16.grey_levels == 16


def test_canvas_accepts_inks_and_raw_values():
    c = Canvas()
    assert c.ink(Ink.PRIMARY) == MONO16.value(Ink.PRIMARY)
    assert c.ink(42) == 42  # legacy raw values still work


def test_a_face_renders_under_every_palette():
    """The real fallback check: the same face code must produce a full framebuffer on
    any panel, without the face knowing which one it is."""
    from datetime import UTC, datetime

    from coucal.faces import phase0
    from coucal.faces.base import PANEL_H, PANEL_W, RenderState
    from coucal.hal.interfaces import Position, PowerReading, TimeQuality, TimeReading

    utc = datetime(2026, 7, 20, 0, 30, tzinfo=UTC)
    state = RenderState(
        time=TimeReading(utc=utc, quality=TimeQuality.GPS),
        position=Position(18.85, 99.05, 320.0),
        power=PowerReading(13.0, 0.4, 18.0, 1.1),
        local_time=utc,
        tick=1,
    )
    for name in PALETTES:
        framebuffer = phase0.render(state, palette=palette_module.get(name))
        assert len(framebuffer) == PANEL_W * PANEL_H, f"{name} produced a short framebuffer"
