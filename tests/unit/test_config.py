from datetime import time
from pathlib import Path

from coucal.config import SilenceWindow, UnitConfig

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"


def test_loads_example_and_units():
    for name in ("unit.example.toml", "unit-01.toml", "unit-02.toml"):
        cfg = UnitConfig.load(CONFIG_DIR / name)
        assert cfg.location.timezone == "Asia/Bangkok"
        assert 18.0 < cfg.location.latitude < 19.0
        assert cfg.methods.ayanamsa == "lahiri"
        assert cfg.power.hibernate_v < cfg.power.shed_to_dateonly_v < cfg.power.shed_to_hourly_v


def test_units_differ_only_in_identity():
    u1 = UnitConfig.load(CONFIG_DIR / "unit-01.toml")
    u2 = UnitConfig.load(CONFIG_DIR / "unit-02.toml")
    assert u1.unit_id != u2.unit_id
    # Software-relevant policy is identical across units.
    assert u1.power == u2.power
    assert u1.methods == u2.methods


def test_silence_window_same_day():
    w = SilenceWindow(time(4, 30), time(6, 30))
    assert w.contains(time(5, 0))
    assert not w.contains(time(6, 30))  # end is exclusive
    assert not w.contains(time(4, 0))


def test_silence_window_crossing_midnight():
    w = SilenceWindow(time(22, 0), time(2, 0))
    assert w.contains(time(23, 30))
    assert w.contains(time(1, 0))
    assert not w.contains(time(12, 0))
