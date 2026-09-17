"""Шаг 1. Сбор DIY-проектов из выдачи Google/Яндекс через XMLRiver -> data/serp.jsonl (resume)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "services"))
import xmlriver_client as xr

QUERIES = [
    "простые поделки из дерева своими руками шуруповертом",
    "что сделать из дерева своими руками для дома идеи с чертежами",
    "полка из дерева своими руками пошагово размеры материалы",
    "скворечник своими руками чертеж размеры",
    "табурет из бруска своими руками чертеж",
    "обувница из дерева своими руками",
    "органайзер для инструмента своими руками из фанеры",
    "ящик для инструментов из дерева своими руками чертеж",
    "вешалка настенная из дерева своими руками",
    "кормушка для птиц из дерева своими руками чертеж",
    "подставка для цветов из дерева своими руками",
    "грядка из досок своими руками",
    "компостер из поддонов досок своими руками",
    "стеллаж из бруса своими руками в гараж",
    "полка для ванной из дерева своими руками",
    "разделочная доска держатель ножей своими руками",
    "ключница из дерева своими руками",
    "домик для кошки своими руками из фанеры",
    "лежанка для собаки из дерева своими руками",
    "скамейка из досок своими руками простая",
    "подставка под ноутбук из дерева своими руками",
    "короб для хранения из фанеры своими руками",
    "табуретка-стремянка своими руками чертеж",
    "перфорированная панель для инструмента своими руками",
    "поделки из профильной трубы без сварки на болтах",
    "стеллаж из перфорированного уголка своими руками",
    "полка лофт из металла и дерева своими руками без сварки",
    "вешалка из водопроводных труб лофт своими руками",
    "держатель для дров из металла своими руками без сварки",
    "подстолье из профильной трубы на болтах",
    "проекты для начинающих с шуруповертом",
    "что можно сделать шуруповертом своими руками",
    "мебель из бруса на саморезах своими руками",
    "ящик для рассады из досок своими руками",
    "подвесные качели из доски своими руками",
    "садовая тележка ящик на колесах из дерева своими руками",
    "wooden diy projects for beginners with a drill",
    "easy 2x4 projects beginner woodworking",
    "simple scrap wood projects cordless drill",
    "diy pipe shelf no welding",
    "easy weekend woodworking projects under 50 dollars",
    "pocket hole projects beginner plans",
    "diy shoe rack wood plans simple",
    "diy wall mounted tool organizer plywood",
    "diy bird house plans easy",
]

def main():
    out = Path("data/serp.jsonl")
    done = set()
    if out.exists():
        for l in out.open(encoding="utf-8"):
            r = json.loads(l); done.add((r["query"], r["engine"]))
    tasks = []
    for q in QUERIES:
        en = all(ord(c) < 128 for c in q)
        for eng in (["google"] if en else ["google", "yandex"]):
            if (q, eng) not in done:
                tasks.append({"query": q, "engine": eng, "top": 10, "region": "US" if en else "RU"})
    print("платных запросов:", len(tasks))
    with out.open("a", encoding="utf-8") as f:
        for t, res, err in xr.search_many(tasks):
            if err:
                print("ERR", err); continue
            f.write(json.dumps({"query": t["query"], "engine": t["engine"], "results": res}, ensure_ascii=False) + "\n"); f.flush()
            print("ok", t["engine"], len(res), t["query"])

if __name__ == "__main__":
    main()
