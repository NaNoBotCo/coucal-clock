# The panel, and the question of colour

## Short answer

**Colour e-ink is real, buyable, and open to us. We are not fitting it, and the clock is
built so that we could.**

Black is the floor: every face renders completely and beautifully in 16 greys. Colour, if
a future panel offers it, blooms on top without a single face being rewritten.

---

## What colour e-ink actually is, in 2026

**E Ink Spectra 6** is the mature full-colour electrophoretic technology. Six pigments —
black, white, red, yellow, green, blue — driven directly, with no colour filter array and
no backlight, so it keeps the paper-like quality that made us choose e-ink at all. Panels
are readily available from Waveshare, Good Display and Seeed:

| Panel | Resolution | Notes |
|---|---|---|
| Spectra 6, 13.3" | 1600 × 1200 (~200 ppi) | the largest common size |
| Spectra 6, 7.3" | 800 × 480 | |
| Spectra 6, 4" | 600 × 400 | |
| **Our mono 10.3"** | **1872 × 1404** | 16 greys, sub-second partial refresh |

The other colour family, **Kaleido**, puts a colour filter array over a mono panel. It
refreshes fast but the colour is muted and it wants a frontlight — which would make the
clock glow. Ruled out on those grounds alone.

## Why we are not fitting it

Three costs, and the second is decisive.

**1. Resolution goes down.** 1600 × 1200 is 24% fewer pixels than the mono panel, on a
larger diagonal. Fine dial engraving, small Thai text, and Tai Tham's stacked diacritics
all want every pixel they can get.

**2. There is no partial refresh.** Vendor pages advertise partial refresh on Spectra 6
product listings, but that text is boilerplate carried over from mono panels — the
technology does not support it. **Every update is a full-screen refresh taking 12–19
seconds**, with the characteristic flashing inversion as pigments migrate.

Think about what that means in a wat. The clock wakes every five minutes. Roughly 288
times a day, the face would blank, flash through colour inversions for a quarter of a
minute, and settle. In a hall where people are chanting. A ceremonial object should be
still; this would twitch.

**3. Power.** A 12–19 second full refresh at colour drive currents, ~288 times daily,
against a 4 Wh/day budget through the Chiang Mai wet season. It would force far slower
updates — which then breaks the heartbeat, whose whole value is stepping often enough
that a person can watch it move.

Note that costs 2 and 3 are not really separate from the design: they attack the
**silence** and the **liveness detection**, which are two of the clock's core promises.

## Why the door stays open

E Ink Spectra 6 Plus has already been announced with faster refresh and higher
resolution, and this clock is meant to outlive several generations of panel. In 2045 the
trade-off may simply be gone.

So the *architecture* accommodates colour completely, today:

- **`faces/palette.py`** — faces draw in semantic inks (`Ink.SACRED`, `Ink.WARNING`),
  never in grey values. `MONO16` is the default and the fallback; `SPECTRA6` is defined
  and tested.
- **Palettes carry panel capabilities** — `supports_partial_refresh`, `grey_levels` —
  so a compositor can adapt rather than assume.
- **Tests render every face under every palette**, so a colour path cannot rot unnoticed.

Fitting a colour panel later means: write the driver behind the existing `Display`
contract, set the palette, adjust layout for the new resolution. No face is rewritten.

## The rule that makes the fallback honest

> **Meaning is never carried by colour alone.**

A low-battery warning is a warning because of its words, its weight, and its position.
The red merely reinforces. This is what allows a mono panel to lose every colour and lose
no information — and it is simply good practice for anyone reading the dial with
imperfect sight, at two metres, in a dim hall.

`tests/unit/test_palette.py` enforces it: `Ink.WARNING` and `Ink.SACRED` deliberately
collapse onto ordinary ink in `MONO16`, and the test asserts they do.

## If we ever do fit colour

The palette is written as a **woodblock reading** of the six pigments — the register of a
Lanna temple mural, red and gold on cream — not as an attempt at photographic colour. Six
flat inks suit instrument dials far better than they suit photographs. Green is
deliberately left unassigned, available for whoever finds a use for it.

---

**Sources:** [Waveshare 13.3" Spectra 6](https://www.waveshare.com/13.3inch-e-paper-hat-plus-e.htm) ·
[Waveshare 7.3" Spectra 6](https://www.waveshare.com/7.3inch-e-paper-hat-e.htm) ·
[E Ink Spectra 6 product page](https://www.eink.com/brand/detail/Spectra6) ·
[Good Display GDEP133C02](https://www.good-display.com/product/559.html) ·
[Seeed Studio 13.3" six-colour](https://www.seeedstudio.com/13-3inch-Six-Color-eInk-ePaper-Display-with-1200x1600-Pixels-p-6569.html) ·
[Spectra 6 Plus announcement](https://goodereader.com/blog/e-paper/new-e-ink-spectra-6-plus-offers-faster-refresh-and-higher-resolution)
