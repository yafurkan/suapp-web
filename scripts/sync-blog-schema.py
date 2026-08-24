#!/usr/bin/env python3
"""
Suu — blog indeksinin Blog.blogPost şemasını yazı klasörüyle eşitle

sync-blog-index.py GÖRÜNÜR kartları eşitler; bu script aynı işi JSON-LD
tarafında yapar. İkisi ayrı çünkü kart eklenmiş ama şemaya girmemiş yazılar
birikmişti: blog-en.html'in Blog.blogPost dizisi 48 yazının 29'unu taşıyordu
ve eksik 19'un tamamı kalori + fitness yazılarıydı — yani tam olarak AI
aramalarında görünmeyen iki kategori.

Bir yazı görünür kartta olup şemada olmayınca, sayfayı okuyan getirici onu
"blogun bir parçası" olarak değil, tekil bir sayfa olarak görür; koleksiyonun
otoritesinden pay almaz.

Alan değerleri yazının KENDİ meta verisinden okunur (uydurulmaz):
headline → <title> (site son eki atılır), datePublished/dateModified →
Article JSON-LD, image → og:image.

Kullanım:
    python3 scripts/sync-blog-schema.py            # önizleme
    python3 scripts/sync-blog-schema.py --apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _langs import blog_langs

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
LANGS = blog_langs(with_bcp47=True)

RE_LD = re.compile(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', re.S)
RE_TITLE = re.compile(r"<title>(.*?)</title>", re.S)
RE_OG_IMAGE = re.compile(r'<meta\s+property="og:image"\s+content="([^"]+)"')


def unescape(s: str) -> str:
    for a, b in (("&amp;", "&"), ("&#x27;", "'"), ("&#39;", "'"),
                 ("&quot;", '"'), ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " ")):
        s = s.replace(a, b)
    return s.strip()


def article_meta(path: Path) -> dict | None:
    """Yazının kendi meta verisinden BlogPosting alanlarını çıkar."""
    t = path.read_text(encoding="utf-8")

    m = RE_TITLE.search(t)
    if not m:
        return None
    headline = unescape(m.group(1))
    # "… | Suu" / "… — Suu" gibi site son eklerini at
    headline = re.sub(r"\s*[|·—–-]\s*Suu(\s+Blog)?\s*$", "", headline).strip()

    published = modified = None
    for lm in RE_LD.finditer(t):
        try:
            d = json.loads(lm.group(1))
        except json.JSONDecodeError:
            continue
        for node in (d.get("@graph", []) if isinstance(d, dict) else []) + ([d] if isinstance(d, dict) else []):
            if not isinstance(node, dict):
                continue
            ty = node.get("@type")
            types = ty if isinstance(ty, list) else [ty]
            if "Article" in types or "BlogPosting" in types:
                published = published or node.get("datePublished")
                modified = modified or node.get("dateModified")
    if not published:
        return None

    img = RE_OG_IMAGE.search(t)
    return {
        "headline": headline,
        "datePublished": published,
        "dateModified": modified,
        "image": img.group(1) if img else None,
    }


def build_post(url: str, meta: dict, in_lang: str) -> dict:
    post = {
        "@type": "BlogPosting",
        "headline": meta["headline"],
        "url": url,
        "datePublished": meta["datePublished"],
    }
    if meta.get("dateModified"):
        post["dateModified"] = meta["dateModified"]
    post["inLanguage"] = in_lang
    if meta.get("image"):
        post["image"] = meta["image"]
    return post


def main() -> int:
    apply = "--apply" in sys.argv
    total_added = 0

    for lang, (index_file, folder, prefix, in_lang) in LANGS.items():
        index_path = ROOT / index_file
        if not index_path.exists():
            print(f"  {index_file:<14} — yok, atlandı")
            continue

        text = index_path.read_text(encoding="utf-8")

        target = None
        for m in RE_LD.finditer(text):
            try:
                d = json.loads(m.group(1))
            except json.JSONDecodeError:
                continue
            if isinstance(d, dict) and d.get("@type") == "Blog":
                target = (m, d)
                break
        if not target:
            print(f"  {index_file:<14} — Blog şeması bulunamadı, atlandı")
            continue

        match, blog = target
        existing = {p.get("url") for p in blog.get("blogPost", [])}

        added = []
        for f in sorted((ROOT / folder).glob("*.html")):
            url = f"{BASE}/{prefix}{f.name}"
            if url in existing:
                continue
            meta = article_meta(f)
            if not meta:
                print(f"      ! {f.name} — meta okunamadı, atlandı")
                continue
            added.append(build_post(url, meta, in_lang))

        if not added:
            print(f"  {index_file:<14} ✓ şema güncel ({len(existing)} yazı)")
            continue

        # En yeni yazı en üstte dursun: tarihe göre azalan sırala
        posts = blog.get("blogPost", []) + added
        posts.sort(key=lambda p: p.get("datePublished", ""), reverse=True)
        blog["blogPost"] = posts

        new_json = json.dumps(blog, ensure_ascii=False, indent=2)
        new_block = f'<script type="application/ld+json">\n{new_json}\n    </script>'
        text = text[: match.start()] + new_block + text[match.end():]

        print(f"  {index_file:<14} + {len(added)} yazı (toplam {len(posts)})")
        for p in added:
            print(f"      + {p['url'].rsplit('/', 1)[-1]}")
        total_added += len(added)

        if apply:
            index_path.write_text(text, encoding="utf-8")

    print()
    if total_added == 0:
        print("Tüm blog şemaları güncel.")
    elif apply:
        print(f"{total_added} yazı şemaya eklendi — yazıldı")
    else:
        print(f"{total_added} yazı eklenecek — ÖNİZLEME (yazılmadı)")
        print("Uygulamak için: python3 scripts/sync-blog-schema.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
