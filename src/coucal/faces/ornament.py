"""Lanna ornament — the drawing vocabulary the Northern faces are built from.

Not decoration applied afterwards. These are the motifs a Lanna carver or manuscript
illuminator actually uses, reduced to line and repetition so they survive at 16 greys on
e-ink and read at two metres:

* **naga (นาค)** — the serpent that guards every wat stair and temple gable. Here a
  running scale-and-crest border, the way it edges a manuscript panel.
* **lai kanok (ลายกนก)** — the flame-tendril, the fundamental Thai/Lanna decorative
  curve, used as a corner spandrel.
* **lotus (บัว)** — the seat, the offering. Used for the dial hub and for marking.
* **dhamma wheel spokes** — radial division, which is also how a dial marks its hours.

Everything is drawn in semantic inks and pure geometry: no bitmaps, no fonts, nothing
that can fail to load. A stranger in 2096 can read this file and see exactly what is
being drawn and why.
"""

from __future__ import annotations

import math

from .base import Canvas
from .palette import Ink


def polar(cx: float, cy: float, r: float, deg_from_12: float) -> tuple[float, float]:
    """A point on a circle, measured clockwise from twelve o'clock."""
    a = math.radians(deg_from_12 - 90.0)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def naga_ring(
    c: Canvas,
    cx: float,
    cy: float,
    r: float,
    *,
    scales: int = 72,
    depth: float = 13.0,
    ink=Ink.FAINT,
) -> None:
    """A naga's back running around a circle — paired arcs raised into a crest.

    Each 'scale' is a small arc stepped alternately in and out, so the eye reads a
    serpent's spine rather than a dotted line. Two containing rules keep it a border
    rather than a texture.
    """
    c.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ink, width=2)
    inner = r - depth
    c.ellipse([cx - inner, cy - inner, cx + inner, cy + inner], outline=ink, width=2)

    step = 360.0 / scales
    for i in range(scales):
        a0 = i * step
        mid = a0 + step / 2
        # Alternate the crest in and out to give the spine its rhythm.
        peak = r if i % 2 == 0 else inner
        trough = inner if i % 2 == 0 else r
        x0, y0 = polar(cx, cy, trough, a0)
        x1, y1 = polar(cx, cy, peak, mid)
        x2, y2 = polar(cx, cy, trough, a0 + step)
        c.line([(x0, y0), (x1, y1)], fill=ink, width=2)
        c.line([(x1, y1), (x2, y2)], fill=ink, width=2)


def kanok_corner(
    c: Canvas, x: float, y: float, size: float, *, quadrant: int = 0, ink=Ink.FAINT
) -> None:
    """A flame-tendril spandrel (ลายกนก) tucked into a corner.

    Built as a family of nested quarter-spirals springing from the corner — the
    characteristic Lanna curl, drawn thin so it frames without shouting.
    """
    # quadrant: 0 = top-left, 1 = top-right, 2 = bottom-right, 3 = bottom-left
    sx = 1 if quadrant in (0, 3) else -1
    sy = 1 if quadrant in (0, 1) else -1

    for k, scale in enumerate((1.0, 0.72, 0.48, 0.3)):
        s = size * scale
        pts = []
        # A quarter of a logarithmic-ish spiral: radius eases as the angle sweeps.
        steps = 26
        for i in range(steps + 1):
            t = i / steps
            ang = math.radians(90.0 * t)
            rad = s * (0.25 + 0.75 * (1.0 - t) ** 1.6)
            px = x + sx * (s - rad * math.cos(ang))
            py = y + sy * (s - rad * math.sin(ang))
            pts.append((px, py))
        width = 3 if k == 0 else 2
        for a, b in zip(pts, pts[1:], strict=False):
            c.line([a, b], fill=ink, width=width)


def lotus_hub(c: Canvas, cx: float, cy: float, r: float, *, petals: int = 8) -> None:
    """A lotus seat, used where a dial would otherwise have a plain hub."""
    half = 360.0 / (petals * 2)
    for i in range(petals):
        ang = i * (360.0 / petals)
        # Each petal is a filled lozenge: base, two shoulders, tip. Thin outlines read
        # as a spiky star at dial scale; filled petals read as a flower.
        base = polar(cx, cy, r * 0.20, ang)
        tip = polar(cx, cy, r, ang)
        left = polar(cx, cy, r * 0.66, ang - half * 0.85)
        right = polar(cx, cy, r * 0.66, ang + half * 0.85)
        c.draw.polygon([base, left, tip, right], fill=c.ink(Ink.PRIMARY))
    c.ellipse(
        [cx - r * 0.32, cy - r * 0.32, cx + r * 0.32, cy + r * 0.32],
        fill=Ink.PRIMARY,
    )


