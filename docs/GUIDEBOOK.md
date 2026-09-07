# The Guidebook — making this clock more awesome

Written after a gemba walk of the product and a review of every defect found while
building it. This is an operating manual for whoever works on the clock next — the
rules are extracted from real failures, each one paid for, and the craft directions
follow the project's own law: **doors, not debts**.

---

## Part 1 — The defect ledger, distilled into rules

Every rule below exists because the mistake actually happened in this repository.

### 1. Built is not shipped. Reachable is shipped.
The Lanna face was written, registered, calendar-tested, screenshot-baselined — and
**unreachable**. Nothing consumed the button; the loop always drew the default face.
Every test passed. *Rule:* after building anything, walk to it through the product's
own controls, in the running product. Enforced: `test_pressing_reaches_every_live_face`.

### 2. Every timed behaviour obeys exactly one clock. Name it.
The 90-second auto-return counted *virtual* seconds, so a one-day time-warp read as
86,400 seconds of idleness and booted the reviewer home. *Rule:* for each timed
behaviour, decide whose clock it obeys — **the sky's** (almanac, coucal calls, moon)
or **the human's** (interaction, auto-return) — and write the choice down at the call
site. On the device they coincide; in the simulator they diverge wildly, which is what
makes the simulator good at exposing the confusion.

### 3. Reproduce the STRUCTURE, not just the behaviour — and it may be exact.
The moon aperture was rebuilt six times. Illumination-driven position; a straight slide;
a rotary path; a rotary path with moon-sized clouds; one moon on a full revolution. Each
was a guess at the *shape* of a mechanism I had not actually drawn out, and each was
fitted numerically until the numbers looked good — RMS 0.021 at best, with a
"the residual is inherent" comment excusing it.

Then the user sketched the geometry: a stationary plate with a straight top edge, two
humps standing on it, a notch between, and a disc of two moons behind. Fitted to *that*
structure, the error fell to **RMS 0.0045, worst 0.7 points** — a factor of five better,
instantly. (The shipped dial keeps a different arrangement, chosen for its full monthly
revolution; the measurement stands either way, and both are recorded in `ornament.py`.)

Two lessons, and the second is the sharper one:

*Rule (a):* when imitating an instrument, get its actual **construction** — the parts and
how they are arranged — before touching parameters. No amount of fitting rescues a wrong
structure, and a good fit on a wrong structure is a trap: it produces plausible numbers
and a "this residual is inherent" story that is simply false.

*Rule (b):* **do not assume the old design is a compromise.** I twice wrote that
mechanical moonphases are "geometric approximations" and bounded my error accordingly.
They are not. The optimiser, free to pick any hump-to-moon radius ratio from 0.75 to
1.45, converged on **1.00** — it rediscovered the watchmakers' proportion, because equal
radii intersect in a lune that tracks real illumination to under a percentage point. The
tradition had the exact answer; I had been grading my own approximation against itself.

### 3d. Measure the naive version before you build on it.
The moon dial was to be driven by a gear re-synced monthly. The obvious implementation —
advance at a constant rate through the month — was measured first: **10.65° out, 8.4
points of illumination**, because the synodic month varies by half a day. That is eight
times the dial's own geometric error, so it would have silently become the whole error
budget. Driving the fraction from the true elongation instead costs nothing. *Rule:*
before adopting a simplification, measure what it costs against the thing it replaces —
and compare it to the error budget you already have, not to zero.

### 4. Derived-by-hand drifts. Derive by code, anchor on published truth.
Hand-written festival names were wrong twice (เดือนสี่เป็ง for what is เดือนห้าเป็ง); the
doubled month mapped 8b→12 instead of 8b→10; Asalha appeared on both eighth months.
*Rule:* anything that can be derived from a datum must be derived — and the derivation
must be re-verified at every published anchor (the 50-row Thai PBS table; Yi Peng =
เดือนยี่ full moon).

### 5. Measure the artifact. Descriptions lie.
The brief said "de440s covers 1550–2650" — de440s covers 1849–2150; the horizon belongs
to full de440. Waveshare's Spectra 6 page advertises partial refresh — the technology
has none. The notofonts repos "contain the fonts" — sources only, no TTFs. IGRF-13 was
specified — already expired. *Rule:* download the file, read its span, checksum it,
record what was measured (`data/ephemeris/PROVENANCE.md` is the pattern).

### 6. Ornament needs a governor.
The first guilloche pass shouted over the numerals. *Rule:* decoration gets its own
semantic ink (`Ink.ENGRAVING`), lighter than any reading ink, and an **ink budget test**
(ground < 12% of the dial). Guilloche is felt before it is seen.

### 7. Lay out text by measurement, never by guessed offset.
"ค่ำ" collided with the numeral the moment ๖ became ๑๕. Thai varies in width far more
than Latin. *Rule:* `Canvas.measure()` first, position second.

### 8. State transitions deserve their own display policy.
Switching faces under partial refresh left the old face ghosted beneath the new one —
visible smudge on a real screenshot. *Rule:* a transition that rewrites the panel earns
a full refresh; steady-state updates stay partial.

### 9. The honest gap beats the plausible guess.
Outside the authority table the clock says **บ่ฮู้ข้างขึ้นข้างแฮม** rather than inventing a
month. The 60-name มื้อ cycle is absent until an epoch anchor is verified. *Rule:* on a
sacred object, absence is dignified; a confident error is not. Show the limit, in the
reader's language.

