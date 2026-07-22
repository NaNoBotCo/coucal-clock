"""Fake sensors: time, position, power, button — all reading from scriptable state.

The power model is deliberately simple but honest enough to exercise the steward's
load-shedding ladder: a battery voltage that a weather/solar profile can drive down
over simulated days, and a button whose presses the GUI (or a test) can enqueue.
"""

from __future__ import annotations

from collections import deque

from ..interfaces import (
    ButtonEvent,
    Position,
    PowerReading,
    TimeQuality,
    TimeReading,
)
from .timeline import SimTimeline


class SimTimeSource:
    """TimeSource backed by a SimTimeline. Quality reflects the timeline's GPS state."""

    def __init__(self, timeline: SimTimeline, holdover_warn_days: int = 30) -> None:
        self._t = timeline
        self._warn = holdover_warn_days
        self.disciplined: list = []  # record of discipline_rtc calls, for tests

    def now(self) -> TimeReading:
        if self._t.gps_available:
            quality = TimeQuality.GPS
        elif self._t.holdover_days > self._warn:
            quality = TimeQuality.RTC_STALE
        else:
            quality = TimeQuality.RTC
        return TimeReading(
            utc=self._t.now(),
            quality=quality,
            holdover_days=0.0 if self._t.gps_available else self._t.holdover_days,
        )

    def discipline_rtc(self, utc) -> None:
        self.disciplined.append(utc)


class SimPositionSource:
    def __init__(self, latitude: float, longitude: float, elevation_m: float) -> None:
        self._pos = Position(latitude, longitude, elevation_m, has_fix=True)

    def position(self) -> Position:
        return self._pos


class SimPowerTelemetry:
    """A scriptable battery. Set ``battery_volts`` directly, or run a profile.

    ``charge_rate_v_per_hr`` lets a simulated day of sun/overcast move the voltage
    when the simulator advances virtual hours (call ``integrate``).
    """

    def __init__(self, battery_volts: float = 13.0) -> None:
        self.battery_volts = battery_volts
        self.battery_amps = 0.5
        self.panel_volts = 18.0
        self.panel_amps = 1.2
        # Positive when the sun is charging, negative during load-only overcast nights.
        self.charge_rate_v_per_hr = 0.0

    def integrate(self, hours: float) -> None:
        self.battery_volts = max(
            9.0, min(14.4, self.battery_volts + self.charge_rate_v_per_hr * hours)
        )

    def read(self) -> PowerReading:
        return PowerReading(
            battery_volts=self.battery_volts,
            battery_amps=self.battery_amps,
            panel_volts=self.panel_volts,
            panel_amps=self.panel_amps,
        )


class SimButton:
    """A queue of button events. The GUI or a test calls ``press`` to enqueue one."""

    def __init__(self) -> None:
        self._events: deque[ButtonEvent] = deque()

    def press(self) -> None:
        self._events.append(ButtonEvent.PRESS)

    def poll(self) -> ButtonEvent:
        return self._events.popleft() if self._events else ButtonEvent.NONE
