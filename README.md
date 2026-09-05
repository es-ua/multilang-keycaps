<div align="center">

# multilang-keycaps

**3D‑printable MX keycaps with EN · RU · UK · DE legends — generated, not bought.**

Parametric [CadQuery](https://cadquery.readthedocs.io) generator that outputs every key of a layout as
separate multi‑material bodies, ready for Bambu Lab H2D / AMS.

[![License: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Models: CC BY 4.0](https://img.shields.io/badge/models-CC%20BY%204.0-lightgrey.svg)](LICENSE-models)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](pyproject.toml)
[![CadQuery](https://img.shields.io/badge/built%20with-CadQuery-orange.svg)](https://github.com/CadQuery/cadquery)

<!-- TODO: docs/images/hero.png — render of the alpha block, white/red on black -->

</div>

---

## Why

Off‑the‑shelf keycap sets rarely cover more than two languages, and none do
Ukrainian + Russian + German on a single QWERTY set. If you type in four
languages, your options are stickers or a compromise. This project makes the
set you actually need — and lets you re‑generate it in an afternoon if you
change your mind about a color, a font, or a key width.

## What you get

Each key is exported as **four bodies** that stack into one multi‑material print
(printed face‑down on a smooth plate, no supports):

| Body | Material | Purpose |
|------|----------|---------|
| `_base` | translucent PETG | walls + MX stem — per‑key RGB shines through |
| `_top` | black PETG‑CF | 2.2 mm opaque cap with legend pockets |
| `_legA` | white PETG | Latin + German legends |
| `_legB` | red PETG | Cyrillic legends (RU + UK) |

Plus one multi‑part `.3mf` per key so Bambu Studio imports it with parts already split.

### Legend layout

```
┌──────────────┐
│ EN        RU │
│              │
│ DE        UK │   UK is printed only where it differs from RU
└──────────────┘
```

| Key | EN | RU | UK | DE |
|-----|----|----|----|----|
| `S` | S | Ы | І | |
| `]` | ] | Ъ | Ї | |
| `'` | ' | Э | Є | Ä |
| `[` | [ | Х | | Ü |
| `;` | ; | Ж | | Ö |
| `-` | - | | | ß |
| `\` | \ | | Ґ | |
| `` ` `` | ` | Ё | | |

Single‑legend keys (digits, F‑row, modifiers) get one centered legend.

## Quick start

```bash
git clone https://github.com/es-ua/multilang-keycaps
cd multilang-keycaps
uv sync                      # or: pip install -e .
uv run keycaps build --test  # Q, S, ], ', -, Backspace → out/
```

Then:

```bash
uv run keycaps build --layout ansi_104          # full set
uv run keycaps build --keys Q W E R T Y         # subset
uv run keycaps build --layout k98_pro --plate   # one 3MF, all keys laid out face-down
```

Requires a font with Cyrillic glyphs. DejaVu Sans Bold is the default
(`apt install fonts-dejavu-core`); override with `--font /path/to/font.ttf`.

## Printing (Bambu Lab H2D)

Print **face‑down**. Only the first ~11 layers change color, so purge waste is small.

| Nozzle | Filaments | Notes |
|--------|-----------|-------|
| Left | translucent PETG, black PETG‑CF | both PETG → minimal purge; hardened gears for CF |
| Right | white PETG, red PETG | keeps carbon out of the white legends |

Layer order from the plate up: legends (0.45 mm) → black top (2.2 mm) → translucent base.

Tips that matter with PETG‑CF: dry it (6–8 h), 0.4 mm hardened nozzle, and if the
stem is tight, bump `stem_clearance` in the config — CF is stiffer than plain PETG.

Full notes: [`docs/printing.md`](docs/printing.md).

## Geometry

Flat XDA‑style profile, tuned for a wide legend area:

| Parameter | Value |
|-----------|-------|
| 1u footprint | 18.0 × 18.0 mm (19.05 mm pitch) |
| Height | 9.0 mm |
| Top plate | 14.0 × 14.0 mm |
| Wall | 1.4 mm |
| Top thickness | 2.2 mm |
| Legend depth | 0.45 mm |
| Stem | MX cross, +0.10 / +0.05 mm clearance |

All values live in `keycaps/config.py` and can be overridden with `--config my.yaml`.

## Make it yours

**Layouts are data.** `layouts/*.json`:

```json
{ "name": "S", "width_u": 1,
  "legends": [
    { "text": "S", "pos": "tl", "group": "A" },
    { "text": "Ы", "pos": "tr", "group": "B" },
    { "text": "І", "pos": "br", "group": "B" }
  ]}
```

- Add a language: add a legend with a new `pos`/`group`.
- Change colors: groups map to filaments in the slicer, nothing to change in code.
- Other board: edit `width_u` per key. `layouts/k98_pro.json` targets the
  GravaStar Mercury K98 Pro; bottom‑row widths are marked `TODO` until measured.

## Compatibility

- Any MX‑stem switch, mechanical or Hall‑effect (tested: GravaStar Mercury V75, Mercury K98 Pro).
- Windows / macOS / Linux for generation; any slicer that reads STL or 3MF.

## Roadmap

- [ ] Cherry stabilizer cutouts for ≥ 2u keys
- [ ] Sculpted (row‑profiled) variant
- [ ] Shine‑through legend mode
- [ ] Pre‑built STL packs in Releases

## License

Code — [MIT](LICENSE). Generated models — [CC BY 4.0](LICENSE-models).

---

<details>
<summary>По‑русски</summary>

Генератор 3D‑печатных MX‑кейкапов с легендами на четырёх языках (EN/RU/UK/DE)
под многоцветную печать на Bambu Lab H2D. Каждая клавиша — четыре тела: прозрачная
база (подсветка проходит), чёрная крышка, белые латинские/немецкие и красные
кириллические легенды. Раскладки и цветовые группы — обычный JSON, менять код не нужно.

Быстрый старт: `uv sync && uv run keycaps build --test`.

</details>