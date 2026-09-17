"""Облегчённая копия каталога Петровича + FTS5-индекс для подбора материалов."""
import json, sqlite3
from pathlib import Path

SRC = r"C:/Users/Yuri/PycharmProjects/PythonProject/idea-parser-petrovich/data/petrovich.sqlite3"
DST = Path(__file__).resolve().parent.parent / "data" / "catalog.sqlite3"

def main():
    DST.unlink(missing_ok=True)
    s = sqlite3.connect(SRC); d = sqlite3.connect(DST)
    d.execute("create table products(code integer primary key, title text, section text, path text, price real, unit text, chars text, url text, image text)")
    rows = []
    for code, title, sec, path, price, unit, chars, imgs, url in s.execute(
            "select code,title,section_title,category_path_json,price_retail,unit,characteristics_json,images_json,url from products"):
        try: path = " / ".join(x.get("title", "") if isinstance(x, dict) else str(x) for x in json.loads(path))
        except Exception: pass
        try: img = (json.loads(imgs) or [""])[0]
        except Exception: img = ""
        rows.append((code, title, sec, path, price, unit, chars, url, img if isinstance(img, str) else json.dumps(img)))
    d.executemany("insert into products values(?,?,?,?,?,?,?,?,?)", rows)
    d.execute("create virtual table fts using fts5(title, section, path, content='products', content_rowid='code', tokenize='unicode61')")
    d.execute("insert into fts(rowid,title,section,path) select code,title,section,path from products")
    d.commit(); print("products:", len(rows))

if __name__ == "__main__":
    main()
