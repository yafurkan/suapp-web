#!/usr/bin/env python3
"""
Suu — Üçüncü taraf kaynaklar için preconnect enjektörü

Sayfaların çoğu Google Fonts ve cdnjs'ten render'ı bloklayan CSS çekiyor ama
yalnızca 88'inde preconnect vardı (SEO denetimi, 2026-08-20). Preconnect
olmadan tarayıcı DNS + TCP + TLS el sıkışmasını CSS isteği sırasına kadar
başlatmıyor; bu her kaynak için ~2 gidiş-dönüş, LCP'ye doğrudan biniyor.

Ayrıca düzeltir: fonts.googleapis.com'a yanlış konmuş `crossorigin`.
Stil sayfası CORS ile çekilmediği için crossorigin'li preconnect AYRI bir
bağlantı açıyor ve gerçek istek onu kullanamıyor — yani preconnect boşa
gidiyor. crossorigin yalnızca font dosyalarını sunan fonts.gstatic.com'a ait.

Kullanım:
    python3 scripts/inject-preconnect.py            # önizleme
    python3 scripts/inject-preconnect.py --apply
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".qodo", ".github", "worker"}

GOOGLE_FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com">'
GSTATIC = '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
CDNJS = '<link rel="preconnect" href="https://cdnjs.cloudflare.com">'

RE_ANY_PRECONNECT = re.compile(
    r'[ \t]*<link[^>]+rel=["\']preconnect["\'][^>]*>[ \t]*\n?', re.I)
RE_FIRST_3P_CSS = re.compile(
    r'[ \t]*<link[^>]+href=["\']https://(?:fonts\.googleapis\.com|cdnjs\.cloudflare\.com)[^>]*>',
    re.I)


def process(text: str) -> tuple[str, bool]:
    head_end = text.find("</head>")
    if head_end == -1:
        return text, False
    head = text[:head_end]

    wants_fonts = "fonts.googleapis.com/css" in head
    wants_cdnjs = "cdnjs.cloudflare.com" in head
    if not (wants_fonts or wants_cdnjs):
        return text, False

    # Mevcut preconnect'leri sıfırla; doğru sırayla yeniden yazılacak.
    cleaned_head = RE_ANY_PRECONNECT.sub("", head)

    m = RE_FIRST_3P_CSS.search(cleaned_head)
    if not m:
        return text, False

    indent = re.match(r"[ \t]*", m.group(0)).group(0)
    lines = []
    if wants_fonts:
        lines += [GOOGLE_FONTS, GSTATIC]
    if wants_cdnjs:
        lines.append(CDNJS)
    block = "".join(f"{indent}{l}\n" for l in lines)

    new_head = cleaned_head[:m.start()] + block + cleaned_head[m.start():]
    new = new_head + text[head_end:]
    return new, new != text


def main() -> int:
    apply = "--apply" in sys.argv
    edited = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new, changed = process(text)
        if changed:
            edited.append(str(path.relative_to(ROOT)))
            if apply:
                path.write_text(new, encoding="utf-8")

    print(f"{len(edited)} sayfa güncellenecek")
    for e in edited[:8]:
        print(f"  {e}")
    if len(edited) > 8:
        print(f"  … ve {len(edited) - 8} tane daha")
    print("\nuygulandı" if apply else "\nÖNİZLEME — uygulamak için: --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
