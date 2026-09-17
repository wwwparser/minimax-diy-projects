"""Шаг 3. Бесплатные модели OpenRouter извлекают DIY-проекты из страниц -> data/extracted.jsonl (resume)."""
import concurrent.futures, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "services"))
from llm_client import chat_json

SYSTEM = "Ты извлекаешь данные из статей о DIY-проектах. Отвечай только валидным JSON, по-русски."
PROMPT = """Из текста статьи извлеки ВСЕ конкретные DIY-проекты из дерева и/или металла, которые описаны с материалами или размерами.
Не выдумывай. Если проектов нет — верни {{"projects": []}}. Не больше 8 проектов со страницы.

Схема:
{{"projects": [{{
 "name": "короткое название по-русски, напр. 'Настенная полка из доски'",
 "material": "дерево | металл | дерево+металл",
 "summary": "1-2 предложения, что это и зачем",
 "size": "габариты, если есть",
 "materials": [{{"item": "что купить, напр. 'доска строганая'", "spec": "размер/сечение/параметры", "qty": "количество числом", "unit": "шт|м|кг|л|уп"}}],
 "tools": ["инструменты, упомянутые в статье"],
 "steps": ["до 6 коротких шагов"],
 "needs_welding": false,
 "needs_big_tools": "список крупного инструмента кроме дрели-шуруповёрта (циркулярка, фрезер, болгарка, лобзик, торцовка), или пусто",
 "difficulty": 1
}}]}}
difficulty: 1 — очень просто, 5 — сложно.

URL: {url}
Заголовок: {title}
Текст:
{text}"""

def work(page):
    for attempt in range(3):
        try:
            data = chat_json(SYSTEM, PROMPT.format(url=page["url"], title=page["title"], text=page["text"][:12000]), max_tokens=4000)
            return {"url": page["url"], "title": page["title"], "projects": data.get("projects", [])}
        except Exception as e:
            err = str(e); time.sleep(5)
    return {"url": page["url"], "error": err[:300]}

def main(limit=None, threads=4):
    out = Path("data/extracted.jsonl")
    done = {json.loads(l)["url"] for l in out.open(encoding="utf-8") if '"error"' not in l} if out.exists() else set()
    pages = [json.loads(l) for l in open("data/pages.jsonl", encoding="utf-8")]
    pages = [p for p in pages if len(p.get("text") or "") > 800 and p["url"] not in done][:limit]
    print("страниц:", len(pages)); t0 = time.time()
    with out.open("a", encoding="utf-8") as f, concurrent.futures.ThreadPoolExecutor(threads) as pool:
        for i, r in enumerate(pool.map(work, pages), 1):
            f.write(json.dumps(r, ensure_ascii=False) + "\n"); f.flush()
            print(i, f"{time.time()-t0:.0f}s", len(r.get("projects", [])), r.get("error", "")[:80], r["url"][:70])

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else 4)
