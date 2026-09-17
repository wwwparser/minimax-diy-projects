"""Шаг 6. Картинки в ChatGPT через Browser Bridge (живой Chrome): на проект — иллюстрация, плакат, инструкция.

Один чат на проект, три запроса подряд. Resume: готовые файлы out/images/NN_<kind>.png пропускаются.
Мост общий: работаем в своей сессии и всегда проверяем, что целевая вкладка — chatgpt.com.

python src/make_images.py              # все проекты по порядку (сначала топ-10)
python src/make_images.py 1 11 20      # только эти
"""
import base64, json, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, r"C:/Users/Yuri/.claude/skills/browser-bridge")
import bridge as B

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


class WrongTab(RuntimeError):
    pass


def guard():
    info = B.tabinfo()
    if not info.get("ok") or "chatgpt.com" not in (info.get("url") or ""):
        raise WrongTab(f"целевая вкладка не ChatGPT: {info}")


def ev(js):
    guard()
    r = B.js_eval(js)
    if isinstance(r, dict) and r.get("_error"):
        raise RuntimeError(r["_error"])
    return r


IMGS = """(() => [...new Set([...document.querySelectorAll('main img')]
  .filter(i => /oaiusercontent|backend-api|estuary/.test(i.src) && i.naturalWidth >= 512)
  .map(i => i.src))])()"""
BUSY = "!!document.querySelector('[data-testid=\"stop-button\"]')"
LAST_TEXT = """(() => { const m=[...document.querySelectorAll('[data-message-author-role="assistant"]')].pop();
  return m ? m.innerText.slice(0, 400) : ''; })()"""


def new_chat():
    ev("location.href='https://chatgpt.com/'")
    time.sleep(10)
    for _ in range(20):
        if ev("!!document.querySelector('#prompt-textarea')"):
            return
        time.sleep(2)
    raise RuntimeError("поле ввода не появилось")


def send(text):
    ev("document.querySelector('#prompt-textarea').focus()")
    guard(); B.cdp("Input.insertText", {"text": text}); time.sleep(1.5)
    for _ in range(10):
        if ev("!!document.querySelector('[data-testid=\"send-button\"]')"):
            ev("document.querySelector('[data-testid=\"send-button\"]').click()"); return
        time.sleep(1)
    raise RuntimeError("кнопка отправки не найдена")


def wait_image(before, timeout=480):
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(8)
        imgs = ev(IMGS) or []
        new = [s for s in imgs if s not in before]
        if new and not ev(BUSY):
            time.sleep(4)
            imgs = ev(IMGS) or []
            return [s for s in imgs if s not in before][-1]
        if not ev(BUSY) and time.time() - t0 > 40 and not new:
            txt = ev(LAST_TEXT) or ""
            return "TEXT:" + txt
    return None


def download(src, fn):
    b64 = ev(f"""(async()=>{{const r=await fetch({json.dumps(src)});const b=await r.blob();
      return await new Promise(res=>{{const f=new FileReader();f.onload=()=>res(f.result.split(',')[1]);f.readAsDataURL(b);}});}})()""")
    fn.write_bytes(base64.b64decode(b64))


def project(item):
    todo = [k for k in KINDS if not (OUT / f"{item['id']:02d}_{k}.png").exists()]
    if not todo:
        return
    log(f"[{item['id']}] {item['name']}: {', '.join(todo)}")
    new_chat()
    for kind in todo:
        fn = OUT / f"{item['id']:02d}_{kind}.png"
        for attempt in range(3):
            before = ev(IMGS) or []
            send(item[kind])
            res = wait_image(before)
            if res and not res.startswith("TEXT:"):
                download(res, fn)
                log(f"  OK {fn.name} {fn.stat().st_size // 1024} КБ")
                break
            txt = (res or "")[5:]
            log(f"  нет картинки ({kind}), попытка {attempt + 1}: {txt[:160]!r}")
            if any(w in txt.lower() for w in ("лимит", "limit", "попробуйте позже", "try again later")):
                log("  лимит генерации — пауза 30 мин"); time.sleep(1800); new_chat()
            else:
                send("Нужна именно картинка. Сгенерируй изображение по описанию выше.")
                res = wait_image(ev(IMGS) or [])
                if res and not res.startswith("TEXT:"):
                    download(res, fn); log(f"  OK {fn.name}"); break


def bridge_busy() -> str:
    """Мост до v1.2 — одна закреплённая вкладка на всех: пока пишется занятие йоги, не лезем."""
    out = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | % CommandLine"],
                         capture_output=True).stdout.decode("cp866", "replace")
    return next((m for m in ("slide_timeline.py", "pin_watchdog.py", "job_capture.py") if m in out), "")


if __name__ == "__main__":
    if (busy := bridge_busy()) and "--force" not in sys.argv:
        sys.exit(f"мост занят другим проектом ({busy}) — запусти после окончания записи или с --force (мост v1.2)")
    if not B.supports_sessions():
        sys.exit(f"мост без сессий ({B.get('/status')}) — нужен v1.2: перезапустить bridge.py serve и обновить расширение")
    B.set_session(SESSION)
    items = json.loads((OUT / "prompts.json").read_text(encoding="utf-8"))
    only = {int(x) for x in sys.argv[1:] if x.isdigit()}
    info = B.tabinfo()
    if "chatgpt.com" not in (info.get("url") or ""):
        log(f"закрепляю вкладку ChatGPT за сессией {SESSION}: {B.pin('https://chatgpt.com/')}"); time.sleep(10)
    for it in items:
        if only and it["id"] not in only:
            continue
        for attempt in range(3):
            try:
                project(it); break
            except WrongTab as e:
                sys.exit(f"СТОП: {e}")
            except Exception as e:
                log(f"  ошибка {type(e).__name__}: {e}; повтор через 30 с"); time.sleep(30)
    log("готово")
