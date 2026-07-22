"""Builder for the real Raspberry Pi HAL. Implemented in Phase 5.

Kept as a named seam so the factory has a symmetric target and a future maintainer
has an obvious place to start. Each driver will live beside this file (gps.py,
rtc.py, eink.py, ina219.py, wittypi.py, audio.py, automaton.py, button.py,
watchdog.py) and satisfy the matching Protocol in ``hal.interfaces``.
"""

from __future__ import annotations

from ...config import UnitConfig
from ..interfaces import HAL


def build_real_hal(config: UnitConfig) -> HAL:
    raise NotImplementedError(
        "Real hardware HAL lands in Phase 5. Use COUCAL_HAL=sim for Phase 0–4 development."
    )