def rays(
    c: Canvas,
    cx: float,
    cy: float,
    r_inner: float,
    r_outer: float,
    *,
    count: int = 12,
    offset_deg: float = 0.0,
    ink=Ink.FAINT,
    width: int = 2,
) -> None:
    """Radial division — the spokes of a wheel, the divisions of a dial."""
    for i in range(count):
        ang = offset_deg + i * (360.0 / count)
        c.line([polar(cx, cy, r_inner, ang), polar(cx, cy, r_outer, ang)], fill=ink, width=width)


def moon_disc(c: Canvas, cx: float, cy: float, r: float, illumination: float, waxing: bool) -> None:
    """The moon as it actually appears tonight.

    Unlit disc, then the lit half, then a terminator ellipse either carved out of the
    lit half (crescent) or added to it (gibbous).
    """
    k = max(0.0, min(1.0, illumination))
    c.ellipse([cx - r, cy - r, cx + r, cy + r], fill=Ink.FAINT, outline=Ink.PRIMARY, width=3)
    start, end = (-90, 90) if waxing else (90, 270)
    c.draw.pieslice([cx - r, cy - r, cx + r, cy + r], start, end, fill=c.ink(Ink.PAPER))

    half_width = r * abs(1.0 - 2.0 * k)
    if half_width > 1:
        c.ellipse(
            [cx - half_width, cy - r, cx + half_width, cy + r],
            fill=Ink.FAINT if k < 0.5 else Ink.PAPER,
        )
    c.ellipse([cx - r, cy - r, cx + r, cy + r], outline=Ink.PRIMARY, width=3)


# --------------------------------------------------------------------------- #
# Guilloche — engine turning
#
# The faint, endlessly-repeating engraved field that gives a fine watch dial its depth.
# Traditionally cut on a rose engine; here generated as hypotrochoids, which is the same
# mathematics the machine performs mechanically.
#
# It must stay *faint*. Guilloche is felt before it is seen: at two metres it should read
# as a subtle tone on the dial, never as pattern competing with the reading.
# --------------------------------------------------------------------------- #


def guilloche_rosette(
    c: Canvas,
    cx: float,
    cy: float,
    r: float,
    *,
    petals: int = 12,
    depth: float = 0.26,
    passes: int = 3,
    ink=Ink.FAINT,
    clip_r: float | None = None,
) -> None:
    """A rose-engine rosette: nested hypotrochoid curves.

    ``petals`` sets the fold symmetry (12 here, to agree with the twelve hours, the
    twelve months and the twelve-year cycle). Each pass is a slightly smaller curve, so
    the field reads as turned metal rather than a single outline.
    """
    limit = clip_r if clip_r is not None else r
    for p in range(passes):
        scale = 1.0 - p * (0.16 / max(1, passes - 1) if passes > 1 else 0)
        rr = r * scale
        amp = rr * depth
        pts = []
        steps = 720
        for i in range(steps + 1):
            t = 2.0 * math.pi * i / steps
            rad = rr - amp + amp * math.cos(petals * t)
            if rad > limit:
                rad = limit
            pts.append((cx + rad * math.cos(t), cy + rad * math.sin(t)))
        for a, b in zip(pts, pts[1:], strict=False):
            c.line([a, b], fill=ink, width=1)


