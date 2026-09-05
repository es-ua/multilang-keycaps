"""Build every key that carries a RU/UK/DE legend (the "alphabet" set, 36 keys) as Bambu projects.

    .venv/bin/python scripts/build_alphabet.py          # both variants
    .venv/bin/python scripts/build_alphabet.py flat     # only out/alphabet.3mf        (flat top, face-down)
    .venv/bin/python scripts/build_alphabet.py dish     # only out/dish/alphabet_dish.3mf (0.6 mm dish, face-up)
    .venv/bin/python scripts/build_alphabet.py dish_round   # dish + GravaStar-like rounded edges -> out/dish/round/
    .venv/bin/python scripts/build_alphabet.py flat_round   # flat + rounded edges -> out/round/

Keys are laid out in three keyboard-like rows (QWERTY row, home row + ` and -, bottom row),
280 x 60 mm on the H2D bed. Same pipeline and slicer fixes as scripts/build_test.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_test as bt  # noqa: E402
import keycaps_gen as g  # noqa: E402

OUT_ROOT = g.OUT_DIR


VARIANTS = ("flat", "dish", "flat_round", "dish_round")


def build(variant: str) -> str:
    dish = variant.startswith("dish")
    rnd = variant.endswith("_round")
    g.OUT_DIR = OUT_ROOT
    g.LEG_UNDERCUT = 0.6
    g.DISH_DEPTH = bt.DISH if dish else 0.0
    g.LEG_RAISE = 0.4 if dish else 0.0  # face-down: the face lies on the bed
    g.EDGE_ROUND, g.TOP_ROUND = (bt.ROUND_EDGE, bt.ROUND_TOP) if rnd else (0.0, 0.0)
    name = "alphabet" + ("_dish" if dish else "") + ("_round" if rnd else "") + ".3mf"
    if dish:
        g.OUT_DIR = os.path.join(g.OUT_DIR, "dish")
    if rnd:
        g.OUT_DIR = os.path.join(g.OUT_DIR, "round")
    return bt.build_plate(bt.MULTILANG_ROWS, name)


if __name__ == "__main__":
    wanted = sys.argv[1:] or ["flat", "dish"]
    for v in wanted:
        if v not in VARIANTS:
            sys.exit(f"unknown variant {v!r}: use one of {VARIANTS}")
        build(v)
