"""Build every key that carries a RU/UK/DE legend (the "alphabet" set, 36 keys) as Bambu projects.

    .venv/bin/python scripts/build_alphabet.py          # both variants
    .venv/bin/python scripts/build_alphabet.py flat     # only out/alphabet.3mf        (flat top, face-down)
    .venv/bin/python scripts/build_alphabet.py dish     # only out/dish/alphabet_dish.3mf (0.6 mm dish, face-up)
    .venv/bin/python scripts/build_alphabet.py dish_round   # dish + GravaStar-like rounded edges -> out/dish/round/
    .venv/bin/python scripts/build_alphabet.py flat_round   # flat + rounded edges -> out/round/
    .venv/bin/python scripts/build_alphabet.py dish_round_qwertz   # ... + German QWERTZ DE legends -> out/dish/round/qwertz/

Variant name = "flat" or "dish", optionally followed by "_round" and/or "_qwertz".

Keys are laid out in three keyboard-like rows (QWERTY row, home row + ` and -, bottom row),
280 x 60 mm on the H2D bed. Same pipeline and slicer fixes as scripts/build_test.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_test as bt  # noqa: E402
import keycaps_gen as g  # noqa: E402

OUT_ROOT = g.OUT_DIR


KEYS_QWERTY = g.KEYS


def parse_variant(variant: str) -> tuple[bool, bool, bool]:
    tokens = variant.split("_")
    if tokens[0] not in ("flat", "dish") or any(t not in ("round", "qwertz") for t in tokens[1:]):
        raise SystemExit(f"unknown variant {variant!r}: flat|dish[_round][_qwertz]")
    return tokens[0] == "dish", "round" in tokens[1:], "qwertz" in tokens[1:]


def build(variant: str) -> str:
    dish, rnd, qwertz = parse_variant(variant)
    g.KEYS = g.qwertz_keys(KEYS_QWERTY) if qwertz else KEYS_QWERTY
    g.OUT_DIR = OUT_ROOT
    g.LEG_UNDERCUT = 0.6
    g.DISH_DEPTH = bt.DISH if dish else 0.0
    g.LEG_RAISE = 0.4 if dish else 0.0  # face-down: the face lies on the bed
    g.EDGE_ROUND, g.TOP_ROUND = (bt.ROUND_EDGE, bt.ROUND_TOP) if rnd else (0.0, 0.0)
    name = "alphabet" + ("_dish" if dish else "") + ("_round" if rnd else "") + ("_qwertz" if qwertz else "") + ".3mf"
    if dish:
        g.OUT_DIR = os.path.join(g.OUT_DIR, "dish")
    if rnd:
        g.OUT_DIR = os.path.join(g.OUT_DIR, "round")
    if qwertz:
        g.OUT_DIR = os.path.join(g.OUT_DIR, "qwertz")
    return bt.build_plate(bt.MULTILANG_ROWS, name)


if __name__ == "__main__":
    for v in sys.argv[1:] or ["flat", "dish"]:
        build(v)
