"""Шаг 2. Скачать страницы из выдачи и вытащить основной текст -> data/pages.jsonl (resume)."""
import concurrent.futures, json, re
from pathlib import Path
import requests
try:
    import trafilatura
except ImportError:
    trafilatura = None
from bs4 import BeautifulSoup

SKIP = re.compile(r"youtube\.|youtu\.be|vk\.com|ozon\.|wildberries|market\.yandex|avito|pinterest|instagram|tiktok|dzen\.ru/video|rutube|amazon\.|etsy\.|reddit\.|facebook|lemanapro|leroymerlin\.ru/product|petrovich\.ru/product", re.I)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"}

def extract(html):
    if trafilatura:
        t = trafilatura.extract(html, include_tables=True, favor_recall=True)
        if t and len(t) > 500:
            return t
    soup = BeautifulSoup(html, "html.parser")
    for x in soup(["script", "style", "nav", "header", "footer", "aside"]):
        x.decompose()
    return re.sub(r"\n\s*\n+", "\n", soup.get_text("\n", strip=True))

def fetch(item):
    url, title = item
    try:
        r = requests.get(url, headers=UA, timeout=25)
        r.raise_for_status()
        return {"url": url, "title": title, "text": extract(r.text)[:30000]}
    except Exception as e:
        return {"url": url, "title": title, "error": str(e)[:200]}

def main():
    urls = {}
    for l in open("data/serp.jsonl", encoding="utf-8"):
        for r in json.loads(l)["results"]:
            if not SKIP.search(r["url"]):
                urls.setdefault(r["url"], r["title"])
    out = Path("data/pages.jsonl")
    done = {json.loads(l)["url"] for l in out.open(encoding="utf-8")} if out.exists() else set()
    todo = [(u, t) for u, t in urls.items() if u not in done]
    print("к загрузке:", len(todo))
    with out.open("a", encoding="utf-8") as f, concurrent.futures.ThreadPoolExecutor(16) as pool:
        for res in pool.map(fetch, todo):
            f.write(json.dumps(res, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