def sri_yantra_field(
    c: Canvas,
    cx: float,
    cy: float,
    r: float,
    *,
    sides: int = 12,
    ink=Ink.FAINT,
    clip_r: float | None = None,
) -> None:
    """A twelve-sided yantra field, drawn as the dial's engraved ground.

    The Sri Yantra's structure is interpenetrating triangles — one family pointing up
    (Shiva), one down (Shakti) — enclosed by lotus petals and a square earth-precinct
    with four gates. This is a *twelve-sided* reading of that structure rather than a
    reproduction: the enclosure is a dodecagon, agreeing with the twelve hours and the
    twelve-year cycle already on the face, and the triangle families are drawn at
    twelve-fold symmetry.

    Kept deliberately faint. It is the ground the readings sit on, not an object of
    contemplation in its own right — this is a clock in a Buddhist wat, and the motif
    is here as engine-turning, in the register of a dial, not as a ritual diagram.
    """
    limit = clip_r if clip_r is not None else r

    def poly(radius: float, n: int, rotate: float = 0.0, width: int = 1) -> None:
        pts = [
            (
                cx + min(radius, limit) * math.cos(2 * math.pi * i / n + rotate),
                cy + min(radius, limit) * math.sin(2 * math.pi * i / n + rotate),
            )
            for i in range(n)
        ]
        for a, b in zip(pts, pts[1:] + pts[:1], strict=False):
            c.line([a, b], fill=ink, width=width)

    # The enclosing dodecagon, twice, for a bhupura-like precinct.
    poly(r, sides)
    poly(r * 0.94, sides, rotate=math.pi / sides)

    # Interpenetrating triangle families. Alternating rotation makes them interlock the
    # way the yantra's do, without pretending to be the true nine-triangle construction.
    for k, radius in enumerate((0.84, 0.62, 0.42)):
        up = k % 2 == 0
        rot = 0.0 if up else math.pi / 3
        poly(r * radius, 3, rotate=rot)
        poly(r * radius, 3, rotate=rot + math.pi / 3)

    # A small central bindu circle to close the figure.
    br = min(r * 0.06, limit)
    c.ellipse([cx - br, cy - br, cx + br, cy + br], outline=ink, width=1)


# --------------------------------------------------------------------------- #
# The moon complication
#
# THE MOVEMENT. One disc carries TWO moons, 180 deg apart, and makes ONE FULL 360 deg
# TURN PER TWO LUNATIONS — 180 deg a month. That is the only rate consistent with two
# moons: one crosses the aperture this month, its partner the next. The disc's angle
# comes from :mod:`coucal.almanac.lunation`, which re-datums it at every true new moon,
# so nothing accumulates and nothing drifts.
#
#     theta_i = disc_angle - 90 + 180*i
#     moon_i  = (DISC_R*sin(theta_i), DISC_CY - DISC_R*cos(theta_i))
#
# The crossing moon rises from behind the LEFT hump, arcs over the top (full at the
# notch), and sets behind the RIGHT — one synodic month. Its partner spends that month
# beneath the plate. At new moon one is setting as the other rises and BOTH are hidden,
# which is why the plate has to cover so much of the viewport.
#
# THE PROPORTIONS. Fitted numerically against the moon's real illumination,
# (1 - cos alpha)/2, with the design requirements as hard constraints:
#
#     moon slightly SMALLER than the cloud     MOON_R / HUMP_R = 0.82
#     plate covers most of the frame           71%
#     a visible notch between the humps        gap 0.28 of a viewport radius
#     the humps clip the moon, never the rim   rim share 0.00%
#     the partner never shows                  0.00%
#
# Result: RMS 0.0037 against real illumination, worst 1.1 percentage points. Note the
# larger moon turned out to be *more* accurate as well as more legible, so there was no
# trade to make between the two.
#
# Equal-ish radii are what make the crescent: two circles of comparable size intersect
# in a lune with horns, where a much larger occluder would cut a flat-edged D.
# --------------------------------------------------------------------------- #

MOON_R = 0.3508  # moon radius, in viewport radii
HUMP_R = 0.4266  # cloud radius — deliberately a little larger than the moon
HUMP_X = 0.7083  # the humps stand this far either side of the middle...
PLATE_Y = -0.0894  # ...on the plate's straight top edge, just above the dial centre
DISC_R = 0.5506  # radius of the disc carrying the two moons
DISC_CY = 0.0708  # its centre, essentially the middle of the dial


def crossing_index(disc_angle_deg: float) -> int:
    """Which of the disc's two moons is the one crossing the aperture."""
    return 0 if (disc_angle_deg % 360.0) < 180.0 else 1


def moon_position(disc_angle_deg: float, index: int = 0) -> tuple[float, float]:
    """Centre of one of the disc's two moons, in viewport units (y down)."""
    theta = math.radians(disc_angle_deg - 90.0 + 180.0 * index)
    return (DISC_R * math.sin(theta), DISC_CY - DISC_R * math.cos(theta))


