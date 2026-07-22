# Golden tests — validation against published authority

Each almanac module is checked against **published, citable values** for Chiang Mai
coordinates, not against our own output. A golden fixture is a JSON file in
`fixtures/` shaped like this:

```json
{
  "module": "solar",
  "description": "Sunrise/sunset at the temple, 1 Jan 2026",
  "source": "Time and Date AS, Chiang Mai, 2026-01-01, https://www.timeanddate.com/...",
  "retrieved": "2026-07-19",
  "inputs": { "utc": "2026-01-01T00:00:00+00:00", "lat": 18.85, "lon": 99.05, "elev_m": 320 },
  "expected": { "sunrise_local": "06:52", "sunset_local": "18:00" },
  "tolerance": { "sunrise_local": "120s", "sunset_local": "120s" }
}
```

Rules that keep this honest for posterity:

- **Cite the source and the date it was retrieved.** A stranger in 2070 must be able
  to see where the number came from and judge it.
- **Name the canonical method** in the fixture when a tradition has competing schools
  (ayanamsa, hexagram derivation, intercalation) — the same enum the face prints in
  small type. A disagreement then reads as a documented choice, not a bug.
- **Tolerances are explicit**, per field. Times allow a couple of minutes (rounding and
  refraction models differ between publishers); discrete values (a tithi number, a
  waxing/waning day) must match exactly.
- **The table wins over the algorithm** for the Thai calendar where the official
  calendar reflects an authority's intercalation decision; such divergences are logged,
  not silently reconciled.

`tests/test_golden.py` discovers every fixture and dispatches it to the evaluator
registered for its `module`. A fixture whose module has not been built yet is **skipped
with a clear message**, so fixtures can be written ahead of the code (Phase 1+).
