#!/usr/bin/env python3
"""
Suu — blog indekslerini üret (blog.html, blog-en.html, blog-ar.html …)

Eskiden indeksler elle bakılan dosyalardı: kartları sync-blog-index.py
gridin başına ekliyordu, kategori yoktu, TR indeksindeki "Toplam Yazı / Bu Ay
/ Son Güncelleme" sayaçları Nisan 2026'da sabitlenmiş sayılardı (60 yazı
varken "19"), AR/RU indekslerinin <title>'ı tek bir yazının başlığıydı.

Artık her indeks tek kaynaktan üretilir:
  - yazı listesi  → blog_langs() klasörleri (yönlendirme sayfaları hariç)
  - başlık/özet/tarih/görsel → yazının KENDİ meta verisi (uydurulmaz)
  - kategori      → content/blog-index.json "assign" (küme anahtarı ya da
                    "lang/slug"); atanmamış yazı slug'dan tahmin edilir ve
                    uyarı basılır
  - arayüz metni  → content/blog-index.json "copy"
  - şablon        → content/blog-index.html.j2
  - kart görseli  → yazının og:image PNG'sinden 600×315 WebP küçük resim
                    (assets/og/blog/thumb/), yalnızca eksik/eskiyse üretilir

Sayılar (yazı, kategori, son güncelleme) derleme anında yazılardan hesaplanır.
Hreflang bloğu yazılmaz; inject-hreflang.py ekler, bu script mevcut bloğu korur.
Blog JSON-LD'si tüm yazıları taşır, bu yüzden sync-blog-index.py ve
sync-blog-schema.py bu sayfalarda yapacak iş bulamaz (ikisi de üretilmiş
indeksi atlar).

Kullanım:
    python3 scripts/build-blog-index.py            # önizleme
    python3 scripts/build-blog-index.py --apply
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from _langs import table

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
CONFIG = CONTENT / "blog-index.json"
REGISTRY = CONTENT / "page-registry.json"
THUMB_DIR = ROOT / "assets" / "og" / "blog" / "thumb"
BASE = "https://suuapp.com"
MARKER = ("<!-- ÜRETİLMİŞ DOSYA — kaynak: scripts/build-blog-index.py + content/blog-index.json "
          "+ content/blog-index.html.j2. Elle düzenlemeyin. -->")
THUMB_SIZE = (600, 315)
WORDS_PER_MIN = 200
# inject-breadcrumb-schema.py yazılarda aynı adları kullanıyor
BLOG_CRUMB = {"ar": "المدونة", "ru": "Блог", "uk": "Блог"}

RE_LD = re.compile(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', re.S)
RE_HREFLANG = re.compile(
    r"\n    <!-- Hreflang cluster \(auto-injected\) -->\n(?:    <link rel=\"alternate\" hreflang=[^\n]+\n)+")

# Atanmamış yazılar için son çare (uyarı basılır): slug → kategori.
GUESS = [
    (r"-vs-|karsilastir|alternati|badail|en-iyi|best-|afdal|luchsh|najkrashch|migliore|beste-", "compare"),
    (r"kahve|coffee|caff|kafein|cay-|tea|alkol|alcohol|enerji|energy|soda|kola|juice|meyve", "drinks"),
    (r"hamile|pregnan|emzir|breastfe|bobrek|kidney|cilt|skin|uyku|sleep|yorgun|tired", "health"),
    (r"egzersiz|spor|sport|workout|exercise|antren|allenam|trenuv|kosu|running|walk", "exercise"),
    (r"kalori|calori|kalorij|makro|macro|kilo|weight|diet|beslen|nutrition", "calories"),
]


def meta(page: str, key: str) -> str:
    k = re.escape(key)
    m = (re.search(rf'<meta\s+(?:name|property)="{k}"\s+content="([^"]*)"', page)
         or re.search(rf'<meta\s+content="([^"]*)"\s+(?:name|property)="{k}"', page))
    return html.unescape(m.group(1)).strip() if m else ""


def clean_title(t: str) -> str:
    t = re.sub(r"\s+", " ", html.unescape(t)).strip()
    return re.sub(r"\s*[|·—–-]\s*(?:Suu(?:\s+Blog)?|مدونة Suu|Блог Suu)\s*$", "", t).strip()


def ld_dates(page: str) -> tuple[str | None, str | None]:
    pub = mod = None
    for m in RE_LD.finditer(page):
        try:
            d = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        nodes = []
        if isinstance(d, dict):
            nodes = [d] + [n for n in d.get("@graph", []) if isinstance(n, dict)]
        elif isinstance(d, list):
            nodes = [n for n in d if isinstance(n, dict)]
        for n in nodes:
            ty = n.get("@type")
            types = ty if isinstance(ty, list) else [ty]
            if any(isinstance(t, str) and (t.endswith("Article") or t == "BlogPosting") for t in types):
                pub = pub or n.get("datePublished")
                mod = mod or n.get("dateModified")
    return pub, mod


def read_minutes(page: str) -> int:
    m = (re.search(r"<article\b.*?</article>", page, re.S)
         or re.search(r"<main\b.*?</main>", page, re.S)
         or re.search(r"<body\b.*?</body>", page, re.S))
    body = m.group(0) if m else page
    body = re.sub(r"<(script|style|svg|nav|footer|aside)\b.*?</\1>", " ", body, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    words = len(re.findall(r"\w+", text))
    return max(2, round(words / WORDS_PER_MIN))


def trim(s: str, limit: int = 170) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= limit:
        return s
    return s[: limit - 5].rsplit(" ", 1)[0].rstrip(",;:—–-") + "…"


def plural(lang: str, n: int, forms: list[str]) -> str:
    if len(forms) == 1:
        return forms[0]
    if len(forms) == 3:  # ru / uk
        if n % 10 == 1 and n % 100 != 11:
            return forms[0]
        if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            return forms[1]
        return forms[2]
    if lang == "ar":  # 3–10 → jam' ; 11+ → tamyiz (mufrad mansub)
        return forms[1] if 3 <= n % 100 <= 10 else forms[0]
    return forms[0] if n == 1 else forms[1]


def fmt_date(iso: str, lang: str, langs: dict) -> str:
    y, mo, d = (int(x) for x in iso[:10].split("-"))
    row = langs[lang]
    return row["date_fmt"].format(d=d, month=row["months"][mo - 1], y=y)


def thumb_of(og_url: str) -> tuple[Path, Path] | None:
    """og:image → (kaynak PNG, hedef WebP); site dışı/eksik görselde None."""
    if "/assets/og/blog/" not in og_url:
        return None
    rel = og_url.split("suuapp.com/", 1)[-1].lstrip("/")
    src = ROOT / rel
    if not src.exists():
        return None
    return src, THUMB_DIR / (src.stem + ".webp")


def make_thumb(src: Path, dst: Path) -> None:
    from PIL import Image
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB").resize(THUMB_SIZE, Image.LANCZOS)
        im.save(dst, "WEBP", quality=80, method=6)


def category_lookup(cfg: dict, registry: dict, warnings: list[str]):
    by_cluster, by_page = {}, {}
    for cat, items in cfg["assign"].items():
        for it in items:
            target = by_page if "/" in it else by_cluster
            if it in target:
                warnings.append(f"'{it}' iki kategoride: {target[it]} ve {cat}")
            target[it] = cat
    page_cluster = {}
    for key, v in registry.get("blog", {}).items():
        if key.startswith("_") or not isinstance(v, dict):
            continue
        for lang, slug in v.items():
            page_cluster[(lang, slug)] = key
    known = set(page_cluster.values())
    for k in by_cluster:
        if k not in known:
            warnings.append(f"assign: '{k}' page-registry.json blog kümelerinde yok")
    return by_cluster, by_page, page_cluster


def main() -> int:
    apply = "--apply" in sys.argv
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    langs = table()
    cats = {c["key"]: c for c in cfg["categories"]}
    warnings: list[str] = []
    by_cluster, by_page, page_cluster = category_lookup(cfg, registry, warnings)

    env = Environment(loader=FileSystemLoader(str(CONTENT)), undefined=StrictUndefined,
                      autoescape=True, keep_trailing_newline=True)
    template = env.get_template("blog-index.html.j2")

    thumbs_todo: dict[Path, Path] = {}
    changed = 0

    # blog_langs() indeks dosyası olmayan dili döndürmez; burada yazı klasörü
    # olan her dil işlenir ki yeni bir dilin indeksi ilk build'de oluşsun.
    targets = []
    for lang, row in langs.items():
        index_file, folder = row.get("blog_index"), row.get("blog_dir")
        if not index_file or not folder or not (ROOT / folder).is_dir():
            continue
        if lang not in cfg["copy"]:
            warnings.append(f"{index_file}: content/blog-index.json copy.{lang} yok — atlandı")
            continue
        targets.append((lang, index_file, folder, folder.rstrip("/") + "/", row["bcp47"]))

    for lang, index_file, folder, prefix, bcp47 in targets:
        c = cfg["copy"][lang]
        row = langs[lang]
        url = f"{BASE}/{index_file}"

        posts = []
        for f in sorted((ROOT / folder).glob("*.html")):
            page = f.read_text(encoding="utf-8")
            if 'http-equiv="refresh"' in page:
                continue  # redirect-cannibals.py yönlendirme sayfası
            slug = f.stem
            title = clean_title(meta(page, "og:title") or
                                (re.search(r"<title>(.*?)</title>", page, re.S) or [None, ""])[1])
            pub, mod = ld_dates(page)
            pub = pub or meta(page, "article:published_time")
            mod = mod or meta(page, "article:modified_time") or None
            if not pub:
                warnings.append(f"{prefix}{f.name}: yayın tarihi yok — atlandı")
                continue

            cluster = page_cluster.get((lang, slug))
            cat = by_page.get(f"{lang}/{slug}") or (by_cluster.get(cluster) if cluster else None)
            if not cat:
                cat = next((k for pat, k in GUESS if re.search(pat, slug)), "water")
                warnings.append(f"{prefix}{f.name}: kategori atanmadı → tahmin '{cat}' "
                                f"(content/blog-index.json assign'a ekle)")
            cd = cats[cat]

            og = meta(page, "og:image")
            th = thumb_of(og)
            thumb = None
            if th:
                src, dst = th
                if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
                    thumbs_todo[src] = dst
                thumb = "/" + dst.relative_to(ROOT).as_posix()

            posts.append({
                "href": f"/{prefix}{f.name}",
                "url": f"{BASE}/{prefix}{f.name}",
                "title": title,
                "excerpt": trim(meta(page, "description") or meta(page, "og:description")),
                "pub": pub, "mod": mod, "image": og or None,
                "date_iso": pub[:10],
                "date_display": fmt_date(pub, lang, langs),
                "read": c["min_read"].format(n=read_minutes(page)),
                "cat": cat, "cat_label": cd["label"][lang], "emoji": cd["emoji"],
                "color": cd["color"], "bg": cd["bg"], "thumb": thumb,
            })

        posts.sort(key=lambda p: (p["pub"][:10], p["pub"], p["title"]), reverse=True)

        sections = []
        for cd in cfg["categories"]:
            items = [p for p in posts if p["cat"] == cd["key"]]
            if items:
                sections.append({"key": cd["key"], "id": f"cat-{cd['key']}", "emoji": cd["emoji"],
                                 "color": cd["color"], "bg": cd["bg"], "label": cd["label"][lang],
                                 "desc": cd["desc"][lang], "posts": items})

        updated_iso = max((p["mod"] or p["pub"])[:10] for p in posts)

        blog_ld = {
            "@context": "https://schema.org",
            "@type": "Blog",
            "@id": f"{url}#blog",
            "url": url,
            "name": c["schema_name"],
            "description": c["description"],
            "inLanguage": bcp47,
            "publisher": {
                "@type": "Organization",
                "@id": f"{BASE}/#organization",
                "name": "Suu",
                "url": BASE,
                "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/og-image.png"},
            },
            "blogPost": [],
        }
        for p in posts:
            bp = {"@type": "BlogPosting", "headline": p["title"], "url": p["url"],
                  "datePublished": p["pub"]}
            if p["mod"]:
                bp["dateModified"] = p["mod"]
            bp["inLanguage"] = bcp47
            if p["image"]:
                bp["image"] = p["image"]
            blog_ld["blogPost"].append(bp)

        home = row["home_href"]
        crumbs_ld = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": c["breadcrumb_home"],
                 "item": BASE + (home if home.startswith("/") else "/" + home)},
                {"@type": "ListItem", "position": 2, "name": BLOG_CRUMB.get(lang, "Blog"),
                 "item": url},
            ],
        }

        def ld(obj: dict) -> str:
            return json.dumps(obj, ensure_ascii=False, indent=2).replace("</", "<\\/")

        llms = "/llms.txt" if lang == "tr" else f"/llms-{lang}.txt"
        out = template.render(
            marker=MARKER, lang=lang, dir=row.get("dir", "ltr"), locale=row["locale"],
            url=url, home=home, c=c, feed=row["feed"], feed_title=row["feed_title"],
            llms=llms, llms_full=llms.replace("/llms", "/llms-full"),
            total=len(posts), posts_word=plural(lang, len(posts), c["posts"]),
            cats_word=plural(lang, len(sections), c["cats"]),
            updated_iso=updated_iso, updated_display=fmt_date(updated_iso, lang, langs),
            sections=sections, latest=posts[:3],
            blog_ld=ld(blog_ld), crumbs_ld=ld(crumbs_ld),
            results_js=json.dumps(c["results"], ensure_ascii=False),
        )

        path = ROOT / index_file
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old:
            m = RE_HREFLANG.search(old)
            if m:  # inject-hreflang.py'nin bloğunu koru; yoksa her build onu düşürür
                canon = f'    <link rel="canonical" href="{url}">\n'
                out = out.replace(canon, canon + m.group(0).lstrip("\n") + "\n", 1)

        status = "yeni" if old is None else ("güncel" if old == out else "değişecek")
        print(f"  {index_file:<14} {len(posts):3d} yazı · {len(sections)} kategori · "
              f"son güncelleme {updated_iso}  {status}")
        if old != out:
            changed += 1
            if apply:
                path.write_text(out, encoding="utf-8")

    if thumbs_todo:
        print(f"\n  küçük resim: {len(thumbs_todo)} WebP {'üretiliyor' if apply else 'üretilecek'}")
        if apply:
            for src, dst in thumbs_todo.items():
                make_thumb(src, dst)

    if warnings:
        print("\nUyarılar:")
        for w in warnings:
            print(f"  ⚠ {w}")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{changed} indeks değişti — {mode}")
    if not apply and (changed or thumbs_todo):
        print("Uygulamak için: python3 scripts/build-blog-index.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
