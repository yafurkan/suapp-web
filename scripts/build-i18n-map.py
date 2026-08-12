#!/usr/bin/env python3
"""
Suu — Dil haritası üreticisi

content/page-registry.json  →  i18n-map.json  (site kökü, lang-switcher.js okur)

Neden: eskiden lang-switcher.js içinde elle yazılmış bir PAGE_MAP vardı.
Her sayfa ailesi 4 kez (her dilin dosya adı için bir kez) tekrar giriliyordu;
42 TR blog yazısının sadece 28'inin haritası vardı, kalanında dil butonları
hiçbir şey yapmıyordu. 7 dilde bu yapı sürdürülemezdi.

Artık kayıt defterinde aile başına TEK satır var; bu script her dosya adı için
ters indeksi üretiyor. Aynı kaynak hreflang ve sitemap için de kullanılabilir.

Çıktı biçimi:
    {
      "_langs": ["tr", "en", ...],
      "_shared": ["gizlilik-politikasi.html", ...],
      "pages": {
        "<dosya adı>": { "tr": "/...", "en": "/...", ... }
      }
    }

Kullanım:
    python3 scripts/build-i18n-map.py            # önizleme
    python3 scripts/build-i18n-map.py --apply
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "content" / "page-registry.json"
OUTPUT = ROOT / "i18n-map.json"
SWITCHER_TEMPLATE = ROOT / "content" / "lang-switcher.template.js"
SWITCHER_OUTPUT = ROOT / "lang-switcher.js"


def blog_url(lang: str, slug: str) -> str:
    return f"/blog/{slug}.html" if lang == "tr" else f"/blog/{lang}/{slug}.html"


def root_url(path: str) -> str:
    return path if path.startswith("/") else f"/{path}"


def basename(url: str) -> str:
    """URL → dosya adı. '/' ana sayfayı temsil eder."""
    name = url.rstrip("/").rsplit("/", 1)[-1]
    return name or "index.html"


def build(registry: dict) -> dict:
    langs: list[str] = registry["_languages"]
    pages: dict[str, dict[str, str]] = {}
    collisions: list[str] = []

    def add_family(variants: dict[str, str]) -> None:
        # Aynı dosya adı birden çok ailede geçerse (ör. suu-vs-yazio her dilde
        # aynı slug) tek girdi yeterli — çakışmayı sessizce birleştir.
        for url in variants.values():
            key = basename(url)
            if key in pages and pages[key] != variants:
                collisions.append(key)
            pages[key] = variants

    for family in registry["root"].values():
        add_family({lang: root_url(p) for lang, p in family.items()})

    for cluster in registry["blog"].values():
        add_family({lang: blog_url(lang, slug) for lang, slug in cluster.items()})

    if collisions:
        print(f"UYARI: {len(set(collisions))} dosya adı birden fazla ailede geçiyor:", file=sys.stderr)
        for c in sorted(set(collisions)):
            print(f"  {c}", file=sys.stderr)

    return {
        "_generated_by": "scripts/build-i18n-map.py",
        "_source": "content/page-registry.json",
        "_langs": langs,
        "_default": registry["_default"],
        "_shared": registry["shared"],
        "pages": dict(sorted(pages.items())),
    }


def main() -> int:
    apply = "--apply" in sys.argv

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    data = build(registry)
    out = json.dumps(data, ensure_ascii=False, indent=1) + "\n"

    old = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
    changed = old != out

    # Kapsam raporu
    per_lang: dict[str, int] = {l: 0 for l in data["_langs"]}
    for variants in data["pages"].values():
        for lang in variants:
            per_lang[lang] += 1

    print(f"{len(data['pages'])} dosya adı haritalandı")
    print("  dil başına giriş:", ", ".join(f"{l}={n}" for l, n in per_lang.items()))
    print(f"  paylaşılan (tek URL) sayfa: {len(data['_shared'])}")

    # Dil seçici — harita dosyaya gömülür, ek ağ isteği olmaz
    template = SWITCHER_TEMPLATE.read_text(encoding="utf-8")
    if "__I18N_MAP__" not in template:
        print("HATA: şablonda __I18N_MAP__ yer tutucusu yok.", file=sys.stderr)
        return 2
    embedded = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    switcher = template.replace("__I18N_MAP__", embedded)

    old_switcher = SWITCHER_OUTPUT.read_text(encoding="utf-8") if SWITCHER_OUTPUT.exists() else ""
    switcher_changed = old_switcher != switcher

    if apply:
        OUTPUT.write_text(out, encoding="utf-8")
        SWITCHER_OUTPUT.write_text(switcher, encoding="utf-8")
        print(f"\n{OUTPUT.relative_to(ROOT)} yazıldı ({len(out) // 1024} KB)")
        print(f"{SWITCHER_OUTPUT.relative_to(ROOT)} yazıldı ({len(switcher) // 1024} KB, harita gömülü)")
    else:
        print(f"\nÖNİZLEME — harita {'değişti' if changed else 'aynı'}, "
              f"switcher {'değişti' if switcher_changed else 'aynı'}")
        if changed or switcher_changed:
            print("Uygulamak için: python3 scripts/build-i18n-map.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
