import pytest

from coucal.hal.interfaces import RefreshMode
from coucal.hal.sim.display import GREY_LEVELS, HEIGHT, WIDTH, SimDisplay


def _solid(value: int) -> bytes:
    return bytes([value]) * (WIDTH * HEIGHT)


def test_push_rejects_wrong_size():
    d = SimDisplay()
    with pytest.raises(ValueError):
        d.push(b"\x00" * 10)


def test_quantizes_to_16_levels():
    d = SimDisplay(ghosting=False)
    # A full sweep of 0..255 should collapse to exactly 16 distinct values.
    ramp = bytes([int(i * 255 / (WIDTH - 1)) for i in range(WIDTH)]) * HEIGHT
    d.push(ramp, mode=RefreshMode.FULL)
    assert len(set(d.image.tobytes())) <= GREY_LEVELS


def test_full_refresh_resets_ghost_counter():
    d = SimDisplay()
    d.push(_solid(0), mode=RefreshMode.PARTIAL)
    d.push(_solid(255), mode=RefreshMode.PARTIAL)
    assert d.partials_since_full == 2
    d.push(_solid(128), mode=RefreshMode.FULL)
    assert d.partials_since_full == 0
    assert d.full_refreshes == 1


def test_clear_is_white():
    d = SimDisplay()
    d.push(_solid(0), mode=RefreshMode.FULL)
    d.clear()
    assert d.image.getpixel((0, 0)) == 255


def test_ghosting_leaves_residue_partial_but_not_full():
    ghost = SimDisplay(ghosting=True)
    ghost.push(_solid(0), mode=RefreshMode.FULL)  # all black
    ghost.push(_solid(255), mode=RefreshMode.PARTIAL)  # now white, but ghost of black
    # With ghosting, a partial refresh of white over black is not perfectly white.
    assert ghost.image.getpixel((0, 0)) < 255

    clean = SimDisplay(ghosting=False)
    clean.push(_solid(0), mode=RefreshMode.FULL)
    clean.push(_solid(255), mode=RefreshMode.PARTIAL)
    assert clean.image.getpixel((0, 0)) == 255
