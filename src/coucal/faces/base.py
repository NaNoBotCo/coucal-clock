"""Drawing scaffold shared by every face.

``Canvas`` wraps a Pillow greyscale image sized to the panel and hands back a
framebuffer (``bytes``) suitable for ``Display.push``. ``RenderState`` is the
immutable bundle of facts a face draws from — the sole input to ``render``.

Typography: Phase 0 uses Pillow's scalable default font so the pipeline works with
no vendored assets. Phase 3 swaps in the bundled Noto families (Thai / Latin /
Symbols 2) via ``Canvas.font`` without touching face code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from ..hal.interfaces import Position, PowerReading, TimeReading
from . import palette as palette_module
from .palette import Ink, Palette

if TYPE_CHECKING:  # annotations only — no runtime dependency on the astronomy stack
    from ..almanac.lanna import Festival, LannaDay
    from ..almanac.lunation import Lunation
    from ..almanac.solar_lunar import MoonState, SolarDay
    from ..almanac.thai import ThaiDay

PANEL_W = 1872
PANEL_H = 1404

_FONT_DIR = Path(__file__).resolve().parents[3] / "data" / "fonts"

# Legacy raw grey values. Prefer `Ink.*` in new face code — these remain only so that
# drawing helpers written before the palette existed keep working.
INK = 0
INK_SOFT = 68
INK_FAINT = 136
PAPER = 255


@dataclass(frozen=True)
class RenderState:
    """Everything a face needs to draw a frame. Pure data, no hardware handles.

    The almanac fields are optional. If the ephemeris is missing the clock still shows
    the time rather than refusing to draw, so every face must handle ``None``.
    """

    time: TimeReading
    position: Position
    power: PowerReading
    local_time: datetime  # civil time in the temple's timezone
    tick: int  # monotonically increasing wake counter (drives heartbeat)
    unit_label: str = ""
    power_state: str = "normal"  # normal | hourly | date_only | hibernate
    time_confidence: str = "exact"  # from services.timebase
    # Astronomy (Phase 1). Under `from __future__ import annotations` these are strings,
    # so the face layer never imports the astronomy stack at runtime.
    sun: SolarDay | None = None
    moon: MoonState | None = None
    lunation: Lunation | None = None
    thai: ThaiDay | None = None
    next_wan_phra: ThaiDay | None = None
    lanna: LannaDay | None = None
    festival: Festival | None = None
    next_festival: Festival | None = None
    next_dawn: datetime | None = None
    next_dusk: datetime | None = None


# Bundled faces, all SIL Open Font License (licences vendored beside them).
# Noto Sans Thai carries Latin as well, so it serves as the everyday face and mixed
# Thai/English strings — "หอระฆัง / bell tower" — render from a single file.
FONT_DEFAULT = "NotoSansThai-Variable.ttf"
FONT_LATIN = "NotoSans-Variable.ttf"
FONT_TAI_THAM = "NotoSansTaiTham-Variable.ttf"  # the Lanna / Tua Mueang script
FONT_SERIF_THAI = "NotoSerifThai-Variable.ttf"  # ceremonial register

# Unicode block for Tai Tham (Lanna). Detecting it is what lets a face mix scripts.
TAI_THAM_RANGE = (0x1A20, 0x1AAF)


def has_tai_tham(text: str) -> bool:
    lo, hi = TAI_THAM_RANGE
    return any(lo <= ord(ch) <= hi for ch in text)


# Weight axis values. The bundled Noto families are variable fonts carrying 100-900, so
# a face can set real typographic hierarchy — a Light month name under a Bold numeral —
# rather than relying on size alone. On a greyscale panel, weight contrast is the main
# tool available for making a composition feel engraved rather than typed.
W_LIGHT = 300
W_REGULAR = 400
W_MEDIUM = 500
W_SEMIBOLD = 600
W_BOLD = 700


@lru_cache(maxsize=192)
def _load_font(
    size: int, family: str = FONT_DEFAULT, weight: int = W_REGULAR
) -> ImageFont.FreeTypeFont:
    """Load a bundled face at a given optical weight.

    The fallback chain matters for posterity: a stripped install with no `data/fonts/`
    still renders a legible clock, just without Thai glyphs. A font without a weight
    axis simply ignores the request. Nothing crashes for want of a typeface.
    """
    for name in (family, FONT_DEFAULT, FONT_LATIN):
        candidate = _FONT_DIR / name
        if candidate.exists():
            font = ImageFont.truetype(str(candidate), size)
            if weight != W_REGULAR:
                try:
                    font.set_variation_by_axes([weight, 100])  # [Weight, Width]
                except Exception:
                    pass  # static font, or no such axis — regular is a fine fallback
            return font
    # Pillow >= 10: the default font is scalable via `size`.
    return ImageFont.load_default(size=size)


def font_for(text: str, size: int, weight: int = W_REGULAR) -> ImageFont.FreeTypeFont:
    """Pick the face that can actually draw this string.

    Pillow does no automatic font fallback, so script selection is ours to do. Today
    this is a simple two-way choice — Tai Tham or everything else. A face that mixes
    Tai Tham *and* Thai in one string will need to draw it in runs; that is a Phase 3
    problem, recorded here where whoever hits it will look.
    """
    return _load_font(size, FONT_TAI_THAM if has_tai_tham(text) else FONT_DEFAULT, weight)


class Canvas:
    """A panel-sized drawing surface that speaks in meanings, not colours.

    Pass an :class:`~coucal.faces.palette.Ink` anywhere a fill is wanted and the active
    palette resolves it. Raw integers are still accepted so existing drawing code keeps
    working, but faces should prefer inks — that is what lets the same face render on a
    greyscale panel today and a colour one later without being rewritten.
    """

    def __init__(self, palette: Palette | None = None) -> None:
        self.palette = palette or palette_module.DEFAULT
        self.image = Image.new("L", (PANEL_W, PANEL_H), color=self.ink(Ink.PAPER))
        self.draw = ImageDraw.Draw(self.image)

    def ink(self, value) -> int:
        """Resolve an ``Ink`` (or pass through a raw byte value)."""
        if isinstance(value, Ink):
            return self.palette.value(value)
        return value

    def font(
        self, size: int, family: str = FONT_DEFAULT, weight: int = W_REGULAR
    ) -> ImageFont.FreeTypeFont:
        return _load_font(size, family, weight)

    def text(
        self, xy, s, size, fill=Ink.PRIMARY, anchor="la", family=None, weight=W_REGULAR
    ) -> None:
        """Draw text, choosing a face that can render the script unless one is named."""
        font = self.font(size, family, weight) if family else font_for(s, size, weight)
        self.draw.text(xy, s, font=font, fill=self.ink(fill), anchor=anchor)

    def measure(
        self, s: str, size: int, family: str | None = None, weight: int = W_REGULAR
    ) -> tuple[int, int]:
        """(width, height) of a string as it would be drawn.

        Faces should compose from measured widths rather than guessed offsets —
        hand-tuned offsets break the moment a font, a size, or a numeral changes, and
        Thai text varies in width far more than Latin does.
        """
        font = self.font(size, family, weight) if family else font_for(s, size, weight)
        box = self.draw.textbbox((0, 0), s, font=font)
        return box[2] - box[0], box[3] - box[1]

    def line(self, xy, fill=Ink.FAINT, width=1) -> None:
        self.draw.line(xy, fill=self.ink(fill), width=width)

    def rectangle(self, xy, fill=None, outline=None, width=1) -> None:
        self.draw.rectangle(
            xy,
            fill=self.ink(fill) if fill is not None else None,
            outline=self.ink(outline) if outline is not None else None,
            width=width,
        )

    def ellipse(self, xy, fill=None, outline=None, width=1) -> None:
        self.draw.ellipse(
            xy,
            fill=self.ink(fill) if fill is not None else None,
            outline=self.ink(outline) if outline is not None else None,
            width=width,
        )

    def to_framebuffer(self) -> bytes:
        return self.image.tobytes()
