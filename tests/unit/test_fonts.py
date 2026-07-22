"""Typography: script coverage, and the licence promise.

Beauty on e-ink is mostly typography, and the clock has to render three scripts —
Latin, Thai, and Tai Tham (the Lanna / Tua Mueang script of the wat it will stand in).
Pillow does no automatic font fallback, so picking the right face is our job and these
tests keep it honest.
"""

from pathlib import Path

import pytest

from coucal.faces.base import (
    _FONT_DIR,
    FONT_DEFAULT,
    FONT_LATIN,
    FONT_SERIF_THAI,
    FONT_TAI_THAM,
    font_for,
    has_tai_tham,
)

BUNDLED = (FONT_DEFAULT, FONT_LATIN, FONT_TAI_THAM, FONT_SERIF_THAI)


@pytest.mark.parametrize("name", BUNDLED)
def test_font_is_bundled(name):
    assert (_FONT_DIR / name).exists(), f"{name} missing — run scripts/fetch_data.sh"


def test_every_bundled_font_ships_its_licence():
    """We promised vendored licences. A font without one is a posterity liability."""
    licences = list(_FONT_DIR.glob("OFL*.txt"))
    assert len(licences) >= len(BUNDLED), "expected an OFL licence per bundled family"
    for path in licences:
        assert "SIL OPEN FONT LICENSE" in path.read_text(encoding="utf-8").upper()


def test_tai_tham_is_detected():
    assert has_tai_tham("ᨠᩅᩫᩁ")  # Lanna script
    assert not has_tai_tham("หอระฆัง")  # Thai script is a different block
    assert not has_tai_tham("bell tower")


def test_script_selects_the_right_face():
    assert Path(font_for("ᨠᩅᩫᩁ", 40).path).name == FONT_TAI_THAM
    assert Path(font_for("หอระฆัง / bell tower", 40).path).name == FONT_DEFAULT
    assert Path(font_for("COUCAL CLOCK", 40).path).name == FONT_DEFAULT


def test_thai_and_latin_render_from_one_face():
    """The unit labels mix scripts — 'หอระฆัง / bell tower'. If the everyday face did
    not carry Latin too, every label would need splitting into runs."""
    font = font_for("หอระฆัง / bell tower", 40)
    for ch in "หอระฆังbell towerBELL":
        if ch == " ":
            continue
        assert font.getmask(ch).getbbox() is not None, f"no glyph for {ch!r}"


def test_missing_font_directory_does_not_crash(monkeypatch):
    """A stripped install with no data/fonts must still draw a legible clock."""
    from coucal.faces import base

    base._load_font.cache_clear()
    monkeypatch.setattr(base, "_FONT_DIR", Path("/nonexistent/fonts"))
    font = base._load_font(32)
    assert font is not None
    base._load_font.cache_clear()
