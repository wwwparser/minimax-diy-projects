"""Каталог покупок для diy-project-engineer из локальной базы Петровича (data/catalog.sqlite3).

Разбирает названия товаров регулярками в структурированные спецификации (сечение, длина, d×L самореза,
фасовка, объём, набор коронок…). Результат: engineering/catalog_petrovich.yaml.
"""
import re
import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NUM = r"(\d+(?:[.,]\d+)?)"


def f(x):
    return float(str(x).replace(",", "."))


def pack_of(title):
    m = re.search(r"\((\d+)\s*шт\.?\)", title)
    return int(m.group(1)) if m else 1


RULES = []


def rule(like, rx):
    def deco(fn):
        RULES.append((like, re.compile(rx, re.I), fn))
        return fn
    return deco


# ---------------- материалы
@rule("Доска сухая строганая%", rf"Доска сухая строганая {NUM}х{NUM}х{NUM} мм")
def _board(m, t):
    return {"kind": "stock", "stock": {"type": "board", "material": "pine", "thickness": f(m[1]), "width": f(m[2]), "length": f(m[3])}}


@rule("Брусок%", rf"Брусок (?:сухой строганый )?{NUM}х{NUM}х{NUM} мм")
def _bar(m, t):
    return {"kind": "stock", "stock": {"type": "bar", "material": "pine", "thickness": f(m[1]), "width": f(m[2]), "length": f(m[3])}}


@rule("Раскладка%", rf"Раскладка {NUM}х{NUM}х{NUM} мм")
def _lath(m, t):
    return {"kind": "stock", "stock": {"type": "bar", "material": "pine", "thickness": f(m[2]), "width": f(m[1]), "length": f(m[3])}}


@rule("Фанера ФК%", rf"Фанера ФК {NUM}х{NUM}х{NUM} мм")
def _ply(m, t):
    return {"kind": "stock", "stock": {"type": "sheet", "material": "birch_plywood", "thickness": f(m[1]), "length": f(m[2]), "width": f(m[3])}}


@rule("Щит мебельный ЛДСП%", rf"Щит мебельный ЛДСП {NUM}х{NUM}х{NUM} мм")
def _panel(m, t):
    return {"kind": "stock", "stock": {"type": "sheet", "material": "chipboard", "length": f(m[1]), "width": f(m[2]), "thickness": f(m[3])}}


@rule("Труба профильная%", rf"Труба профильная {NUM}х{NUM}х{NUM} мм {NUM} м")
def _tube(m, t):
    return {"kind": "stock", "stock": {"type": "rect_tube", "material": "steel", "width": f(m[1]), "thickness": f(m[2]), "wall": f(m[3]), "length": f(m[4]) * 1000}}


@rule("Уголок горячекатаный%", rf"Уголок горячекатаный {NUM}х{NUM}х{NUM} мм {NUM} м")
def _angle(m, t):
    return {"kind": "stock", "stock": {"type": "angle", "material": "steel", "width": f(m[1]), "thickness": f(m[2]), "wall": f(m[3]), "length": f(m[4]) * 1000}}


@rule("Полоса горячекатаная%", rf"Полоса горячекатаная {NUM}х{NUM} мм {NUM} м")
def _flat(m, t):
    return {"kind": "stock", "stock": {"type": "flat_bar", "material": "steel", "width": f(m[1]), "thickness": f(m[2]), "length": f(m[3]) * 1000}}


@rule("Труба стальная водогазопроводная ДУ%", rf"ДУ {NUM}х{NUM} мм {NUM} м")
def _vgp(m, t):
    outer = {15: 21.3, 20: 26.8, 25: 33.5, 32: 42.3}.get(int(f(m[1])), f(m[1]) + 6)
    return {"kind": "stock", "stock": {"type": "round_tube", "material": "galvanized" if "оцинк" in t else "steel",
                                       "diameter": outer, "wall": f(m[2]), "length": f(m[3]) * 1000}}


@rule("Шпилька резьбовая оцинкованная d%", rf"d{NUM}x{NUM} мм")
def _rod(m, t):
    return {"kind": "stock", "stock": {"type": "threaded_rod", "material": "galvanized", "diameter": f(m[1]), "length": f(m[2])}}


@rule("Канат%джутовый%", rf"d{NUM} мм")
def _rope(m, t):
    return {"kind": "stock", "stock": {"type": "rope", "material": "jute", "diameter": f(m[1]), "length": 1000}} \
        if "пог" in t or "(" not in t else None


@rule("Цепь %оцинкованная d%", rf"d{NUM} мм")
def _chain(m, t):
    return {"kind": "stock", "stock": {"type": "chain", "material": "galvanized", "diameter": f(m[1]), "length": 1000}} \
        if "м)" not in t else None


@rule("Сетка кладочная оцинкованная%", rf"{NUM}х{NUM} м")
def _mesh(m, t):
    return {"kind": "stock", "stock": {"type": "mesh", "material": "galvanized", "width": f(m[1]) * 1000, "length": f(m[2]) * 1000}}


