"""Select and build the HAL bundle for the current environment.

    COUCAL_HAL=sim   (desktop default)  -> fakes, driven by a virtual timeline
    COUCAL_HAL=real  (set by systemd)   -> Raspberry Pi drivers

Code above the HAL calls ``build_hal(config)`` and never learns which it got.
"""

from __future__ import annotations

import os

from ..config import UnitConfig
from .interfaces import HAL


def build_hal(config: UnitConfig, kind: str | None = None) -> HAL:
    kind = kind or os.environ.get("COUCAL_HAL", "sim")

    if kind == "sim":
        from .sim.build import build_sim_harness

        harness = build_sim_harness(
            latitude=config.location.latitude,
            longitude=config.location.longitude,
            elevation_m=config.location.elevation_m,
            holdover_warn_days=config.power.holdover_warn_days,
        )
        return harness.hal

    if kind == "real":
        from .real.build import build_real_hal  # imported lazily: needs Pi libraries

        return build_real_hal(config)

    raise ValueError(f"Unknown COUCAL_HAL={kind!r} (expected 'sim' or 'real')")
