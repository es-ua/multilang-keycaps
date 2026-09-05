# multilang-keycaps

Parametric generator for 3D‑printable MX keycaps with multi‑language legends
(EN / RU / UK / DE), built for multi‑material FDM printing (Bambu Lab H2D + AMS).
Pure CadQuery, no OpenSCAD.

## Commands
- `uv sync` — install deps (cadquery, pytest). System font `fonts-dejavu-core` must be present.
- `uv run keycaps build --test` — 6 test keys (Q, S, ], ', -, Backspace 2u) → `out/`
- `uv run keycaps build --layout ansi_104` — full set
- `uv run keycaps build --keys Q W E` — subset
- `uv run pytest` — geometry tests; `-m "not slow"` skips full‑layout build
- `uv run python scripts/render.py` — README renders

## Architecture
- `keycaps/geometry.py` — cap body, MX stem, base/top split
- `keycaps/legends.py` — text placement, color groups
- `keycaps/config.py` — `PrintConfig` dataclass (all mm values live here, nowhere else)
- `layouts/*.json` — layouts as data: `name, width_u, en, ru, uk, de, group`
- Per key export: `_base` (clear PETG), `_top` (black PETG‑CF), `_legA` (translucent blue PETG),
  `_legB` (translucent pink PETG), plus one multi‑part 3MF.

## Fixed design decisions — do not change without being asked
- Two top variants, both kept: flat top printed face‑down (default, `DISH_DEPTH = 0`) and a
  0.6 mm spherical dish printed face‑up (`--dish`). The dish sphere passes through the four corners
  of the top plate so every edge sags the same, matching the GravaStar Mercury stock caps;
  `DISH_SHAPE = "cyl"` is the Cherry/OEM alternative. Decision on which ships is pending a print
  test of the 9‑key QWE/ASD/ZXC set in both variants (2026‑09‑05).
- 1u = 18.0 × 18.0 × 9.0 mm, top plate 14 × 14 mm, top thickness 2.2 mm.
- Legends are shine‑through: full‑depth columns through the black top (cavity ceiling → face),
  printed in translucent PETG (`LEG_THROUGH = True`); `False` gives the old 0.45 mm inlay.
- Stem clearance is tuned for PETG‑CF (+0.10 mm cross length, +0.05 mm cross thickness).
- Legend layout on a key (big letters in opposite corners, small ones in the other two):
  ```
  EN   DE     EN and RU are 6.0 mm, glyph outline hugs the top‑left / bottom‑right corner (1.5 mm margin);
  UK   RU     DE (top‑right) and UK (bottom‑left) are 3.2 mm; UK printed only where it differs from RU.
              If EN+RU do not fit vertically with a 1.2 mm gap, both shrink together.
  ```
- Legend groups: A = EN+DE, B = RU+UK. Groups are data (`group` field), not code.

## Conventions
- Python 3.11+, type hints, ruff defaults. Conventional commits.
- Every geometry change needs a test in `tests/` (bounding box / z‑layers / zero intersection).
- Docs and README in English; a short Russian section at the bottom of README is fine.
- Never commit `out/` (generated STL/3MF). Release artifacts go to GitHub Releases.

## Slicer gotchas (verified on sliced G-code, Bambu Studio 02.08)
- Keep `resolution = 0` in the embedded project settings. With the default 0.012 mm contour
  simplification Bambu drops multi‑part pockets shaped like curved glyphs (S, C, O, Q, Ф) and prints
  them in the top part's black. `scripts/build_test.py` sets it; do not remove.
- Export meshes go through `clean_mesh()` (trimesh: merge vertices, drop degenerate faces, fix winding).
- Handy check after slicing: `--slice 1 --export-3mf` via the Bambu CLI, then measure filament per
  letter body in the G-code (see the session scratch script `measure.py` pattern: point‑in‑solid on
  segment midpoints).

## Known open items
- `layouts/k98_pro.json` bottom‑row and right‑block widths are unmeasured (TODO markers) —
  ask before guessing.
- Cherry stabilizer cutouts for ≥2u keys are optional (`stabilizer: "none" | "cherry"`).
