# Coucal Clock

A pair of ceremonial almanac clocks donated to a wat (Buddhist temple) in **San Sai,
Chiang Mai, Thailand** (~18.85 °N, 99.05 °E, ICT / UTC+7, no DST).

The physical form is an ornately carved teak cuckoo clock whose bird is a **greater coucal**
(นกกระปูด, *Centropus sinensis*) — the dawn-and-dusk time-marker bird of Thai villages.
Inside, a Raspberry Pi, a 10.3" e-ink display, and solar power replace the mechanical movement.
It is a **merit offering**: it must run unattended, offline, for decades.

Every architecture decision is subordinate to that requirement. See the design brief and
`MAINTENANCE.md` (the bilingual temple-attendant manual, rendered in Phase 6).

## The one rule that shapes everything

**The astronomy/calendar core (`almanac`) and the display faces (`faces`) are pure functions
of `(civil_time, position, config)`.** They have no clock and touch no hardware. Because of
this, the entire system runs on a desktop simulator that can age it through years in minutes.

## Quick start (desktop simulator — no hardware required)

**Easiest:** double-click **`Coucal Simulator.command`** in Finder. It opens the
simulator window and needs no network.

From a terminal:

```bash
make install   # one-time: creates .venv and installs requirements-dev.txt
make sim       # opens the simulator window (time-warp + fake sensors)
make test      # unit + golden + property + screenshot tests
make frame     # render one face to out/frame.png, no window
```

### Things to try in the simulator

| Do this | To see |
|---|---|
| Click **1 hr/s** or **1 day/s** | the clock aging; the **heartbeat** dot steps once per wake |
| Watch the *partials since last full* counter | why the compositor schedules periodic full clears |
| Drag **Battery volts** below 12.6 / 12.2 / 12.0 | the load-shedding ladder: hourly → date-only → hibernate |
| Uncheck **GPS fix available**, then step forward days | RTC holdover, and the time-confidence state going stale past 30 d |
| Click **Full refresh / clear ghosting** | accumulated partial-refresh ghosting wiped |

### Python version note

The project needs **Python ≥ 3.11** (it uses `tomllib` and `datetime.UTC`). On macOS,
a bare `python3` may resolve to the system 3.9, which cannot run this code — the
Makefile searches for `python3.13/3.12/3.11` explicitly. Override with
`make PY=/path/to/python3.12 install`.

The simulator needs **Tkinter**, which Homebrew ships separately:

```bash
brew install python-tk@3.13     # match your Python's version
```

Two dependency sets, deliberately kept apart:

- **`pyproject.toml`** pins the exact versions that ship *on the clock* (Python 3.11,
  Raspberry Pi OS). These are the posterity pins, validated by `make offline-install`
  against `vendor/wheels/` during the Phase 5 image build.
- **`requirements-dev.txt`** pins what works on a current *desktop* Python. Some device
  pins (e.g. Pillow 10.4.0) have no wheels for 3.13 and would compile from source.

## Layout

| Path | What it is |
|------|-----------|
| `src/coucal/hal/` | Hardware Abstraction Layer. `interfaces.py` = Protocols; `real/` = Pi drivers; `sim/` = fakes. |
| `src/coucal/almanac/` | Pure computation core (solar/lunar, Thai, Vedic, Taoist, Babylonian, Hellenistic, Pythagorean, compass). Golden-tested. |
| `src/coucal/services/` | `timebase`, `compositor`, `voice`, `steward`, `installer`. |
| `src/coucal/faces/` | The 8 display faces. Pure `state -> drawing`. |
| `src/coucal/sim/` | The desktop simulator (Tk window + time-warp + scriptable sensors). |
| `src/coucal/app.py` | The main loop: read time+power → compose → refresh → sleep. |
| `data/` | Bundled, read-only: DE440 ephemeris, IGRF, fonts, coucal audio, Thai calendar table. |
| `config/` | One TOML per unit. Identical software; only these files differ between the two clocks. |
| `tests/golden/` | Published-value fixtures, each citing its source. |

## HAL selection

`COUCAL_HAL=sim` (desktop default) or `COUCAL_HAL=real` (set by systemd on the Pi).
`coucal.hal.factory.build_hal(config)` returns the right bundle. Code above the HAL never
imports a hardware library.

