"""Fake e-ink panel.

Reproduces the two things about the real IT8951 panel that actually shape the UI:

  1. **16 grey levels.** The incoming 8-bit framebuffer is quantised to 16 shades,
     so dithering and greyscale texture look on screen exactly as they will on glass.
  2. **Ghosting.** Partial refreshes leave a faint residue of prior frames; only a
     full refresh (or ``clear``) wipes it. This is why the compositor schedules
     periodic full clears — and the sim lets us *see* when one is overdue.

The panel keeps the latest image (Pillow ``Image``, mode "L"). The GUI reads it;
tests assert on it; ``save_png`` dumps it for screenshot regression.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from ..interfaces import RefreshMode

WIDTH = 1872
HEIGHT = 1404
GREY_LEVELS = 16


def _quantize_16(img: Image.Image) -> Image.Image:
    """Snap an 8-bit greyscale image to the panel's 16 discrete levels."""
    step = 255 / (GREY_LEVELS - 1)
    return img.point(lambda v: round(round(v / step) * step))


class SimDisplay:
    width = WIDTH
    height = HEIGHT

    def __init__(self, ghosting: bool = True) -> None:
        self._ghosting = ghosting
        # Start white, as an e-ink panel powers up after a clear.
        self.image = Image.new("L", (WIDTH, HEIGHT), color=255)
        self._ghost = Image.new("L", (WIDTH, HEIGHT), color=255)
        self.partial_refreshes = 0
        self.full_refreshes = 0
        self.partials_since_full = 0
        # The GUI sets this to be notified when the panel content changes.
        self.on_update = None

    def _incoming(self, framebuffer: bytes) -> Image.Image:
        if len(framebuffer) != WIDTH * HEIGHT:
            raise ValueError(f"framebuffer is {len(framebuffer)} bytes, expected {WIDTH * HEIGHT}")
        return _quantize_16(Image.frombytes("L", (WIDTH, HEIGHT), framebuffer))

    def push(
        self,
        framebuffer: bytes,
        mode: RefreshMode = RefreshMode.PARTIAL,
        region: tuple[int, int, int, int] | None = None,
    ) -> None:
        incoming = self._incoming(framebuffer)

        if mode is RefreshMode.FULL:
            self.image = incoming
            self._ghost = incoming.copy()
            self.full_refreshes += 1
            self.partials_since_full = 0
        else:
            base = incoming
            if region is not None:
                # Partial refresh only rewrites the region; the rest keeps prior pixels.
                x, y, w, h = region
                merged = self.image.copy()
                merged.paste(incoming.crop((x, y, x + w, y + h)), (x, y))
                base = merged
            self.image = self._apply_ghost(base)
            self.partial_refreshes += 1
            self.partials_since_full += 1

        if self.on_update is not None:
            self.on_update(self.image)

    def _apply_ghost(self, target: Image.Image) -> Image.Image:
        """Blend a faint memory of the previous frame to mimic partial-refresh ghosting."""
        if not self._ghosting:
            self._ghost = target.copy()
            return target
        # 6% of the old frame bleeds through; accumulates until a full refresh.
        blended = Image.blend(target, self._ghost, alpha=0.06)
        self._ghost = blended.copy()
        return blended

    def clear(self) -> None:
        self.image = Image.new("L", (WIDTH, HEIGHT), color=255)
        self._ghost = self.image.copy()
        self.full_refreshes += 1
        self.partials_since_full = 0
        if self.on_update is not None:
            self.on_update(self.image)

    def save_png(self, path: str | Path) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.image.save(path)