# ---------------- крепёж
@rule("Саморезы ГД%", rf"Саморезы ГД {NUM}x{NUM} мм")
def _gd(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "wood_screw", "diameter": f(m[2]), "length": f(m[1])}}


@rule("Саморезы по дереву%конструкционные%", rf"Саморезы по дереву {NUM}x{NUM} мм")
def _konstr(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "wood_screw", "diameter": f(m[2]), "length": f(m[1])}}


@rule("Болт оцинкованный M%DIN 933%", rf"M{NUM}x{NUM} мм")
def _bolt(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "bolt", "diameter": f(m[1]), "length": f(m[2])}}


@rule("Болт мебельный%", rf"{NUM}х{NUM} мм")
def _cbolt(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "bolt", "diameter": f(m[1]), "length": f(m[2]), "head": "carriage", "nut_included": True}}


@rule("Гайка шестигранная оцинкованная М%DIN 934 (%", rf"М{NUM} DIN 934 \(")
def _nut(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "nut", "diameter": f(m[1])}}


@rule("Шайба оцинкованная %DIN 125%", rf"Шайба оцинкованная {NUM}х{NUM} мм")
def _washer(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "washer", "diameter": f(m[1])}}


@rule("Дюбель универсальный Hard-Fix%с шурупом%", rf"{NUM}x{NUM} мм")
def _dowel(m, t):
    return {"kind": "fastener", "pack": pack_of(t), "fastener": {"type": "wall_dowel", "diameter": f(m[1]), "length": f(m[2])}}


# ---------------- фурнитура
@rule("Петля%карточная%", rf"{NUM}х{NUM} мм")
def _hinge(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "butt_hinge", "size": str(int(f(m[1])))}}


@rule("Уголок крепежный оцинкованный%", rf"{NUM}х{NUM}х{NUM}")
def _bracket(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "corner_bracket", "size": f"{int(f(m[1]))}"}}


@rule("Уголок мебельный оцинкованный%", rf"{NUM}х{NUM}х{NUM}")
def _fbracket(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "furniture_bracket", "size": f"{int(f(m[1]))}"}}


@rule("Крючок-вешалка%", r"№(\d)")
def _hook(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "hook", "size": m[1]}}


@rule("Опора колесная поворотная%", rf"{NUM} мм")
def _caster(m, t):
    return {"kind": "hardware", "pack": pack_of(t), "hardware": {"type": "caster", "size": str(int(f(m[1])))}}


@rule("Ножка мебельная стальная%", rf"{NUM}х{NUM} мм")
def _leg(m, t):
    return {"kind": "hardware", "pack": pack_of(t), "hardware": {"type": "furniture_leg", "size": str(int(f(m[2])))}}


@rule("Ручка-скоба%", r"(\d+)")
def _handle(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "handle", "size": m[1]}}


@rule("Шуруп-кольцо%", rf"{NUM}x{NUM} мм")
def _eye(m, t):
    return {"kind": "hardware", "pack": pack_of(t), "hardware": {"type": "screw_eye", "size": f"{m[1]}x{m[2]}"}}


@rule("Карабин пружинный%", rf"d{NUM} мм")
def _carab(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "carabiner", "size": str(int(f(m[1])))}}


@rule("Кронштейн для полки%", rf"{NUM} мм")
def _shelfbr(m, t):
    return {"kind": "hardware", "pack": 1, "hardware": {"type": "shelf_bracket", "size": str(int(f(m[1])))}}


# ---------------- отделка и расходники
@rule("Антисептик Dali универсальный%", rf"{NUM} л")
def _antis(m, t):
    return {"kind": "finish", "finish": {"type": "antiseptic", "volume_l": f(m[1])}}


@rule("Лак алкидный яхтный аэрозольный%", r"(\d+) мл")
def _lacaer(m, t):
    return {"kind": "finish", "finish": {"type": "varnish_aerosol", "volume_l": f(m[1]) / 1000}}


@rule("Лак алкидно-уретановый паркетный Престиж%", rf"{NUM} л")
def _lac(m, t):
    return {"kind": "finish", "finish": {"type": "varnish", "volume_l": f(m[1])}}


@rule("Морилка MasterGood водная%", rf"{NUM} л")
def _stain(m, t):
    return {"kind": "finish", "finish": {"type": "stain", "volume_l": f(m[1])}}


@rule("Масло Радуга для дерева%", rf"{NUM} л")
def _oil(m, t):
    return {"kind": "finish", "finish": {"type": "oil", "volume_l": f(m[1])}}


@rule("Эмаль аэрозольная Престиж%", r"(\d+) мл")
def _enaer(m, t):
    return {"kind": "finish", "finish": {"type": "enamel_aerosol", "volume_l": f(m[1]) / 1000}}


