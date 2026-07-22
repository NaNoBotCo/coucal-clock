# Repairability — designing for the year 2096

## The premise

The software will survive. The parts will not.

Python source, a documented file format, and a printed schematic are all readable in
seventy years. What will not exist is the Raspberry Pi Zero 2 W, this particular
Waveshare panel, and quite possibly the microSD *format* itself.

So "repairable" cannot mean *keep it running*. It has to mean:

> **A person in 2096 can put a 2096 brain into a 2026 teak case, and the clock works again.**

That reframes the object. The clock is a **case, a carved coucal, and a display**.
The computer inside it is a consumable, like a battery or a lightbulb.

Everything below follows from that one sentence.

---

## 1. The repair contract is `hal/interfaces.py`

The most important repairability decision is already made and already in the code.

Every single thing the clock needs from the physical world is expressed as nine small
contracts in [`src/coucal/hal/interfaces.py`](../src/coucal/hal/interfaces.py):

| Contract | What a future maintainer must provide |
|---|---|
| `TimeSource` | the current UTC time, and how much to trust it |
| `PositionSource` | latitude, longitude, elevation |
| `PowerTelemetry` | battery volts and amps |
| `Button` | "was the button pressed since I last asked?" |
| `Display` | accept a greyscale picture and put it on the screen |
| `AudioSink` | play a sound file at a volume |
| `Automaton` | move the bird |
| `Watchdog` | "I am still alive" |
| `PowerController` | sleep until a given time; shut down cleanly |

**Nothing above that layer knows what a Raspberry Pi is.** The almanac, the calendars,
the eight-plus faces, the coucal's dawn schedule — none of it can tell the difference
between real hardware and the desktop simulator, because that difference is confined to
those nine contracts.

### What this buys

A maintainer in 2096 does **not** need to understand the Thai lunisolar calendar, the
Lahiri ayanamsa, e-ink refresh budgets, or the compositor. They need to write one file
implementing nine interfaces against whatever hardware exists then. That is a weekend of
work for a competent person, rather than a rewrite.

They can check their work before touching the clock: the test suite runs entirely
against the simulator, so a new hardware implementation can be developed and validated
on a desk.

### Consequence for us

`hal/interfaces.py` must be documented as a **hardware specification** — expected units,
timings, voltage ranges, and what "good" looks like for each signal — not merely as a
testing seam. It is the most important file in the repository for posterity.

---

## 2. Module boundaries

Each subsystem is independently replaceable. Any one can die and be swapped without
disturbing the others.

```
        ┌──────────── service panel (opens with one common tool) ────────────┐
        │                                                                   │
        │   [COMPUTE]────┬──── J1 ──── [DISPLAY]   e-ink panel + controller  │
        │                ├──── J2 ──── [POWER]     battery, MPPT, telemetry  │
        │                ├──── J3 ──── [AUDIO]     amplifier + exciter       │
        │                ├──── J4 ──── [BIRD]      servo, door linkage       │
        │                ├──── J5 ──── [SENSORS]   GPS antenna, RTC          │
        │                └──── J6 ──── [BUTTON]    brass button              │
        │                                                                   │
        │   [MANUAL POCKET]   [ENGRAVED PLATE]   [SPARES DRAWER]             │
        └───────────────────────────────────────────────────────────────────┘
```

Rules:

- **Every connector is keyed and labelled** — `J1`…`J6`, matching the manual and the
  engraved plate. A connector that can only go in one way, one place.
- **Nothing glued.** Nothing soldered that could have been a plug.
- **No proprietary stacking connectors** where a generic one will do. Prefer plain,
  documented I²C / SPI / UART / PWM at published pinouts over a vendor-specific HAT,
  even at some cost in tidiness. A documented wire can be recreated; a discontinued
  board cannot.
- **Wire colours are documented and consistent** across both units.

---

## 3. What lives inside the case

### The manual

Printed on archival paper, bilingual (Thai / English), in a pocket behind the service
panel. Generated from [`MAINTENANCE.md`](../MAINTENANCE.md).

**Not a URL. Not a QR code** — a QR code is a URL wearing a costume, and domains die
long before teak does.

### The engraved plate

A metal plate fixed inside the case. Metal outlives paper, SD cards, and every cloud
service that will ever exist. It carries, in permanent form:

- What this object is, and that it is a merit offering
- The connector map (`J1`…`J6`) with voltages and signal types
- The nine interface names from the repair contract above
- Where the full source came from, and the release it was built from
- One sentence of intent: *the computer is a consumable; the clock is the case*

Kept short enough to engrave, complete enough to rebuild from.

### The spares drawer

A sealed drawer inside the case, shipped with the clock:

- Pre-imaged microSD cards (more than one; they fail)
- A spare compute module
- Fuses
- A spare button
- The wiring diagram, printed

**This is probably worth more than every other measure combined.** It buys twenty to
thirty years outright, cheaply, *today*, while the parts are still in production. No
amount of documentation substitutes for the actual part being in the box.

---

## 4. Graceful degradation

The clock should lose capability in a dignified order, and always say what it has lost
rather than silently faking it.

| What dies | What happens |
|---|---|
| GPS | Runs on the RTC. Shows a time-confidence mark; says so plainly after 30 days. |
| RTC *and* GPS | Says it does not know the time, rather than displaying a guess. |
| Solar / battery low | Sheds load: hourly updates → date only → a "sleeping" face, then rests. |
| Audio or bird | The clock still keeps and shows time. The call is silently skipped. |
| Display | The one true failure. Nothing else matters if the face is dark — hence the spares. |
| Compute | Replace the module. This is the designed-for repair. |

The **heartbeat** (see `MAINTENANCE.md`) is what makes any of this detectable: e-ink
holds its last image without power, so a dead clock still looks like a working one. The
stepping dot is the only signal that distinguishes them.

---

## 5. The rebuild drill

Documentation that has never been tested is a guess.

**Before either unit is donated**, run this drill: hand the printed manual and the
spares drawer to someone who did not build the clock, and ask them to replace the
compute module and bring it back to life. Whatever they get stuck on is a documentation
defect, not a user error. Fix it and repeat.

A second drill, worth doing once: implement the nine contracts against a *deliberately
different* piece of hardware — any other small computer and any other display — purely
to prove the repair contract is real and not accidentally shaped like a Raspberry Pi.

---

## 6. Model expiry — the clock's other clock

Repairing the hardware is not enough if the clock's *knowledge* silently goes stale.
Every bundled model has a horizon:

| Bundled data | Good until | On expiry |
|---|---|---|
|  Planetary ephemeris (DE440) | 2650 | The sun, moon, and planets stop being computable |
| Thai calendar authority table | ~2126 | Falls back to the algorithm; logs divergence |
| Magnetic model (IGRF) | ~5 years per generation | Compass drifts; must be declared stale, not hidden |

The magnetic model is the near-term one: **IGRF-13 covers 2020–2025 and is already
expired as of 2026** — the current generation should be bundled instead, and this is
worth re-checking whenever the compass face is built.

This is exactly what the planned **"What this clock does not know"** face exists to
show. A clock that states its own uncertainty is more trustworthy at seventy years than
one that quietly draws a confident, wrong north.
