"""The application core: one wake cycle, and the headless entry point.

A wake cycle is intentionally tiny in Phase 0 — read time and power from the HAL,
build an immutable ``RenderState``, render the Phase 0 face, push it to the panel,
feed the watchdog. Later phases layer the almanac, the eight faces, voice, and the
steward on top of this same shape. The interactive simulator (``coucal.sim``) calls
``render_cycle`` repeatedly with time-warp; the real device loop arrives in Phase 5.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from .config import UnitConfig
from .faces.base import RenderState
from .hal.interfaces import HAL, RefreshMode

# A full refresh every this many partial refreshes clears accumulated ghosting.
FULL_REFRESH_EVERY = 24

# Which face was last pushed, so a change can force a full refresh.
_last_face: dict[str, str] = {}


def _local_tz(name: str):
    """Temple-local timezone. ICT is a fixed UTC+7 with no DST; fall back to that
    if the zoneinfo database is unavailable (keeps posterity installs robust)."""
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo(name)
    except Exception:
        return timezone(timedelta(hours=7))


def _almanac(config: UnitConfig, local_time: datetime):
    """Sun, moon, and the next two coucal calls — or ``None``s if unavailable.

    A missing ephemeris is an expected condition (a fresh checkout before
    ``scripts/fetch_data.sh`` has run), and the clock must still show the time. Only
    that specific case is swallowed; a genuine astronomy bug is left to surface rather
    than being quietly rendered as a blank panel.
    """
    from .almanac.ephemeris import Observer, get_sky
    from .almanac.solar_lunar import moon_state, next_coucal_calls, sun_day

    observer = Observer(
        latitude=config.location.latitude,
        longitude=config.location.longitude,
        elevation_m=config.location.elevation_m,
        timezone_name=config.location.timezone,
    )
    try:
        sky = get_sky(observer)
    except FileNotFoundError:
        return None, None, None, None, None

    if not sky.covers(local_time):
        # Past the end of the ephemeris. The clock still keeps time; it simply cannot
        # claim to know where the sun is. Admitting that is the point.
        return None, None, None, None, None

    from .almanac.lunation import lunation_at

    sun = sun_day(sky, local_time.date())
    moon = moon_state(sky, local_time)
    dawn, dusk = next_coucal_calls(sky, local_time)
    lun = lunation_at(sky, local_time)
    return sun, moon, dawn, dusk, lun


def build_state(
    hal: HAL, config: UnitConfig, tick: int, power_state: str = "normal"
) -> RenderState:
    reading = hal.time.now()
    power = hal.power.read()
    tz = _local_tz(config.location.timezone)
    local = reading.utc.astimezone(tz)
    sun, moon, dawn, dusk, lunation = _almanac(config, local)
    from .almanac.lanna import festival_on as _festival_on
    from .almanac.lanna import lanna_day as _lanna_day
    from .almanac.lanna import next_festival as _next_festival
    from .almanac.thai import next_wan_phra as _next_wan_phra
    from .almanac.thai import thai_day as _thai_day

    thai = _thai_day(local.date())
    upcoming = _next_wan_phra(local.date())
    lanna = _lanna_day(local.date())
    today_festival = _festival_on(local.date())
    coming_festival = _next_festival(local.date())
    return RenderState(
        time=reading,
        position=hal.position.position(),
        power=power,
        local_time=local,
        tick=tick,
        unit_label=config.label,
        power_state=power_state,
        sun=sun,
        moon=moon,
        next_dawn=dawn,
        next_dusk=dusk,
        lunation=lunation,
        thai=thai,
        next_wan_phra=upcoming,
        lanna=lanna,
        festival=today_festival,
        next_festival=coming_festival,
    )


def render_cycle(
    hal: HAL,
    config: UnitConfig,
    tick: int,
    power_state: str = "normal",
    face_key: str | None = None,
) -> RenderState:
    """One wake: compose the current face and push it to the display. Returns the state.

    ``face_key`` names the face to draw; omitting it draws the one the clock rests on.
    The registry resolves it, so adding or reordering faces never means editing this
    loop.
    """
    from .faces import registry

    state = build_state(hal, config, tick, power_state)
    spec = registry.get(face_key) if face_key else registry.default_face()
    if spec.status != registry.LIVE:  # a face that is not built cannot be shown
        spec = registry.default_face()
    framebuffer = spec.render(state)

    # A face change rewrites the entire panel, so it earns a full refresh. A partial
    # one leaves the previous face ghosted underneath the new one — which is exactly
    # what a reader sees as smudge, and the reason this is not merely cosmetic.
    changed_face = spec.key != _last_face.get("key")
    _last_face["key"] = spec.key
    mode = (
        RefreshMode.FULL if changed_face or tick % FULL_REFRESH_EVERY == 0 else RefreshMode.PARTIAL
    )
    hal.display.push(framebuffer, mode=mode)
    hal.watchdog.feed()
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Coucal Clock — headless single-frame render.")
    parser.add_argument("--config", default="config/unit-01.toml", help="unit TOML path")
    parser.add_argument("--out", default="out/frame.png", help="PNG output path")
    parser.add_argument("--at", help="ISO-8601 UTC instant to render (default: sim epoch)")
    args = parser.parse_args(argv)

    config = UnitConfig.load(args.config)

    # Headless render is sim-only, so build the harness directly to control time.
    from .hal.sim.build import build_sim_harness

    start = None
    if args.at:
        start = datetime.fromisoformat(args.at)
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)

    harness = build_sim_harness(
        latitude=config.location.latitude,
        longitude=config.location.longitude,
        elevation_m=config.location.elevation_m,
        start_utc=start,
        holdover_warn_days=config.power.holdover_warn_days,
    )
    hal = harness.hal

    state = render_cycle(hal, config, tick=0)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    harness.display.save_png(args.out)
    print(f"Rendered {config.unit_id} at {state.local_time.isoformat()} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
