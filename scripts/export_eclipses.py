#!/usr/bin/env python3
"""Export an exact eclipse table from DE440, for the web moon dial to draw.

WHY A TABLE AND NOT A FORMULA
    The web page carries a compact series for the moon's elongation, which is fine
    for a phase (0.4 deg) but nowhere near good enough to decide whether the moon
    actually enters the Earth's umbra — that turns on a fraction of a degree of
    ecliptic latitude, and a borderline call would be wrong on the page while
    looking perfectly confident. So the eclipses are computed ONCE, here, from the
    same JPL DE440 ephemeris the clock itself reads, and shipped as data.

    Skyfield's ``eclipselib.lunar_eclipses`` is the authority for the lunar ones;
    it returns the shadow geometry in radians, which is exactly what a drawing
    needs. Solar eclipses have no global finder in Skyfield, so those are computed
    the way they are actually experienced: TOPOCENTRICALLY FROM THE TEMPLE, by
    tracking the sun-moon separation across each new moon and asking whether the
    discs overlap while the sun is above the horizon. That is a narrower claim than
    "a solar eclipse occurs" — and it is the true and useful one for this audience.

Run:  PYTHONPATH=src .venv/bin/python scripts/export_eclipses.py --out <path.json>
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
from skyfield import almanac, eclipselib
from skyfield.api import wgs84
from skyfield.framelib import ecliptic_frame

from coucal.almanac.ephemeris import Observer, get_sky

TEMPLE = Observer(18.85, 99.05, 320.0, "Asia/Bangkok")
SUN_RADIUS_KM = 695700.0
MOON_RADIUS_KM = 1737.4


def _ms(t) -> int:
    """Milliseconds since the Unix epoch — what JavaScript's Date wants."""
    return int(t.utc_datetime().timestamp() * 1000)


def lunar_table(sky, t0, t1, topos):
    """Every lunar eclipse in the span, with the shadow geometry needed to draw it."""
    times, kinds, details = eclipselib.lunar_eclipses(t0, t1, sky.eph)
    earth, moon, sun = sky.eph["earth"], sky.eph["moon"], sky.eph["sun"]
    place = earth + topos
    out = []
    for i, (t, kind) in enumerate(zip(times, kinds, strict=False)):
        r_moon = float(details["moon_radius_radians"][i])
        d_min = float(details["closest_approach_radians"][i]) / r_moon
        umbra = float(details["umbra_radius_radians"][i]) / r_moon
        penumbra = float(details["penumbra_radius_radians"][i]) / r_moon

        # How fast the shadow crosses, in moon-radii per hour, measured rather than
        # assumed: take the real separation an hour either side of greatest eclipse
        # and back out the transverse rate. The relative motion is near enough
        # linear over the few hours an eclipse lasts.
        rates = []
        for dt_h in (-1.0, 1.0):
            tt = sky.ts.from_datetime(t.utc_datetime() + timedelta(hours=dt_h))
            m = earth.at(tt).observe(moon).apparent()
            s = earth.at(tt).observe(sun).apparent()
            sep = m.separation_from(s).radians          # moon-to-sun angle
            sep_shadow = (math.pi - sep) / r_moon        # ...to the ANTI-sun point
            rates.append(math.sqrt(max(sep_shadow**2 - d_min**2, 0.0)) / abs(dt_h))
        rate = sum(rates) / len(rates)

        # Is the moon actually up over the wat when it happens? A lunar eclipse is
        # only an event for people who can see it.
        alt = place.at(t).observe(moon).apparent().altaz()[0].degrees

        out.append({
            "t": _ms(t),
            "k": "lunar",
            "type": eclipselib.LUNAR_ECLIPSES[kind],
            "mag": round(float(details["umbral_magnitude"][i]), 3),
            "d": round(d_min, 4),
            "u": round(umbra, 4),
            "p": round(penumbra, 4),
            "rate": round(rate, 4),
            "alt": round(float(alt), 1),
        })
    return out


def solar_table(sky, start: datetime, end: datetime, topos):
    """Solar eclipses AS SEEN FROM THE TEMPLE — the only honest local claim.

    At each new moon, walk the hours around it and find the least angular distance
    between the sun's and moon's centres from this spot on the ground. The discs
    overlap when that falls below the sum of their apparent radii.
    """
    ts, earth = sky.ts, sky.eph["earth"]
    moon, sun = sky.eph["moon"], sky.eph["sun"]
    place = earth + topos
    t0, t1 = ts.from_datetime(start), ts.from_datetime(end)
    times, kinds = almanac.find_discrete(t0, t1, almanac.moon_phases(sky.eph))
    news = [t for t, k in zip(times, kinds, strict=False) if k == 0]

    out = []
    for t_new in news:
        base = t_new.utc_datetime()
        # +/- 5 h at one-minute steps: wider than any eclipse, fine enough not to
        # skip the minimum.
        grid = ts.from_datetimes([base + timedelta(minutes=m) for m in range(-300, 301)])
        astro_m = place.at(grid).observe(moon).apparent()
        astro_s = place.at(grid).observe(sun).apparent()
        sep = astro_m.separation_from(astro_s).radians
        r_s = np.arcsin(SUN_RADIUS_KM / astro_s.distance().km)
        r_m = np.arcsin(MOON_RADIUS_KM / astro_m.distance().km)
        gap = sep - (r_s + r_m)                      # < 0 means the discs overlap
        i = int(np.argmin(gap))
        if gap[i] >= 0:
            continue                                  # no eclipse here
        alt = astro_s.altaz()[0].degrees[i]
        if alt < -0.5:
            continue                                  # sun below the horizon: not ours
        # Standard eclipse magnitude: the fraction of the SUN'S DIAMETER covered.
        mag = float((r_s[i] + r_m[i] - sep[i]) / (2 * r_s[i]))
        ratio = float(r_m[i] / r_s[i])
        if sep[i] <= abs(r_s[i] - r_m[i]):
            kind = "Total" if ratio >= 1.0 else "Annular"
        else:
            kind = "Partial"
        out.append({
            "t": _ms(grid[i]),
            "k": "solar",
            "type": kind,
            "mag": round(mag, 3),
            "alt": round(float(alt), 1),
        })
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="JSON file to write")
    ap.add_argument("--from-year", type=int, default=2024)
    ap.add_argument("--to-year", type=int, default=2076)
    args = ap.parse_args(argv)

    sky = get_sky(TEMPLE)
    topos = wgs84.latlon(TEMPLE.latitude, TEMPLE.longitude, TEMPLE.elevation_m)
    start = datetime(args.from_year, 1, 1, tzinfo=UTC)
    end = datetime(args.to_year, 1, 1, tzinfo=UTC)
    t0, t1 = sky.ts.from_datetime(start), sky.ts.from_datetime(end)

    lunar = lunar_table(sky, t0, t1, topos)
    solar = solar_table(sky, start, end, topos)
    rows = sorted(lunar + solar, key=lambda r: r["t"])

    payload = {
        "source": "JPL DE440 via Skyfield eclipselib (lunar) and topocentric "
                  "sun-moon separation (solar, as seen from the temple)",
        "site": {"lat": TEMPLE.latitude, "lon": TEMPLE.longitude,
                 "name": "San Sai, Chiang Mai"},
        "span": [args.from_year, args.to_year],
        "eclipses": rows,
    }
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")

    up = sum(1 for r in lunar if r["alt"] > 0)
    print(f"  lunar: {len(lunar)}  ({up} with the moon above the horizon at the wat)")
    print(f"  solar: {len(solar)} visible from the wat")
    print(f"  {len(rows)} rows, {out.stat().st_size / 1024:.1f} KB → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
