"""Interactive simulator window.

Layout: a scaled preview of the 1872x1404 e-ink panel on the left; a control column
on the right — time-warp (pause / rates / step / jump), the brass button, a battery
slider with live load-shedding state, a GPS toggle to exercise RTC holdover, and a
full-refresh/clear control with a ghosting counter.

Because the almanac and faces are pure functions of civil time, dragging the rate up
ages the whole clock through months in seconds — the heartbeat dot steps on every
simulated wake, exactly as it will on the temple wall.
"""

from __future__ import annotations

import argparse
import time
import tkinter as tk
from datetime import UTC, datetime, timedelta

from PIL import ImageTk

from ..app import render_cycle
from ..config import UnitConfig
from ..faces import registry
from ..hal.sim.build import build_sim_harness
from ..services.navigator import Navigator
from .power_policy import HIBERNATE, power_state_for

PREVIEW_W = 860  # scaled-down panel width in the window

# Control-panel typography. Deliberately large: the simulator is used at a desk by
# someone who should not have to squint at 11 pt chrome to read the clock's state.
UI_BODY = ("TkDefaultFont", 15)
UI_HEAD = ("TkDefaultFont", 17, "bold")
UI_CLOCK = ("TkDefaultFont", 20, "bold")

RATES = [
    ("‖ pause", 0.0),
    ("1×", 1.0),
    ("1 min/s", 60.0),
    ("1 hr/s", 3600.0),
    ("1 day/s", 86400.0),
    ("1 wk/s", 604800.0),
]