@rule("Грунт-эмаль аэрозольная%", r"(\d+) мл")
def _primaer(m, t):
    return {"kind": "finish", "finish": {"type": "enamel_aerosol", "volume_l": f(m[1]) / 1000, "rust": True}}


@rule("Клей ПВА Момент Столяр%", r"(\d+) г")
def _glue(m, t):
    return {"kind": "glue", "glue": {"type": "pva", "mass_kg": f(m[1]) / 1000}}


@rule("Наждачная бумага Flexione 230х280%", r"Р(\d+)")
def _sand(m, t):
    return {"kind": "consumable", "consumable": {"type": "sandpaper", "grit": int(m[1]), "sheets": 1}}


# ---------------- оснастка
@rule("Сверло по дереву спиральное%", rf"{NUM}х{NUM} мм")
def _drill(m, t):
    return {"kind": "tool", "tool": {"type": "twist_drill", "diameter": f(m[1])}} if "зенкер" not in t else \
        {"kind": "tool", "tool": {"type": "twist_drill_countersink", "diameter": f(m[1])}}


@rule("Сверло по металлу спиральное%", rf"{NUM}х{NUM} мм")
def _mdrill(m, t):
    return {"kind": "tool", "tool": {"type": "metal_drill", "diameter": f(m[1])}}


@rule("Сверло по дереву перьевое%", rf"{NUM}х{NUM} мм")
def _spade(m, t):
    return {"kind": "tool", "tool": {"type": "spade_bit", "diameter": f(m[1])}}


@rule("Набор коронок%по дереву%", rf"d{NUM}-{NUM} мм")
def _holesaw(m, t):
    return {"kind": "tool", "tool": {"type": "hole_saw", "min": f(m[1]), "max": f(m[2]), "set": True}}


@rule("Бита%PH2 магнитная 25 мм%", r"(PH2)")
def _bit(m, t):
    return {"kind": "tool", "tool": {"type": "screwdriver_bit"}}


@rule("Ножовка по дереву%", r"(\d+) мм")
def _saw(m, t):
    return {"kind": "tool", "tool": {"type": "hand_saw"}}


@rule("Ножовка по металлу%", r"(\d+) мм")
def _hsaw(m, t):
    return {"kind": "tool", "tool": {"type": "hacksaw"}}


@rule("Стусло%", r"(\d+)х")
def _miter(m, t):
    return {"kind": "tool", "tool": {"type": "miter_box"}} if "с пилой" not in t else None


@rule("Рулетка с фиксатором%", r"(\d) м")
def _tape(m, t):
    return {"kind": "tool", "tool": {"type": "tape_measure"}}


@rule("Карандаш строительный%", r"(Hesler)")
def _pencil(m, t):
    return {"kind": "tool", "tool": {"type": "pencil"}}


@rule("Очки защитные%", r"(Исток)")
def _glasses(m, t):
    return {"kind": "tool", "tool": {"type": "safety_glasses"}}


@rule("Струбцина столярная%", rf"{NUM}х{NUM} мм")
def _clamp(m, t):
    return {"kind": "tool", "tool": {"type": "clamp"}}


@rule("Ключ комбинированный рожково-накидной%", r"(\d+) мм")
def _wrench(m, t):
    return {"kind": "tool", "tool": {"type": "wrench", "diameter": float(m[1])}}


@rule("Шкант мебельный%", r"(\d+)х(\d+) мм")
def _dowel_pin(m, t):
    return {"kind": "hardware", "pack": pack_of(t), "hardware": {"type": "dowel_pin", "size": f"{m[1]}x{m[2]}"}}


def build():
    con = sqlite3.connect(ROOT / "data" / "catalog.sqlite3")
    items, seen = [], set()
    for like, rx, fn in RULES:
        for code, title, price, unit, url in con.execute(
                "select code,title,price,unit,url from products where title like ? and price>0", (like,)):
            if code in seen:
                continue
            m = rx.search(title)
            if not m:
                continue
            spec = fn(m, title)
            if not spec:
                continue
            seen.add(code)
            items.append({"sku": str(code), "name": title, "price": price, "unit": unit, "url": url, **spec})
    # одинаковые спецификации — оставить самую дешёвую за единицу
    best = {}
    for it in items:
        spec = it.get(it["kind"])
        key = (it["kind"], yaml.safe_dump(spec, sort_keys=True), it.get("pack", 1))
        per = it["price"] / float(it.get("pack", 1))
        if key not in best or per < best[key][0]:
            best[key] = (per, it)
    out = [v[1] for v in best.values()]
    (ROOT / "engineering" / "catalog_petrovich.yaml").write_text(
        "# Сгенерировано build_petrovich_catalog.py из снимка каталога Петровича 16.09.2026 (Москва, розница)\n" +
        yaml.safe_dump({"items": out}, allow_unicode=True, sort_keys=False, width=160), encoding="utf-8")
    from collections import Counter
    print(len(out), Counter(i["kind"] for i in out))


if __name__ == "__main__":
    build()
