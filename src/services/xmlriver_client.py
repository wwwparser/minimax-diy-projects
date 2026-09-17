import concurrent.futures, math, os, re, time
import xml.etree.ElementTree as ET
from html import unescape

import requests

ENDPOINTS = {"google": "https://xmlriver.com/search/xml",
             "yandex": "https://xmlriver.com/search_yandex/xml"}
MAX_THREADS = 10          # столько даёт стандартный аккаунт
RESULTS_PER_PAGE = 10     # больше groupby не выдаёт, глубже — только page

# регион -> (Criteria ID для Google country, Яндекс lr, язык)
REGIONS = {"RU": ("2643", "225", "ru"), "RU-MOSCOW": ("1011969", "213", "ru"),
           "US": ("2840", "84", "en"), "UK": ("2826", "102", "en"),
           "FR": ("2250", "124", "fr")}


class XmlRiverError(RuntimeError):
    pass


def region_params(engine: str, region: str = "RU", language: str = "") -> dict:
    """Google: регион — country, язык — lr. Яндекс: регион — lr, язык — lang."""
    key = (region or "").upper().replace(" ", "-")
    loc = lr = None
    if key in REGIONS:
        loc, lr, lang_default = REGIONS[key]
        language = language or lang_default
    elif region.isdigit():
        loc = lr = region
    if engine == "google":
        return {k: v for k, v in (("country", loc), ("lr", language)) if v}
    return {k: v for k, v in (("lr", lr), ("lang", language)) if v}


def _decode(r: requests.Response) -> str:
    """Строго, без errors='ignore' — иначе кириллица превратится в мусор."""
    for enc in ("utf-8", "windows-1251"):
        try:
            return r.content.decode(enc)
        except UnicodeDecodeError:
            continue
    return r.content.decode("utf-8", "replace")


def raw_search(query: str, engine: str = "google", page: int | None = None,
               region: str = "RU", language: str = "", ai: bool = False,
               retries: int = 5) -> str:
    """Сырой XML одной страницы. Разные ошибки XMLRiver требуют разной паузы."""
    user, key = os.getenv("XMLRIVER_USER"), os.getenv("XMLRIVER_KEY")
    if not user or not key:
        raise RuntimeError("XMLRIVER_USER/XMLRIVER_KEY не заданы в .env")
    params = {"user": user, "key": key, "query": query, "groupby": RESULTS_PER_PAGE,
              **region_params(engine, region, language)}
    # Google считает страницы с 1, Яндекс с 0
    params["page"] = (1 if engine == "google" else 0) if page is None else page
    if ai:
        params["ai"] = "1"

    last = ""
    for attempt in range(retries):
        try:
            r = requests.get(ENDPOINTS[engine], params=params, timeout=180)
        except requests.RequestException as e:
            last = str(e)
            time.sleep(4 * (attempt + 1))
            continue
        text = _decode(r)
        m = re.search(r"<error[^>]*>(.*?)</error>", text, re.S)
        if not m:
            return text
        last = unescape(m.group(1)).strip()
        if attempt >= retries - 1:
            break
        # «заняты все каналы» — лимит потоков, короткий ретрай бесполезен
        time.sleep((15 if "канал" in last.lower() else 4) * (attempt + 1))
    raise XmlRiverError(f"XMLRiver [{engine}] «{query}»: {last}")


def parse_serp(xml_text: str, start: int = 0) -> list[dict]:
    root = ET.fromstring(xml_text)          # <error> уже отсеян в raw_search
    return [{"position": start + i,
             "url": doc.findtext("url", "") or "",
             "title": (doc.findtext("title", "") or "").strip(),
             "snippet": " ".join(p.text or "" for p in doc.iter("passage")).strip()}
            for i, doc in enumerate(root.iter("doc"), 1)]


def search(query: str, engine: str = "google", top: int = 10,
           region: str = "RU", language: str = "") -> list[dict]:
    """[{'position','url','title','snippet'}, ...]. top > 10 = доп. ПЛАТНЫЕ запросы."""
    base = 1 if engine == "google" else 0
    out = []
    for n in range(max(1, math.ceil(top / RESULTS_PER_PAGE))):
        xml_text = raw_search(query, engine, page=base + n, region=region, language=language)
        out.extend(parse_serp(xml_text, start=n * RESULTS_PER_PAGE))
        if len(out) >= top:
            break
    return out[:top]


def planned_requests(queries: int, engines: int, top: int) -> int:
    """Сколько платных запросов уйдёт — называть пользователю ДО запуска."""
    return queries * engines * max(1, math.ceil(top / RESULTS_PER_PAGE))


def search_many(tasks: list[dict], threads: int = MAX_THREADS):
    """Параллельный сбор. tasks: [{'query','engine','top','region'}, ...].
    Отдаёт (task, results, error) по мере готовности."""
    def run(t):
        try:
            return t, search(t["query"], t.get("engine", "google"), t.get("top", 10),
                             t.get("region", "RU"), t.get("language", "")), None
        except XmlRiverError as e:
            return t, None, e
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(threads, MAX_THREADS)) as pool:
        for f in concurrent.futures.as_completed([pool.submit(run, t) for t in tasks]):
            yield f.result()


def _load_env():
    from pathlib import Path
    p = Path(__file__).resolve().parents[2] / ".env"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()
