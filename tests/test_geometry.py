"""Geometry invariants for keycaps_gen (flat and dished variants)."""
import os
import sys

import cadquery as cq
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import keycaps_gen as g  # noqa: E402

g.FONT_PATH = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")
KEY = {k[0]: k for k in g.KEYS}
TOL = 0.01


def bb(w):
    return w.val().BoundingBox(tolerance=1e-3)


@pytest.fixture(params=[0.0, 0.6], ids=["flat", "dish"])
def dish(request, monkeypatch):
    monkeypatch.setattr(g, "DISH_DEPTH", request.param)
    return request.param


@pytest.mark.parametrize("name", ["S", "quote", "backslash", "backspace"])
def test_footprint_and_split(name, dish):
    base, top, legA, legB = g.build_key(*KEY[name])
    full = bb(base.union(top))
    w = KEY[name][1] * g.UNIT - g.GAP
    assert abs(full.xlen - w) < TOL and abs(full.ylen - 18.0) < TOL and abs(full.zlen - 9.0) < TOL
    split = g.HEIGHT - g.TOP_THK - dish
    assert abs(bb(base).zmax - split) < TOL and abs(bb(top).zmin - split) < TOL
    assert abs(bb(base).zmin) < TOL and abs(bb(top).zmax - g.HEIGHT) < TOL  # raise lives in the legends only


@pytest.mark.parametrize("name", ["S", "quote", "backslash"])
def test_legends_layer_and_no_intersection(name, dish):
    base, top, legA, legB = g.build_key(*KEY[name])
    legs = [l for l in (legA, legB) if l is not None]
    assert legs
    for leg in legs:
        assert leg.val().Volume() > 0.1
        b = bb(leg)
        assert b.zmax <= g.HEIGHT + g.LEG_RAISE + TOL
        if g.LEG_THROUGH and dish == 0:
            assert abs(b.zmax - (g.HEIGHT + g.LEG_RAISE)) < TOL  # letters stand proud of the flat face
        if g.LEG_THROUGH:
            # shine-through: legend spans the whole top plate and pokes LEG_UNDERCUT below the cavity ceiling
            assert abs(b.zmin - (g.HEIGHT - g.TOP_THK - g.LEG_UNDERCUT)) < TOL
        else:
            assert b.zmin >= g.HEIGHT - dish - g.LEG_DEPTH - TOL
        assert top.intersect(leg).val().Volume() < 1e-6
        assert base.intersect(leg).val().Volume() < 1e-6
    if legA is not None and legB is not None:
        assert legA.intersect(legB).val().Volume() < 1e-6


def test_dish_depth(dish):
    base, top, _, _ = g.build_key(*KEY["W"])

    def z_at(x, y):
        probe = cq.Workplane("XY").box(0.2, 0.2, 20, centered=(True, True, False)).translate((x, y, 0))
        return bb(probe.intersect(top)).zmax

    assert abs(z_at(0, 0) - (g.HEIGHT - dish)) < TOL
    # spherical dish through the corners: every edge sags the same, only the corners stay at full height
    assert abs(z_at(0, -6.3) - z_at(6.3, 0)) < TOL
    assert z_at(6.3, 6.3) > g.HEIGHT - 0.15
    if dish:
        assert g.HEIGHT - dish + TOL < z_at(0, -6.3) < g.HEIGHT - 0.2


def test_big_legends_hug_opposite_corners():
    base, top, legA, legB = g.build_key(*KEY["W"])
    tw = g.UNIT - g.GAP - 2 * g.TOP_INSET
    hx = tw / 2 - g.LEG_MARGIN
    a, b = bb(legA), bb(legB)
    assert abs(a.xmin + hx) < TOL and abs(a.ymax - hx) < TOL  # EN top-left
    assert abs(b.xmax - hx) < TOL and abs(b.ymin + hx) < TOL  # RU bottom-right
    assert a.ymin - b.ymax >= g.LEG_GAP - TOL  # vertical gap between the two big letters


