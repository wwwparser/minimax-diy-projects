"""Поиск по локальной копии каталога Петровича (FTS5)."""
import re, sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "catalog.sqlite3"
_con = None

def con():
    global _con
    if _con is None:
        _con = sqlite3.connect(DB, check_same_thread=False)
    return _con

def search(query: str, limit: int = 15, must: str = "", exclude: str = "", max_price: float | None = None):
    """query — слова (префиксный поиск, все обязательны). must/exclude — regex по названию."""
    words = [w for w in re.findall(r"[\wА-Яа-яЁё]+", query.lower()) if len(w) > 1]
    fts = " ".join(f'"{w}"*' for w in words)
    rows = con().execute(
        "select p.code,p.title,p.price,p.unit,p.path,p.url,p.image from fts join products p on p.code=fts.rowid "
        "where fts match ? and p.price>0 order by rank limit 400", (fts,)).fetchall()
    out = []
    for code, title, price, unit, path, url, image in rows:
        if must and not re.search(must, title, re.I): continue
        if exclude and re.search(exclude, title, re.I): continue
        if max_price and price > max_price: continue
        out.append({"code": code, "title": title, "price": price, "unit": unit, "path": path, "url": url, "image": image})
    return out[:limit]

if __name__ == "__main__":
    import sys
    for r in search(" ".join(sys.argv[1:]), 25):
        print(f'{r["code"]:>7} {r["price"]:>8.0f} {r["unit"]:<5} {r["title"][:95]} | {r["path"][-40:]}')
