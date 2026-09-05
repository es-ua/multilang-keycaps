"""
Генератор MX-кейкапов с четырёхъязычными легендами (EN / RU / UK / DE) для QWERTY.
Четыре тела на клавишу — печать лицом вниз:
  _base.stl    прозрачный/translucent PETG  (стенки + стем, подсветка проходит)
  _top.stl     чёрный PETG-CF               (крышка с карманами под легенды)
  _legA.stl    прозрачный голубой PETG      (EN + DE), сквозные, подсветка просвечивает
  _legB.stl    прозрачный розовый PETG      (RU + UK), сквозные

pip install cadquery
python keycaps_gen.py            # все клавиши -> ./out/<имя>_body.stl + _legend.stl
python keycaps_gen.py Q W E      # только выбранные
python keycaps_gen.py --test     # тестовый ряд: Q, S, ], ', -, 2u Backspace

Раскладка легенд на лицевой стороне (вид сверху):
    EN            DE
    UK            RU   (UK печатается только там, где отличается от RU)
EN и RU крупные по диагонали в противоположных углах, DE/UK мелкие в двух других.
"""

import sys, os
import cadquery as cq

# ---------- Параметры печати ----------
UNIT      = 19.05        # шаг клавиш
GAP       = 1.05         # зазор между кейкапами -> 1u = 18.0 мм
HEIGHT    = 9.0          # высота кейкапа (плоский XDA-подобный профиль)
TOP_INSET = 2.0          # сужение верха с каждой стороны (18 -> 14 мм)
WALL      = 1.4          # толщина стенок
TOP_THK   = 2.2          # толщина крыши (чёрная часть); 2.2 мм чёрного CF светонепроницаемо
CHAMFER   = 0.6          # фаска по верхней кромке (если TOP_ROUND = 0)
EDGE_ROUND = 0.0         # радиус скругления четырёх вертикальных углов колпачка (0 = острые), как у GravaStar ~2 мм
TOP_ROUND  = 0.0         # радиус скругления верхней кромки вместо фаски (0 = фаска CHAMFER)

# MX-стем. CF жёстче — зазор чуть больше обычного.
STEM_OD   = 5.6          # наружный диаметр стема
STEM_H    = 4.0          # глубина крестовины
CROSS_W   = 4.15 + 0.10  # длина лучей креста (+допуск для CF)
CROSS_T_H = 1.30 + 0.05  # толщина горизонтального луча
CROSS_T_V = 1.15 + 0.05  # толщина вертикального луча

# Легенды
FONT      = "DejaVu Sans"          # должен поддерживать кириллицу
FONT_PATH = None                   # или путь к .ttf, напр. "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LEG_SIZE  = 2.4                    # высота шрифта, мм (меньше 2.0 на 0.4 сопле нечитаемо)
LEG_SIZE_EN = 6.0                  # латиница, прижата к левому верхнему углу
LEG_SIZE_RU = 6.0                  # кириллица, прижата к правому нижнему углу
LEG_SIZE_SMALL = 3.2               # DE (правый верхний угол) и UK (левый нижний), штрих ~0.6 мм
LEG_DEPTH = 0.45                   # глубина вставки легенды, если LEG_THROUGH = False
LEG_THROUGH = True                 # True: легенда сквозная через всю крышку (от потолка полости до лица),
                                   # печатается прозрачным PETG, подсветка из базы просвечивает сквозь букву
LEG_RAISE = 0.4                    # на сколько буква выступает НАД лицом (2 слоя); верх выступа повторяет ямку.
                                   # Только при печати лицом вверх: лицом вниз это оторвало бы крышку от стола
LEG_UNDERCUT = 0.6                 # на сколько буква выступает НИЖЕ потолка полости бугорком внутрь (3 слоя):
                                   # убирает совпадение плоскостей буква/потолок при слайсинге. При печати
                                   # лицом вверх бугорки висят под потолком полости, нужны поддержки слайсера
LEG_MARGIN= 1.5                    # отступ от края верхней площадки
LEG_GAP   = 1.2                    # минимальный зазор между EN и RU; если не влезают, обе уменьшаются
LEG_PRISM = 4.5                    # высота заготовки легенды; обрезается по коже верха толщиной LEG_DEPTH

# Вогнутый верх. 0 = плоский верх, печать лицом вниз. > 0 = ямка глубиной DISH_DEPTH в центре
# относительно углов площадки, печатать лицом ВВЕРХ. DISH_SHAPE: "sphere" — сфера через все четыре
# угла, все кромки прогнуты одинаково (как GravaStar Mercury); "cyl" — цилиндр как у Cherry/OEM,
# боковые кромки прямые.
DISH_DEPTH = 0.0
DISH_SHAPE = "sphere"

OUT_DIR = "out"

