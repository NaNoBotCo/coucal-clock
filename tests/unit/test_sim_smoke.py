"""Smoke test for the simulator window.

Builds the real Tk UI, pumps a few event-loop iterations, and tears it down — enough
to catch a broken widget, a missing callback, or a render crash. Skipped wherever Tk
cannot open a display (headless CI, a Python built without _tkinter), so it protects
the GUI on a workstation without turning CI red.
"""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

CONFIG = Path(__file__).resolve().parents[2] / "config" / "unit-01.toml"


def _tk_available() -> bool:
    """Check imports only.

    Deliberately does NOT instantiate a probe ``Tk()``: on macOS, creating a second
    Tk root after destroying the first segfaults the interpreter, so a throwaway
    probe would crash the very test it is guarding.
    """
    try:
        import tkinter  # noqa: F401

        from PIL import ImageTk  # noqa: F401
    except Exception:
        return False
    # On X11 (headless CI) tkinter imports fine but Tk() has no display to open.
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _tk_available(), reason="Tk display unavailable (headless or no _tkinter)"
)


def test_simulator_builds_renders_and_steps():
    from coucal.config import UnitConfig
    from coucal.sim.__main__ import Simulator

    sim = Simulator(UnitConfig.load(CONFIG))
    try:
        sim.root.withdraw()  # keep the window off-screen during the test
        first_tick = sim.tick

        # Pump the event loop; the periodic _loop callback must not raise.
        for _ in range(5):
            sim.root.update()

        # A manual step must advance virtual time and wake the clock.
        before = sim.harness.timeline.now()
        sim._step(timedelta(days=1))
        assert sim.harness.timeline.now() - before == timedelta(days=1)
        assert sim.tick > first_tick

        # The interactive controls must not raise.
        sim._press_button()
        sim._clear()
        sim.gps_on.set(False)
        sim._toggle_gps()

        # Something was actually drawn to the panel.
        assert sim.harness.display.full_refreshes + sim.harness.display.partial_refreshes > 0

        # Regression: choosing a face and then warping time must NOT reset it. The
        # 90 s auto-return counts wall-clock idleness at the desk, never virtual time —
        # a +1 month step is thirty days of sky and zero seconds of person.
        sim._show_face("lanna")
        sim._step(timedelta(days=30))
        sim._step(timedelta(hours=3))
        for _ in range(3):
            sim.root.update()
        assert sim.navigator.current.key == "lanna", (
            "time-warp booted the reviewer back to the home face"
        )
    finally:
        sim.root.destroy()
