"""Build keycaps and write a Bambu Studio project (.3mf) with keys laid face-down.

    .venv/bin/python scripts/build_test.py               # 6-key test set -> out/test_plate.3mf
    .venv/bin/python scripts/build_test.py --multilang   # every key with RU/UK/DE legend -> out/multilang_plate.3mf
    .venv/bin/python scripts/build_test.py Q W E         # any keys from keycaps_gen.KEYS -> out/custom_plate.3mf
    .venv/bin/python scripts/build_test.py -o qwe.3mf Q W E / A S D / Z X C   # "/" starts a new row
    .venv/bin/python scripts/build_test.py --dish ...    # concave (0.6 mm) top, laid FACE-UP; output gets _dish suffix
    .venv/bin/python scripts/build_test.py --undercut 0.3 ...   # legend bump below the cavity ceiling (default 0.6;
                                                                # face-up these bumps need slicer supports)
    .venv/bin/python scripts/build_test.py --raise 0.4 ...      # legend stands proud of the face (default 0.4 with
                                                                # --dish, 0 face-down where the face lies on the bed)
    .venv/bin/python scripts/build_test.py --round ...          # GravaStar-like rounded cap: 2 mm corner fillets,
                                                                # 1 mm top-edge fillet; output gets _round suffix
    .venv/bin/python scripts/build_test.py --qwertz ...         # German QWERTZ DE legends (Z<->Y, + # - ^);
                                                                # output gets _qwertz suffix
    .venv/bin/python scripts/build_test.py --emboss ...         # opaque white/red letters embossed 0.4 mm on top of
                                                                # the face (no shine-through), always face-up; _emboss

In the 3MF every key is ONE object with parts ``_base/_top/_legA/_legB`` and the
filament slot is already assigned per part (1 clear base, 2 black top, 3 translucent blue
legA, 4 translucent pink legB), so Bambu Studio opens it ready to slice. Per-key STLs are written alongside.

Font: fonts/DejaVuSans-Bold.ttf (Cyrillic + ⌫⇥⏎⇧ glyphs). Interim helper until
the ``keycaps`` package / ``keycaps build`` CLI from KEYCAPS_TZ.md exists.
"""
import json
import os

import cadquery as cq
import sys
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import numpy as np  # noqa: E402
import trimesh  # noqa: E402

import keycaps_gen as g  # noqa: E402

KEYS_QWERTY = g.KEYS
g.FONT_PATH = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")

PLATE_GAP = 3.0  # mm between caps on the bed
TESS_TOL, TESS_ANG = 0.05, 0.5  # mesh tolerance (mm) and angular tolerance (rad) for STL/3MF export
DISH = 0.6  # mm, dish depth used by --dish
ROUND_EDGE, ROUND_TOP = 2.0, 1.0  # mm, fillets used by --round
EMBOSS = 0.4  # mm, relief height used by --emboss
EMBOSS_COLOURS = {"legA": "#FFFFFF", "legB": "#E02020"}  # opaque white / red PETG Basic
BED = (350.0, 320.0)  # Bambu Lab H2D; the plate is centered on the bed
# Part order matters: where parts overlap, Bambu Studio gives precedence to the part listed FIRST.
# Legends go before the black top so the slicer never fills a letter with black.
PARTS = ("base", "legA", "legB", "top")
SLOTS = ("base", "top", "legA", "legB")  # filament slot order: 1 clear, 2 black, 3 blue, 4 pink
FILAMENT = {name: i + 1 for i, name in enumerate(SLOTS)}  # AMS slot per part
COLOURS = {"base": "#E6E6E6", "top": "#202020", "legA": "#7FC8FF", "legB": "#FF8AC8"}  # clear, black, blue, pink
# Which filament of the template each slot clones (values + preset id): all PETG.
# Template slot 0 = "Bambu PETG Translucent", slot 2 = "Bambu PETG Basic".
TEMPLATE_SLOT = {"base": 0, "top": 2, "legA": 0, "legB": 0}
# Per-part slicer overrides (Bambu model_settings.config keys). Translucent parts print solid so the
# light path has no infill pattern inside.
FLUSH_DEFAULT = "300"  # mm³ purge between two different translucent colours; "Re-calculate" in Studio refines it
PART_SETTINGS = {
    "base": {"sparse_infill_density": "100%"},
    "legA": {"sparse_infill_density": "100%"},
    "legB": {"sparse_infill_density": "100%"},
}
# H2D dual nozzle: filament -> extruder (1 left, 2 right). PETG + PETG-CF left, white/red right.
NOZZLE = {"base": 1, "top": 1, "legA": 2, "legB": 2}
# Full Bambu Studio project config (printer/process/filament presets) so the 3MF opens as an
# H2D project instead of "invalid config, load geometry only". Slots 1-4 are re-coloured.
PROJECT_TEMPLATE = os.path.join(ROOT, "templates", "h2d_project_settings.config")

