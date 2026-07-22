from pathlib import Path

from coucal.config import UnitConfig
from coucal.sim.power_policy import DATE_ONLY, HIBERNATE, HOURLY, NORMAL, power_state_for

CONFIG = UnitConfig.load(Path(__file__).resolve().parents[2] / "config" / "unit-01.toml")


def test_load_shedding_ladder():
    p = CONFIG.power
    assert power_state_for(13.0, p) == NORMAL
    assert power_state_for(p.shed_to_hourly_v - 0.01, p) == HOURLY
    assert power_state_for(p.shed_to_dateonly_v - 0.01, p) == DATE_ONLY
    assert power_state_for(p.hibernate_v - 0.01, p) == HIBERNATE


def test_boundaries_are_inclusive_of_the_better_state():
    p = CONFIG.power
    # Exactly at a threshold stays in the healthier state (strict less-than to shed).
    assert power_state_for(p.shed_to_hourly_v, p) == NORMAL
    assert power_state_for(p.hibernate_v, p) == DATE_ONLY
