"""Tests for the face catalogue.

Beyond the mechanical checks, two of these encode design commitments from
``docs/GROWING.md``: the catalogue stays finishable, and navigation can only ever land
on a face that actually exists.
"""

import pytest

from coucal.faces import registry
from coucal.faces.registry import (
    CATEGORIES,
    LIVE,
    OPEN,
    STATUSES,
    FaceSpec,
    all_faces,
    committed_faces,
    live_faces,
)


def test_keys_are_unique_and_fields_valid():
    faces = all_faces()
    assert len({f.key for f in faces}) == len(faces)
    for f in faces:
        assert f.category in CATEGORIES
        assert f.status in STATUSES


def test_order_is_unique_within_each_category():
    for category in CATEGORIES:
        orders = [f.order for f in all_faces() if f.category == category]
        assert len(orders) == len(set(orders)), f"duplicate order in {category!r}"


def test_only_live_faces_have_a_renderer():
    for f in all_faces():
        if f.status == LIVE:
            assert callable(f.render), f"{f.key} is live but not renderable"
        else:
            assert f.render is None, f"{f.key} is not live but has a renderer"


def test_catalogue_stays_finishable():
    """The committed set is the clock we are actually building — it must stay small
    enough to finish. Growth belongs in docs/GROWING.md as open doors, not here as
    unmet obligations (see that document's first principle)."""
    assert len(committed_faces()) <= 12, (
        "committed faces are growing into a backlog; move new ideas to docs/GROWING.md"
    )


def test_the_unopened_door_is_open_and_never_scheduled():
    reserved = registry.get("reserved")
    assert reserved.status == OPEN
    assert reserved.render is None


def test_default_face_is_live():
    # Falls back to a built face while `main` is unbuilt, so the clock always shows
    # something during the build-out.
    assert registry.default_face() in live_faces()


def test_main_is_the_intended_default_and_is_lanna_rooted():
    main = registry.get("main")
    assert main.is_default
    assert main.category == "core"
    assert "Lanna" in main.note  # the clock stands in a Lanna wat; face 0 reflects that


def test_navigation_only_lands_on_live_faces():
    live = live_faces()
    assert live, "expected at least one live face"
    start = live[0].key
    assert registry.next_face(start) in live
    assert registry.next_category(start) in live


def test_navigation_cycles_within_a_category():
    live = [f for f in live_faces() if f.category == "meta"]
    if len(live) > 1:
        keys = [f.key for f in live]
        assert registry.next_face(keys[-1]).key == keys[0]


def test_register_rejects_inconsistent_specs():
    with pytest.raises(ValueError):
        registry.register(FaceSpec("bad_category", "x", "x", "bogus", 99))
    with pytest.raises(ValueError):
        registry.register(FaceSpec("bad_status", "x", "x", "meta", 98, status="someday"))
    with pytest.raises(ValueError):
        registry.register(FaceSpec("live_no_render", "x", "x", "meta", 97, status=LIVE))
