#!/usr/bin/env python3
"""
Suu — Hreflang kümesi enjektörü

Kaynak: content/page-registry.json  (dil seçici ve sitemap ile AYNI kaynak)

Eskiden bu dosyanın içinde ayrı bir CLUSTERS tablosu vardı; lang-switcher.js'in
PAGE_MAP'i ve rebuild-sitemap.py bambaşka listeler kullanıyordu. Üç kaynak
zamanla birbirinden ayrıldı. Artık tek kayıt defteri var — sapma imkânsız.

Yaptığı: her sayfanın <head>'indeki mevcut hreflang etiketlerini silip
kayıt defterine göre yeniden yazar. x-default varsayılan dile (tr) işaret eder;
o dilde karşılığı yoksa kümedeki ilk dile düşer.

Kullanım:
    python3 scripts/inject-hreflang.py            # önizleme
    python3 scripts/inject-hreflang.py --apply
    python3 scripts/inject-hreflang.py --apply --only blog
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "content" / "page-registry.json"
BASE = "https://suuapp.com"

RE_HREFLANG = re.compile(
    r'\s*<link\s+rel=["\']alternate["\']\s+hreflang=["\'][^"\']+["\']\s+href=["\'][^"\']+["\'][ \t]*/?>[ \t]*\n?',
    re.IGNORECASE,
)
RE_HREFLANG_FLIP = re.compile(
    r'\s*<link\s+hreflang=["\'][^"\']+["\']\s+rel=["\']alternate["\']\s+href=["\'][^"\']+["\'][ \t]*/?>[ \t]*\n?',
    re.IGNORECASE,
)
RE_CANONICAL = re.compile(
    r'(<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']+["\']\s*/?>)',
    re.IGNORECASE,
)
# Kendi bıraktığımız başlık yorumu — her çalıştırmada birikmesin diye önce silinir
RE_OWN_COMMENT = re.compile(
    r'[ \t]*<!--\s*Hreflang(?: cluster)?[^>]*-->[ \t]*\n?',
    re.IGNORECASE,
)


def abs_url(path: str) -> str:
    return f"{BASE}/" if path == "/" else f"{BASE}/{path.lstrip('/')}"


def local_path(url_path: str) -> Path:
    return ROOT / ("index.html" if url_path == "/" else url_path.lstrip("/"))


def render_block(pairs: list[tuple[str, str]]) -> str:
    lines = ["", "    <!-- Hreflang cluster (auto-injected) -->"]
    for lang, href in pairs:
        lines.append(f'    <link rel="alternate" hreflang="{lang}" href="{href}">')
    return "\n".join(lines) + "\n"


def inject(html: str, pairs: list[tuple[str, str]]) -> tuple[str, bool]:
    new = RE_HREFLANG.sub("\n", html)
    new = RE_HREFLANG_FLIP.sub("\n", new)
    new = RE_OWN_COMMENT.sub("", new)
    new = re.sub(r"\n{3,}", "\n\n", new)
    block = render_block(pairs)

    if RE_CANONICAL.search(new):
        new = RE_CANONICAL.sub(lambda m: m.group(1) + block, new, count=1)
    elif "</head>" in new:
        new = new.replace("</head>", block + "</head>", 1)
    else:
        return html, False

    return new, new != html


def family_urls(variants: dict[str, str], kind: str, default_lang: str) -> dict[str, str]:
    """Aile → { lang: mutlak URL }"""
    out: dict[str, str] = {}
    for lang, value in variants.items():
        if kind == "blog":
            rel = f"blog/{value}.html" if lang == default_lang else f"blog/{lang}/{value}.html"
        else:
            rel = value
        out[lang] = abs_url(rel)
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    default_lang = reg["_default"]
    order = reg["_languages"]

    edited: list[str] = []
    missing: list[str] = []
    unchanged = 0

    for kind in ("root", "blog"):
        if only and only != kind:
            continue
        for family, variants in reg[kind].items():
            urls = family_urls(variants, kind, default_lang)

            pairs = [(lang, urls[lang]) for lang in order if lang in urls]
            if len(pairs) < 2:
                continue                      # tek dilli aile — hreflang gereksiz
            xdefault = urls.get(default_lang) or pairs[0][1]
            pairs.append(("x-default", xdefault))

            for lang, url in urls.items():
                rel = "/" if url == f"{BASE}/" else url[len(BASE) + 1:]
                path = local_path(rel)
                if not path.exists():
                    missing.append(f"{kind}/{family} [{lang}] → {rel}")
                    continue
                html = path.read_text(encoding="utf-8")
                new, changed = inject(html, pairs)
                if changed:
                    edited.append(str(path.relative_to(ROOT)))
                    if apply:
                        path.write_text(new, encoding="utf-8")
                else:
                    unchanged += 1

    print(f"{len(edited)} dosya güncellenecek, {unchanged} zaten güncel")
    if missing:
        print(f"\n{len(missing)} kayıtlı sayfa diskte yok (kayıt defterini gözden geçirin):")
        for m in missing[:20]:
            print(f"  {m}")
        if len(missing) > 20:
            print(f"  … ve {len(missing) - 20} tane daha")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{mode}")
    if not apply and edited:
        print("Uygulamak için: python3 scripts/inject-hreflang.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