### 10. Validate against the phenomenon, not against your own threshold.
The moon complication shipped with a test asserting the "looks full" band at a
**self-chosen 0.985 visibility threshold** — where it scored 4.4 days and passed. At
every threshold a human actually uses it was catastrophic: 7.8 days at 95%, 9.9 at 90%,
against the real moon's 4.2 and 6.0. The test was measuring my model against my own
tolerance, so it could not fail. *Rule:* find the external ground truth the thing is
imitating — here, illumination = (1 − cos α)/2 — and score against **that**, across the
whole range, not at a threshold you picked. If no external truth exists, you do not yet
understand what you are building.

### 11. Verification means driving the product, not the function.
The face-reachability bug survived 155 passing tests because every test exercised parts
in isolation. *Rule:* before claiming, run the simulator headless, press the controls,
warp the year, and look at the PNG with your own eyes. The screenshot the user sends
should never be the first time anyone looked.

---

## Part 2 — The gemba drill

Before claiming any visual or behavioural change:

1. **Render the states, not the state**: ordinary day · วันศีล · festival (Yi Peng) ·
   degraded (no GPS, low battery, no ephemeris, out-of-table date). Look at each.
2. **Drive the real simulator** (headless Tk is fine): press every control, switch every
   face, warp +1 hour / +1 day / +1 month / +1 year, come back. Nothing may reset,
   collide, or ghost.
3. **Check the widest text**: ๑๕ not ๖, เดือนสิบเอ็ด not เดือนยี่, RTC-stale not GPS.
4. **Run the suite; regenerate baselines only deliberately** — and view the new baseline
   before accepting it. A baseline is a design sign-off, not a test fixture.
5. **Report with the picture.** If it can be seen, show it.

---

## Part 3 — Craft directions (doors, not debts)

No dates, no owners. Complete at every stage. Ordered roughly by awe-per-effort.

**Dial craft**
- **The moon is now fitted, not tuned.** Its five constants minimise RMS against real
  illumination (0.026), and the bands match the sky exactly. Any future change must
  re-run that fit — the numbers are not adjustable by taste.
- **Day arc**: sunrise→sunset drawn as an arc on the chapter-ring rim with a small sun
  index at the current hour — the whole day visible at a glance. Cheap: `SolarDay`
  already computes everything.
- **Hands**: designed hands (pierced spade, or a Lanna flame-tip echoing kanok) instead
  of tapered rectangles. The hands are the most-looked-at object on the clock.
- **Dither module**: ordered/Bayer dithering for tonal fields — twilight gradients on
  the day arc, soft shading inside the moon window. 16 greys can look like velvet.
- **Moon accuracy:** the shipped geometry measures RMS 0.021 against real illumination.
  The watchmakers' equal-radius arrangement measured 0.0045 on the same test and is
  documented in `ornament.py`; adopting it would trade the full monthly revolution for a
  five-fold accuracy gain. An open door, deliberately not walked through.
- **Moon: settled.** One moon, one full revolution per synodic month, clipped by two
  cloud arcs meeting at the dial's exact centre. Fitted against real illumination
  (RMS 0.021, worst 4.4 points). The residual is inherent — a circular arc cannot cut an
  elliptical terminator — and is bounded by test. If more accuracy is ever wanted, the
  route is to draw the moon's true terminator on the disc itself rather than to move
  the clouds around.
- **Unify the Main face** with the craft the Lanna face now has: same moon complication,
  same weights, optional guilloche ground.

**Reckoning depth**
- **Extend the authority table** beyond 2026 (Eade's rules computed, table cross-checked,
  divergences logged — the design brief's original plan).
- **True Songkran**: compute the solar ingress instead of the fixed 16 April approximation
  for the CS year boundary.
- **มื้อ 60-day cycle**: mine the corpus for one page equating a named CS date to a named
  day (กาบไจ้ …) — one verified anchor unlocks the whole cycle. Until then, absent.
- **เข้าอินทขีล** with a citable anchoring rule; **Tai Tham month names** and CS year in
  Tai Tham digits (U+1A80–1A89) once a reader of Tua Mueang has checked orthography.

**Instrument feel**
- **Coucal subdial**: a small dial at 6 o'clock whose single hand points at the next
  call — dawn on the left arc, dusk on the right.
- **Power reserve** as a horological subdial (already an open door in GROWING.md).
- **Festival aperture**: days-to-next-festival as a small numbered window, like a date
  aperture on a wristwatch.

**Workshop tools**
- **`make gallery`**: render every live face × solstices, equinoxes, festivals, degraded
  states into `out/gallery/` — the whole clock reviewable in one scroll.
- **Sim: jump-to-date** field and one-click festival jumps (ยี่เป็ง, ปี๋ใหม่เมือง, วันศีล).
- **A year in a minute**: script that renders 365 daily frames to an animation for
  reviewing seasonal drift — dawn moving, moon turning, festivals arriving.

---

## Part 4 — What "awesome" means here

Not more features. The clock is awesome when:

- **It is still.** No flicker, no glow, no twitch. Refreshes are budgeted.
- **It is honest.** Every claim traceable to sky, table, or measured file — and every
  limit spoken in the reader's own words.
- **It is local.** Lanna first: the reckoning of the wat it hangs in, corroborated by
  manuscripts its own community wrote.
- **It is legible at two metres**, by weight contrast and geometry — engraved, not typed.
- **It survives us.** Repairable in 2096 (`REPAIR.md`), growable by strangers
  (`GROWING.md`), complete at every stage of its life.

The instrument should feel like it was made by someone who loved both the sky and the
wat — and it should keep telling the truth long after everyone who built it is gone.
