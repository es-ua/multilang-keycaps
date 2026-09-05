# multilang-keycaps

Parametric generator for 3D‑printable MX keycaps with multi‑language legends
(EN / RU / UK / DE), built for multi‑material FDM printing (Bambu Lab H2D + AMS).
Pure CadQuery, no OpenSCAD.

## Commands (current state: single-module generator, no `uv`/`keycaps` CLI yet)
- `python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt` — deps (cadquery, trimesh, pytest).
- `.venv/bin/python scripts/build_test.py -o name.3mf Q W E / A S D / Z X C` — Bambu project + STLs, `/` = new row;
  flags `--dish`, `--round`, `--qwertz`, `--undercut X`, `--raise X`, `--multilang`.
- `.venv/bin/python scripts/build_alphabet.py flat|dish[_round][_qwertz]` — the 36 multilang keys.
- `.venv/bin/python -m pytest -q tests` — geometry tests.
- Output: `out/`, `out/dish/`, `out/round/`, `out/dish/round/` (+ `*_layout.json` with key bed positions).
- The `uv run keycaps build ...` commands from KEYCAPS_TZ.md are the target design, not implemented.

## Architecture
- `keycaps_gen.py` — everything geometric: constants at the top, `KEYS` layout list, `cap_body`, `legends`, `build_key`.
- `scripts/build_test.py` — plate layout, mesh cleaning, Bambu 3MF writer, project settings from `templates/`.
- `scripts/build_alphabet.py` — the 36-key set in all variants.
- Planned (KEYCAPS_TZ.md): `keycaps/geometry.py`, `legends.py`, `config.py`, `layouts/*.json`.
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
- `--qwertz` variant: DE corner gets Z↔Y and `] \ / `` ` ``` → `+ # - ^` via `QWERTZ_DE` in `keycaps_gen.py`;
  the default QWERTY `KEYS` list is never modified in place.

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