def moon_visible_fraction(
    disc_angle_deg: float, index: int | None = None, n_r: int = 12, n_t: int = 32
) -> float:
    """Fraction of a moon's disc left visible by the plate and its two humps.

    ``index`` defaults to whichever moon is crossing. Pure geometry on an equal-area
    grid — the function the accuracy tests check, and the one the fit minimised.
    """
    if index is None:
        index = crossing_index(disc_angle_deg)
    mx, my = moon_position(disc_angle_deg, index)
    total = visible = 0
    for i in range(n_r):
        r = MOON_R * math.sqrt((i + 0.5) / n_r)
        for j in range(n_t):
            t = 2.0 * math.pi * j / n_t
            px, py = mx + r * math.cos(t), my + r * math.sin(t)
            total += 1
            if px * px + py * py > 1.0:
                continue  # the viewport rim — unreachable by construction
            if py > PLATE_Y:
                continue  # behind the plate
            if (px + HUMP_X) ** 2 + (py - PLATE_Y) ** 2 < HUMP_R * HUMP_R:
                continue  # behind the left hump
            if (px - HUMP_X) ** 2 + (py - PLATE_Y) ** 2 < HUMP_R * HUMP_R:
                continue  # behind the right hump
            visible += 1
    return visible / total


def moon_complication(
    c: Canvas,
    cx: float,
    cy: float,
    radius: float,
    disc_angle_deg: float,
) -> None:
    """A moon-phase aperture: two moons on a turning disc behind a humped plate.

    Takes the gear's angle, not a phase — the mechanism is the thing being drawn.
    Rendered on a layer and pasted through a circular mask, so every edge is a true
    clip rather than a painted seam.
    """
    from PIL import Image, ImageDraw

    size = int(radius * 2)
    r = radius
    layer = Image.new("L", (size, size), color=c.ink(Ink.FAINT))  # the night sky
    d = ImageDraw.Draw(layer)
    paper, primary = c.ink(Ink.PAPER), c.ink(Ink.PRIMARY)
    engraving = c.ink(Ink.ENGRAVING)

    def L(x: float, y: float) -> tuple[float, float]:
        return (r + x * r, r + y * r)

    def disc(x: float, y: float, rad: float, **kw) -> None:
        px, py = L(x, y)
        rr = rad * r
        d.ellipse([px - rr, py - rr, px + rr, py + rr], **kw)

    # Stars, fixed in the sky above the plate.
    for fx, fy, sr in (
        (-0.58, -0.58, 6),
        (0.58, -0.54, 5),
        (-0.20, -0.86, 5),
        (0.24, -0.82, 4),
        (-0.84, -0.20, 5),
        (0.84, -0.16, 4),
        (0.02, -0.62, 4),
    ):
        sx, sy = L(fx, fy)
        for i in range(3):
            a = math.pi * i / 3
            d.line(
                [
                    (sx - sr * math.cos(a), sy - sr * math.sin(a)),
                    (sx + sr * math.cos(a), sy + sr * math.sin(a)),
                ],
                fill=paper,
                width=2,
            )

    # Both moons of the disc. The partner is under the plate and will be covered.
    mr = MOON_R * r
    for index in (1, 0):
        mx, my = moon_position(disc_angle_deg, index)
        mcx, mcy = L(mx, my)
        d.ellipse([mcx - mr, mcy - mr, mcx + mr, mcy + mr], fill=paper, outline=primary, width=3)
        eye = mr * 0.13
        for sx in (-0.30, 0.30):
            ex, ey = mcx + mr * sx, mcy - mr * 0.24
            d.ellipse([ex - eye, ey - eye, ex + eye, ey + eye], fill=primary)
        m = mr * 0.44
        d.arc(
            [mcx - m, mcy - m * 0.32, mcx + m, mcy + m * 1.05],
            start=20,
            end=160,
            fill=primary,
            width=max(2, int(mr * 0.11)),
        )

    # The stationary plate: a straight edge with two humps standing on it.
    _, gy = L(0.0, PLATE_Y)
    d.rectangle([0, gy, size, size], fill=paper)
    for sign in (-1.0, 1.0):
        disc(sign * HUMP_X, PLATE_Y, HUMP_R, fill=paper)
    for sign in (-1.0, 1.0):
        px, py = L(sign * HUMP_X, PLATE_Y)
        hr = HUMP_R * r
        d.arc([px - hr, py - hr, px + hr, py + hr], start=180, end=360, fill=primary, width=3)
        for fx, fy, fr in ((-0.36, 0.30, 0.20), (0.02, 0.16, 0.24), (0.40, 0.34, 0.18)):
            qx, qy = L(sign * HUMP_X + fx * HUMP_R, PLATE_Y + fy * HUMP_R)
            qr = fr * HUMP_R * r
            d.arc([qx - qr, qy - qr, qx + qr, qy + qr], start=195, end=115, fill=engraving, width=2)
    for x0, x1 in (
        (-1.0, -HUMP_X - HUMP_R),
        (-HUMP_X + HUMP_R, HUMP_X - HUMP_R),
        (HUMP_X + HUMP_R, 1.0),
    ):
        if x1 > x0:
            d.line([L(x0, PLATE_Y), L(x1, PLATE_Y)], fill=primary, width=3)

    # Clip to the circular viewport, then set the bezel.
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
    c.image.paste(layer, (int(cx - r), int(cy - r)), mask)
    c.ellipse([cx - r, cy - r, cx + r, cy + r], outline=Ink.PRIMARY, width=4)
    o = r + 9
    c.ellipse([cx - o, cy - o, cx + o, cy + o], outline=Ink.FAINT, width=2)