# ---------- Раскладка ----------
# (имя_файла, ширина_u, en, ru, uk_если_отличается, de)
# en может быть "1!" -> низ "1", верх-слева "!" не делаем, чтобы не перегружать: печатаем как есть.
KEYS = [
    # ряд цифр
    ("grave",  1, "`",  "Ё", None, None),
    ("1", 1, "1", None, None, None), ("2", 1, "2", None, None, None), ("3", 1, "3", None, None, None),
    ("4", 1, "4", None, None, None), ("5", 1, "5", None, None, None), ("6", 1, "6", None, None, None),
    ("7", 1, "7", None, None, None), ("8", 1, "8", None, None, None), ("9", 1, "9", None, None, None),
    ("0", 1, "0", None, None, None),
    ("minus",  1, "-",  None, None, "ß"),
    ("equal",  1, "=",  None, None, None),
    ("backspace", 2, "⌫", None, None, None),
    # верхний буквенный ряд
    ("tab", 1.5, "⇥", None, None, None),
    ("Q", 1, "Q", "Й", None, None), ("W", 1, "W", "Ц", None, None), ("E", 1, "E", "У", None, None),
    ("R", 1, "R", "К", None, None), ("T", 1, "T", "Е", None, None), ("Y", 1, "Y", "Н", None, None),
    ("U", 1, "U", "Г", None, None), ("I", 1, "I", "Ш", None, None), ("O", 1, "O", "Щ", None, None),
    ("P", 1, "P", "З", None, None),
    ("lbracket", 1, "[", "Х", None, "Ü"),
    ("rbracket", 1, "]", "Ъ", "Ї", None),
    ("backslash", 1.5, "\\", None, "Ґ", None),
    # средний ряд
    ("caps", 1.75, "⇪", None, None, None),
    ("A", 1, "A", "Ф", None, None), ("S", 1, "S", "Ы", "І", None), ("D", 1, "D", "В", None, None),
    ("F", 1, "F", "А", None, None), ("G", 1, "G", "П", None, None), ("H", 1, "H", "Р", None, None),
    ("J", 1, "J", "О", None, None), ("K", 1, "K", "Л", None, None), ("L", 1, "L", "Д", None, None),
    ("semicolon", 1, ";", "Ж", None, "Ö"),
    ("quote", 1, "'", "Э", "Є", "Ä"),
    ("enter", 2.25, "⏎", None, None, None),
    # нижний ряд
    ("lshift", 2.25, "⇧", None, None, None),
    ("Z", 1, "Z", "Я", None, None), ("X", 1, "X", "Ч", None, None), ("C", 1, "C", "С", None, None),
    ("V", 1, "V", "М", None, None), ("B", 1, "B", "И", None, None), ("N", 1, "N", "Т", None, None),
    ("M", 1, "M", "Ь", None, None),
    ("comma",  1, ",", "Б", None, None),
    ("period", 1, ".", "Ю", None, None),
    ("slash",  1, "/", ".", None, None),
    ("rshift", 1.75, "⇧", None, None, None),
    # модификаторы (у K98 Pro нижний ряд сжат — промерь, могут быть 1u/1.25u)
    ("ctrl", 1.25, "Ctrl", None, None, None),
    ("win",  1.25, "⌘",   None, None, None),
    ("alt",  1.25, "Alt",  None, None, None),
    ("space", 6.25, "", None, None, None),
    ("altgr", 1, "AltGr", None, None, None),
    ("fn",    1, "Fn",  None, None, None),
    ("rctrl", 1, "Ctrl", None, None, None),
    # F-ряд и нумпад
    *[(f"F{i}", 1, f"F{i}", None, None, None) for i in range(1, 13)],
    ("esc", 1, "Esc", None, None, None),
    *[(f"num{i}", 1, str(i), None, None, None) for i in range(0, 10)],
    ("numplus", 1, "+", None, None, None), ("numminus", 1, "-", None, None, None),
    ("numstar", 1, "*", None, None, None), ("numslash", 1, "/", None, None, None),
    ("numdot", 1, ".", None, None, None), ("numenter", 1, "⏎", None, None, None),
]

TEST_SET = ["Q", "S", "rbracket", "quote", "minus", "backspace"]


