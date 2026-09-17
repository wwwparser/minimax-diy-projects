"""Шаг 7. Статический сайт для GitHub Pages -> docs/ (index + страница на каждый проект).

Картинки из out/images/*.png конвертируются в WebP (docs/img), без картинки — аккуратная заглушка.
python src/build_site.py
"""
import html, json, shutil
from pathlib import Path
from PIL import Image

from short_names import short
from steps4 import STEPS4

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
IMG_SRC = ROOT / "out" / "images"
SIZES = {"illustration": 1400, "poster": 1200, "howto": 1200}
KIND_RU = {"illustration": "Иллюстрация", "poster": "Плакат", "howto": "Как сделать"}
E = html.escape

CSS = """
:root{--bg:#f6f1e7;--card:#fffdf8;--ink:#2a2118;--muted:#6f6254;--line:#e3d8c6;--accent:#c4622d;--accent2:#2f5d50;--chip:#efe6d6}
@media (prefers-color-scheme:dark){:root{--bg:#1c1814;--card:#26211b;--ink:#f1e9dc;--muted:#b3a693;--line:#3a3128;--accent:#e38552;--accent2:#7fb8a4;--chip:#332b23}}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 Manrope,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--accent2)}img{max-width:100%;display:block}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
header.top{padding:40px 0 24px;border-bottom:1px solid var(--line)}
.kicker{font:600 13px/1 Manrope,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--accent)}
h1{font:800 clamp(28px,5vw,52px)/1.08 Unbounded,Manrope,sans-serif;margin:12px 0 14px;letter-spacing:-.01em;overflow-wrap:break-word;hyphens:auto}
h2{font:700 24px/1.2 Unbounded,Manrope,sans-serif;margin:36px 0 14px}
.lead{max-width:760px;color:var(--muted);font-size:18px;margin:0}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px 14px}
.stat b{font:700 22px/1 Unbounded,sans-serif;display:block}.stat span{color:var(--muted);font-size:13px}
.filters{position:sticky;top:0;z-index:5;background:var(--bg);padding:14px 0;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:10px;align-items:center}
.filters input[type=search]{flex:1 1 220px;min-width:0;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit}
.seg{display:flex;gap:6px;flex-wrap:wrap}
.seg button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:7px 12px;font:600 14px Manrope,sans-serif;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.filters label{font-size:14px;color:var(--muted);display:flex;gap:8px;align-items:center}
select{padding:8px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);font:inherit}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px;padding:22px 0 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;text-decoration:none;color:inherit;display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 28px rgba(60,40,20,.12)}
.card .ph{aspect-ratio:3/2;background:var(--chip);position:relative;overflow:hidden}
.card .ph img{width:100%;height:100%;object-fit:cover}
.card .body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:8px;flex:1}
.card h3{font:700 17px/1.25 Manrope,sans-serif;margin:0}
.meta{display:flex;flex-wrap:wrap;gap:6px}
.chip{background:var(--chip);border-radius:999px;padding:3px 9px;font-size:12.5px;color:var(--muted)}
.price{margin-top:auto;font:800 20px/1 Unbounded,sans-serif;color:var(--accent)}
.star{position:absolute;top:10px;left:10px;background:var(--accent);color:#fff;font:700 12px Manrope;border-radius:999px;padding:4px 9px}
.placeholder{width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:18px;text-align:center;
 font:700 18px/1.2 Unbounded,sans-serif;color:var(--muted);background:repeating-linear-gradient(45deg,var(--chip) 0 14px,transparent 14px 28px)}
.empty{padding:40px 0;color:var(--muted)}
footer{border-top:1px solid var(--line);padding:26px 0 40px;color:var(--muted);font-size:14px}
/* project page */
.crumbs{padding:18px 0 0;font-size:14px}
.hero{display:grid;grid-template-columns:1.2fr 1fr;gap:28px;align-items:start;padding:14px 0 10px}
@media (max-width:820px){.hero{grid-template-columns:1fr}}
.hero .ph{border-radius:18px;overflow:hidden;background:var(--chip);aspect-ratio:3/2}
.hero .ph img{width:100%;height:100%;object-fit:cover}
.total{display:inline-flex;align-items:baseline;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 16px;margin:14px 0}
.total b{font:800 30px/1 Unbounded,sans-serif;color:var(--accent)}
ol.steps{padding-left:22px}ol.steps li{margin:6px 0}
.gallery{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media (max-width:720px){.gallery{grid-template-columns:1fr}}
.gallery figure{margin:0;background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden}
.gallery figcaption{padding:10px 14px;font-weight:700}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:15px;min-width:560px}
th,td{padding:9px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:13px;color:var(--muted);font-weight:700}
td.num{text-align:right;white-space:nowrap}
tr.group td{background:var(--chip);font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
tr.sum td{font-weight:800}
.note{background:var(--card);border-left:4px solid var(--accent2);padding:12px 16px;border-radius:8px;color:var(--muted)}
.nav2{display:flex;justify-content:space-between;gap:12px;padding:30px 0}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Unbounded:wght@700;800&display=swap" rel="stylesheet">')


def page(title, body, desc, depth=0):
    pre = "../" * depth
    return f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🪚</text></svg>">
{FONTS}<link rel="stylesheet" href="{pre}style.css"></head><body>{body}
<footer><div class="wrap">Цены — розница «Петрович», Москва, снимок каталога 16.09.2026; перед покупкой проверяйте на сайте.
Идеи — из открытых статей (ссылки на страницах проектов), адаптированы под шуруповёрт 12 В и ручной инструмент. Иллюстрации и плакаты сгенерированы ChatGPT.</div></footer></body></html>"""


