"""THE REPAIR CONTRACT — the boundary between this clock's mind and its body.

*If you are reading this file in order to bring a dead clock back to life, you are in
the right place, and you do not need to read anything else.*

Everything the system needs from the physical world is expressed below as nine
``typing.Protocol`` contracts plus a few frozen data types. The almanac, the calendars,
the display faces, and the coucal's dawn schedule depend only on these names. They
cannot tell whether they are running on a Raspberry Pi or on a laptop simulator,
because that is the only difference these nine contracts hide.

**To port this clock to hardware that did not exist when it was built:** implement
these nine Protocols against whatever parts you have, and assemble them into a ``HAL``
(bottom of this file). Nothing else in the repository needs to change. You do not need
to understand the Thai lunisolar calendar, the Lahiri ayanamsa, or e-ink refresh
budgets. Develop and test your implementation on a desk against the existing test
suite before you open the case — the tests run entirely without hardware.

The original 2026 implementations are your worked examples:
    ``hal/real/``  — Raspberry Pi Zero 2 W, Waveshare 10.3" IT8951, DS3231, INA219
    ``hal/sim/``   — desktop fakes, and the reference for expected behaviour

Units and conventions are stated on each contract below. Where a unit is given, honour
it exactly; the almanac assumes it. See ``docs/REPAIR.md`` for the physical side —
connector map, service panel, spares drawer.

Data flows in one direction: sensors report facts (time, position, power, button), the
compositor pushes a framebuffer, and actuators (audio, automaton) are commanded.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

# --------------------------------------------------------------------------- #
# Data types — plain, frozen, hardware-agnostic facts.
# --------------------------------------------------------------------------- #


class TimeQuality(Enum):
    """How much to trust the current time. Drives the time-confidence glyph."""

    GPS = "gps"  # live satellite fix — authoritative
    RTC = "rtc"  # DS3231 holdover — good, drifts ~2 min/year
    RTC_STALE = "stale"  # holdover beyond the configured warning horizon
    UNKNOWN = "unknown"  # no trustworthy source (cold boot, no RTC, no GPS)


@dataclass(frozen=True)
class TimeReading:
    """A civil-time reading with provenance. ``utc`` is always timezone-aware UTC."""

    utc: datetime
    quality: TimeQuality
    holdover_days: float = 0.0  # time since last GPS discipline, in days


@dataclass(frozen=True)
class Position:
    """Topocentric observer location. Fixed after install; GPS confirms it."""

    latitude: float  # degrees, +north
    longitude: float  # degrees, +east
    elevation_m: float
    has_fix: bool = True


@dataclass(frozen=True)
class PowerReading:
    """A snapshot from the INA219 battery/panel telemetry."""

    battery_volts: float
    battery_amps: float  # +charging, -discharging
    panel_volts: float
    panel_amps: float

    @property
    def battery_watts(self) -> float:
        return self.battery_volts * self.battery_amps


class RefreshMode(Enum):
    """E-ink refresh strategy. Partial is cheap but ghosts; full clears ghosting."""

    PARTIAL = "partial"
    FULL = "full"


class ButtonEvent(Enum):
    NONE = "none"
    PRESS = "press"


# --------------------------------------------------------------------------- #
# Sensor Protocols — the clock reads the world.
# --------------------------------------------------------------------------- #


@runtime_checkable
class TimeSource(Protocol):
    """Arbitrated civil time. Real impl fuses GPS > RTC; sim provides time-warp.

    CONTRACT
      * ``now()`` returns a timezone-aware UTC datetime. Never naive, never local time.
      * Must not jump backwards during normal operation; the compositor and the voice
        scheduler both assume monotonic civil time between wakes.
      * Report quality honestly. A confident wrong time is the worst failure this clock
        can have — prefer ``TimeQuality.UNKNOWN`` over a guess.
      * 2026 build: u-blox NEO-M8N over UART for the fix; DS3231 over I²C for holdover
        (drifts roughly 2 minutes per year). Indoor fixes may be marginal — degrading to
        RTC is expected behaviour, not an error.
    """

    def now(self) -> TimeReading: ...

    def discipline_rtc(self, utc: datetime) -> None:
        """Push an authoritative time into the holdover RTC (GPS -> DS3231)."""


@runtime_checkable
class PositionSource(Protocol):
    """Observer position. Stationary device: usually the configured fix, GPS-confirmed."""

    def position(self) -> Position: ...


@runtime_checkable
class PowerTelemetry(Protocol):
    """Battery/panel electrical readings for the steward's budget enforcement.

    CONTRACT
      * Volts are DC volts at the battery terminals; amps are positive when CHARGING
        and negative when discharging. The load-shedding thresholds in ``unit.toml``
        are absolute battery volts, so a substitute chemistry needs those retuned.
      * 2026 build: INA219 over I²C, 12.8 V nominal LiFePO4 (~10 Ah) fed by roughly a
        30 W panel through an MPPT controller. Working band is about 12.0–13.4 V.
      * If you cannot measure current, report 0.0 amps rather than inventing a value —
        the steward degrades to voltage-only decisions safely.
    """

    def read(self) -> PowerReading: ...


@runtime_checkable
class Button(Protocol):
    """The single brass button.

    CONTRACT
      * Edge-triggered and debounced in the implementation: one physical press yields
        exactly one ``PRESS``, and ``poll()`` consumes it. Holding the button down must
        not produce a stream of events.
      * Presses that arrive while the board is asleep should be latched and delivered on
        the next poll — otherwise a visitor's press is silently lost.
      * Short press cycles faces; the display returns to the default face after 90 s.
    """

    def poll(self) -> ButtonEvent: ...


# --------------------------------------------------------------------------- #
# Actuator Protocols — the clock acts on the world.
# --------------------------------------------------------------------------- #


@runtime_checkable
class Display(Protocol):
    """The 10.3" e-ink panel: 1872x1404, 16 grey levels.

    CONTRACT
      * ``framebuffer`` is exactly ``width * height`` bytes, one per pixel, row-major
        from the top-left. 0 is black, 255 is white. The panel quantises to 16 levels.
      * ``region`` is ``(x, y, w, h)`` and limits a PARTIAL refresh to that box.
      * A partial refresh is fast and cheap but leaves faint residue of prior frames;
        a full refresh is slow and visibly flashes, but clears that ghosting. The
        compositor budgets these — honour the distinction rather than promoting every
        refresh to full.
      * The image MUST persist with no power. This is the whole reason the clock can be
        solar, and the reason the heartbeat exists: a dead clock still shows a plausible
        face, so liveness has to be visible in the image itself.
      * 2026 build: Waveshare 10.3" with IT8951 controller over SPI. Partial refresh
        well under a second; full refresh a few seconds.
    """

    width: int
    height: int

    def push(
        self,
        framebuffer: bytes,
        mode: RefreshMode = RefreshMode.PARTIAL,
        region: tuple[int, int, int, int] | None = None,
    ) -> None: ...

    def clear(self) -> None:
        """Full white clear — removes accumulated ghosting."""


@runtime_checkable
class AudioSink(Protocol):
    """Plays a coucal field recording through the case-bonded exciter."""

    def play(self, sound_path: str, volume: float) -> None: ...

    def stop(self) -> None: ...

    @property
    def is_playing(self) -> bool: ...


@runtime_checkable
class Automaton(Protocol):
    """The carved coucal's door + motion. Driven only during a call."""

    def perform(self, call_kind: str) -> None:
        """Open door, animate bird for the given call kind, return to rest."""

    def rest(self) -> None:
        """Ensure the bird is stowed and the door is closed."""


# --------------------------------------------------------------------------- #
# System Protocols — keeping the device alive.
# --------------------------------------------------------------------------- #


@runtime_checkable
class Watchdog(Protocol):
    """Hardware watchdog. Must be fed or the board resets — proves liveness."""

    def feed(self) -> None: ...


@runtime_checkable
class PowerController(Protocol):
    """Scheduled duty-cycling (Witty Pi-class). Sleeps the board until a wake time."""

    def sleep_until(self, wake_utc: datetime) -> None: ...

    def request_shutdown(self) -> None:
        """Brownout-safe clean shutdown. The 'sleeping' face is rendered first."""


# --------------------------------------------------------------------------- #
# The bundle handed to the application.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class HAL:
    """Everything the application needs from the physical world, in one place."""

    time: TimeSource
    position: PositionSource
    power: PowerTelemetry
    button: Button
    display: Display
    audio: AudioSink
    automaton: Automaton
    watchdog: Watchdog
    power_controller: PowerController
    kind: str  # "sim" | "real" — for logging and self-test