# ---------- Геометрия ----------
def cap_body(width_u: float):
    w = width_u * UNIT - GAP
    d = UNIT - GAP
    tw, td = w - 2 * TOP_INSET, d - 2 * TOP_INSET

    outer = (cq.Workplane("XY")
             .rect(w, d).workplane(offset=HEIGHT).rect(tw, td)
             .loft(combine=True))
    if EDGE_ROUND > 0:
        outer = outer.edges("not(<Z or >Z)").fillet(EDGE_ROUND)   # четыре наклонных ребра углов
    if TOP_ROUND > 0:
        outer = outer.edges(">Z").fillet(TOP_ROUND)
    else:
        outer = outer.edges(">Z").chamfer(CHAMFER)

    # внутренняя полость
    iw, id_ = w - 2 * WALL, d - 2 * WALL
    itw, itd = tw - 2 * WALL, td - 2 * WALL
    ih = HEIGHT - TOP_THK
    inner = (cq.Workplane("XY")
             .rect(iw, id_).workplane(offset=ih).rect(itw, itd)
             .loft(combine=True))
    body = outer.cut(inner)

    # стем
    stem = (cq.Workplane("XY").circle(STEM_OD / 2).extrude(ih + 0.01))
    cross = (cq.Workplane("XY").rect(CROSS_W, CROSS_T_H).extrude(STEM_H)
             .union(cq.Workplane("XY").rect(CROSS_T_V, CROSS_W).extrude(STEM_H)))
    stem = stem.cut(cross)
    body = body.union(stem)

    # усиление под широкие клавиши (>=2u): рёбра к стенкам вместо стабилизаторов
    if width_u >= 2:
        rib = cq.Workplane("XY").rect(iw, 1.2).extrude(ih + 0.01)
        body = body.union(rib)
    return body, tw, td, outer


TEXT_CHORD = 0.05                  # допуск дискретизации кривых глифа в ломаную, мм


def _polyline(wire, chord=None):
    """Замкнутая ломаная по проволоке: кривые бьются по хорде, прямые остаются двумя точками."""
    chord = chord or TEXT_CHORD
    pts = []
    for e in wire.Edges() if hasattr(wire, "Edges") else wire.edges().vals():
        if e.geomType() == "LINE":
            n = 1
        else:
            n = max(4, int(e.Length() / chord) + 1)
        for i in range(n):
            pts.append(e.positionAt(i / n, mode="length"))
    return cq.Wire.makePolygon(pts, close=True)


def make_text(txt: str, size: float):
    """Призма текста высотой LEG_PRISM, торчит на 0.5 мм над верхом; режется по коже в build_key.

    Глифы переводятся в многоугольники (плоские грани): B-spline стенки букв давали слайсеру Bambu
    сетки, на которых кривые буквы (S, C, Q, Ф) пропадали и заливались чёрным.
    """
    kw = dict(kind="bold", halign="center", valign="center")
    if FONT_PATH:
        kw["fontPath"] = FONT_PATH
    else:
        kw["font"] = FONT
    glyphs = cq.Workplane("XY").text(txt, size, 1.0, **kw)
    solids = []
    for face in glyphs.faces("<Z").vals():
        outer = _polyline(face.outerWire())
        inners = [_polyline(w) for w in face.innerWires()]
        f = cq.Face.makeFromWires(outer, inners)
        solids.append(cq.Solid.extrudeLinear(f, cq.Vector(0, 0, LEG_PRISM)))
    comp = cq.Compound.makeCompound(solids)
    return cq.Workplane("XY").newObject([comp]).translate((0, 0, HEIGHT + 0.5 - LEG_PRISM))