def convert_images():
    out = DOCS / "img"; out.mkdir(parents=True, exist_ok=True)
    have = {}
    for png in sorted(IMG_SRC.glob("*_*.png")):
        pid, kind = png.stem.split("_", 1)
        if kind not in SIZES:
            continue
        dst = out / f"{pid}_{kind}.webp"
        if not dst.exists() or dst.stat().st_mtime < png.stat().st_mtime:
            im = Image.open(png).convert("RGB"); im.thumbnail((SIZES[kind], SIZES[kind] * 2))
            im.save(dst, "WEBP", quality=82, method=6)
        if kind == "illustration":
            th = out / f"{pid}_thumb.webp"
            if not th.exists() or th.stat().st_mtime < png.stat().st_mtime:
                im = Image.open(png).convert("RGB"); im.thumbnail((640, 640)); im.save(th, "WEBP", quality=78, method=6)
        have.setdefault(int(pid), set()).add(kind)
    return have


def ph(p, have, pre, cls="", thumb=False):
    if "illustration" in have.get(p["id"], ()):
        f = f"{p['id']:02d}_thumb.webp" if thumb else f"{p['id']:02d}_illustration.webp"
        return f'<img src="{pre}img/{f}" alt="{E(p["name"])}" loading="lazy">'
    return f'<div class="placeholder">{E(p["name"])}</div>'


