"""
Генератор MX-кейкапов с четырёхъязычными легендами (EN / RU / UK / DE) для QWERTY.
Четыре тела на клавишу — печать лицом вниз:
  _base.stl    прозрачный/translucent PETG  (стенки + стем, подсветка проходит)
  _top.stl     чёрный PETG-CF               (крышка с карманами под легенды)
  _legA.stl    белый PETG                   (EN + DE)
  _legB.stl    красный PETG                 (RU + UK)

pip install cadquery
python keycaps_gen.py            # все клавиши -> ./out/<имя>_body.stl + _legend.stl
python keycaps_gen.py Q W E      # только выбранные
python keycaps_gen.py --test     # тестовый ряд: Q, S, ], ', -, 2u Backspace

Раскладка легенд на лицевой стороне (вид сверху):
    EN            RU
    DE            UK   (UK печатается только там, где отличается от RU)
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
CHAMFER   = 0.6          # фаска по верхней кромке

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
LEG_SIZE_SMALL = 1.9               # для DE/UK в нижних углах
LEG_DEPTH = 0.45                   # глубина вставки легенды
LEG_MARGIN= 0.9                    # отступ от края верхней площадки

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
    return body, tw, td


def make_text(txt: str, size: float):
    kw = dict(kind="bold", halign="center", valign="center")
    if FONT_PATH:
        kw["fontPath"] = FONT_PATH
    else:
        kw["font"] = FONT
    return cq.Workplane("XY").text(txt, size, LEG_DEPTH, **kw)


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
        t = make_text(txt, s).translate((x, y, HEIGHT - LEG_DEPTH))
        parts[grp].append(t)

    if single:
        place(en, LEG_SIZE * 1.15, 0, 0)
    else:
        q = 0.48  # смещение в квадрант
        place(en, LEG_SIZE, -hx * q, hy * q)
        place(ru, LEG_SIZE,  hx * q, hy * q, "B")
        place(de, LEG_SIZE_SMALL, -hx * q, -hy * q)
        place(uk, LEG_SIZE_SMALL,  hx * q, -hy * q, "B")

    def merge(lst):
        if not lst:
            return None
        r = lst[0]
        for p in lst[1:]:
            r = r.union(p)
        return r
    return merge(parts["A"]), merge(parts["B"])


def build_key(name, width_u, en, ru, uk, de):
    body, tw, td = cap_body(width_u)
    legA, legB = legends(en, ru, uk, de, tw, td)
    for leg in (legA, legB):
        if leg is not None:
            body = body.cut(leg)
    # разрез по высоте: низ (прозрачный) / верх (чёрная крышка)
    z = HEIGHT - TOP_THK
    big = 200
    lower = cq.Workplane("XY").box(big, big, z, centered=(True, True, False))
    upper = cq.Workplane("XY").box(big, big, HEIGHT, centered=(True, True, False)).translate((0, 0, z))
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
