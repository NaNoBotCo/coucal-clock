"""The face catalogue and navigation — the single source of truth for what this clock shows.

Every face is one entry here plus one module. Adding a face is an *addition*, never
surgery: register a ``FaceSpec`` and write ``render(state) -> bytes``. No existing face,
and nothing outside this package, has to change. That property is deliberate — see
``docs/GROWING.md``.

**This file lists only what the clock is actually going to be.** It is not a wish list
and not a backlog. A face that someone might add one day lives in ``docs/GROWING.md`` as
an open door, not here as an unmet obligation. The clock is complete at every stage of
its life; it is never a partial clock waiting to be finished.

Three statuses, and only three:

    live       built and reachable by the button
    committed  intended for the donated clock (Phases 1-6)
    open       a door left unlocked; nothing is owed, no date is implied

**Navigation.** One brass button cannot usefully cycle a long list, so faces are grouped
and the button does two things:

    short press  ->  next face within the current category
    long press   ->  first face of the next category

After 90 s with no input the display returns to the default face.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

# Long-press order. Sequenced so it reads as a journey: the here-and-now, then the
# world's calendars, then its divinatory systems, then the clock's own self-knowledge.
CATEGORIES = ("core", "calendar", "divination", "meta")

LIVE = "live"
COMMITTED = "committed"
OPEN = "open"
STATUSES = (LIVE, COMMITTED, OPEN)


@dataclass(frozen=True)
class FaceSpec:
    key: str  # stable identifier; never reused or renamed once shipped
    title_en: str
    title_th: str
    category: str
    order: int  # sort position within its category
    # render(state, palette=None) -> framebuffer bytes. The palette argument is
    # optional so a face can be written mono-only and still gain colour later.
    render: Callable[..., bytes] | None = None
    status: str = COMMITTED
    is_default: bool = False  # the face the clock rests on after 90 s
    note: str = ""  # what it shows, and which canonical method it names
    sources: tuple[str, ...] = field(default=())  # what its golden tests validate against


_REGISTRY: dict[str, FaceSpec] = {}


def register(spec: FaceSpec) -> FaceSpec:
    if spec.key in _REGISTRY:
        raise ValueError(f"duplicate face key: {spec.key!r}")
    if spec.category not in CATEGORIES:
        raise ValueError(f"unknown category {spec.category!r} for face {spec.key!r}")
    if spec.status not in STATUSES:
        raise ValueError(f"unknown status {spec.status!r} for face {spec.key!r}")
    if spec.status == LIVE and spec.render is None:
        raise ValueError(f"face {spec.key!r} is live but has no render function")
    if spec.status != LIVE and spec.render is not None:
        raise ValueError(f"face {spec.key!r} is not live but already has a render function")
    _REGISTRY[spec.key] = spec
    return spec


def all_faces() -> list[FaceSpec]:
    return sorted(_REGISTRY.values(), key=lambda s: (CATEGORIES.index(s.category), s.order))


def live_faces() -> list[FaceSpec]:
    """Only the faces that actually exist — what the button cycles."""
    return [s for s in all_faces() if s.status == LIVE]


def committed_faces() -> list[FaceSpec]:
    """What the donated clock is intended to have. Finite and finishable."""
    return [s for s in all_faces() if s.status == COMMITTED]


def get(key: str) -> FaceSpec:
    return _REGISTRY[key]


def default_face() -> FaceSpec:
    """The face the clock rests on.

    Falls back to the first live face while the intended default is still unbuilt, so
    the clock always has something to show during the build-out.
    """
    live = live_faces()
    if not live:
        raise RuntimeError("no live faces registered")
    for spec in live:
        if spec.is_default:
            return spec
    return live[0]


def next_face(current_key: str) -> FaceSpec:
    """Short press: the next live face within the same category, wrapping."""
    live = live_faces()
    same = [s for s in live if s.category == get(current_key).category]
    if len(same) <= 1:
        return _advance(live, current_key)
    keys = [s.key for s in same]
    return same[(keys.index(current_key) + 1) % len(same)]


def next_category(current_key: str) -> FaceSpec:
    """Long press: the first live face of the next category that has one."""
    live = live_faces()
    start = CATEGORIES.index(get(current_key).category)
    for step in range(1, len(CATEGORIES) + 1):
        category = CATEGORIES[(start + step) % len(CATEGORIES)]
        in_category = [s for s in live if s.category == category]
        if in_category:
            return in_category[0]
    return get(current_key)


def _advance(live: list[FaceSpec], current_key: str) -> FaceSpec:
    keys = [s.key for s in live]
    if current_key not in keys:
        return live[0]
    return live[(keys.index(current_key) + 1) % len(live)]


# --------------------------------------------------------------------------- #
# THE CATALOGUE
#
# The original design brief, plus Lanna. Face 0 is Lanna-rooted by intent: this clock
# stands in a Lanna wat, so the date a passer-by reads is the one their own tradition
# keeps, with central Thai BE below it.
#
# Anything not in this list is not a shortfall. See docs/GROWING.md.
# --------------------------------------------------------------------------- #

from . import lanna as _lanna  # noqa: E402
from . import main as _main  # noqa: E402  (registered below; needs register())
from . import phase0 as _phase0  # noqa: E402

# --- core ------------------------------------------------------------------
register(
    FaceSpec(
        key="main",
        title_en="Main",
        title_th="หน้าปัดหลัก",
        category="core",
        order=0,
        is_default=True,
        render=_main.render,
        status=LIVE,
        note=(
            "Analog dial + HH:MM; Lanna date primary (Chulasakarat era, Lanna month, "
            "waxing/waning day); central Thai BE below; CE small; moon phase; next "
            "coucal call; battery / time-confidence / heartbeat glyphs."
        ),
    )
)

# --- calendar --------------------------------------------------------------
register(
    FaceSpec(
        key="lanna",
        title_en="Lanna",
        title_th="ล้านนา",
        category="calendar",
        order=0,
        render=_lanna.render,
        status=LIVE,
        note=(
            "Full Lanna reckoning: Chulasakarat year, 60-year cycle, Lanna month "
            "numbering (runs ~2 months ahead of central Thai), day qualities."
        ),
        sources=("Lanna manuscript corpus (own digitisation)", "Lanna almanac tradition"),
    )
)
register(
    FaceSpec(
        key="thai",
        title_en="Thai",
        title_th="ไทย",
        category="calendar",
        order=1,
        note="BE date, waxing/waning day, wan phra, 12-year animal cycle, thaksa.",
        sources=("Official Thai calendar (bundled authority table)", "Eade calendrical rules"),
    )
)
register(
    FaceSpec(
        key="panchanga",
        title_en="Panchanga",
        title_th="ปัญจางค์",
        category="calendar",
        order=2,
        note="Tithi, vara, nakshatra+pada, yoga, karana; rahu kala; Lahiri sidereal.",
        sources=("Drik Panchang, Chiang Mai coordinates",),
    )
)
register(
    FaceSpec(
        key="taoist",
        title_en="Taoist",
        title_th="เต๋า",
        category="calendar",
        order=3,
        note="Four pillars, five elements, jieqi solar term, 28 xiu, Plum Blossom hexagram.",
        sources=("Hong Kong Observatory conversion tables",),
    )
)
register(
    FaceSpec(
        key="babylonian",
        title_en="Babylonian",
        title_th="บาบิโลน",
        category="calendar",
        order=4,
        note=(
            "Sexagesimal time, lunar day from first crescent (Yallop), "
            "Metonic position, Saros series of the next local eclipse."
        ),
    )
)
register(
    FaceSpec(
        key="hellenistic",
        title_en="Hellenistic",
        title_th="กรีก",
        category="calendar",
        order=5,
        note=(
            "Planetary day ruler and unequal hour, decan, Lots of Fortune/Spirit, "
            "Antikythera Metonic and Saros dials."
        ),
    )
)

# --- divination ------------------------------------------------------------
register(
    FaceSpec(
        key="pythagorean",
        title_en="Pythagorean",
        title_th="พีทาโกรัส",
        category="divination",
        order=0,
        note="Tetractys of the date's digital root; monochord ratio of the day-fraction.",
    )
)
register(
    FaceSpec(
        key="compass",
        title_en="Compass",
        title_th="เข็มทิศ",
        category="divination",
        order=1,
        note=(
            "One rose at true installed heading: thaksa, lo pan 24 mountains, vastu "
            "guardians, Greek anemoi. Declination-corrected; says so when stale."
        ),
    )
)
register(
    FaceSpec(
        key="reserved",
        title_en="(the unopened door)",
        title_th="(ประตูที่ยังไม่เปิด)",
        category="divination",
        order=9,
        status=OPEN,
        note=(
            "Deliberately empty, and deliberately never scheduled. Reserved for a "
            "tradition nobody has added yet. A merit offering should leave room for "
            "the future to speak into it. Explained in MAINTENANCE.md so that whoever "
            "cares for the clock knows the emptiness is intended, not a fault."
        ),
    )
)

# --- meta ------------------------------------------------------------------
register(
    FaceSpec(
        key="phase0",
        title_en="Diagnostic",
        title_th="ตรวจสอบ",
        category="meta",
        order=9,
        render=_phase0.render,
        status=LIVE,
        note="Pipeline self-test; also the boot self-test face.",
    )
)
