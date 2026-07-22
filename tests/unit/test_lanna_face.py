"""Tests for the Lanna face and its ornament vocabulary.

Faces are pure, so these render real states and assert on the framebuffer. They cannot
judge beauty, but they can guarantee the face never crashes, never silently blanks, and
always changes when the thing it displays changes.
"""

from datetime import UTC, date, datetime

import pytest

from coucal.almanac.lanna import festival_on, lanna_day, next_festival
from coucal.almanac.thai import next_wan_phra, thai_day
from coucal.faces import lanna as lanna_face
from coucal.faces import palette as palette_module
from coucal.faces.base import PANEL_H, PANEL_W, Canvas, RenderState
from coucal.faces.ornament import kanok_corner, lotus_hub, moon_disc, naga_ring, polar, rays
from coucal.hal.interfaces import Position, PowerReading, TimeQuality, TimeReading


def _state(when: date, tick: int = 3) -> RenderState:
    local = datetime(when.year, when.month, when.day, 9, 40, tzinfo=UTC)
    return RenderState(
        time=TimeReading(utc=local, quality=TimeQuality.GPS),
        position=Position(18.85, 99.05, 320.0),
        power=PowerReading(13.0, 0.4, 18.0, 1.1),
        local_time=local,
        tick=tick,
        lanna=lanna_day(when),
        thai=thai_day(when),
        next_wan_phra=next_wan_phra(when),
        festival=festival_on(when),
        next_festival=next_festival(when),
    )


def test_renders_a_full_framebuffer():
    fb = lanna_face.render(_state(date(2026, 7, 20)))
    assert len(fb) == PANEL_W * PANEL_H


def test_face_is_not_blank():
    """A face that silently renders all-white would still pass a size check."""
    fb = lanna_face.render(_state(date(2026, 7, 20)))
    assert len(set(fb)) > 3, "expected real tonal range, not a blank panel"
    inked = sum(1 for b in fb if b < 200)
    assert inked > 20_000, "suspiciously little ink — did the face fail to draw?"


def test_the_zodiac_band_has_twelve_animals():
    assert len(lanna_face.ZODIAC_LABELS) == 12


def test_festival_day_differs_from_an_ordinary_day():
    """Yi Peng must actually look different, or the festival is decorative."""
    ordinary = lanna_face.render(_state(date(2026, 7, 20)))
    yi_peng = lanna_face.render(_state(date(2026, 11, 24)))
    assert ordinary != yi_peng


def test_the_face_changes_when_the_year_animal_changes():
    a = lanna_face.render(_state(date(2026, 7, 20)))  # ปีไส้
    b = lanna_face.render(_state(date(2027, 7, 20)))  # the next animal
    assert a != b


def test_heartbeat_still_steps_on_this_face():
    a = lanna_face.render(_state(date(2026, 7, 20), tick=0))
    b = lanna_face.render(_state(date(2026, 7, 20), tick=1))
    assert a != b, "the heartbeat must be visible on every face, not just the main one"


def test_renders_under_every_palette():
    state = _state(date(2026, 11, 24))
    for name in palette_module.PALETTES:
        fb = lanna_face.render(state, palette=palette_module.get(name))
        assert len(fb) == PANEL_W * PANEL_H, f"{name} produced a short framebuffer"


def test_renders_outside_the_calendar_table_without_crashing():
    """Past the authority table the face must still draw — saying it does not know."""
    fb = lanna_face.render(_state(date(2040, 5, 1)))
    assert len(fb) == PANEL_W * PANEL_H


def test_renders_with_no_almanac_at_all():
    """A missing ephemeris must not take the face down."""
    local = datetime(2026, 7, 20, 9, 40, tzinfo=UTC)
    bare = RenderState(
        time=TimeReading(utc=local, quality=TimeQuality.UNKNOWN),
        position=Position(18.85, 99.05, 320.0),
        power=PowerReading(12.1, -0.2, 14.0, 0.0),
        local_time=local,
        tick=1,
        power_state="date_only",
    )
    assert len(lanna_face.render(bare)) == PANEL_W * PANEL_H


# --- ornament --------------------------------------------------------------


def test_polar_geometry_starts_at_twelve_oclock():
    x, y = polar(100, 100, 50, 0)
    assert x == pytest.approx(100) and y == pytest.approx(50)  # straight up
    x, y = polar(100, 100, 50, 90)
    assert x == pytest.approx(150) and y == pytest.approx(100)  # three o'clock


