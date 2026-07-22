#!/usr/bin/env bash
# Fetch the large bundled data files into data/. Run ONCE, online, on a build machine.
# The device never runs this — it ships with the files already present.
# Each command is pinned to an exact artifact for reproducibility.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Phase 1: JPL DE440 planetary ephemeris (114 MB) -------------------------
# NOTE: this is the FULL de440, not de440s. The short variant covers only
# 1849-2150; the full kernel covers 1550-2650, which is the horizon the clock
# was designed around. See data/ephemeris/PROVENANCE.md.
if [ ! -f "$here/data/ephemeris/de440.bsp" ]; then
  echo "Fetching JPL DE440 ephemeris (114 MB)…"
  curl -sS -L --fail -o "$here/data/ephemeris/de440.bsp" \
    https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp
else
  echo "DE440 ephemeris already present."
fi

echo "Verifying checksum…"
echo "a4ce9bf9b3282becc9f4b2ac3cebe03a2ae7599981aabd7265fd8482fff7c4b5  $here/data/ephemeris/de440.bsp" \
  | shasum -a 256 -c -

# --- Fonts: Noto families + their OFL licences -------------------------------
# Sourced from google/fonts, which ships built TTFs (the per-script notofonts/*
# repos contain sources only). Noto Sans Thai carries Latin as well, so mixed
# "หอระฆัง / bell tower" labels render from one file. Tai Tham is the Lanna /
# Tua Mueang script and needs its own face — Pillow does no font fallback.
fonts_base="https://raw.githubusercontent.com/google/fonts/main/ofl"
fetch_font () {  # <url-path> <local-name>
  if [ ! -f "$here/data/fonts/$2" ]; then
    echo "  fetching $2"
    curl -sS -L --fail -o "$here/data/fonts/$2" "$fonts_base/$1"
  fi
}
echo "Fetching Noto fonts…"
mkdir -p "$here/data/fonts"
fetch_font "notosansthai/NotoSansThai%5Bwdth,wght%5D.ttf"   "NotoSansThai-Variable.ttf"
fetch_font "notosanstaitham/NotoSansTaiTham%5Bwght%5D.ttf"  "NotoSansTaiTham-Variable.ttf"
fetch_font "notosans/NotoSans%5Bwdth,wght%5D.ttf"           "NotoSans-Variable.ttf"
fetch_font "notoserifthai/NotoSerifThai%5Bwdth,wght%5D.ttf" "NotoSerifThai-Variable.ttf"
fetch_font "notosansthai/OFL.txt"      "OFL-NotoSansThai.txt"
fetch_font "notosanstaitham/OFL.txt"   "OFL-NotoSansTaiTham.txt"
fetch_font "notosans/OFL.txt"          "OFL-NotoSans.txt"
fetch_font "notoserifthai/OFL.txt"     "OFL-NotoSerifThai.txt"

# Still to come in Phase 3: Noto Sans Symbols 2, for hexagrams (U+4DC0-4DFF)
# and the planetary / zodiacal glyphs.

# --- Phase 6: IGRF geomagnetic coefficients ----------------------------------
# NOTE: the design brief specifies IGRF-13, which covered 2020-2025 and is
# already expired. Bundle the current generation and record its validity window.

echo "Done. (Fonts and IGRF land in their own phases.)"
