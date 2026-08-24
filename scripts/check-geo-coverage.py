#!/usr/bin/env python3
"""
Suu — dil başına GEO kapsama denetimi

Bir dili açmak tek bir iş değil: ana sayfa, blog indeksi, besleme, llms
dosyaları, karşılaştırma merkezi, kayıt defteri kümeleri ve üç para
sorgusunun sayfaları. Bunlardan biri atlanınca hiçbir script hata vermiyor —
sayfa yayında görünür ama kümeden veya keşiften düşer.

Bu script her YAYIN dili için o listeyi tek tek doğrular ve eksikleri
sayar. Yayında olmayan diller (content/languages.json → published: false)
yalnızca bilgi olarak listelenir.

Ayrıca kontrol edilenler:
    · yetim yazı        — blog indeksinde kartı olmayan dosya
    · kırık iç bağlantı — var olmayan .html'e işaret eden href
    · hreflang bütünlüğü — kayıt defterindeki küme ile sayfadaki etiketler

Kullanım:
    python3 scripts/check-geo-coverage.py
    python3 scripts/check-geo-coverage.py --lang uk
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from _langs import blog_langs, published, table

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "content" / "page-registry.json"

# Üç para sorgusu — GEO çalışmasının çekirdeği. Kayıt defterindeki küme
# anahtarları; bir dilin bu üçünden birinde sayfası yoksa o dil o sorgu
# ailesinde yapay zekâ cevabına aday değildir.
MONEY_CLUSTERS = {
    "su-takip-uygulamasi-neden-kullanmaliyim": "en iyi su takip uygulaması",
    "en-iyi-kalori-uygulamasi": "en iyi kalori uygulaması",
    "en-iyi-egzersiz-takip-uygulamasi": "en iyi egzersiz uygulaması",
}

RE_HREF = re.compile(r'href="(/?[A-Za-z0-9_./-]+\.html)"')
RE_HREFLANG = re.compile(r'<link rel="alternate" hreflang="([a-z-]+)"')


def rel_path(lang: str, slug: str, default: str) -> Path:
    return ROOT / (f"blog/{slug}.html" if lang == default else f"blog/{lang}/{slug}.html")


def main() -> int:
    only = None
    if "--lang" in sys.argv:
        only = sys.argv[sys.argv.index("--lang") + 1]

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    default = reg["_default"]
    langs = table()
    live = published()
    blogs = blog_langs()
    problems = 0

    print("Dil başına GEO kapsaması\n")
    header = f"{'dil':<5} {'ana':<4} {'blog':<5} {'besl':<5} {'llms':<5} {'hub':<4} {'su':<4} {'kal':<4} {'egz':<4} {'yazı':>5}"
    print(header)
    print("-" * len(header))

    for code, entry in langs.items():
        if only and code != only:
            continue
        is_live = code in live

        home_ok = code in reg["root"]["home"]
        blog_ok = code in blogs
        feed_ok = (ROOT / entry["feed"]).exists()
        llms_ok = ((ROOT / ("llms.txt" if code == default else f"llms-{code}.txt")).exists()
                   and (ROOT / ("llms-full.txt" if code == default
                                else f"llms-full-{code}.txt")).exists())
        hub_ok = code in reg["root"]["comparisons"]

        money = {}
        for cluster in MONEY_CLUSTERS:
            slug = reg["blog"].get(cluster, {}).get(code)
            money[cluster] = bool(slug) and rel_path(code, slug, default).exists()

        posts = len(list((ROOT / entry["blog_dir"]).glob("*.html"))) \
            if (ROOT / entry["blog_dir"]).is_dir() else 0

        def m(ok: bool) -> str:
            return "✓" if ok else ("✗" if is_live else "·")

        row = (f"{code:<5} {m(home_ok):<4} {m(blog_ok):<5} {m(feed_ok):<5} {m(llms_ok):<5} "
               f"{m(hub_ok):<4} " + " ".join(f"{m(money[c]):<3}" for c in MONEY_CLUSTERS)
               + f" {posts:>5}")
        print(row + ("" if is_live else "   (yayında değil)"))

        if is_live:
            problems += sum(1 for ok in (home_ok, blog_ok, feed_ok, llms_ok, hub_ok) if not ok)
            problems += sum(1 for ok in money.values() if not ok)

    # ── Yetim yazı: dosyası var ama indeksinde kartı yok ──────────────
    print("\nYetim yazılar (blog indeksinde kartı yok)")
    orphans = 0
    for code, (index_name, folder, _) in blogs.items():
        if only and code != only:
            continue
        index = (ROOT / index_name).read_text(encoding="utf-8")
        missing = [p.name for p in sorted((ROOT / folder).glob("*.html"))
                   if p.name not in index]
        if missing:
            orphans += len(missing)
            print(f"  {index_name}: {', '.join(missing[:5])}"
                  + (f" … +{len(missing)-5}" if len(missing) > 5 else ""))
    print("  yok" if not orphans else f"  TOPLAM {orphans}")
    problems += orphans

    # ── Kırık iç bağlantı ─────────────────────────────────────────────
    print("\nKırık iç bağlantılar")
    broken: dict[str, list[str]] = {}
    scan = [ROOT / n for n in reg["root"]["home"].values() if n != "/"]
    scan += [ROOT / n for n in reg["root"]["comparisons"].values()]
    scan += [ROOT / n for _, (n, _, _) in blogs.items()]
    for _, folder, _ in blogs.values():
        scan += sorted((ROOT / folder).glob("*.html"))
    for f in scan:
        if not f.exists():
            continue
        html = f.read_text(encoding="utf-8")
        for href in set(RE_HREF.findall(html)):
            target = (ROOT / href.lstrip("/")) if href.startswith("/") \
                else (f.parent / href)
            if not target.exists():
                broken.setdefault(href, []).append(f.name)
    for href, srcs in sorted(broken.items()):
        print(f"  {href}  ← {', '.join(sorted(set(srcs))[:3])}")
    print("  yok" if not broken else f"  TOPLAM {len(broken)}")
    problems += len(broken)

    # ── hreflang: kayıt defteri ile sayfa uyuşuyor mu ─────────────────
    print("\nhreflang bütünlüğü (kayıt defteri ↔ sayfa)")
    mismatched = 0
    for cluster, variants in list(reg["root"].items()) + list(reg["blog"].items()):
        if not isinstance(variants, dict):
            continue
        expected = set(variants) | {"x-default"}
        for code, slug in variants.items():
            page = (ROOT / "index.html") if slug == "/" else (
                ROOT / slug if cluster in reg["root"] else rel_path(code, slug, default))
            if not page.exists():
                continue
            found = set(RE_HREFLANG.findall(page.read_text(encoding="utf-8")))
            if found and found != expected:
                mismatched += 1
                if mismatched <= 5:
                    print(f"  {page.name}: beklenen {sorted(expected)} · bulunan {sorted(found)}")
    print("  sorun yok" if not mismatched else f"  TOPLAM {mismatched} "
          "(inject-hreflang.py --apply çalıştırın)")
    problems += mismatched

    print(f"\nToplam sorun: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
