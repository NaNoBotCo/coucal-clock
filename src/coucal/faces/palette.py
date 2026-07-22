"""Semantic inks — how a face says *what* it is drawing, not *what colour* to use.

Faces never name a grey value or an RGB triple. They ask for an **ink** with a meaning
— ``Ink.SACRED``, ``Ink.WARNING`` — and the active :class:`Palette` decides how that
looks on whatever panel is actually fitted.

That indirection is the whole point:

* **Black is the fallback.** The mono palette is the floor. Every ink resolves to a
  legible grey on a 16-level panel, so the clock is complete and beautiful with no
  colour at all.
* **Colour blooms when available.** A colour panel resolves the same inks to real
  pigments. No face changes; only the palette does.

Doing this now, with one face built, is deliberate — the same reasoning as the face
registry. Retrofitting semantic inks across a dozen finished faces would be a rewrite;
writing them this way from the start costs nothing.

## The rule that makes the fallback honest

**Meaning is never carried by colour alone.** A warning is a warning because of its
words, its weight, and its position — the red is a reinforcement, not the message. This
is what lets the mono panel lose every colour and lose no information, and it is also
plain good practice for anyone reading the dial with imperfect sight.

A test enforces it: every ink must remain distinguishable, or redundantly encoded, once
flattened to grey.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Ink(Enum):
    """What a mark *means*. Faces speak only in these."""

    PAPER = "paper"  # the background the panel rests at
    PRIMARY = "primary"  # the main reading: time, date, the thing you came for
    SECONDARY = "secondary"  # supporting text
    FAINT = "faint"  # rules, ticks, chrome that must recede
    SACRED = "sacred"  # wan phra, holy days, the ceremonial register
    WARNING = "warning"  # low power, stale time — something needs a human
    CELESTIAL = "celestial"  # sun, moon, planets, sky
    ENGRAVING = "engraving"  # engine-turned ground: the faintest mark on the dial


@dataclass(frozen=True)
class Palette:
    """Maps meanings to what the fitted panel can actually show.

    ``values`` are byte values written into the framebuffer. On a greyscale panel that
    byte is a grey level (0 black … 255 white). On an indexed colour panel it is a
    palette index, and ``rgb`` gives the colour each index displays — which is what the
    simulator draws and what a colour driver would load into the panel.
    """

    name: str
    values: dict[Ink, int]
    rgb: dict[int, tuple[int, int, int]] | None = None  # None => greyscale panel
    grey_levels: int = 16
    supports_partial_refresh: bool = True
    note: str = ""

    @property
    def is_colour(self) -> bool:
        return self.rgb is not None

    def value(self, ink: Ink) -> int:
        return self.values[ink]

    def as_rgb(self, ink: Ink) -> tuple[int, int, int]:
        """What this ink looks like to an eye — for the simulator preview."""
        v = self.value(ink)
        if self.rgb is None:
            return (v, v, v)
        return self.rgb[v]


# --------------------------------------------------------------------------- #
# MONO — the floor. This is the committed 10.3" panel, and the fallback for every
# other panel that might ever be fitted. Values chosen to land cleanly on the
# panel's 16 discrete levels.
# --------------------------------------------------------------------------- #

MONO16 = Palette(
    name="mono16",
    values={
        Ink.PAPER: 255,
        Ink.PRIMARY: 0,
        Ink.SECONDARY: 68,
        Ink.FAINT: 136,
        Ink.SACRED: 0,  # carried by weight and ornament, not hue
        Ink.WARNING: 0,  # carried by words and position, not hue
        Ink.CELESTIAL: 68,
        # Guilloche must be *felt*, not read. 204 is a clean 16-level step and sits
        # far enough above FAINT (136) that it never competes with a numeral.
        Ink.ENGRAVING: 204,
    },
    rgb=None,
    grey_levels=16,
    supports_partial_refresh=True,
    note="Waveshare 10.3in IT8951, 1872x1404, 16 greys, sub-second partial refresh.",
)


# --------------------------------------------------------------------------- #
# SPECTRA 6 — an open door, not a commitment. See docs/GROWING.md.
#
# E Ink Spectra 6 panels carry six pigments: black, white, red, yellow, green, blue.
# The palette below is written as a woodblock reading of those six — the register of a
# Lanna temple mural (red and gold on cream) rather than a screenshot of a photograph.
# Six flat inks suit instrument dials far better than they suit photographs.
#
# The costs are real and are documented in docs/DISPLAY.md: no partial refresh, a
# 12-19 second full-screen refresh, and lower resolution than the mono panel.
# --------------------------------------------------------------------------- #

_SPECTRA6_RGB = {
    0: (0, 0, 0),  # black
    1: (255, 255, 255),  # white
    2: (200, 40, 40),  # red
    3: (220, 180, 60),  # yellow
    4: (60, 130, 80),  # green
    5: (50, 80, 160),  # blue
}

SPECTRA6 = Palette(
    name="spectra6",
    values={
        Ink.PAPER: 1,
        Ink.PRIMARY: 0,
        Ink.SECONDARY: 0,
        Ink.FAINT: 0,
        Ink.SACRED: 3,  # gold — the ceremonial register
        Ink.WARNING: 2,  # red, reinforcing words that already say it
        Ink.CELESTIAL: 5,  # the sky
        # A six-pigment panel has no light grey, so the engraved ground simply is
        # not drawn there rather than being rendered as solid ink.
        Ink.ENGRAVING: 1,
    },
    rgb=_SPECTRA6_RGB,
    grey_levels=2,
    supports_partial_refresh=False,
    note=(
        "E Ink Spectra 6: six pigments, no partial refresh, 12-19 s full refresh. "
        "Green (index 4) is deliberately unassigned and available."
    ),
)


PALETTES = {p.name: p for p in (MONO16, SPECTRA6)}
DEFAULT = MONO16


def get(name: str) -> Palette:
    if name not in PALETTES:
        raise ValueError(f"unknown palette {name!r}; have {sorted(PALETTES)}")
    return PALETTES[name]