def test_every_ornament_draws_without_error():
    c = Canvas()
    naga_ring(c, 400, 400, 300)
    kanok_corner(c, 50, 50, 100, quadrant=0)
    lotus_hub(c, 400, 400, 40)
    rays(c, 400, 400, 100, 200, count=12)
    moon_disc(c, 400, 400, 60, 0.5, True)
    assert len(c.to_framebuffer()) == PANEL_W * PANEL_H


@pytest.mark.parametrize("illumination", [0.0, 0.25, 0.5, 0.75, 1.0])
@pytest.mark.parametrize("waxing", [True, False])
def test_moon_disc_handles_every_phase(illumination, waxing):
    c = Canvas()
    moon_disc(c, 400, 400, 60, illumination, waxing)
    assert len(c.to_framebuffer()) == PANEL_W * PANEL_H


# --- the engraved ground and the moon complication -------------------------


def test_guilloche_stays_faint():
    """The ground must never compete with the reading. ENGRAVING is the lightest ink;
    if it ever darkens toward FAINT the dial becomes noise."""
    from coucal.faces.palette import MONO16, Ink

    assert MONO16.value(Ink.ENGRAVING) > MONO16.value(Ink.FAINT) + 40
    assert MONO16.value(Ink.ENGRAVING) < MONO16.value(Ink.PAPER)


def test_engraving_is_absent_rather_than_solid_on_a_colour_panel():
    """Spectra 6 has no light grey. The ground must vanish, not render as black ink."""
    from coucal.faces.palette import SPECTRA6, Ink

    assert SPECTRA6.value(Ink.ENGRAVING) == SPECTRA6.value(Ink.PAPER)


def test_ground_is_drawn_but_does_not_dominate():
    """Render the ground alone: it should mark the dial, yet leave it overwhelmingly
    paper — a guilloche that inks a large fraction of the face is too strong."""
    from coucal.faces.base import Canvas
    from coucal.faces.lanna import _draw_ground

    c = Canvas()
    _draw_ground(c)
    data = c.to_framebuffer()
    marked = sum(1 for b in data if b < 250)
    assert marked > 5_000, "the ground did not draw at all"
    assert marked < len(data) * 0.12, "the ground is too heavy — it will fight the numerals"


def _moon_frame(disc_angle: float) -> bytes:
    from coucal.faces.base import Canvas
    from coucal.faces.ornament import moon_complication

    c = Canvas()
    moon_complication(c, 400, 400, 120, disc_angle)
    return c.to_framebuffer()


def _disc(phase_deg: float, parity: int = 0) -> float:
    from coucal.almanac.lunation import disc_angle_for_phase

    return disc_angle_for_phase(phase_deg, parity)


def test_two_moons_on_one_disc_turning_half_a_turn_a_month():
    """Two moons 180 deg apart; the disc turns 360 deg per TWO lunations. One crosses
    the aperture this month, its partner the next."""
    import math

    from coucal.faces.ornament import DISC_CY, DISC_R, crossing_index, moon_position

    for g in range(0, 360, 20):
        ax, ay = moon_position(g, 0)
        bx, by = moon_position(g, 1)
        assert math.hypot(ax, ay - DISC_CY) == pytest.approx(DISC_R)
        assert math.hypot(bx, by - DISC_CY) == pytest.approx(DISC_R)
        assert ax + bx == pytest.approx(0.0, abs=1e-9)
        assert (ay - DISC_CY) == pytest.approx(-(by - DISC_CY), abs=1e-9)

    # One lunation advances the gear exactly 180 deg, and swaps which moon is up.
    assert _disc(0, 0) == pytest.approx(0.0)
    assert _disc(359.999, 0) == pytest.approx(180.0, abs=0.01)
    assert _disc(0, 1) == pytest.approx(180.0)
    assert crossing_index(_disc(90, 0)) == 0
    assert crossing_index(_disc(90, 1)) == 1

    # The crossing moon rises left, tops at full, sets right.
    assert moon_position(_disc(0), 0)[0] < 0
    assert moon_position(_disc(180), 0) == pytest.approx((0.0, DISC_CY - DISC_R), abs=1e-9)
    assert moon_position(_disc(359.99), 0)[0] > 0


def test_at_new_moon_both_moons_are_hidden():
    """One sets as its pal rises. The plate must swallow both at once — which is why
    it covers so much of the viewport."""
    from coucal.faces.ornament import moon_visible_fraction

    for parity in (0, 1):
        for phase in (0.0, 1.0, 359.0):
            g = _disc(phase, parity)
            assert moon_visible_fraction(g, 0) < 0.03
            assert moon_visible_fraction(g, 1) < 0.03


