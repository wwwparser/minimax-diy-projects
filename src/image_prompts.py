"""Промпты трёх картинок на каждый проект: иллюстрация, плакат, пошаговая инструкция -> out/images/prompts.json"""
import json
from collections import OrderedDict
from pathlib import Path
from short_names import short
from steps4 import STEPS4

ROOT = Path(__file__).resolve().parent.parent

def shop_lines(p, n=5):
    agg = OrderedDict()
    for l in p["bom"]:
        if l["kind"] == "оснастка":
            continue
        k = short(l); agg[k] = agg.get(k, 0) + l["sum"]
    items = sorted(agg.items(), key=lambda x: -x[1])
    top, rest = items[:n], items[n:]
    lines = [f"{k} — {round(v)} ₽" for k, v in top]
    if rest:
        lines.append(f"Крепёж и мелочи — {round(sum(v for _, v in rest))} ₽")
    if p["tools_total"]:
        lines.append(f"Оснастка — {p['tools_total']} ₽")
    return lines

def material_hint(p):
    m = p["material"]
    if "фанер" in p["name"].lower() or any(l["code"] in (634466, 109060) for l in p["bom"] if l["kind"] == "материал") and m == "дерево":
        return "из берёзовой фанеры и светлой сосны"
    if m == "металл":
        return "из стали, окрашенной матовой грунт-эмалью, соединения на болтах"
    if m == "дерево":
        return "из светлой строганой сосны, видны аккуратные саморезы"
    return "из светлой сосны и тёмной окрашенной стали"

def prompts(p):
    steps = STEPS4[p["id"]]
    ill = (f"Создай изображение (не отвечай текстом). Фотореалистичная горизонтальная фотография 3:2, мягкий дневной свет, "
           f"уютный реальный интерьер или сад по назначению изделия. Главный объект крупно: готовое изделие «{p['name']}» — "
           f"{p['summary']} Размер: {p['size']}. Сделано {material_hint(p)}. Выглядит как аккуратная домашняя работа. "
           f"Никакого текста, надписей и логотипов на изображении.")
    shop = "\n".join(f"• {s}" for s in shop_lines(p))
    st = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))
    poster = (f"Создай изображение (не отвечай текстом): вертикальный плакат 2:3 в стиле журнала «Сделай сам», крафтовая бумага, "
              f"чистая инфографика, крупная иллюстрация готового изделия «{p['name']}» ({material_hint(p)}) и небольшой "
              f"зелёный аккумуляторный шуруповёрт рядом.\n\nВесь текст — на русском, крупно, без ошибок, дословно:\n\n"
              f"Заголовок: {p['name']}\nПод заголовком: Сложность {p['difficulty']} из 5 · около {p['hours']} ч\n\n"
              f"Блок «Что купить»:\n{shop}\n\nБлок «Как сделать»:\n{st}\n\nКрупный ценник: ИТОГО {p['total']} ₽")
    howto = (f"Создай изображение (не отвечай текстом): квадратная пошаговая инструкция 1:1 из 4 панелей 2×2, стиль чистой "
             f"технической иллюстрации, светлый фон. Тема: как сделать «{p['name']}» {material_hint(p)} с помощью "
             f"аккумуляторного шуруповёрта и ручной ножовки. В каждой панели руки мастера выполняют шаг, в углу крупная цифра. "
             f"Под каждой панелью короткая подпись на русском без ошибок, дословно:\n" + st)
    return {"illustration": ill, "poster": poster, "howto": howto}

if __name__ == "__main__":
    est = json.loads((ROOT / "out" / "estimates.json").read_text(encoding="utf-8"))
    est.sort(key=lambda p: (not p["top"], p["id"]))       # сначала топ-10
    out = ROOT / "out" / "images"; out.mkdir(parents=True, exist_ok=True)
    data = [{"id": p["id"], "name": p["name"], **prompts(p)} for p in est]
    (out / "prompts.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(data)); print(data[5]["poster"]); print(data[5]["howto"])
