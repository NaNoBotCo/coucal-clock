"""Typed loader for a unit's TOML configuration.

One `unit.toml` fully describes a clock. Parsing is centralised here so every
service sees the same validated, typed view. Uses the stdlib ``tomllib`` (Python
3.11+) — no third-party TOML dependency, which matters for offline posterity.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path


def _parse_hhmm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


@dataclass(frozen=True)
class SilenceWindow:
    start: time
    end: time
    note: str = ""

    def contains(self, t: time) -> bool:
        """True if ``t`` falls within the window (handles windows crossing midnight)."""
        if self.start <= self.end:
            return self.start <= t < self.end
        return t >= self.start or t < self.end


@dataclass(frozen=True)
class AbbotConfig:
    silence_windows: tuple[SilenceWindow, ...]
    audio_enabled: bool
    volume_day: float
    volume_night: float
    wan_phra_distinct: bool
    call_at_dawn: bool
    call_at_dusk: bool


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    elevation_m: float
    timezone: str
    true_heading_deg: float


@dataclass(frozen=True)
class PowerConfig:
    mode: str  # "duty_cycled" | "always_on"
    wake_interval_min: int
    target_wh_per_day: float
    shed_to_hourly_v: float
    shed_to_dateonly_v: float
    hibernate_v: float
    holdover_warn_days: int


@dataclass(frozen=True)
class Methods:
    ayanamsa: str
    hexagram_school: str
    thai_intercalation: str
    crescent_criterion: str


@dataclass(frozen=True)
class UnitConfig:
    unit_id: str
    label: str
    location: Location
    power: PowerConfig
    methods: Methods
    abbot: AbbotConfig
    source_path: Path | None = field(default=None, compare=False)

    @classmethod
    def load(cls, path: str | Path) -> UnitConfig:
        path = Path(path)
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
        return cls.from_dict(raw, source_path=path)

    @classmethod
    def from_dict(cls, raw: dict, source_path: Path | None = None) -> UnitConfig:
        a = raw["abbot"]
        windows = tuple(
            SilenceWindow(_parse_hhmm(w["start"]), _parse_hhmm(w["end"]), w.get("note", ""))
            for w in a.get("silence_windows", [])
        )
        abbot = AbbotConfig(
            silence_windows=windows,
            audio_enabled=bool(a["audio_enabled"]),
            volume_day=float(a["volume_day"]),
            volume_night=float(a["volume_night"]),
            wan_phra_distinct=bool(a["wan_phra_distinct"]),
            call_at_dawn=bool(a["call_at_dawn"]),
            call_at_dusk=bool(a["call_at_dusk"]),
        )
        loc = raw["location"]
        location = Location(
            latitude=float(loc["latitude"]),
            longitude=float(loc["longitude"]),
            elevation_m=float(loc["elevation_m"]),
            timezone=str(loc["timezone"]),
            true_heading_deg=float(loc["true_heading_deg"]),
        )
        p = raw["power"]
        power = PowerConfig(
            mode=str(p["mode"]),
            wake_interval_min=int(p["wake_interval_min"]),
            target_wh_per_day=float(p["target_wh_per_day"]),
            shed_to_hourly_v=float(p["shed_to_hourly_v"]),
            shed_to_dateonly_v=float(p["shed_to_dateonly_v"]),
            hibernate_v=float(p["hibernate_v"]),
            holdover_warn_days=int(p["holdover_warn_days"]),
        )
        m = raw["methods"]
        methods = Methods(
            ayanamsa=str(m["ayanamsa"]),
            hexagram_school=str(m["hexagram_school"]),
            thai_intercalation=str(m["thai_intercalation"]),
            crescent_criterion=str(m["crescent_criterion"]),
        )
        u = raw["unit"]
        return cls(
            unit_id=str(u["id"]),
            label=str(u["label"]),
            location=location,
            power=power,
            methods=methods,
            abbot=abbot,
            source_path=source_path,
        )
