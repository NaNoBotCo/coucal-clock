"""Sun and moon — the foundation every other calendar in this clock stands on.

Pure functions of a :class:`~coucal.almanac.ephemeris.Sky` and a moment. No clock, no
hardware, no I/O.

This module matters beyond its own face: the coucal calls at **computed civil dawn and
dusk**, so the bird's voice drifts through the year exactly as a living coucal's does.
The Thai and Lanna calendars need lunar phase; the Hellenistic hours need true sunrise
and sunset; the Babylonian month needs the moon. All of it comes from here.

Conventions, stated once:
  * Every returned datetime is timezone-aware and in the observer's local zone.
  * A "day" means a local civil day, midnight to midnight at the temple.
  * Sunrise/sunset use the standard −0.8333° horizon (upper limb plus refraction),
    which is what published almanacs and newspapers print.
  * Twilight boundaries are the standard −6° / −12° / −18° solar depressions.
  * Any event that does not occur on a given day is ``None`` rather than an error.
    At Chiang Mai's latitude that is essentially never for the sun, but the moon
    routinely skips a rise or set, and the code must not pretend otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from skyfield import almanac

from .ephemeris import Sky

# Standard almanac horizon for the sun: upper limb touching, corrected for refraction.
SUN_HORIZON_DEG = -0.8333

# Solar depression angles defining each twilight.
CIVIL_DEG = -6.0
NAUTICAL_DEG = -12.0
ASTRONOMICAL_DEG = -18.0

PHASE_NAMES = (
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
)


@dataclass(frozen=True)
class SolarDay:
    """Everything the sun does on one local civil day."""

    day: date
    sunrise: datetime | None
    sunset: datetime | None
    solar_noon: datetime | None
    civil_dawn: datetime | None
    civil_dusk: datetime | None
    nautical_dawn: datetime | None
    nautical_dusk: datetime | None
    astronomical_dawn: datetime | None
    astronomical_dusk: datetime | None

    @property
    def day_length(self) -> timedelta | None:
        if self.sunrise is None or self.sunset is None:
            return None
        return self.sunset - self.sunrise


@dataclass(frozen=True)
class MoonState:
    """The moon at one instant, plus the next two phase events."""

    when: datetime
    phase_angle_deg: float  # 0 = new, 90 = first quarter, 180 = full
    illumination: float  # 0.0 - 1.0 of the disc lit
    phase_name: str
    moonrise: datetime | None
    moonset: datetime | None
    next_new_moon: datetime
    next_full_moon: datetime

    @property
    def is_waxing(self) -> bool:
        return self.phase_angle_deg < 180.0


def _local(sky: Sky, t) -> datetime:
    return t.utc_datetime().astimezone(sky.observer.tz)


def _first_or_none(sky: Sky, times, flags=None) -> datetime | None:
    """First event in the window, or None if it never actually happened.

    Skyfield's rise/set finders return a companion boolean per time saying whether the
    event genuinely occurred (as opposed to the body never crossing the horizon). We
    honour it rather than silently reporting a fictitious moonrise.
    """
    if len(times) == 0:
        return None
    if flags is not None:
        for t, ok in zip(times, flags, strict=False):
            if ok:
                return _local(sky, t)
        return None
    return _local(sky, times[0])


def sun_day(sky: Sky, day: date) -> SolarDay:
    """Sunrise, sunset, solar noon and all three twilights for one local day."""
    start, end = sky.local_day_bounds(day)
    t0, t1 = sky.t(start), sky.t(end)

    rise_t, rise_ok = almanac.find_risings(
        sky.place, sky.sun, t0, t1, horizon_degrees=SUN_HORIZON_DEG
    )
    set_t, set_ok = almanac.find_settings(
        sky.place, sky.sun, t0, t1, horizon_degrees=SUN_HORIZON_DEG
    )

    transit_t = almanac.find_transits(sky.place, sky.sun, t0, t1)
    solar_noon = _local(sky, transit_t[0]) if len(transit_t) else None

    def twilight(depression: float) -> tuple[datetime | None, datetime | None]:
        """(morning, evening) crossings of a given solar depression."""
        up, up_ok = almanac.find_risings(sky.place, sky.sun, t0, t1, horizon_degrees=depression)
        down, down_ok = almanac.find_settings(
            sky.place, sky.sun, t0, t1, horizon_degrees=depression
        )
        return _first_or_none(sky, up, up_ok), _first_or_none(sky, down, down_ok)

    civil_dawn, civil_dusk = twilight(CIVIL_DEG)
    naut_dawn, naut_dusk = twilight(NAUTICAL_DEG)
    astro_dawn, astro_dusk = twilight(ASTRONOMICAL_DEG)

    return SolarDay(
        day=day,
        sunrise=_first_or_none(sky, rise_t, rise_ok),
        sunset=_first_or_none(sky, set_t, set_ok),
        solar_noon=solar_noon,
        civil_dawn=civil_dawn,
        civil_dusk=civil_dusk,
        nautical_dawn=naut_dawn,
        nautical_dusk=naut_dusk,
        astronomical_dawn=astro_dawn,
        astronomical_dusk=astro_dusk,
    )


def _phase_name(angle_deg: float) -> str:
    """Name the phase from the sun-moon elongation.

    The four exact phases occupy narrow windows either side of their exact angle; the
    crescents and gibbous phases fill the rest. A clock should say "Full Moon" on the
    night it is full, not "Waxing Gibbous" at 179.5°.
    """
    a = angle_deg % 360.0
    edge = 7.0  # degrees either side counted as the named phase
    if a < edge or a >= 360.0 - edge:
        return "New Moon"
    if abs(a - 90.0) < edge:
        return "First Quarter"
    if abs(a - 180.0) < edge:
        return "Full Moon"
    if abs(a - 270.0) < edge:
        return "Last Quarter"
    if a < 90.0:
        return "Waxing Crescent"
    if a < 180.0:
        return "Waxing Gibbous"
    if a < 270.0:
        return "Waning Gibbous"
    return "Waning Crescent"


def moon_state(sky: Sky, when: datetime) -> MoonState:
    """Phase, illumination, rise/set for the local day, and the next new and full moons."""
    t = sky.t(when)
    angle = almanac.moon_phase(sky.eph, t).degrees.item()
    illumination = float(almanac.fraction_illuminated(sky.eph, "moon", t))

    local_day = when.astimezone(sky.observer.tz).date()
    start, end = sky.local_day_bounds(local_day)
    t0, t1 = sky.t(start), sky.t(end)
    rise_t, rise_ok = almanac.find_risings(sky.place, sky.moon, t0, t1)
    set_t, set_ok = almanac.find_settings(sky.place, sky.moon, t0, t1)

    # A synodic month is ~29.53 days; 40 days guarantees we catch the next of each.
    search_end = sky.t(when + timedelta(days=40))
    phase_times, phase_kinds = almanac.find_discrete(t, search_end, almanac.moon_phases(sky.eph))

    next_new = next_full = None
    for pt, kind in zip(phase_times, phase_kinds, strict=False):
        if kind == 0 and next_new is None:
            next_new = _local(sky, pt)
        elif kind == 2 and next_full is None:
            next_full = _local(sky, pt)
        if next_new and next_full:
            break

    if next_new is None or next_full is None:  # pragma: no cover - 40 days always suffices
        raise RuntimeError("no new/full moon found within 40 days — ephemeris exhausted?")

    return MoonState(
        when=when.astimezone(sky.observer.tz),
        phase_angle_deg=angle,
        illumination=illumination,
        phase_name=_phase_name(angle),
        moonrise=_first_or_none(sky, rise_t, rise_ok),
        moonset=_first_or_none(sky, set_t, set_ok),
        next_new_moon=next_new,
        next_full_moon=next_full,
    )


def next_coucal_calls(sky: Sky, after: datetime) -> tuple[datetime, datetime]:
    """The next civil dawn and civil dusk at or after ``after``.

    This is what makes the bird alive rather than mechanical: the call time drifts
    through the year with the real sun, as a coucal's does.

    Returns ``(next_dawn, next_dusk)`` — each the next occurrence of that event
    independently. Around midday the next dusk is today and the next dawn is tomorrow,
    so ``next_dusk`` may well be earlier than ``next_dawn``. That is correct: they are
    two separate upcoming calls, not a matched pair.
    """
    local_day = after.astimezone(sky.observer.tz).date()
    next_dawn: datetime | None = None
    next_dusk: datetime | None = None

    for offset in range(4):
        day = sun_day(sky, local_day + timedelta(days=offset))
        if next_dawn is None and day.civil_dawn and day.civil_dawn >= after:
            next_dawn = day.civil_dawn
        if next_dusk is None and day.civil_dusk and day.civil_dusk >= after:
            next_dusk = day.civil_dusk
        if next_dawn and next_dusk:
            return next_dawn, next_dusk

    raise RuntimeError("could not find the next dawn and dusk within four days")
