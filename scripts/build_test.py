"""Build keycaps and write a Bambu Studio project (.3mf) with keys laid face-down.

    .venv/bin/python scripts/build_test.py               # 6-key test set -> out/test_plate.3mf
    .venv/bin/python scripts/build_test.py --multilang   # every key with RU/UK/DE legend -> out/multilang_plate.3mf
    .venv/bin/python scripts/build_test.py Q W E         # any keys from keycaps_gen.KEYS -> out/custom_plate.3mf

In the 3MF every key is ONE object with parts ``_base/_top/_legA/_legB`` and the
filament slot is already assigned per part (1 base, 2 top, 3 legA, 4 legB), so Bambu
Studio opens it ready to slice. Per-key STLs are written alongside.

Font: fonts/DejaVuSans-Bold.ttf (Cyrillic + ⌫⇥⏎⇧ glyphs). Interim helper until
the ``keycaps`` package / ``keycaps build`` CLI from KEYCAPS_TZ.md exists.
"""
import os
import sys
import uuid
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import keycaps_gen as g  # noqa: E402

g.FONT_PATH = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")

PLATE_GAP = 3.0  # mm between caps on the bed
BED = (350.0, 320.0)  # Bambu Lab H2D; the plate is centered on the bed
PARTS = ("base", "top", "legA", "legB")
FILAMENT = {"base": 1, "top": 2, "legA": 3, "legB": 4}  # AMS slot per part
# H2D dual nozzle: filament -> extruder (1 left, 2 right). PETG + PETG-CF left, white/red right.
FILAMENT_MAPS = "1 1 2 2"

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


def write_bambu_3mf(path: str, keys: list[dict]) -> None:
    """keys: [{name, x, y, parts: [(suffix, verts, tris), ...]}] with x/y in bed coords."""
    files: dict[str, str] = {}
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
            f'      <mesh_stat face_count="{n}" edges_fixed="0" degenerate_facets="0" '
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
        f'    <metadata key="filament_maps" value="{FILAMENT_MAPS}"/>\n'
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


def build_plate(rows: list[list[str]], out_name: str) -> None:
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
            shapes = g.build_key(*k)
            g.export(name, *shapes)
            w = k[1] * g.UNIT - g.GAP
            cx = x + w / 2
            x += w + PLATE_GAP
            parts = []
            for suffix, shape in zip(PARTS, shapes):
                if shape is None:
                    continue
                # face-down: flip about X so the legend face sits on z=0; key stays centered at origin
                s = shape.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, g.HEIGHT))
                parts.append((suffix, *s.val().tessellate(0.01, 0.1)))
            keys.append({"name": name, "x": cx, "y": cy, "parts": parts})

    out = os.path.join(g.OUT_DIR, out_name)
    write_bambu_3mf(out, keys)
    n_parts = sum(len(k["parts"]) for k in keys)
    print(f"ok {out}: {len(keys)} keys, {n_parts} parts, plate {plate_w:.1f} x {plate_h:.1f} mm")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--multilang"]:
        build_plate(MULTILANG_ROWS, "multilang_plate.3mf")
    elif args:
        build_plate([args], "custom_plate.3mf")
    else:
        build_plate([g.TEST_SET], "test_plate.3mf")
