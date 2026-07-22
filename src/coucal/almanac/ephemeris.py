"""Loading the ephemeris and describing the observer.

This is the **only** module in ``almanac`` that touches the disk. Everything else takes
a ready-made :class:`Sky` and is a pure function of it plus a moment in time. Keeping
the I/O in one small place is what lets the rest of the almanac be exhaustively golden-
tested and rendered at any date in seconds.

Offline by construction: the kernel is read from the bundled file with ``load_file``,
and the timescale uses Skyfield's built-in leap-second table. Nothing here reaches the
network, at build time or ever.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from skyfield.api import load, load_file, wgs84

# data/ephemeris/de440.bsp, relative to this file (src/coucal/almanac/ephemeris.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EPHEMERIS = _REPO_ROOT / "data" / "ephemeris" / "de440.bsp"


@dataclass(frozen=True)
class Observer:
    """Where the clock stands. Fixed at installation."""

    latitude: float  # degrees, +north
    longitude: float  # degrees, +east
    elevation_m: float = 0.0
    timezone_name: str = "Asia/Bangkok"

    @property
    def tz(self):
        """Temple-local timezone.

        ICT is a fixed UTC+7 with no DST; fall back to that if the zoneinfo database
        is unavailable, so a minimal posterity install still keeps correct civil time.
        """
        try:
            from zoneinfo import ZoneInfo

            return ZoneInfo(self.timezone_name)
        except Exception:
            return timezone(timedelta(hours=7))


class Sky:
    """A loaded ephemeris bound to one observer.

    Construct once and reuse: loading the kernel is the expensive part, and the clock
    holds a single instance for its whole life.
    """

    def __init__(self, observer: Observer, ephemeris_path: str | Path | None = None) -> None:
        self.observer = observer
        self.ts = load.timescale()  # built-in leap seconds; no download
        self.path = Path(ephemeris_path or DEFAULT_EPHEMERIS)
        if not self.path.exists():
            raise FileNotFoundError(
                f"Ephemeris not found at {self.path}. "
                "Run scripts/fetch_data.sh (see data/ephemeris/PROVENANCE.md)."
            )
        self.eph = load_file(str(self.path))
        self.earth = self.eph["earth"]
        self.sun = self.eph["sun"]
        self.moon = self.eph["moon"]
        self.topos = wgs84.latlon(
            observer.latitude, observer.longitude, elevation_m=observer.elevation_m
        )
        # The observer as a body in space — what rise/set and transit calculations need.
        self.place = self.earth + self.topos

    # --- time helpers ------------------------------------------------------
    def t(self, dt: datetime):
        """A Skyfield time from a timezone-aware datetime."""
        if dt.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return self.ts.from_datetime(dt)

    def local_day_bounds(self, day) -> tuple[datetime, datetime]:
        """The UTC instants bracketing a local civil day (local midnight to midnight)."""
        tz = self.observer.tz
        start = datetime(day.year, day.month, day.day, tzinfo=tz)
        return start, start + timedelta(days=1)

    # --- honest limits -----------------------------------------------------
    def span(self) -> tuple[datetime, datetime]:
        """The real coverage of the loaded kernel, measured from the file itself.

        Feeds the clock's own account of what it does and does not know. Never quote a
        span from documentation — read it from the data.
        """
        seg = self.eph.spk.segments[0]
        a = self.ts.tdb_jd(seg.start_jd).utc_datetime()
        b = self.ts.tdb_jd(seg.end_jd).utc_datetime()
        return a, b

    def covers(self, dt: datetime) -> bool:
        a, b = self.span()
        return a <= dt <= b


@lru_cache(maxsize=4)
def _cached_sky(lat: float, lon: float, elev: float, tzname: str, path: str | None) -> Sky:
    return Sky(Observer(lat, lon, elev, tzname), path)


def get_sky(observer: Observer, ephemeris_path: str | Path | None = None) -> Sky:
    """Shared :class:`Sky` for an observer — avoids re-reading a 114 MB kernel."""
    return _cached_sky(
        observer.latitude,
        observer.longitude,
        observer.elevation_m,
        observer.timezone_name,
        str(ephemeris_path) if ephemeris_path else None,
    )


def ephemeris_span(ephemeris_path: str | Path | None = None) -> tuple[datetime, datetime]:
    """Coverage of the bundled kernel, without needing an observer."""
    sky = Sky(Observer(0.0, 0.0), ephemeris_path)
    return sky.span()