def test_the_partner_is_never_visible_mid_month():
    from coucal.faces.ornament import crossing_index, moon_visible_fraction

    worst = 0.0
    for phase in range(0, 360, 5):
        for parity in (0, 1):
            g = _disc(phase, parity)
            partner = 1 - crossing_index(g)
            worst = max(worst, moon_visible_fraction(g, partner))
    assert worst < 0.01, f"the partner moon shows through ({worst:.1%})"


def test_moon_is_slightly_smaller_than_the_cloud():
    """A deliberate proportion: comparable radii cut a true crescent with horns, and
    the moon reads as nestling behind the cloud rather than matching it."""
    from coucal.faces.ornament import HUMP_R, MOON_R

    assert 0.78 <= MOON_R / HUMP_R <= 0.95


def test_the_humps_leave_a_visible_notch():
    from coucal.faces.ornament import HUMP_R, HUMP_X

    assert HUMP_X - HUMP_R > 0.05, "the humps must not merge into one bank"


def test_moon_matches_the_real_moon():
    """Accuracy against the sky itself: illumination = (1 - cos alpha)/2."""
    import math

    from coucal.faces.ornament import moon_visible_fraction

    errors = [
        moon_visible_fraction(_disc(a)) - (1 - math.cos(math.radians(a))) / 2
        for a in range(0, 360, 10)
    ]
    rms = math.sqrt(sum(e * e for e in errors) / len(errors))
    assert rms < 0.010, f"visible fraction tracks illumination poorly (RMS {rms:.4f})"
    assert max(abs(e) for e in errors) < 0.025, "a phase is off by more than 2.5 points"

    shown = [moon_visible_fraction(_disc(a)) for a in range(0, 360)]
    lit = [(1 - math.cos(math.radians(a))) / 2 for a in range(0, 360)]
    for threshold in (0.99, 0.95, 0.90):
        ours = sum(1 for v in shown if v >= threshold) / 360 * 29.53
        real = sum(1 for v in lit if v >= threshold) / 360 * 29.53
        assert abs(ours - real) <= 0.6, (
            f"shown>={threshold}: {ours:.1f} days vs the real moon's {real:.1f}"
        )


def test_moon_is_dark_at_new_and_whole_at_full():
    from coucal.faces.ornament import moon_visible_fraction

    assert moon_visible_fraction(_disc(0)) < 0.03
    assert moon_visible_fraction(_disc(180)) > 0.98
    assert moon_visible_fraction(_disc(90)) == pytest.approx(0.5, abs=0.03)


def test_the_humps_clip_the_moon_never_the_rim():
    """An early version had the viewport rim doing 87% of the occlusion, so the moon
    appeared to slide off the edge instead of being shaped."""
    import math

    from coucal.faces.ornament import MOON_R, moon_position

    worst = 0.0
    for g in range(0, 360, 5):
        mx, my = moon_position(g, crossing := 0 if g < 180 else 1)
        assert crossing in (0, 1)
        total = rim = 0
        for i in range(10):
            r = MOON_R * math.sqrt((i + 0.5) / 10)
            for j in range(24):
                t = 2 * math.pi * j / 24
                px, py = mx + r * math.cos(t), my + r * math.sin(t)
                total += 1
                if px * px + py * py > 1.0:
                    rim += 1
        worst = max(worst, rim / total)
    assert worst == 0.0, f"the rim is carving the moon ({worst:.1%})"


def test_the_plate_covers_most_of_the_viewport():
    from coucal.faces.ornament import HUMP_R, HUMP_X, PLATE_Y

    n = 90
    inside = covered = 0
    for i in range(n):
        y = -1.0 + 2.0 * (i + 0.5) / n
        for j in range(n):
            x = -1.0 + 2.0 * (j + 0.5) / n
            if x * x + y * y > 1.0:
                continue
            inside += 1
            if (
                y > PLATE_Y
                or (x + HUMP_X) ** 2 + (y - PLATE_Y) ** 2 < HUMP_R**2
                or (x - HUMP_X) ** 2 + (y - PLATE_Y) ** 2 < HUMP_R**2
            ):
                covered += 1
    assert 0.62 <= covered / inside <= 0.80


def test_font_weight_axis_is_actually_applied():
    """Weight is the main tool for hierarchy on a greyscale panel. If the variable axis
    silently stopped applying, every face would flatten without any test noticing."""
    from coucal.faces.base import FONT_SERIF_THAI, W_BOLD, W_LIGHT, Canvas

    c = Canvas()
    light = c.measure("ขึ้น ๑๕ ค่ำ", 70, FONT_SERIF_THAI, W_LIGHT)
    bold = c.measure("ขึ้น ๑๕ ค่ำ", 70, FONT_SERIF_THAI, W_BOLD)
    assert light != bold
