# Bundled data (read-only, vendored for posterity)

Everything the clock needs to compute, offline, forever. Large binaries are fetched by
`scripts/fetch_data.sh` (documented, reproducible) and then committed via Git LFS or
copied onto the OS image. Nothing here changes at runtime.

| Path | What | Source / license | Phase |
|------|------|------------------|-------|
| `ephemeris/de440.bsp` | JPL DE440 planetary ephemeris. Verified span **1549-12-30 → 2650-01-24** (114 MB). See `ephemeris/PROVENANCE.md` — the *short* `de440s` reaches only 2150. | NASA/JPL, public | 1 ✅ |
| `fonts/` | Noto Sans Thai, **Noto Sans Tai Tham** (the Lanna / Tua Mueang script — required for the Lanna face), Noto Sans, Noto Serif Thai, Noto Sans Symbols 2 (+ hexagrams U+4DC0–4DFF, planetary/zodiacal glyphs) | SIL Open Font License 1.1 | 3 |
| `igrf/igrf13.coef` | IGRF-13 geomagnetic coefficients + validity dates | IAGA, public | 6 |
| `audio/coucal/` | Greater coucal field recordings (dawn/dusk/wan-phra) | recorded for this project | 4 |
| `tables/thai_calendar_2026_2126.csv` | Precomputed Thai lunisolar authority table; wins over the algorithm on intercalation disputes | compiled from official Thai calendars | 2 |

Until a file is added, its module falls back gracefully (e.g. Phase 0 faces use
Pillow's scalable default font when `fonts/` is empty).
