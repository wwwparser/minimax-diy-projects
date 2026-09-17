"""Пересобрать сайт с новыми картинками и выложить на GitHub Pages (commit + push, если есть изменения)."""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")

if __name__ == "__main__":
    subprocess.run([sys.executable, str(ROOT / "src" / "build_site.py")], check=True)
    git("add", "docs")
    if not git("diff", "--cached", "--quiet").returncode:
        print("изменений нет"); sys.exit()
    n = len(list((ROOT / "docs" / "img").glob("*_illustration.webp")))
    git("commit", "-m", f"Сайт: картинки для {n} проектов\n\nCo-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>")
    r = git("push", "-q")
    print("push:", r.returncode, r.stderr.strip()[:200])