# Keyboard-like rows for the multilang set (grave/minus tucked onto the home row).
MULTILANG_ROWS = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "lbracket", "rbracket", "backslash"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L", "semicolon", "quote", "grave", "minus"],
    ["Z", "X", "C", "V", "B", "N", "M", "comma", "period", "slash"],
]

XML_HEAD = '<?xml version="1.0" encoding="UTF-8"?>\n'
NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="p"')


def _mesh_xml(obj_id: int, verts, tris) -> str:
    out = [f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">', "   <mesh>", "    <vertices>"]
    out.extend(f'     <vertex x="{v.x:.4f}" y="{v.y:.4f}" z="{v.z:.4f}"/>' for v in verts)
    out.append("    </vertices>")
    out.append("    <triangles>")
    out.extend(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
    out.append("    </triangles>")
    out.append("   </mesh>")
    out.append("  </object>")
    return "\n".join(out)


def project_settings() -> tuple[str, str]:
    """Return (project_settings.config JSON, plate filament_maps) built from the template.

    The template has N filaments (some PLA). Rebuild every per-filament array so the project has
    exactly len(PARTS) slots, each a clone of a PETG filament from the template (TEMPLATE_SLOT).
    """
    cfg = json.load(open(PROJECT_TEMPLATE))
    n = len(cfg["filament_colour"])
    idx = [TEMPLATE_SLOT[p] for p in SLOTS]
    m = len(idx)
    for key, v in list(cfg.items()):
        if not isinstance(v, list) or key == "different_settings_to_system":
            continue
        if len(v) == n:                       # one value per filament
            cfg[key] = [v[i] for i in idx]
        elif len(v) == 2 * n:                 # per filament × 2 extruders
            cfg[key] = [v[2 * i + e] for i in idx for e in range(2)]
        elif len(v) == 4 * n:                 # per filament × 4 (AMS drying tables)
            cfg[key] = [v[4 * i + e] for i in idx for e in range(4)]
        elif len(v) == 2 * n * n:             # flush volume matrix, one n×n block per extruder
            new = []
            for e in range(2):
                for ia, a in enumerate(idx):
                    for ib, b in enumerate(idx):
                        val = v[e * n * n + a * n + b]
                        if ia != ib and float(val) == 0:
                            val = FLUSH_DEFAULT  # slots cloned from the same template filament: never 0
                        new.append(val)
            cfg[key] = new
    cfg["filament_self_index"] = [str(i + 1) for i in range(m) for _ in range(2)]
    cfg["different_settings_to_system"] = [""] * (m + 2)  # print + filaments + printer
    cfg["filament_colour"] = [COLOURS[p] for p in SLOTS]
    fmap = [str(NOZZLE[p]) for p in SLOTS]
    cfg["filament_map"] = fmap
    cfg["filament_map_mode"] = "Manual"
    # no slicer supports baked into the project; the user decides in Bambu Studio
    cfg["enable_support"] = "0"
    # Bambu Studio 2.8 bug: with the default "resolution" (0.012 mm contour simplification) the slicer
    # drops multi-part pockets shaped like curved glyphs (S, C, O, Q, Ф) and fills them with the top
    # part's filament. resolution = 0 disables the simplification; verified on the sliced G-code.
    cfg["resolution"] = "0"
    cfg["different_settings_to_system"] = ["" if v == "enable_support" else v
                                           for v in cfg.get("different_settings_to_system", [])]
    return json.dumps(cfg, indent=4, ensure_ascii=False), " ".join(fmap)


def set_emboss() -> None:
    """Switch to opaque embossed legends: relief on top of the face, no pocket, white/red PETG Basic."""
    g.LEG_EMBOSS = EMBOSS
    g.LEG_THROUGH = False
    g.LEG_RAISE = 0.0
    g.LEG_UNDERCUT = 0.0
    COLOURS.update(EMBOSS_COLOURS)
    TEMPLATE_SLOT["legA"] = TEMPLATE_SLOT["legB"] = TEMPLATE_SLOT["top"]  # PETG Basic preset values
    PART_SETTINGS.pop("legA", None)
    PART_SETTINGS.pop("legB", None)


def clean_mesh(verts, tris):
    """Make an export mesh slicer-proof: merge duplicate vertices, drop degenerate triangles and
    force consistent outward winding. CadQuery's tessellation of boolean-cut pockets (letters S, C, Q,
    Ф) left a few inverted wall triangles; Bambu Studio then lost the whole pocket and filled it black."""
    m = trimesh.Trimesh(np.array([(v.x, v.y, v.z) for v in verts]), np.array(tris, dtype=np.int64), process=True)
    m.update_faces(m.nondegenerate_faces())
    m.remove_unreferenced_vertices()
    trimesh.repair.fix_winding(m)
    trimesh.repair.fix_normals(m)
    if not m.is_watertight:
        trimesh.repair.fill_holes(m)
    V = [cq.Vector(*row) for row in m.vertices]
    T = [tuple(int(i) for i in f) for f in m.faces]
    return V, T


def write_bambu_3mf(path: str, keys: list[dict]) -> None:
    """keys: [{name, x, y, parts: [(suffix, verts, tris), ...]}] with x/y in bed coords."""
    files: dict[str, str] = {}
    files["Metadata/project_settings.config"], filament_maps = project_settings()
    next_id = 1
    model_objects, build_items, rels, config_objects, instances = [], [], [], [], []

    for key in keys:
        part_ids = []
        meshes = []
        for suffix, verts, tris in key["parts"]:
            part_ids.append((next_id, suffix, len(tris)))
            meshes.append(_mesh_xml(next_id, verts, tris))
            next_id += 1
        obj_id = next_id
        next_id += 1

        obj_file = f"3D/Objects/object_{obj_id}.model"
        files[obj_file] = (XML_HEAD + f'<model unit="millimeter" xml:lang="en-US" {NS}>\n'
                           ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                           + "\n".join(meshes) + "\n </resources>\n <build/>\n</model>\n")
        rels.append(f' <Relationship Target="/{obj_file}" Id="rel-{obj_id}" '
                    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')

        comps = "\n".join(
            f'    <component p:path="/{obj_file}" objectid="{pid}" p:UUID="{uuid.uuid4()}" '
            'transform="1 0 0 0 1 0 0 0 1 0 0 0"/>' for pid, _, _ in part_ids)
        model_objects.append(f'  <object id="{obj_id}" p:UUID="{uuid.uuid4()}" type="model">\n'
                             f"   <components>\n{comps}\n   </components>\n  </object>")
        build_items.append(f'  <item objectid="{obj_id}" p:UUID="{uuid.uuid4()}" '
                           f'transform="1 0 0 0 1 0 0 0 1 {key["x"]:.4f} {key["y"]:.4f} 0" printable="1"/>')

        parts_cfg = "\n".join(
            f'    <part id="{pid}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{key["name"]}_{suffix}"/>\n'
            f'      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n'
            f'      <metadata key="extruder" value="{FILAMENT[suffix]}"/>\n'
            + "".join(f'      <metadata key="{k}" value="{v}"/>\n' for k, v in PART_SETTINGS.get(suffix, {}).items())
            + f'      <mesh_stat face_count="{n}" edges_fixed="0" degenerate_facets="0" '
            f'facets_removed="0" facets_reversed="0" backwards_edges="0"/>\n'
            f"    </part>" for pid, suffix, n in part_ids)
        config_objects.append(f'  <object id="{obj_id}">\n'
                              f'    <metadata key="name" value="{key["name"]}"/>\n'
                              f'    <metadata key="extruder" value="{FILAMENT["base"]}"/>\n'
                              f'    <metadata face_count="{sum(n for _, _, n in part_ids)}"/>\n'
                              f"{parts_cfg}\n  </object>")
        instances.append(f'    <model_instance>\n      <metadata key="object_id" value="{obj_id}"/>\n'
                         f'      <metadata key="instance_id" value="0"/>\n    </model_instance>')

    files["3D/3dmodel.model"] = (
        XML_HEAD + f'<model unit="millimeter" xml:lang="en-US" {NS}>\n'
        ' <metadata name="Application">BambuStudio-02.01.01.52</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        ' <metadata name="Title">multilang-keycaps</metadata>\n'
        " <resources>\n" + "\n".join(model_objects) + "\n </resources>\n"
        f' <build p:UUID="{uuid.uuid4()}">\n' + "\n".join(build_items) + "\n </build>\n</model>\n")
    files["3D/_rels/3dmodel.model.rels"] = (
        XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(rels) + "\n</Relationships>\n")
    files["Metadata/model_settings.config"] = (
        XML_HEAD + "<config>\n" + "\n".join(config_objects) + "\n  <plate>\n"
        '    <metadata key="plater_id" value="1"/>\n'
        '    <metadata key="plater_name" value="keycaps"/>\n'
        '    <metadata key="locked" value="false"/>\n'
        '    <metadata key="filament_map_mode" value="Manual"/>\n'
        f'    <metadata key="filament_maps" value="{filament_maps}"/>\n'
        + "\n".join(instances) + "\n  </plate>\n</config>\n")
    files["_rels/.rels"] = (
        XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    files["[Content_Types].xml"] = (
        XML_HEAD + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="config" ContentType="application/xml"/>\n</Types>\n')

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)


def build_plate(rows: list[list[str]], out_name: str) -> str:
    by_name = {k[0]: k for k in g.KEYS}
    missing = {n for row in rows for n in row} - set(by_name)
    if missing:
        sys.exit(f"unknown keys: {sorted(missing)}")

    depth = g.UNIT - g.GAP
    row_w = [sum(by_name[n][1] * g.UNIT - g.GAP for n in row) + PLATE_GAP * (len(row) - 1) for row in rows]
    plate_w, plate_h = max(row_w), len(rows) * depth + (len(rows) - 1) * PLATE_GAP
    x0 = (BED[0] - plate_w) / 2
    y0 = (BED[1] + plate_h) / 2 - depth / 2  # first row at the top (far side) like a keyboard

    keys = []
    for r, row in enumerate(rows):
        cy = y0 - r * (depth + PLATE_GAP)
        x = x0
        for name in row:
            k = by_name[name]
            shapes = dict(zip(("base", "top", "legA", "legB"), g.build_key(*k)))
            g.export(name, *(shapes[n] for n in ("base", "top", "legA", "legB")))
            w = k[1] * g.UNIT - g.GAP
            cx = x + w / 2
            x += w + PLATE_GAP
            parts = []
            for suffix in PARTS:
                shape = shapes[suffix]
                if shape is None:
                    continue
                if g.DISH_DEPTH > 0 or g.LEG_EMBOSS > 0:
                    s = shape  # dished or embossed caps print face-up: stem down, face on top
                else:
                    # face-down: flip about X so the legend face sits on z=0; key stays centered at origin
                    s = shape.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, g.HEIGHT))
                parts.append((suffix, *clean_mesh(*s.val().tessellate(TESS_TOL, TESS_ANG))))
            keys.append({"name": name, "x": cx, "y": cy, "parts": parts})

    out = os.path.join(g.OUT_DIR, out_name)
    write_bambu_3mf(out, keys)
    with open(out.replace(".3mf", "_layout.json"), "w") as fh:  # key -> bed position, for G-code checks
        json.dump({k["name"]: [k["x"], k["y"]] for k in keys}, fh, indent=1, ensure_ascii=False)
    n_parts = sum(len(k["parts"]) for k in keys)
    face = ("face-UP (dish %.1f mm)" % g.DISH_DEPTH if g.DISH_DEPTH > 0
            else "face-UP (flat, embossed)" if g.LEG_EMBOSS > 0 else "face-down (flat)")
    legs = (f"embossed {g.LEG_EMBOSS:.1f} mm opaque" if g.LEG_EMBOSS > 0
            else f"undercut {g.LEG_UNDERCUT:.1f} mm, raise {g.LEG_RAISE:.1f} mm")
    print(f"ok {out}: {len(keys)} keys, {n_parts} parts, plate {plate_w:.1f} x {plate_h:.1f} mm, {face}, legends {legs}")
    return out


def parse_rows(tokens: list[str]) -> list[list[str]]:
    rows, cur = [], []
    for t in tokens:
        if t == "/":
            if cur:
                rows.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        rows.append(cur)
    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    out_name = None
    if "-o" in args:
        i = args.index("-o")
        out_name = args[i + 1]
        del args[i:i + 2]
    undercut = raise_ = None
    if "--undercut" in args:
        i = args.index("--undercut")
        undercut = float(args[i + 1])
        del args[i:i + 2]
    if "--raise" in args:
        i = args.index("--raise")
        raise_ = float(args[i + 1])
        del args[i:i + 2]
    if "--dish" in args:
        args.remove("--dish")
        g.DISH_DEPTH = DISH
        g.OUT_DIR = os.path.join(g.OUT_DIR, "dish")  # keep per-key STLs apart from the flat ones
        if out_name:
            out_name = out_name.replace(".3mf", "_dish.3mf")
    if "--round" in args:
        args.remove("--round")
        g.EDGE_ROUND, g.TOP_ROUND = ROUND_EDGE, ROUND_TOP
        g.OUT_DIR = os.path.join(g.OUT_DIR, "round")
        if out_name:
            out_name = out_name.replace(".3mf", "_round.3mf")
    if "--qwertz" in args:
        args.remove("--qwertz")
        g.KEYS = g.qwertz_keys()
        g.OUT_DIR = os.path.join(g.OUT_DIR, "qwertz")
        if out_name:
            out_name = out_name.replace(".3mf", "_qwertz.3mf")
    if "--emboss" in args:
        args.remove("--emboss")
        set_emboss()
        g.OUT_DIR = os.path.join(g.OUT_DIR, "emboss")
        if out_name:
            out_name = out_name.replace(".3mf", "_emboss.3mf")
    if undercut is not None:
        g.LEG_UNDERCUT = undercut
    if raise_ is None and g.DISH_DEPTH == 0:
        raise_ = 0.0  # face-down: the face must stay flat on the bed
    if raise_ is not None:
        g.LEG_RAISE = raise_
    suffix = (("_dish" if g.DISH_DEPTH > 0 else "") + ("_round" if g.EDGE_ROUND > 0 else "")
              + ("_qwertz" if g.KEYS is not KEYS_QWERTY else "") + ("_emboss" if g.LEG_EMBOSS > 0 else ""))
    if args == ["--multilang"]:
        build_plate(MULTILANG_ROWS, out_name or f"multilang_plate{suffix}.3mf")
    elif args:
        build_plate(parse_rows(args), out_name or f"custom_plate{suffix}.3mf")
    else:
        build_plate([g.TEST_SET], out_name or f"test_plate{suffix}.3mf")
