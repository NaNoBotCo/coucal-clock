"""Tests for face navigation.

This exists because the Lanna face was built, registered, tested — and *unreachable*.
The registry knew the face order; nothing consumed the button. The clock rendered
`default_face()` forever. These tests make that class of gap fail loudly.
"""

from datetime import UTC, datetime, timedelta

from coucal.faces import registry
from coucal.services.navigator import AUTO_RETURN, Navigator

NOW = datetime(2026, 7, 20, 9, 0, tzinfo=UTC)


def test_starts_on_the_home_face():
    assert Navigator().current.key == registry.default_face().key


def test_short_press_changes_the_face():
    n = Navigator()
    before = n.current.key
    n.short_press(NOW)
    assert n.current.key != before


def test_pressing_reaches_every_live_face():
    """THE regression test. Every built face must be reachable by pressing the button —
    a face nobody can get to is not shipped, however well it renders."""
    n = Navigator()
    seen = {n.current.key}
    for i in range(40):  # generous: press well past a full cycle
        n.short_press(NOW + timedelta(seconds=i))
        seen.add(n.current.key)
        n.long_press(NOW + timedelta(seconds=i))
        seen.add(n.current.key)

    reachable = {s.key for s in registry.live_faces()}
    assert seen >= reachable, f"unreachable faces: {sorted(reachable - seen)}"


def test_the_lanna_face_is_reachable():
    """Named explicitly, because this is the one that was stranded."""
    n = Navigator()
    for i in range(20):
        if n.current.key == "lanna":
            return
        n.short_press(NOW + timedelta(seconds=i))
    raise AssertionError("could not reach the Lanna face by pressing the button")


def test_navigation_only_lands_on_live_faces():
    n = Navigator()
    live = {s.key for s in registry.live_faces()}
    for i in range(30):
        n.short_press(NOW + timedelta(seconds=i))
        assert n.current.key in live
        n.long_press(NOW + timedelta(seconds=i))
        assert n.current.key in live


def test_returns_home_after_the_idle_window():
    """A visitor who presses and walks away must not leave the clock parked."""
    n = Navigator()
    n.short_press(NOW)
    assert n.current.key != registry.default_face().key

    assert n.tick(NOW + AUTO_RETURN - timedelta(seconds=1)) is False  # not yet
    assert n.tick(NOW + AUTO_RETURN + timedelta(seconds=1)) is True
    assert n.current.key == registry.default_face().key


def test_idle_ticks_do_nothing_when_already_home():
    n = Navigator()
    assert n.tick(NOW + timedelta(hours=1)) is False


def test_unknown_face_key_falls_back_home():
    """A card carrying state from an older release must not brick the display."""
    n = Navigator(current_key="a-face-that-was-removed")
    assert n.current.key == registry.default_face().key


def test_a_non_live_face_falls_back_home():
    committed = registry.committed_faces()
    if committed:
        n = Navigator(current_key=committed[0].key)
        assert n.current.key == registry.default_face().key
