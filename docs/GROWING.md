# How this clock grows

## The principle

**The clock is complete at every stage of its life.**

Whatever faces it has today, it is a finished clock — not a partial one waiting for the
rest. This is a design constraint, not a sentiment, and it has consequences we hold
ourselves to:

1. **No backlog.** `faces/registry.py` lists only what the clock is actually going to
   be. Ideas live here, in prose, as open doors — never in the code as unmet
   obligations. A long list of "planned" entries would make the clock permanently
   indebted, and a merit offering should not carry debt.

2. **Additions never disturb what is already there.** Adding a face requires changing no
   existing face and nothing outside the `faces` package. If an addition would require
   surgery elsewhere, the addition is wrong, or the architecture is — fix that first.

3. **Nothing here is scheduled.** No dates, no phases, no owner. An open door may stay
   shut for fifty years and nothing is lost. If a door is never opened, the clock was
   never incomplete.

4. **New faces may arrive after donation.** The registry only cycles faces that exist,
   so a face added in 2040 needs a card swap and nothing else. The clock can keep
   growing on the temple wall, by hands that never met the people who built it.

## What is committed

The original design brief, plus a Lanna face. That is the clock we are building, and it
is finishable:

**core** — Main (Lanna-rooted, the resting face)
**calendar** — Lanna · Thai · Panchanga · Taoist · Babylonian · Hellenistic
**divination** — Pythagorean · Compass · *(the unopened door)*
**meta** — Diagnostic *(built)*

Phases 1–6 deliver exactly this. There is no Phase 7, because the long tail is not a
phase — it is a door.

---

## Adding a face

Written so that a stranger, or you in fifteen years, can do this without holding the
whole system in mind.

### 1. Write the module

`src/coucal/faces/yourface.py`, one public function:

```python
def render(state: RenderState) -> bytes:
    c = Canvas()
    c.text((90, 70), "Your title", 40)
    return c.to_framebuffer()
```

`RenderState` is everything the clock knows at that instant — time, position, power,
tick. A face is a **pure function**: it reads no clock, touches no hardware, and asks
nothing of the world. That is why any face can be rendered at any date, and why the
simulator can age it through centuries in seconds.

### 2. Register it

One entry in `faces/registry.py`. Set `status=LIVE` and point `render` at your function.

### 3. Prove it

- A **golden test** for whatever the face computes, validated against a *published,
  cited* source — not against our own output. See `tests/golden/README.md`.
- A **screenshot baseline** so later changes cannot silently disfigure it.

That is the whole procedure. If it ever takes more than this, something upstream has
gone wrong and is worth fixing rather than working around.

---

## Open doors

None of these is owed. They are recorded because they are good ideas and because
someone, someday, may want a place to start.

### Sky

- **Orrery** — the visible planets in their true current positions.
- **Star chart** — the sky over the temple right now, topocentric.
- **Equation of time** — true sun against mean sun; why a sundial disagrees with a clock.
- **The Great Year** — our position in the ~26,000-year precession of the equinoxes.

### Further calendars

- **Burmese–Mon** — regionally adjacent to Lanna and historically entangled with it.
- **Tibetan / Kalachakra** — arguably the most contextually apt of all, for a Buddhist temple.
- **Maya** — tzolk'in and Long Count; a genuinely independent calendrical cosmology.

### Further divination

- **Geomancy** (*ʿilm al-raml*) — sixteen figures, deterministic from the moment;
  travelled Arabic → Europe → Africa. A true crossroads system.

### The clock's self-knowledge

- **"What this clock does not know"** — every bundled model has a horizon: the Thai
  authority table to ~2126, the planetary ephemeris to 2650, the magnetic model within
  a few years. A face that states its own uncertainty is more trustworthy at seventy
  years than one that quietly draws a confident, wrong north.
- **Power reserve** — the battery drawn as a horological power-reserve dial rather than
  a gauge.

### A colour panel

Not a face, but the same shape of door. Faces already draw in **semantic inks** rather
than grey values, and a `SPECTRA6` palette is defined and tested, so fitting a colour
e-ink panel later means writing a driver and choosing a palette — no face is rewritten.

We are not fitting one now: colour e-ink has no partial refresh, so every update is a
12–19 second full-screen flash, which would twitch through chanting hours and break both
the power budget and the heartbeat. See **[DISPLAY.md](DISPLAY.md)** for the full
reasoning and the panels surveyed. Newer generations are already narrowing the gap; this
door may open itself.

### A caution, kept here on purpose

Some systems should not be added by a programmer alone. **Ifá/Odu** is among the most
sophisticated divinatory systems humans have built, and it belongs on any honest list —
but it is cast by an initiated babalawo, and a machine generating odu on a timer is a
different act from a machine computing a tithi. If that door is ever opened, it should
be opened *with* practitioners, not merely about them.

The same care applies to any living initiatory tradition. Computability is not
permission.