## Phase status

- [x] **Phase 0** — repo scaffold, HAL, desktop simulator, golden-test harness, CI.
      Also: the **face registry** (`faces/registry.py`) and the **repair contract**
      (`hal/interfaces.py` documented as a hardware spec) — both pulled forward because
      they are structural and expensive to retrofit.
- [x] **Phase 1** — `timebase` (GPS>RTC arbitration, holdover, drift estimate, no
      backwards time) + the Skyfield sun/moon core (rise/set, all three twilights,
      solar noon, day length, phase, illumination, moonrise/set, next new & full,
      and the drifting **coucal call times**). Golden-tested against **published USNO
      values** for Chiang Mai across four seasons.
- [~] Phase 2 — calendar modules. **Thai and Lanna done**: Buddhist Era + Chulasakarat,
      the lunar month in both reckonings, wan phra / วันศีล, the twelve-year zodiac,
      Northern festivals — all driven by a bundled *published* authority table, never
      guessed. Vedic, Taoist, Babylonian, Hellenistic, Pythagorean still to come.
- [~] Phase 3 — compositor + faces. **Two faces live**: Main (Thai-first analog dial)
      and **Lanna** (zodiac band, naga ring, kanok spandrels, lotus hub). Screenshot
      baselines cover both.
- [ ] Phase 4 — `voice` + automaton + silence logic.
- [ ] Phase 5 — `steward`, power modes, watchdogs, read-only root, OS image.
- [ ] Phase 6 — `installer` + bilingual manual + repair-kit artifacts (engraved plate,
      spares drawer, rebuild drill) + two-unit config split.

There is no Phase 7. Phases 1–6 deliver the whole clock.

**Faces: 2 built, 8 committed, 1 door left open.** The catalogue lives in
[`faces/registry.py`](src/coucal/faces/registry.py), and it lists *only what the clock is
actually going to be* — never a wish list. Face 0 is **Lanna-rooted**: this clock stands
in a Lanna wat, so the date a passer-by reads is the one their own tradition keeps, with
central Thai BE below it.

## The Lanna face

See **[docs/LANNA.md](docs/LANNA.md)**. The clock stands in a Lanna wat, so the Northern
reckoning is not a translation of the Thai one — it is a different calendar. The face
carries the Chulasakarat year, the Northern month, the twelve-year zodiac band, and the
Northern festivals (ปี๋ใหม่เมือง, ยี่เป็ง), drawn with Lanna motifs: naga ring, kanok
spandrels, lotus hub. That document records the provenance of every claim it makes, and
what it deliberately does *not* claim.

## The guidebook

See **[docs/GUIDEBOOK.md](docs/GUIDEBOOK.md)** — the defect ledger distilled into working
rules (every rule paid for by a real bug in this repo), the gemba drill run before any
change is claimed, and the craft directions for making the clock more beautiful — doors,
not debts.

## Built to grow

See **[docs/GROWING.md](docs/GROWING.md)**. The clock is **complete at every stage of its
life** — never a partial clock waiting to be finished. So there is no backlog: ideas for
further faces live in that document as *open doors*, with no dates and no owner, and a
door that stays shut for fifty years costs nothing. Because the registry only cycles
faces that exist, a face added in 2040 needs a card swap and nothing else — the clock can
keep growing on the temple wall, by hands that never met the people who built it.

## Built to be repaired

See **[docs/REPAIR.md](docs/REPAIR.md)**. The premise: the software will survive, the
parts will not, so the clock is *a case, a carved bird, and a display* — the computer
inside is a consumable. `hal/interfaces.py` is the repair contract: nine small
interfaces, and a maintainer in 2096 brings the clock back by implementing those
against whatever hardware exists then.

## License note (posterity)

Astronomy is **Skyfield (MIT)** with a bundled **JPL DE440** ephemeris (1550–2650) — deliberately *not*
Swiss Ephemeris / pyswisseph, whose AGPL/commercial licensing complicates a device meant to
be rebuildable by a stranger in 2070. Fonts (Noto) and their licenses are vendored under
`data/fonts/`.
