<div align="center">

# multilang-keycaps

**3D‑printable MX keycaps with shine‑through EN · RU · UK · DE legends, generated with CadQuery
and exported as ready‑to‑slice Bambu Studio projects.**

[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Models: CC BY 4.0](https://img.shields.io/badge/models-CC%20BY%204.0-lightgrey.svg)](LICENSE-models)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](requirements.txt)
[![CadQuery](https://img.shields.io/badge/built%20with-CadQuery-orange.svg)](https://github.com/CadQuery/cadquery)

</div>

---

## Why

No off‑the‑shelf keycap set covers Latin + Russian + Ukrainian + German on one board, and none of
them let RGB shine through the Cyrillic. This generator makes the set you actually need: every key is a
multi‑material print where the legends are **translucent columns going all the way through the black
top**, so the switch LED lights the letters from inside. Change a font, a size, a colour or a layout,
re‑generate, print again.

Target boards: GravaStar Mercury K98 Pro and Mercury V75 (any MX‑stem switch works).
Target printer: Bambu Lab H2D with AMS (the project files are H2D‑specific, the STLs are not).

## What you get

Each key is one object made of four parts. The generator writes per‑key STLs **and** a Bambu Studio
project (`.3mf`) with all keys laid out on the bed, parts already grouped per key, filament slots
assigned, purge matrix filled and the slicer settings that this geometry needs.

| Part | Filament slot | Material | Role |
|------|---------------|----------|------|
| `_base` | 1 | translucent PETG | walls + MX stem, lets the LED through |
| `_top` | 2 | black PETG | 2.2 mm opaque cap around the letters |
| `_legA` | 3 | translucent blue PETG | EN + DE legends, full‑depth columns |
| `_legB` | 4 | translucent pink PETG | RU + UK legends, full‑depth columns |

Slots 1–2 go to the left nozzle, 3–4 to the right one, so black never shares a nozzle with the
colours. Translucent parts are set to 100 % infill so the light path has no pattern inside.

### Legend layout

```
┌──────────────┐
│ EN        DE │   EN and RU: 6.0 mm, glyph outline hugs the corner (1.5 mm margin)
│              │   DE and UK: 3.2 mm in the two remaining corners
│ UK        RU │   UK only where it differs from RU (S→І, ]→Ї, '→Є, \→Ґ)
└──────────────┘
```

If a pair does not fit with a 1.2 mm gap, both letters shrink together. Font: DejaVu Sans Bold
(bundled in `fonts/`, it has Cyrillic and the ⌫⇥⏎⇧ glyphs).

**German QWERTZ** (`--qwertz`, or a `_qwertz` variant of `build_alphabet.py`): the DE corner also
gets what actually moves when you switch to a German layout, on top of Ü Ö Ä ß:
`Z`→Y, `Y`→Z, `]`→+, `\`→#, `/`→-, `` ` ``→^. The acute on `=` is skipped, at 3.2 mm it is a dot.

### Three cap variants, pick after a test print

| Variant | Flag | Top | Print orientation | Legends |
|---------|------|-----|-------------------|---------|
| flat | *(default)* | flat, 0.6 mm chamfer | face‑down on a smooth plate | flush with the face |
| dish | `--dish` | 0.6 mm spherical dish through the four corners | face‑up, stem on the bed | stand 0.4 mm proud, follow the dish |
| round | `--round` | 2 mm corner fillets, 1 mm top‑edge fillet (GravaStar look) | either of the above | as above |

In every variant the letters also poke 0.6 mm *below* the cavity ceiling as small bumps inside the
cap. That kills the coplanar face between letter and ceiling that made slicers render the first
layer of the letters only partially.

## Quick start

```bash
git clone https://github.com/es-ua/multilang-keycaps
cd multilang-keycaps
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 9 keys for a test print (Q W E / A S D / Z X C), flat and dished
.venv/bin/python scripts/build_test.py        -o qweasdzxc.3mf Q W E / A S D / Z X C
.venv/bin/python scripts/build_test.py --dish -o qweasdzxc.3mf Q W E / A S D / Z X C

# every key that carries a RU/UK/DE legend (36 keys, 280 × 60 mm plate)
.venv/bin/python scripts/build_alphabet.py            # flat + dish
.venv/bin/python scripts/build_alphabet.py dish_round # dish + rounded edges
```

Output goes to `out/` (flat), `out/dish/`, `out/round/`, `out/dish/round/`. Next to each `.3mf`
there is a `*_layout.json` with the bed position of every key.

`scripts/build_test.py` options: `/` starts a new row, `-o name.3mf`, `--dish`, `--round`,
`--qwertz`, `--undercut 0.6` (bump below the ceiling), `--raise 0.4` (letters proud of the face,
dish only by default), `--multilang` (same 36‑key set as `build_alphabet.py`).
`build_alphabet.py` takes variant names: `flat`, `dish`, optionally `_round` and/or `_qwertz`
(`dish_round_qwertz`). Every variant lands in its own sub‑folder of `out/`, nothing is overwritten.

## Printing on the H2D

1. Open the `.3mf`. It already carries the H2D 0.4 nozzle printer profile, four PETG filament
   presets, colours, nozzle mapping and per‑part settings. Supports are **off**; the dish variant has
   small overhangs under the cavity ceiling that you may want to support, your call.
2. Slot 2 ships as *Bambu PETG Basic* (black). Switch it to PETG‑CF if you print the top in CF; the
   stem clearance is already tuned for CF (+0.10 / +0.05 mm).
3. Layer height 0.2 mm is fine for the flat variant. For the dish variant use 0.08 mm at least for
   the top 3 mm (adaptive layer height), otherwise the 0.6 mm dish becomes three visible steps.
4. Dry the PETG. Translucent PETG shows every bubble.

### The slicer gotcha you must know about

Bambu Studio 02.08 with its default *Quality → Advanced → Resolution* = 0.012 mm **drops
multi‑part pockets shaped like curved glyphs** (S, C, O, Q, Ф …) and prints them in the top part's
black. The project files set `resolution = 0`, which fixes it. If you switch to another process
preset, set it to 0 again or the round letters come out black.

We found this by slicing with the Bambu CLI and measuring, per letter, how much filament of each
colour lands inside the letter body in the G‑code. The same check is the acceptance test for every
change to the geometry; see `tests/` for the CAD‑level invariants.

## Geometry

| Parameter | Value |
|-----------|-------|
| 1u footprint | 18.0 × 18.0 mm (19.05 mm pitch) |
| Height | 9.0 mm, flat XDA‑like profile, no per‑row sculpting |
| Top plate | 14.0 × 14.0 mm |
| Wall | 1.4 mm |
| Top thickness | 2.2 mm (kept under the dish too) |
| Legends | through the whole top, +0.6 mm below the ceiling, +0.4 mm above the face (dish) |
| Stem | MX cross 4.15 × 1.30 / 1.15 mm, +0.10 / +0.05 mm clearance for CF |
| Keys ≥ 2u | stiffening rib, no stabiliser cut‑outs yet |

Every number lives at the top of `keycaps_gen.py`.

## Make it yours

- **Keys and legends** are the `KEYS` list in `keycaps_gen.py`: `(name, width_u, en, ru, uk, de)`.
  Add a language by adding a column and a corner in `legends()`.
- **Colours per group**: `COLOURS` and `TEMPLATE_SLOT` in `scripts/build_test.py`.
- **Printer profile**: `templates/h2d_project_settings.config` is a full Bambu project config taken
  from an H2D project. Replace it with one from your printer; the script rebuilds the filament
  arrays to exactly four PETG slots and keeps everything else.
- **Per‑part slicer overrides** (infill, walls …): `PART_SETTINGS` in `scripts/build_test.py`.
- **Font**: drop a `.ttf` with Cyrillic into `fonts/` and point `FONT_PATH` at it.

## How the export works (for the curious)

Glyphs are converted to polylines (0.05 mm chord) before any boolean, letters are cut from the cap
and split into per‑material bodies, every mesh is run through `trimesh` (merge vertices, drop
degenerate faces, fix winding) and written into a Bambu‑format 3MF by hand:
`3D/Objects/*.model` per key, components in `3D/3dmodel.model`, part names / filament slots /
overrides in `Metadata/model_settings.config`, the printer config in
`Metadata/project_settings.config`. Bambu Studio's own CLI round‑trips the result without changes.

## Tests

```bash
.venv/bin/python -m pytest -q tests
```

Bounding boxes, base/top split plane, legend z‑range, zero intersection between parts, dish depth
and edge sag, corner alignment and gap of the legends, rounded variant. 20 tests, ~40 s.

## Roadmap

- [ ] Package the generator (`keycaps/` + JSON layouts + CLI) as described in `KEYCAPS_TZ.md`
- [ ] Measure the K98 Pro bottom row and right block widths
- [ ] Cherry stabiliser cut‑outs for ≥ 2u keys
- [ ] Printed comparison of flat / dish / round, then pick one as default
- [ ] Pre‑built 3MF packs in Releases

## License

Code — [MIT](LICENSE). Generated models — [CC BY 4.0](LICENSE-models). DejaVu Sans Bold is bundled
under its own free license (see `fonts/`).

---

<details>
<summary>По‑русски</summary>

Генератор 3D‑печатных MX‑кейкапов с легендами на четырёх языках (EN/RU/UK/DE) под Bambu Lab H2D.
Каждая клавиша это четыре тела: прозрачная база со стемом, чёрная крышка 2.2 мм, голубые EN+DE и
розовые RU+UK буквы. Буквы сквозные, через всю крышку, подсветка светит сквозь них. На выходе STL
на каждую деталь и готовый проект Bambu Studio с раскладкой по столу, слотами филаментов и нужными
настройками слайсера.

Три варианта колпачка: плоский (печать лицом вниз), с ямкой 0.6 мм (лицом вверх), со скруглёнными
кромками как у GravaStar. Важно: в проекте выставлен `resolution = 0`, без этого Bambu Studio 2.8
печатает круглые буквы чёрным.

Быстрый старт: `python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt`, потом
`.venv/bin/python scripts/build_alphabet.py`.

</details>
