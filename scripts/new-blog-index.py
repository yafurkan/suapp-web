#!/usr/bin/env python3
"""
Suu — yeni bir dil için blog indeksi kabuğu üret

Blog indeksleri (blog.html, blog-en.html …) ELLE bakılan dosyalar; kartları
sync-blog-index.py, Blog.blogPost şemasını sync-blog-schema.py dolduruyor.
Bu script yalnızca ilk kabuğu kuruyor: blog-en.html'i klonlar, kart gridini
boşaltır ve dile bağlı metinleri content/languages.json'daki
"blog_index_copy" bloğundan yazar.

Bir kez çalıştırılır. Sonrasında dosya diğer dört indeks gibi elle bakılır —
bu yüzden idempotent DEĞİL: var olan dosyanın üzerine yazmayı reddeder.

Kullanım:
    python3 scripts/new-blog-index.py de           # önizleme
    python3 scripts/new-blog-index.py de --apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _langs import table

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"
SHELL = ROOT / "blog-en.html"


def empty_grid(html: str) -> str:
    """`<div class="articles-grid">` içeriğini boşalt."""
    start = html.index('<div class="articles-grid">')
    depth, i = 0, start
    while True:
        m = re.compile(r"<div\b|</div>").search(html, i)
        if not m:
            raise SystemExit("HATA: articles-grid kapanışı bulunamadı.")
        depth += 1 if m.group(0) == "<div" else -1
        i = m.end()
        if depth == 0:
            break
    return html[:start] + '<div class="articles-grid">\n\n    </div>' + html[i:]


def build(lang: str) -> str:
    entry = table()[lang]
    copy = entry.get("blog_index_copy")
    if not copy:
        raise SystemExit(f"HATA: content/languages.json → {lang}.blog_index_copy yok.")

    html = SHELL.read_text(encoding="utf-8")
    html = empty_grid(html)

    index = entry["blog_index"]
    url = f"{BASE}/{index}"
    home = entry["home_href"]
    hub = entry["ui"].get("hub_href", "/comparisons.html")

    # Blog şeması: yazı listesi boşalır, dil ve adres yeni dile döner.
    # sync-blog-schema.py blogPost'u yazılar eklendikçe dolduruyor.
    def fix_blog_schema(m: re.Match) -> str:
        data = json.loads(m.group(1))
        node = data["@graph"][0] if "@graph" in data else data
        if node.get("@type") != "Blog":
            return m.group(0)
        node["blogPost"] = []
        node["inLanguage"] = entry["bcp47"]
        for key in ("url", "@id", "mainEntityOfPage"):
            if key in node:
                node[key] = url if key != "@id" else f"{url}#blog"
        node["name"] = copy["title"]
        node["description"] = copy["description"]
        body = json.dumps(data, ensure_ascii=False, indent=2)
        return f'<script type="application/ld+json">\n{body}\n</script>'

    html = re.sub(r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
                  fix_blog_schema, html, flags=re.S)

    repl = [
        ('<html lang="en">', f'<html lang="{lang}">'),
        ("Suu Blog — Calorie Counting, GPS Workouts &amp; Hydration Guides", copy["title"]),
        ("Evidence-based guides on calorie counting, AI photo food logging, GPS workout "
         "tracking and hydration — plus comparisons with MyFitnessPal, Yazio and Strava.",
         copy["description"]),
        ("Calories and macros, AI photo food logging, GPS workout tracking and hydration "
         "— plus honest app comparisons.", copy["og_description"]),
        ("calorie counting guide, macro calculation, ai photo calorie app, gps workout "
         "tracking, strava alternative, myfitnesspal alternative, hydration tips, how "
         "much water to drink", copy["keywords"]),
        (f"{BASE}/blog-en.html", url),
        ('href="/llms-en.txt"', f'href="/llms-{lang}.txt"'),
        ('href="/llms-full-en.txt"', f'href="/llms-full-{lang}.txt"'),
        ('title="Suu Blog (English)" href="/feed-en.xml"',
         f'title="{entry["feed_title"]}" href="/{entry["feed"]}"'),
        ('content="en_US"', f'content="{entry["locale"]}"'),
        ('href="hosgeldiniz-en.html"', f'href="{home.lstrip("/")}"'),
        ('href="comparisons.html"', f'href="{hub.lstrip("/")}"'),
        ("</i> Comparisons</a>", f"</i> {copy['nav_comparisons']}</a>"),
        ("</i> Home</a>", f"</i> {copy['nav_home']}</a>"),
        ("<h1>💧 Suu Blog</h1>", f"<h1>{copy['h1']}</h1>"),
        ("Science-backed articles on calories and macros, AI photo food logging, GPS "
         "workout tracking and hydration — plus honest head-to-head app comparisons.",
         copy["lead"]),
        ("<h2>Start Tracking Your Water Today</h2>", f"<h2>{copy['cta_head']}</h2>"),
        ("Suu turns these tips into daily habits — personalized goals, smart reminders, "
         "and friend leagues. Free on iOS and Android.", copy["cta_sub"]),
    ]
    for old, new in repl:
        html = html.replace(old, new)

    # Sözlük yalnızca tr/en'de var — karşılığı olmayan dilde bağlantı bırakma.
    if not entry["ui"].get("glossary_href"):
        html = re.sub(r'\s*<a href="glossary\.html"[^>]*>.*?</a>', "", html, flags=re.S)

    if entry["dir"] == "rtl" and ' dir="rtl"' not in html[:200]:
        html = html.replace(f'<html lang="{lang}">', f'<html lang="{lang}" dir="rtl">', 1)
    return html


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit("Kullanım: python3 scripts/new-blog-index.py <dil> [--apply]")
    lang = args[0]
    apply = "--apply" in sys.argv

    entry = table().get(lang)
    if not entry:
        raise SystemExit(f"HATA: {lang} content/languages.json'da yok.")

    target = ROOT / entry["blog_index"]
    if target.exists():
        raise SystemExit(f"HATA: {target.name} zaten var — bu script yalnızca ilk "
                         f"kabuğu kurar, var olan indekse dokunmaz.")

    html = build(lang)
    print(f"  {entry['blog_index']:<20} {len(html)//1024:>3} KB  "
          f"{'yazıldı' if apply else 'ÖNİZLEME'}")
    if apply:
        target.write_text(html, encoding="utf-8")
        (ROOT / entry["blog_dir"]).mkdir(parents=True, exist_ok=True)
        print(f"  {entry['blog_dir']}/ klasörü hazır")
        print("\nSonra: sync-blog-index.py, sync-blog-schema.py, build-feeds.py, "
              "inject-hreflang.py, update-sitemap.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
