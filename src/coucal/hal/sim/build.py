"""Assemble a complete simulated HAL, sharing one virtual timeline.

Returns a ``SimHarness`` that both *is* usable as a HAL (``.hal``) and exposes the
underlying fakes so the simulator GUI (and tests) can drive the world: scrub time,
press the button, drain the battery, read the framebuffer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ..interfaces import HAL
from .actuators import SimAudioSink, SimAutomaton, SimPowerController, SimWatchdog
from .display import SimDisplay
from .sensors import SimButton, SimPositionSource, SimPowerTelemetry, SimTimeSource
from .timeline import SimTimeline


@dataclass
class SimHarness:
    timeline: SimTimeline
    time: SimTimeSource
    position: SimPositionSource
    power: SimPowerTelemetry
    button: SimButton
    display: SimDisplay
    audio: SimAudioSink
    automaton: SimAutomaton
    watchdog: SimWatchdog
    power_controller: SimPowerController

    @property
    def hal(self) -> HAL:
        return HAL(
            time=self.time,
            position=self.position,
            power=self.power,
            button=self.button,
            display=self.display,
            audio=self.audio,
            automaton=self.automaton,
            watchdog=self.watchdog,
            power_controller=self.power_controller,
            kind="sim",
        )


def build_sim_harness(
    *,
    latitude: float,
    longitude: float,
    elevation_m: float,
    start_utc: datetime | None = None,
    holdover_warn_days: int = 30,
    ghosting: bool = True,
) -> SimHarness:
    # A neutral, deterministic default epoch for the desktop: 2026-07-19 07:00 ICT.
    if start_utc is None:
        start_utc = datetime(2026, 7, 19, 0, 0, tzinfo=UTC)
    timeline = SimTimeline(start_utc)
    return SimHarness(
        timeline=timeline,
        time=SimTimeSource(timeline, holdover_warn_days=holdover_warn_days),
        position=SimPositionSource(latitude, longitude, elevation_m),
        power=SimPowerTelemetry(),
        button=SimButton(),
        display=SimDisplay(ghosting=ghosting),
        audio=SimAudioSink(),
        automaton=SimAutomaton(),
        watchdog=SimWatchdog(),
        power_controller=SimPowerController(timeline),
    )
