from datetime import UTC, datetime, timedelta

from coucal.hal.interfaces import (
    HAL,
    AudioSink,
    Automaton,
    Button,
    ButtonEvent,
    Display,
    PositionSource,
    PowerController,
    PowerTelemetry,
    TimeQuality,
    TimeSource,
    Watchdog,
)
from coucal.hal.sim.build import build_sim_harness


def _harness():
    return build_sim_harness(latitude=18.85, longitude=99.05, elevation_m=320.0)


def test_harness_satisfies_all_protocols():
    hal = _harness().hal
    assert isinstance(hal, HAL)
    assert isinstance(hal.time, TimeSource)
    assert isinstance(hal.position, PositionSource)
    assert isinstance(hal.power, PowerTelemetry)
    assert isinstance(hal.button, Button)
    assert isinstance(hal.display, Display)
    assert isinstance(hal.audio, AudioSink)
    assert isinstance(hal.automaton, Automaton)
    assert isinstance(hal.watchdog, Watchdog)
    assert isinstance(hal.power_controller, PowerController)
    assert hal.kind == "sim"


def test_timeline_advance_is_monotonic():
    h = _harness()
    t0 = h.timeline.now()
    h.timeline.advance(3600)
    assert h.timeline.now() == t0 + timedelta(hours=1)


def test_time_quality_reflects_gps_and_holdover():
    h = _harness()
    assert h.time.now().quality is TimeQuality.GPS
    h.timeline.gps_available = False
    h.timeline.holdover_days = 5
    assert h.time.now().quality is TimeQuality.RTC
    h.timeline.holdover_days = 40
    assert h.time.now().quality is TimeQuality.RTC_STALE


def test_button_queue_returns_one_event_then_empty():
    h = _harness()
    assert h.button.poll() is ButtonEvent.NONE
    h.button.press()
    assert h.button.poll() is ButtonEvent.PRESS
    assert h.button.poll() is ButtonEvent.NONE


def test_power_controller_sleep_fast_forwards_timeline():
    h = _harness()
    wake = h.timeline.now() + timedelta(minutes=5)
    h.power_controller.sleep_until(wake)
    assert h.timeline.now() == wake
    assert h.power_controller.sleeps == [wake]


def test_discipline_rtc_records_calls():
    h = _harness()
    stamp = datetime(2026, 7, 19, tzinfo=UTC)
    h.time.discipline_rtc(stamp)
    assert h.time.disciplined == [stamp]