# --------------------------------------------------------------------------- #
# The twelve zodiac animals, as tiny woodcut stamps
#
# Pure stroke-drawings in a unit square, so they stay crisp at any size and need no
# assets. The style aims at the little animals on a Lanna temple mural: friendly,
# simple, unmistakably each their own beast.
#
# Two are deliberately NORTHERN readings, matching the Lanna cycle the band names:
#   index 4 (สี)   — the GREAT SERPENT / naga, not the Chinese dragon
#   index 11 (ไก๊) — an ELEPHANT: Northern iconography replaces the pig with the
#                    elephant. Documented tradition; verify against the corpus
#                    before donation, like every iconographic choice on this face.
#
# Ops: ("c", x, y, r) circle · ("d", x, y, r) filled dot · ("e", x0,y0,x1,y1) ellipse
#      ("l", pts) polyline · ("a", x, y, r, start, end) arc (PIL degrees)
# --------------------------------------------------------------------------- #

ZODIAC_STROKES: dict[int, tuple] = {
    0: (  # ไจ้ — rat: round body, big ear, curling tail
        ("c", 0.10, 0.20, 0.46),
        ("c", -0.34, -0.38, 0.20),
        ("d", -0.05, 0.02, 0.06),
        ("a", 0.58, 0.40, 0.20, 240, 90),
    ),
    1: (  # เป้า — ox: broad face, up-curved horns, nostrils
        ("c", 0.0, 0.18, 0.42),
        ("a", -0.42, -0.10, 0.30, 80, 230),
        ("a", 0.42, -0.10, 0.30, 310, 100),
        ("d", -0.12, 0.30, 0.05),
        ("d", 0.12, 0.30, 0.05),
        ("d", -0.16, 0.02, 0.05),
        ("d", 0.16, 0.02, 0.05),
    ),
    2: (  # ยี — tiger: ears and forehead stripes
        ("c", 0.0, 0.05, 0.48),
        ("c", -0.40, -0.38, 0.15),
        ("c", 0.40, -0.38, 0.15),
        ("l", ((-0.16, -0.30), (-0.10, -0.10))),
        ("l", ((0.0, -0.34), (0.0, -0.12))),
        ("l", ((0.16, -0.30), (0.10, -0.10))),
        ("d", -0.17, 0.05, 0.05),
        ("d", 0.17, 0.05, 0.05),
        ("d", 0.0, 0.26, 0.06),
    ),
    3: (  # เหม้า — rabbit: the ears say it all
        ("c", 0.0, 0.34, 0.34),
        ("e", -0.40, -0.88, -0.10, -0.02),
        ("e", 0.10, -0.88, 0.40, -0.02),
        ("d", -0.12, 0.28, 0.05),
        ("d", 0.12, 0.28, 0.05),
    ),
    4: (  # สี — the great serpent (naga): undulating body, crested head
        (
            "l",
            (
                (-0.62, 0.52),
                (-0.44, 0.30),
                (-0.26, 0.52),
                (-0.08, 0.30),
                (0.10, 0.52),
                (0.28, 0.30),
            ),
        ),
        ("l", ((0.28, 0.30), (0.36, 0.02))),
        ("c", 0.40, -0.10, 0.17),
        ("l", ((0.28, -0.30), (0.40, -0.56), (0.54, -0.28))),
        ("d", 0.45, -0.11, 0.05),
    ),
    5: (  # ไส้ — the snake: same river, no crest, a flicked tongue
        (
            "l",
            (
                (-0.60, 0.34),
                (-0.42, 0.12),
                (-0.24, 0.34),
                (-0.06, 0.12),
                (0.12, 0.34),
                (0.30, 0.16),
            ),
        ),
        ("c", 0.42, 0.12, 0.13),
        ("l", ((0.54, 0.10), (0.68, 0.04))),
        ("d", 0.44, 0.10, 0.04),
    ),
    6: (  # สะง้า — horse: long head in profile, ear, mane
        (
            "l",
            (
                (-0.18, -0.52),
                (0.46, 0.10),
                (0.34, 0.38),
                (-0.10, 0.28),
                (-0.34, -0.02),
                (-0.18, -0.52),
            ),
        ),
        ("l", ((-0.18, -0.52), (-0.04, -0.72), (0.06, -0.44))),
        ("l", ((-0.30, -0.28), (-0.52, -0.10))),
        ("l", ((-0.24, -0.02), (-0.48, 0.14))),
        ("d", 0.05, -0.10, 0.05),
    ),
    7: (  # เม็ด — goat: back-swept horns and a little beard
        ("c", 0.0, 0.22, 0.36),
        ("a", -0.34, -0.26, 0.30, 40, 220),
        ("a", 0.34, -0.26, 0.30, 320, 140),
        ("l", ((0.0, 0.58), (0.0, 0.80))),
        ("d", -0.13, 0.16, 0.05),
        ("d", 0.13, 0.16, 0.05),
    ),
    8: (  # สัน — monkey: round face, side ears, muzzle
        ("c", 0.0, 0.0, 0.40),
        ("c", -0.50, 0.02, 0.14),
        ("c", 0.50, 0.02, 0.14),
        ("c", 0.0, 0.16, 0.20),
        ("d", -0.14, -0.12, 0.05),
        ("d", 0.14, -0.12, 0.05),
    ),
    9: (  # เร้า — rooster: comb, beak, tail plumes
        ("c", 0.10, 0.22, 0.36),
        ("c", -0.28, -0.26, 0.17),
        ("l", ((-0.42, -0.38), (-0.36, -0.60), (-0.27, -0.42), (-0.18, -0.62), (-0.10, -0.40))),
        ("l", ((-0.44, -0.24), (-0.62, -0.18), (-0.44, -0.14))),
        ("a", 0.52, 0.02, 0.30, 150, 300),
        ("a", 0.56, 0.18, 0.24, 160, 310),
        ("d", -0.30, -0.28, 0.04),
    ),
    10: (  # เส็ด — dog: one floppy ear and a smile
        ("c", 0.04, 0.04, 0.40),
        ("e", -0.60, -0.30, -0.36, 0.22),
        ("d", 0.16, 0.20, 0.06),
        ("d", -0.06, -0.06, 0.05),
        ("d", 0.26, -0.06, 0.05),
        ("a", 0.10, 0.32, 0.14, 20, 160),
    ),
    11: (  # ไก๊ — ELEPHANT (Northern variant for the pig year): ear, head, trunk
        ("a", 0.26, -0.02, 0.30, 290, 130),
        ("c", -0.10, 0.0, 0.36),
        ("l", ((-0.44, 0.10), (-0.58, 0.36), (-0.54, 0.62), (-0.36, 0.70))),
        ("d", -0.18, -0.08, 0.05),
    ),
}