def test_small_legends_in_remaining_corners():
    _, _, legA, legB = g.build_key(*KEY["quote"])  # ' Э Є Ä
    tw = g.UNIT - g.GAP - 2 * g.TOP_INSET
    hx = tw / 2 - g.LEG_MARGIN
    a, b = bb(legA), bb(legB)
    assert abs(a.xmax - hx) < TOL and abs(a.ymax - hx) < TOL   # DE top-right (legA also holds EN)
    assert abs(b.xmin + hx) < TOL and abs(b.ymin + hx) < TOL   # UK bottom-left (legB also holds RU)


def test_pairs_keep_gap():
    for name in ("O", "W", "A", "Q"):
        _, _, legA, legB = g.build_key(*KEY[name])
        assert bb(legA).ymin - bb(legB).ymax >= g.LEG_GAP - TOL


def test_rounded_variant_builds(monkeypatch):
    monkeypatch.setattr(g, "EDGE_ROUND", 2.0)
    monkeypatch.setattr(g, "TOP_ROUND", 1.0)
    monkeypatch.setattr(g, "DISH_DEPTH", 0.6)
    for name in ("S", "backslash"):
        base, top, legA, legB = g.build_key(*KEY[name])
        full = bb(base.union(top))
        w = KEY[name][1] * g.UNIT - g.GAP
        assert abs(full.xlen - w) < TOL and abs(full.ylen - 18.0) < TOL and abs(full.zlen - 9.0) < TOL
        assert base.val().isValid() and top.val().isValid()
        for leg in (legA, legB):
            assert top.intersect(leg).val().Volume() < 1e-6
    # corner is rounded: nothing of a 1u cap at the sharp corner position
    base, top, _, _ = g.build_key(*KEY["S"])
    probe = cq.Workplane("XY").box(0.3, 0.3, 20, centered=(True, True, False)).translate((8.85, 8.85, 0))
    assert top.union(base).intersect(probe).val().Volume() < 1e-6


def test_qwertz_variant_adds_german_legends():
    keys = {k[0]: k for k in g.qwertz_keys()}
    assert keys["Z"][5] == "Y" and keys["Y"][5] == "Z"
    assert keys["rbracket"][5] == "+" and keys["backslash"][5] == "#" and keys["slash"][5] == "-" and keys["grave"][5] == "^"
    assert keys["quote"][5] == "Ä" and keys["minus"][5] == "ß"  # untouched
    assert KEY["Z"][5] is None  # the default layout is not modified
    base, top, legA, legB = g.build_key(*keys["Z"])
    tw = g.UNIT - g.GAP - 2 * g.TOP_INSET
    hx = tw / 2 - g.LEG_MARGIN
    a = bb(legA)
    assert len(legA.val().Solids()) == 2  # Z (top-left) + Y (top-right, DE)
    assert abs(a.xmax - hx) < TOL and abs(a.xmin + hx) < TOL
    assert top.intersect(legA).val().Volume() < 1e-6 and legA.intersect(legB).val().Volume() < 1e-6


@pytest.mark.parametrize("dish", [0.0, 0.6])
def test_embossed_legends_sit_on_the_face(monkeypatch, dish):
    monkeypatch.setattr(g, "LEG_EMBOSS", 0.4)
    monkeypatch.setattr(g, "LEG_THROUGH", False)
    monkeypatch.setattr(g, "DISH_DEPTH", dish)
    base, top, legA, legB = g.build_key(*KEY["S"])
    assert abs(bb(top).zmax - g.HEIGHT) < TOL  # cap height unchanged, relief lives in the legends only
    for leg in (legA, legB):
        b = bb(leg)
        # anchored LEG_EMBOSS_ANCHOR below the face, standing LEG_EMBOSS above it
        assert b.zmin >= g.HEIGHT - dish - g.LEG_EMBOSS_ANCHOR - TOL
        assert b.zmax <= g.HEIGHT + 0.4 + TOL and b.zmax > g.HEIGHT - dish + 0.3
        assert leg.val().Volume() > 0.5
        assert top.intersect(leg).val().Volume() < 1e-6   # pocket cut, no overlap
        assert base.intersect(leg).val().Volume() < 1e-6
        # the anchor is real: part of the legend lies below the face
        below = leg.intersect(cq.Workplane("XY").box(200, 200, g.HEIGHT - dish, centered=(True, True, False)))
        assert below.val().Volume() > 0.2