class Simulator:
    def __init__(self, config: UnitConfig) -> None:
        self.config = config
        self.harness = build_sim_harness(
            latitude=config.location.latitude,
            longitude=config.location.longitude,
            elevation_m=config.location.elevation_m,
            holdover_warn_days=config.power.holdover_warn_days,
        )
        self.tick = 0
        self.navigator = Navigator()
        self._last_wake = None
        self._last_wall = time.monotonic()
        self.wake_interval = timedelta(minutes=config.power.wake_interval_min)

        self.root = tk.Tk()
        self.root.title(f"Coucal Clock simulator — {config.unit_id}")
        self._build_ui()
        self._render_now()  # first frame
        self.root.after(50, self._loop)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.preview = tk.Label(self.root, bd=1, relief="solid")
        self.preview.grid(row=0, column=0, rowspan=40, padx=10, pady=10)

        # Everything in the control column stacks vertically; ``place`` grids a widget
        # into the next free row so we never track a manual counter (and never lint
        # on packed one-liners).
        col = 1
        self._row = 0

        def place(widget, **grid):
            grid.setdefault("sticky", "w")
            grid.setdefault("padx", 8)
            widget.grid(row=self._row, column=col, **grid)
            self._row += 1
            return widget

        def heading(text):
            place(tk.Label(self.root, text=text, font=UI_HEAD), pady=(14, 2))

        self.clock_var = tk.StringVar()
        place(
            tk.Label(self.root, textvariable=self.clock_var, font=UI_CLOCK, justify="left"),
            pady=(10, 4),
        )

        self.status_var = tk.StringVar()
        place(tk.Label(self.root, textvariable=self.status_var, font=UI_BODY, justify="left"))

        heading("Time warp")
        rate_frame = place(tk.Frame(self.root))
        self.rate = tk.DoubleVar(value=0.0)
        for label, value in RATES:
            tk.Radiobutton(
                rate_frame,
                text=label,
                variable=self.rate,
                value=value,
                indicatoron=False,
                width=9,
                font=UI_BODY,
            ).pack(side="left")

        heading("Step forward")
        step_frame = place(tk.Frame(self.root))
        for label, delta in [
            ("+5 min", timedelta(minutes=5)),
            ("+1 hr", timedelta(hours=1)),
            ("+1 day", timedelta(days=1)),
            ("+1 week", timedelta(weeks=1)),
            ("+1 month", timedelta(days=30)),
        ]:
            tk.Button(
                step_frame, text=label, font=UI_BODY, command=lambda d=delta: self._step(d)
            ).pack(side="left")

        heading("Faces")
        self.face_var = tk.StringVar()
        place(tk.Label(self.root, textvariable=self.face_var, font=UI_BODY))

        # One button per built face. The device has only the brass button, but hunting
        # for a face by pressing repeatedly is a poor way to review one at a desk.
        face_frame = place(tk.Frame(self.root))
        for spec in registry.live_faces():
            tk.Button(
                face_frame,
                text=spec.title_en,
                font=UI_BODY,
                command=lambda k=spec.key: self._show_face(k),
            ).pack(side="left", padx=2)

        button_frame = place(tk.Frame(self.root), pady=(6, 0))
        tk.Button(
            button_frame,
            text="🔔  Press (next face)",
            font=UI_BODY,
            command=self._press_button,
        ).pack(side="left", padx=2)
        tk.Button(
            button_frame,
            text="Hold (next group)",
            font=UI_BODY,
            command=self._long_press,
        ).pack(side="left", padx=2)

        heading("Sensors")

        place(tk.Label(self.root, text="Battery volts", font=UI_BODY), pady=(8, 0))
        self.battery = tk.DoubleVar(value=13.0)
        place(
            tk.Scale(
                self.root,
                from_=11.8,
                to=13.4,
                resolution=0.05,
                orient="horizontal",
                variable=self.battery,
                length=340,
                font=UI_BODY,
                command=lambda _=None: self._render_now(),
            )
        )

        self.gps_on = tk.BooleanVar(value=True)
        place(
            tk.Checkbutton(
                self.root,
                text="GPS fix available (uncheck = RTC holdover)",
                variable=self.gps_on,
                font=UI_BODY,
                command=self._toggle_gps,
            ),
            pady=(4, 0),
        )

        place(
            tk.Button(
                self.root,
                text="Full refresh / clear ghosting",
                font=UI_BODY,
                command=self._clear,
            ),
            pady=(12, 0),
        )

        self.refresh_var = tk.StringVar()
        place(tk.Label(self.root, textvariable=self.refresh_var, font=UI_BODY, justify="left"))

        place(
            tk.Label(
                self.root,
                text="keys:  space = pause   ·   b = press button",
                font=UI_BODY,
                fg="#666666",
            ),
            pady=(10, 8),
        )

        # Keyboard shortcuts
        self.root.bind("<space>", lambda _e: self.rate.set(0.0))
        self.root.bind("b", lambda _e: self._press_button())

    # --------------------------------------------------------------- actions
    def _wall_now(self) -> datetime:
        """Human time at the desk.

        The 90 s auto-return exists for a *person who walked away*, so it must count
        real idle seconds. On the device, virtual and real time are the same thing; in
        the simulator the timeline can leap a month while the person is right here,
        mid-review — and warping must never boot them off the face they chose.
        """
        return datetime.now(UTC)

    def _press_button(self) -> None:
        """Short press: next face in this category — the real brass-button behaviour."""
        self.harness.button.press()
        self.harness.button.poll()  # the navigator consumes it
        self.navigator.short_press(self._wall_now())
        self._render_now()

    def _long_press(self) -> None:
        """Long press: jump to the next category of faces."""
        self.navigator.long_press(self._wall_now())
        self._render_now()

    def _show_face(self, key: str) -> None:
        """Jump straight to a named face — a simulator convenience, not on the device."""
        self.navigator.current_key = key
        self.navigator.last_interaction = self._wall_now()
        self._render_now()

    def _toggle_gps(self) -> None:
        self.harness.timeline.gps_available = self.gps_on.get()
        self._render_now()

    def _clear(self) -> None:
        self.harness.display.clear()
        self._render_now()

    def _step(self, delta: timedelta) -> None:
        # Stepping time IS user presence — it must not count toward the idle
        # auto-return, or reviewing a face by warping would keep kicking you home.
        if self.navigator.last_interaction is not None:
            self.navigator.last_interaction = self._wall_now()
        before = self.harness.timeline.now()
        self.harness.timeline.jump(delta)
        self._account_for_elapsed(before, self.harness.timeline.now())
        self._wake()  # a manual step always triggers a wake

    # ----------------------------------------------------------------- loop
    def _loop(self) -> None:
        now = time.monotonic()
        dt = now - self._last_wall
        self._last_wall = now
        before = self.harness.timeline.now()
        self.harness.timeline.rate = self.rate.get()
        self.harness.timeline.tick(dt)
        self._account_for_elapsed(before, self.harness.timeline.now())
        if self.rate.get() and self.navigator.last_interaction is not None:
            # Watching a time-warp run is presence, not absence.
            self.navigator.last_interaction = self._wall_now()
        self._maybe_wake()
        self.root.after(50, self._loop)

    def _account_for_elapsed(self, before, after) -> None:
        """Move the battery and holdover clock as simulated time passes."""
        hours = (after - before).total_seconds() / 3600.0
        if hours <= 0:
            return
        if not self.harness.timeline.gps_available:
            self.harness.timeline.holdover_days += hours / 24.0

    def _maybe_wake(self) -> None:
        vnow = self.harness.timeline.now()
        if self._last_wake is None or (vnow - self._last_wake) >= self.wake_interval:
            self._wake()

    def _wake(self) -> None:
        self._last_wake = self.harness.timeline.now()
        self.tick += 1
        self._render_now()

    # --------------------------------------------------------------- render
    def _render_now(self) -> None:
        # Reflect the battery slider into the fake telemetry before rendering.
        self.harness.power.battery_volts = self.battery.get()
        state_name = power_state_for(self.battery.get(), self.config.power)
        # Auto-return counts WALL seconds, never virtual ones — the return-home exists
        # for a person who walked away, and time-warp is not walking away.
        self.navigator.tick(self._wall_now())
        render_cycle(
            self.harness.hal,
            self.config,
            self.tick,
            power_state=state_name,
            face_key=self.navigator.current_key,
        )
        self._update_preview()
        self._update_labels(state_name)

    def _update_preview(self) -> None:
        img = self.harness.display.image
        scale = PREVIEW_W / img.width
        preview = img.resize((PREVIEW_W, int(img.height * scale)))
        self._photo = ImageTk.PhotoImage(preview)  # keep a reference
        self.preview.configure(image=self._photo)

    def _update_labels(self, state_name: str) -> None:
        reading = self.harness.time.now()
        self.clock_var.set(
            f"UTC   {reading.utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"wake  #{self.tick}   (every {self.config.power.wake_interval_min} min)"
        )
        self.status_var.set(
            f"time source: {reading.quality.value}"
            + (f"  ·  holdover {reading.holdover_days:.1f} d" if not self.gps_on.get() else "")
            + (f"\n⚠ POWER: {state_name.upper()}" if state_name != "normal" else "")
            + ("  — device would render 'sleeping' face" if state_name == HIBERNATE else "")
        )
        spec = self.navigator.current
        home = " (home)" if spec.is_default else ""
        self.face_var.set(f"showing:  {spec.title_en} · {spec.title_th}{home}")

        d = self.harness.display
        self.refresh_var.set(
            f"refreshes: {d.full_refreshes} full · {d.partial_refreshes} partial\n"
            f"partials since last full: {d.partials_since_full}"
        )

    def run(self) -> None:
        self.root.mainloop()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coucal Clock desktop simulator")
    parser.add_argument("--config", default="config/unit-01.toml", help="unit TOML path")
    args = parser.parse_args(argv)
    config = UnitConfig.load(args.config)
    Simulator(config).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
