"""The load-shedding ladder as a pure function.

Extracted here so both the simulator and (in Phase 5) the ``steward`` service share
one definition of what battery voltage means which power state. Pure and testable.
"""

from __future__ import annotations

from ..config import PowerConfig

# Ordered worst-last. Each state below implies fewer display updates / less work.
NORMAL = "normal"
HOURLY = "hourly"
DATE_ONLY = "date_only"
HIBERNATE = "hibernate"


def power_state_for(volts: float, cfg: PowerConfig) -> str:
    if volts < cfg.hibernate_v:
        return HIBERNATE
    if volts < cfg.shed_to_dateonly_v:
        return DATE_ONLY
    if volts < cfg.shed_to_hourly_v:
        return HOURLY
    return NORMAL