def dish_cutter(tw: float, td: float):
    """Тело для вырезания ямки. Кромка ямки на боковых сторонах площадки лежит на высоте HEIGHT."""
    if DISH_SHAPE == "cyl":
        # цилиндр с осью вдоль Y: радиус по полуширине клавиши, глубина в центре = DISH_DEPTH
        r = tw / 2
        R = (r * r + DISH_DEPTH * DISH_DEPTH) / (2 * DISH_DEPTH)
        return (cq.Workplane("XZ").circle(R).extrude(50, both=True)
                .translate((0, 0, HEIGHT - DISH_DEPTH + R)))
    # сфера через углы площадки внутри фаски (квадрат (td-2·CHAMFER)²), растянута по X под широкие
    # клавиши, чтобы и у них на полной высоте HEIGHT оставались только углы
    rim = TOP_ROUND if TOP_ROUND > 0 else CHAMFER
    a = td / 2 - rim
    r = a * 2 ** 0.5
    R = (r * r + DISH_DEPTH * DISH_DEPTH) / (2 * DISH_DEPTH)
    sph = cq.Workplane("XY").sphere(R).translate((0, 0, HEIGHT - DISH_DEPTH + R))
    sx = (tw / 2 - rim) / a
    if abs(sx - 1) < 1e-6:
        return sph
    m = cq.Matrix([[sx, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    return cq.Workplane("XY").newObject([sph.val().transformGeometry(m)])


def legends(en, ru, uk, de, tw, td):
    """Возвращает (legA, legB): A = EN+DE (белый), B = RU+UK (красный). Слой [HEIGHT-LEG_DEPTH, HEIGHT]."""
    parts = {"A": [], "B": []}
    hx, hy = tw / 2 - LEG_MARGIN, td / 2 - LEG_MARGIN
    single = en and not (ru or uk or de)

    def place(txt, size, x, y, grp="A"):
        if not txt:
            return
        # длинные подписи (Ctrl, AltGr) масштабируем по ширине площадки
        s = min(size, (tw - 2 * LEG_MARGIN) / (0.62 * max(len(txt), 1)))
        parts[grp].append(make_text(txt, s).translate((x, y, 0)))

    def corner_text(txt, size):
        t = make_text(txt, size)
        return t, t.val().BoundingBox(tolerance=1e-3)

    def place_corner(txt, size, sx, sy, grp="A"):
        """Легенда, прижатая контуром глифа к углу площадки: sx -1 левый / +1 правый, sy +1 верх / -1 низ."""
        if not txt:
            return
        t, bb = corner_text(txt, size)
        dx = -hx - bb.xmin if sx < 0 else hx - bb.xmax
        dy = hy - bb.ymax if sy > 0 else -hy - bb.ymin
        parts[grp].append(t.translate((dx, dy, 0)))

    if single:
        place(en, LEG_SIZE * 1.15, 0, 0)
    else:
        size_en, size_ru = LEG_SIZE_EN, LEG_SIZE_RU
        if en and ru:
            # EN сверху слева, RU снизу справа: следим за вертикальным зазором LEG_GAP между ними
            h_en = corner_text(en, size_en)[1].ylen
            h_ru = corner_text(ru, size_ru)[1].ylen
            avail = 2 * hy - LEG_GAP
            if h_en + h_ru > avail:
                f = avail / (h_en + h_ru)
                size_en, size_ru = size_en * f, size_ru * f
        place_corner(en, size_en, -1, +1)
        place_corner(ru, size_ru, +1, -1, "B")
        place_corner(de, LEG_SIZE_SMALL, +1, +1)
        place_corner(uk, LEG_SIZE_SMALL, -1, -1, "B")

    def merge(lst):
        if not lst:
            return None
        r = lst[0]
        for p in lst[1:]:
            r = r.union(p)
        return r
    return merge(parts["A"]), merge(parts["B"])


def build_key(name, width_u, en, ru, uk, de):
    body, tw, td, outer = cap_body(width_u)
    if DISH_DEPTH > 0:
        dish = dish_cutter(tw, td)
        body, outer = body.cut(dish), outer.cut(dish)
    # легенда = призма текста ∩ "кожа": либо вся толщина крышки над полостью плюс бугорок LEG_UNDERCUT
    # внутрь полости (сквозная, просвечивает), либо слой LEG_DEPTH под лицом (вставка). Обе повторяют ямку.
    if LEG_THROUGH:
        z0 = HEIGHT - TOP_THK - LEG_UNDERCUT
        # outer, поднятый на LEG_RAISE: его верх (плоский или ямка) становится верхом выступающей буквы
        skin = outer.translate((0, 0, LEG_RAISE)).intersect(
            cq.Workplane("XY").box(200, 200, HEIGHT, centered=(True, True, False)).translate((0, 0, z0)))
    else:
        skin = body.cut(body.translate((0, 0, -LEG_DEPTH)))
    legA, legB = legends(en, ru, uk, de, tw, td)
    legs = []
    for leg in (legA, legB):
        if leg is not None:
            leg = leg.intersect(skin)
            if leg.val().Volume() < 1e-6:
                leg = None
            else:
                body = body.cut(leg)
        legs.append(leg)
    legA, legB = legs
    # разрез по высоте: низ (прозрачный) / верх (чёрная крышка); при ямке чёрного в центре остаётся TOP_THK
    z = HEIGHT - TOP_THK - DISH_DEPTH
    big = 200
    lower = cq.Workplane("XY").box(big, big, z, centered=(True, True, False))
    upper = cq.Workplane("XY").box(big, big, HEIGHT + 5, centered=(True, True, False)).translate((0, 0, z))
    base = body.intersect(lower)
    top = body.intersect(upper)
    return base, top, legA, legB


def export(name, base, top, legA, legB):
    os.makedirs(OUT_DIR, exist_ok=True)
    opt = dict(tolerance=0.01, angularTolerance=0.1)
    cq.exporters.export(base, f"{OUT_DIR}/{name}_base.stl", **opt)
    cq.exporters.export(top,  f"{OUT_DIR}/{name}_top.stl",  **opt)
    if legA is not None:
        cq.exporters.export(legA, f"{OUT_DIR}/{name}_legA.stl", **opt)
    if legB is not None:
        cq.exporters.export(legB, f"{OUT_DIR}/{name}_legB.stl", **opt)
    print("ok", name)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--test"]:
        wanted = TEST_SET
    else:
        wanted = args or None
    for k in KEYS:
        if wanted and k[0] not in wanted:
            continue
        export(k[0], *build_key(*k))
