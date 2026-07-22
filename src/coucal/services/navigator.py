"""Which face is showing, and what the brass button does to it.

The registry knows what faces *exist* and how they are ordered; this service holds the
one piece of mutable state that goes with it — which one is currently on the glass.

Behaviour, as specified:

    short press  ->  next face within the current category
    long press   ->  first face of the next category
    90 s idle    ->  return to the default face

The auto-return matters more than it looks. The clock spends its life showing face 0 to
a courtyard; a visitor who presses the button and walks away must not leave it parked on
the Babylonian dial forever. Returning home is what makes the button safe to offer.

**The time-base contract.** Every ``now`` passed in must be the *human's* clock — the
seconds a person actually experienced. On the device that is simply the RTC. In the
simulator it must be the wall clock, never the virtual timeline: warping the almanac
forward a month is thirty days of sky and zero seconds of person, and conflating the
two booted reviewers back to the home face every time they stepped the calendar. Timed
behaviours each obey exactly one clock — the sky's (almanac, coucal calls) or the
human's (interaction, auto-return) — and this service is on the human side.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..faces import registry

# How long a face stays up after the last press before the clock returns home.
AUTO_RETURN = timedelta(seconds=90)


@dataclass
class Navigator:
    """Tracks the visible face. Pure logic — it never touches hardware or draws."""

    current_key: str = ""
    last_interaction: datetime | None = None

    def __post_init__(self) -> None:
        if not self.current_key:
            self.current_key = registry.default_face().key

    @property
    def current(self):
        """The live face spec to render.

        Falls back to the default if the current key ever names a face that is not live
        — which can happen if a face is removed between releases while a card carries
        older state.
        """
        try:
            spec = registry.get(self.current_key)
        except KeyError:
            spec = registry.default_face()
            self.current_key = spec.key
            return spec
        if spec.status != registry.LIVE:
            spec = registry.default_face()
            self.current_key = spec.key
        return spec

    # --- the button --------------------------------------------------------
    def short_press(self, now: datetime) -> None:
        """Next face within the current category."""
        self.current_key = registry.next_face(self.current_key).key
        self.last_interaction = now

    def long_press(self, now: datetime) -> None:
        """First face of the next category."""
        self.current_key = registry.next_category(self.current_key).key
        self.last_interaction = now

    # --- going home --------------------------------------------------------
    def tick(self, now: datetime) -> bool:
        """Return home if the idle window has elapsed. True if the face changed."""
        if self.last_interaction is None:
            return False
        if now - self.last_interaction < AUTO_RETURN:
            return False
        self.last_interaction = None
        home = registry.default_face().key
        if self.current_key != home:
            self.current_key = home
            return True
        return False

    def go_home(self) -> None:
        self.current_key = registry.default_face().key
        self.last_interaction = None
