"""Build the 6-key test set (Q, S, ], ', -, Backspace 2u).

Writes per-key STLs (_base/_top/_legA/_legB) plus one multi-object
``out/test_plate.3mf`` with every key laid face-down on the bed, 3 mm apart.

    .venv/bin/python scripts/build_test.py            # test set
    .venv/bin/python scripts/build_test.py Q W E      # any keys from keycaps_gen.KEYS

Font: fonts/DejaVuSans-Bold.ttf (Cyrillic + ⌫⇥⏎⇧ glyphs). Interim helper until
the ``keycaps`` package / ``keycaps build --test`` CLI from KEYCAPS_TZ.md exists.
"""
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import cadquery as cq  # noqa: E402
import keycaps_gen as g  # noqa: E402

g.FONT_PATH = os.path.join(ROOT, "fonts", "DejaVuSans-Bold.ttf")

PLATE_GAP = 3.0
COLORS = {"base": "#C8C8C8", "top": "#202020", "legA": "#FFFFFF", "legB": "#E02020"}


def write_3mf(path: str, objects: list[tuple[str, str, list, list]]) -> None:
    cols = list(dict.fromkeys(c for _, c, _, _ in objects))
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:m="http://schemas.microsoft.com/3dmanufacturing/material/2015/02">',
        " <resources>",
        '  <m:colorgroup id="1">',
        *[f'   <m:color color="{c}"/>' for c in cols],
        "  </m:colorgroup>",
    ]
    for i, (name, color, verts, tris) in enumerate(objects, start=2):
        xml.append(f'  <object id="{i}" name="{name}" type="model" pid="1" pindex="{cols.index(color)}">')
        xml.append("   <mesh><vertices>")
        xml.extend(f'    <vertex x="{v.x:.4f}" y="{v.y:.4f}" z="{v.z:.4f}"/>' for v in verts)
        xml.append("   </vertices><triangles>")
        xml.extend(f'    <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris)
        xml.append("   </triangles></mesh>")
        xml.append("  </object>")
    xml.append(" </resources>")
    xml.append(" <build>")
    xml.extend(f'  <item objectid="{i}"/>' for i in range(2, len(objects) + 2))
    xml.append(" </build></model>")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
            "</Types>",
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
            'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
            "</Relationships>",
        )
        z.writestr("3D/3dmodel.model", "\n".join(xml))


def main(wanted: list[str]) -> None:
    keys = [k for k in g.KEYS if k[0] in wanted]
    missing = set(wanted) - {k[0] for k in keys}
    if missing:
        sys.exit(f"unknown keys: {sorted(missing)}")

    objects = []
    x = 0.0
    for k in keys:
        parts = g.build_key(*k)
        g.export(k[0], *parts)
        w = k[1] * g.UNIT - g.GAP
        cx = x + w / 2
        x += w + PLATE_GAP
        for suffix, shape in zip(("base", "top", "legA", "legB"), parts):
            if shape is None:
                continue
            # face-down: flip about X so the legend face sits on z=0
            s = shape.rotate((0, 0, 0), (1, 0, 0), 180).translate((cx, 0, g.HEIGHT))
            verts, tris = s.val().tessellate(0.01, 0.1)
            objects.append((f"{k[0]}_{suffix}", COLORS[suffix], verts, tris))

    out = os.path.join(g.OUT_DIR, "test_plate.3mf")
    write_3mf(out, objects)
    print(f"ok {out}: {len(objects)} bodies, plate width {x - PLATE_GAP:.1f} mm")


if __name__ == "__main__":
    main(sys.argv[1:] or g.TEST_SET)
