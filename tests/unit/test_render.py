from datetime import UTC, datetime

from coucal.faces import phase0
from coucal.faces.base import PANEL_H, PANEL_W, RenderState
from coucal.hal.interfaces import Position, PowerReading, TimeQuality, TimeReading


def _state(tick: int) -> RenderState:
    utc = datetime(2026, 7, 19, 0, 30, tzinfo=UTC)
    return RenderState(
        time=TimeReading(utc=utc, quality=TimeQuality.GPS),
        position=Position(18.85, 99.05, 320.0),
        power=PowerReading(13.0, 0.4, 18.0, 1.1),
        local_time=utc.astimezone(UTC),
        tick=tick,
        unit_label="test",
    )


def test_render_produces_full_framebuffer():
    fb = phase0.render(_state(0))
    assert len(fb) == PANEL_W * PANEL_H


def test_heartbeat_moves_between_ticks():
    # The whole point of the heartbeat: consecutive wakes must differ on screen.
    a = phase0.render(_state(0))
    b = phase0.render(_state(1))
    assert a != b


def test_heartbeat_returns_after_full_cycle():
    # After HEARTBEAT_STEPS wakes the dot is back where it started; only the tick
    # differs, and tick is not otherwise drawn, so the frames match.
    a = phase0.render(_state(0))
    b = phase0.render(_state(phase0.HEARTBEAT_STEPS))
    assert a == b