def build():
    est = json.loads((ROOT / "out" / "estimates.json").read_text(encoding="utf-8"))
    DOCS.mkdir(exist_ok=True); (DOCS / "p").mkdir(exist_ok=True)
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copy(ROOT / "out" / "projects.xlsx", DOCS / "projects.xlsx")
    have = convert_images()
    est.sort(key=lambda p: (not p["top"], p["total"]))

    cards = []
    for p in est:
        cards.append(f"""<a class="card" href="p/{p['id']:02d}.html" data-mat="{E(p['material'])}" data-price="{p['total']}"
 data-diff="{p['difficulty']}" data-top="{int(p['top'])}" data-name="{E(p['name'].lower())}">
 <div class="ph">{ph(p, have, '', thumb=True)}{'<span class="star">★ топ-10</span>' if p['top'] else ''}</div>
 <div class="body"><h3>{E(p['name'])}</h3>
 <div class="meta"><span class="chip">{E(p['material'])}</span><span class="chip">сложность {p['difficulty']}/5</span><span class="chip">~{p['hours']} ч</span></div>
 <div class="price">{p['total']} ₽</div></div></a>""")
    n_img = sum(len(v) for v in have.values())
    body = f"""<header class="top"><div class="wrap"><div class="kicker">Интерскол ДА-10/12В · 36 Н·м</div>
<h1>57 проектов из дерева и металла под шуруповёрт</h1>
<p class="lead">Простые вещи для дома, дачи и мастерской, которые делаются аккумуляторным шуруповёртом и ручной пилой —
без сварки, болгарки и лобзика. К каждому проекту — смета по каталогу «Петровича» до 3000 ₽, куда уже входят свёрла,
биты, ножовка и расходники, пошаговая инструкция и плакат.</p>
<div class="stats"><div class="stat"><b>57</b><span>проектов</span></div><div class="stat"><b>{min(p['total'] for p in est)}–{max(p['total'] for p in est)} ₽</b><span>смета с оснасткой</span></div>
<div class="stat"><b>{sum('металл' in p['material'] for p in est)}</b><span>с металлом</span></div>{f'<div class="stat"><b>{n_img}</b><span>иллюстраций и плакатов</span></div>' if n_img else ''}
<div class="stat"><b><a href="projects.xlsx">XLSX</a></b><span>все сметы таблицей</span></div></div></div></header>
<div class="wrap"><div class="filters">
<input type="search" id="q" placeholder="Найти: полка, скворечник, металл…" aria-label="Поиск">
<div class="seg" id="mat"><button aria-pressed="true" data-v="">Все</button><button aria-pressed="false" data-v="дерево">Дерево</button><button aria-pressed="false" data-v="металл">С металлом</button><button aria-pressed="false" data-v="top">★ Топ-10</button></div>
<label>до <select id="price"><option value="3000">3000 ₽</option><option value="2000">2000 ₽</option><option value="1500">1500 ₽</option></select></label>
<label>сложность <select id="diff"><option value="5">любая</option><option value="1">1 — очень просто</option><option value="2">до 2</option></select></label>
</div><div class="grid" id="grid">{''.join(cards)}</div><div class="empty" id="empty" hidden>Ничего не нашлось — ослабьте фильтры.</div>
<h2>Что понадобится один раз</h2>
<p class="note">Сметы посчитаны так, будто дома есть только шуруповёрт. Ножовка, стусло, биты, свёрла и рулетка покупаются
один раз (≈650 ₽ для дерева, ≈630 ₽ для металла) и переходят в следующие проекты — вторая и третья вещь выходят заметно дешевле сметы.
Шуруповёрт 12 В: отверстия в металле до 8 мм сверлить на 1-й скорости, длинные саморезы — с засверловкой 3 мм.</p></div>
<script>
const q=document.getElementById('q'),price=document.getElementById('price'),diff=document.getElementById('diff'),mat=document.getElementById('mat');
let m='';mat.addEventListener('click',e=>{{const b=e.target.closest('button');if(!b)return;m=b.dataset.v;
 mat.querySelectorAll('button').forEach(x=>x.setAttribute('aria-pressed',x===b));apply();}});
function apply(){{const s=q.value.trim().toLowerCase();let n=0;
 document.querySelectorAll('.card').forEach(c=>{{let ok=(+c.dataset.price<=+price.value)&&(+c.dataset.diff<=+diff.value)&&(!s||c.dataset.name.includes(s));
  if(m==='top')ok=ok&&c.dataset.top==='1';else if(m==='металл')ok=ok&&c.dataset.mat.includes('металл');else if(m)ok=ok&&c.dataset.mat===m;
  c.hidden=!ok;n+=ok;}});document.getElementById('empty').hidden=n>0;}}
[q,price,diff].forEach(x=>x.addEventListener('input',apply));
</script>"""
    (DOCS / "index.html").write_text(page("Проекты под шуруповёрт — сметы и плакаты", body,
        "57 простых проектов из дерева и металла под шуруповёрт 12 В со сметами «Петровича» до 3000 ₽ и плакатами."), encoding="utf-8")

    order = [p["id"] for p in est]
    by_id = {p["id"]: p for p in est}
    for i, p in enumerate(est):
        rows, groups = [], {}
        for l in p["bom"]:
            groups.setdefault(l["kind"], []).append(l)
        for kind in ("материал", "крепёж", "отделка", "расходник", "оснастка"):
            if kind not in groups:
                continue
            rows.append(f'<tr class="group"><td colspan="5">{kind}</td></tr>')
            for l in groups[kind]:
                rows.append(f"""<tr><td><a href="{E(l['url'])}" target="_blank" rel="noopener">{E(short(l))}</a><br><small>{E(l['title'])} · арт. {l['code']}</small></td>
<td>{E(l.get('for', ''))}</td><td class="num">{l['qty']} {E(l['unit'])}</td><td class="num">{l['price']:.0f} ₽</td><td class="num">{l['sum']:.0f} ₽</td></tr>""")
        rows.append(f'<tr class="sum"><td colspan="4">Итого, включая оснастку {p["tools_total"]} ₽</td><td class="num">{p["total"]} ₽</td></tr>')
        gal = "".join(f'<figure><a href="../img/{p["id"]:02d}_{k}.webp" target="_blank"><img src="../img/{p["id"]:02d}_{k}.webp" alt="{KIND_RU[k]}: {E(p["name"])}" loading="lazy"></a><figcaption>{KIND_RU[k]}</figcaption></figure>'
                      for k in ("poster", "howto") if k in have.get(p["id"], ()))
        prev_p = by_id[order[i - 1]] if i else None
        next_p = by_id[order[i + 1]] if i + 1 < len(order) else None
        body = f"""<div class="wrap"><div class="crumbs"><a href="../index.html">← Все проекты</a></div>
<div class="hero"><div class="ph">{ph(p, have, '../')}</div><div>
<div class="kicker">{'★ топ-10 · ' if p['top'] else ''}{E(p['material'])}</div><h1>{E(p['name'])}</h1>
<p class="lead">{E(p['summary'])}</p>
<div class="meta" style="margin-top:12px"><span class="chip">сложность {p['difficulty']}/5</span><span class="chip">~{p['hours']} ч</span><span class="chip">{E(p['size'])}</span></div>
<div class="total"><b>{p['total']} ₽</b><span>смета с оснасткой</span></div>
<ol class="steps">{''.join(f'<li>{E(s)}</li>' for s in STEPS4[p['id']])}</ol></div></div>
{('<h2>Плакат и инструкция</h2><div class="gallery">' + gal + '</div>') if gal else ''}
<h2>Как сделать подробно</h2><ol class="steps">{''.join(f'<li>{E(s)}</li>' for s in p['steps'])}</ol>
<h2>Что купить в «Петровиче»</h2><div class="tablewrap"><table><thead><tr><th>Позиция</th><th>Зачем</th><th>Кол-во</th><th>Цена</th><th>Сумма</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p class="note" style="margin-top:18px">Источник идеи: <a href="{E(p['source'])}" target="_blank" rel="noopener">{E(p['source'][:90])}</a>.
Проект переработан под шуруповёрт 12 В и ручной инструмент.</p>
<div class="nav2">{f'<a href="{prev_p["id"]:02d}.html">← {E(prev_p["name"])}</a>' if prev_p else '<span></span>'}{f'<a href="{next_p["id"]:02d}.html">{E(next_p["name"])} →</a>' if next_p else ''}</div></div>"""
        (DOCS / "p" / f"{p['id']:02d}.html").write_text(page(f"{p['name']} — смета {p['total']} ₽", body, p["summary"], depth=1), encoding="utf-8")
    print(f"сайт: {len(est)} страниц, картинок {n_img}")


if __name__ == "__main__":
    build()
