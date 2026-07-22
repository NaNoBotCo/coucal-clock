"""Fake audio, automaton, watchdog, and power controller.

None of these make sound or move a servo; they record what *would* happen, which is
exactly what the voice-scheduling and power tests need to assert against. The fake
``PowerController`` is wired to the ``SimTimeline`` so that a duty-cycle sleep
fast-forwards virtual time instead of blocking the desktop.
"""

from __future__ import annotations

from datetime import datetime

from .timeline import SimTimeline


class SimAudioSink:
    def __init__(self) -> None:
        self._playing = False
        self.log: list[tuple[str, float]] = []  # (sound_path, volume)

    def play(self, sound_path: str, volume: float) -> None:
        self._playing = True
        self.log.append((sound_path, volume))

    def stop(self) -> None:
        self._playing = False

    @property
    def is_playing(self) -> bool:
        return self._playing


class SimAutomaton:
    def __init__(self) -> None:
        self.log: list[str] = []
        self.at_rest = True

    def perform(self, call_kind: str) -> None:
        self.at_rest = False
        self.log.append(call_kind)
        self.at_rest = True  # the whole motion completes within the call window

    def rest(self) -> None:
        self.at_rest = True


class SimWatchdog:
    def __init__(self) -> None:
        self.feeds = 0
        self.last_feed_utc: datetime | None = None

    def feed(self) -> None:
        self.feeds += 1


class SimPowerController:
    """Duty-cycle sleeps advance the shared timeline instead of blocking."""

    def __init__(self, timeline: SimTimeline) -> None:
        self._t = timeline
        self.sleeps: list[datetime] = []
        self.shutdown_requested = False

    def sleep_until(self, wake_utc: datetime) -> None:
        self.sleeps.append(wake_utc)
        # Fast-forward: the board "wakes" exactly at the scheduled time.
        if wake_utc > self._t.now():
            self._t.set(wake_utc)

    def request_shutdown(self) -> None:
        self.shutdown_requested = True
