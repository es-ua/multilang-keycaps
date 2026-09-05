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
- Per key export: `_base` (clear PETG), `_top` (black PETG‑CF), `_legA` (white), `_legB` (red),
  plus one multi‑part 3MF.

## Fixed design decisions — do not change without being asked
- Print face‑down; top face is flat (no dish).
- 1u = 18.0 × 18.0 × 9.0 mm, top plate 14 × 14 mm, top thickness 2.2 mm, legend depth 0.45 mm.
- Stem clearance is tuned for PETG‑CF (+0.10 mm cross length, +0.05 mm cross thickness).
- Legend layout on a key:
  ```
  EN   RU
  DE   UK   (UK printed only where it differs from RU)
  ```
- Legend groups: A = EN+DE, B = RU+UK. Groups are data (`group` field), not code.

## Conventions
- Python 3.11+, type hints, ruff defaults. Conventional commits.
- Every geometry change needs a test in `tests/` (bounding box / z‑layers / zero intersection).
- Docs and README in English; a short Russian section at the bottom of README is fine.
- Never commit `out/` (generated STL/3MF). Release artifacts go to GitHub Releases.

## Known open items
- `layouts/k98_pro.json` bottom‑row and right‑block widths are unmeasured (TODO markers) —
  ask before guessing.
- Cherry stabilizer cutouts for ≥2u keys are optional (`stabilizer: "none" | "cherry"`).
