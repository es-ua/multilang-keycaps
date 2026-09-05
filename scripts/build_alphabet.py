"""Build every key that carries a RU/UK/DE legend (the "alphabet" set, 36 keys) as Bambu projects.

    .venv/bin/python scripts/build_alphabet.py          # both variants
    .venv/bin/python scripts/build_alphabet.py flat     # only out/alphabet.3mf        (flat top, face-down)
    .venv/bin/python scripts/build_alphabet.py dish     # only out/dish/alphabet_dish.3mf (0.6 mm dish, face-up)

Keys are laid out in three keyboard-like rows (QWERTY row, home row + ` and -, bottom row),
280 x 60 mm on the H2D bed. Same pipeline and slicer fixes as scripts/build_test.py.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_test as bt  # noqa: E402
import keycaps_gen as g  # noqa: E402

OUT_ROOT = g.OUT_DIR


def build(variant: str) -> str:
    g.OUT_DIR = OUT_ROOT
    if variant == "dish":
        g.DISH_DEPTH = bt.DISH
        g.LEG_RAISE = 0.4
        g.LEG_UNDERCUT = 0.6
        g.OUT_DIR = os.path.join(OUT_ROOT, "dish")
        return bt.build_plate(bt.MULTILANG_ROWS, "alphabet_dish.3mf")
    g.DISH_DEPTH = 0.0
    g.LEG_RAISE = 0.0  # face-down: the face lies on the bed
    g.LEG_UNDERCUT = 0.6
    return bt.build_plate(bt.MULTILANG_ROWS, "alphabet.3mf")


if __name__ == "__main__":
    wanted = sys.argv[1:] or ["flat", "dish"]
    for v in wanted:
        if v not in ("flat", "dish"):
            sys.exit(f"unknown variant {v!r}: use flat and/or dish")
        build(v)
