"""Шаг 6. Картинки в ChatGPT через Browser Bridge: на проект — иллюстрация, плакат, инструкция.

Вся работа с ChatGPT (темп, лимиты, проверка окон «Слишком много запросов», API диалога) —
в общем модуле ~/.claude/skills/browser-bridge/chatgpt.py. Здесь только очередь проектов и resume.

python src/make_images.py              # все проекты (сначала топ-10), готовые файлы пропускаются
python src/make_images.py 1 11 20      # только эти
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, r"C:/Users/Yuri/.claude/skills/browser-bridge")
import chatgpt as G

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "images"
KINDS = ("illustration", "poster", "howto")
SESSION = "minimax-images"
LOG = OUT / "log.txt"


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def project(gpt: G.ChatGPT, item):
    todo = [k for k in KINDS if not (OUT / f"{item['id']:02d}_{k}.png").exists()]
    if not todo:
        return
    log(f"[{item['id']}] {item['name']}: {', '.join(todo)}")
    gpt.new_chat()
    for kind in todo:
        fn = OUT / f"{item['id']:02d}_{kind}.png"
        prompt = item[kind]
        for attempt in range(3):
            res = gpt.generate_image(prompt)
            if res.ok:
                fn.write_bytes(res.data)
                log(f"  OK {fn.name} {len(res.data) // 1024} КБ")
                break
            log(f"  нет картинки ({kind}), попытка {attempt + 1}: {res.reason} {res.text[:120]!r}")
            if res.reason == "content_policy":
                gpt.new_chat()
                prompt = item[kind].replace("руки мастера выполняют шаг", "показан результат шага")
            elif res.reason == "text_answer":
                prompt = "Нужна именно картинка, без текста в ответе. Сгенерируй изображение по описанию: " + item[kind]
            else:
                gpt.new_chat()


if __name__ == "__main__":
    gpt = G.ChatGPT(session=SESSION, log=log, rate_per_hour=12, shots_dir=OUT / "blocks")
    items = json.loads((OUT / "prompts.json").read_text(encoding="utf-8"))
    only = {int(x) for x in sys.argv[1:] if x.isdigit()}
    gpt.ensure_tab()
    for it in items:
        if only and it["id"] not in only:
            continue
        for attempt in range(4):
            try:
                project(gpt, it)
                break
            except G.WrongTab as e:
                sys.exit(f"СТОП: {e}")
            except G.Blocked as e:
                if e.kind == "logged_out":
                    sys.exit(f"СТОП: ChatGPT разлогинен — войдите в аккаунт ({e.text[:80]})")
                time.sleep(max(e.wait, 60))
            except Exception as e:
                log(f"  ошибка {type(e).__name__}: {e}; повтор через 2 мин")
                time.sleep(120)
    log("готово")