def zodiac_glyph(
    c: Canvas, cx: float, cy: float, size: float, index: int, *, ink=Ink.SECONDARY
) -> None:
    """Draw one of the twelve year-animals as a small stamp, centred at (cx, cy)."""
    s = size / 2.0
    colour = c.ink(ink)
    width = max(2, int(size * 0.05))

    for op in ZODIAC_STROKES[index % 12]:
        kind = op[0]
        if kind == "c":
            _, x, y, r = op
            c.draw.ellipse(
                [cx + (x - r) * s, cy + (y - r) * s, cx + (x + r) * s, cy + (y + r) * s],
                outline=colour,
                width=width,
            )
        elif kind == "d":
            _, x, y, r = op
            c.draw.ellipse(
                [cx + (x - r) * s, cy + (y - r) * s, cx + (x + r) * s, cy + (y + r) * s],
                fill=colour,
            )
        elif kind == "e":
            _, x0, y0, x1, y1 = op
            c.draw.ellipse(
                [cx + x0 * s, cy + y0 * s, cx + x1 * s, cy + y1 * s],
                outline=colour,
                width=width,
            )
        elif kind == "l":
            _, pts = op
            c.draw.line(
                [(cx + x * s, cy + y * s) for x, y in pts], fill=colour, width=width, joint="curve"
            )
        elif kind == "a":
            _, x, y, r, start, end = op
            c.draw.arc(
                [cx + (x - r) * s, cy + (y - r) * s, cx + (x + r) * s, cy + (y + r) * s],
                start=start,
                end=end,
                fill=colour,
                width=width,
            )
