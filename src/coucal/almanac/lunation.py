"""The lunation gear — a durable monthly mechanism, re-datumed at every new moon.

The moon dial is driven by a single turning disc carrying two moons. This module is
that disc's arbor: it says how far the gear has turned, and it resets itself once a
month against the sky.

## The mechanism

    disc angle = 180 deg * parity  +  180 deg * (fraction through this lunation)

so the disc makes ONE FULL 360 deg TURN PER TWO LUNATIONS, which is the only rate
consistent with carrying two moons: one crosses the aperture this month, its partner
the next. ``parity`` is the lunation count modulo two, and it flips at each new moon.

## The monthly reset, and why it is not a time gear

At every true new moon the count increments and the fraction returns to zero — the gear
re-datums exactly, once a month, against a new-moon instant computed from the bundled
ephemeris. Nothing accumulates, so nothing drifts.

Within the month the fraction comes from the moon's **true elongation**, not from
elapsed time. That choice was measured rather than assumed. Across 25 lunations of
2026-2027 the synodic month varies from **29.284 to 29.814 days**, and a constant-rate
time gear re-synced only at new moon runs up to **10.65 degrees** out — 8.4 percentage
points of illumination, about 21 hours of phase. The dial's own geometry is good to
about 1 point, so a time gear would have been the dominant error by a factor of eight.
Driving the fraction from the elongation costs nothing and is exact.

The new-moon instants are still what make the gear *durable*: they fix the datum and the
parity, so a clock that has been dark for a year comes back knowing exactly which moon
should be in the window.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from skyfield import almanac

from .ephemeris import Sky

# A count has to start somewhere. Lunation parity is all the dial needs, so any fixed
# new moon will do as origin; this one is simply the first of the clock's design era.
EPOCH_NEW_MOON = datetime(2026, 1, 18, 19, 52)  # UTC, approximate; refined on load

MEAN_SYNODIC_DAYS = 29.530588


@dataclass(frozen=True)
class Lunation:
    """Where the gear stands, and the month it stands in."""

    number: int  # new moons since the epoch — increments once per month
    last_new: datetime
    next_new: datetime
    phase_angle_deg: float  # the moon's true elongation: 0 new, 180 full

    @property
    def length_days(self) -> float:
        return (self.next_new - self.last_new).total_seconds() / 86400.0

    @property
    def fraction(self) -> float:
        """How far through this lunation, from the true elongation. 0 at new."""
        return (self.phase_angle_deg % 360.0) / 360.0

    @property
    def parity(self) -> int:
        """Which of the disc's two moons is crossing the aperture this month."""
        return self.number % 2

    @property
    def disc_angle_deg(self) -> float:
        """The gear's rotation: 180 deg per lunation, a full turn every two."""
        return (180.0 * self.parity + 180.0 * self.fraction) % 360.0

    @property
    def age_days(self) -> float:
        """Days since the new moon that opened this lunation."""
        return self.fraction * self.length_days


def _new_moons_around(sky: Sky, when: datetime) -> tuple[datetime, datetime]:
    """The new moons bracketing ``when``. Searched wide enough to always find both."""
    ts = sky.ts
    t0 = ts.from_datetime(when - timedelta(days=MEAN_SYNODIC_DAYS * 1.6))
    t1 = ts.from_datetime(when + timedelta(days=MEAN_SYNODIC_DAYS * 1.6))
    times, kinds = almanac.find_discrete(t0, t1, almanac.moon_phases(sky.eph))
    news = [t.utc_datetime() for t, k in zip(times, kinds, strict=False) if k == 0]
    before = [d for d in news if d <= when]
    after = [d for d in news if d > when]
    if not before or not after:  # pragma: no cover - the window guarantees both
        raise RuntimeError(f"could not bracket {when} with new moons")
    return before[-1], after[0]


def lunation_at(sky: Sky, when: datetime) -> Lunation:
    """The state of the lunation gear at an instant.

    The count is taken from the elapsed mean lunations since the epoch, then corrected
    by the actual bracketing new moon — so it is exact and cannot drift, however long
    the clock has been asleep.
    """
    if when.tzinfo is None:
        raise ValueError("when must be timezone-aware")

    last_new, next_new = _new_moons_around(sky, when)

    # Count of new moons from the epoch to this one. Rounding a mean-lunation estimate
    # is safe: the mean is accurate to well under half a month over any span the
    # ephemeris covers, and we round to the nearest whole lunation.
    epoch = EPOCH_NEW_MOON.replace(tzinfo=last_new.tzinfo)
    elapsed = (last_new - epoch).total_seconds() / 86400.0
    number = round(elapsed / MEAN_SYNODIC_DAYS)

    angle = almanac.moon_phase(sky.eph, sky.ts.from_datetime(when)).degrees.item()
    return Lunation(
        number=number,
        last_new=last_new,
        next_new=next_new,
        phase_angle_deg=angle,
    )


def disc_angle_for_phase(phase_angle_deg: float, parity: int = 0) -> float:
    """The gear angle for a phase, without consulting the ephemeris.

    Useful for tests, for drawing a specimen dial, and for the simulator's time-warp,
    where the parity may be supplied directly.
    """
    return (180.0 * (parity % 2) + (phase_angle_deg % 360.0) / 2.0) % 360.0
