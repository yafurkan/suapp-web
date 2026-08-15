#!/usr/bin/env python3
"""
Suu — yazar satırlarını yazar sayfasına bağla

Sitede 119 yazıda yazar adı yazıyor ama hiçbiri tıklanabilir değil. Yazar
sayfası (yazarlar/furkan-mert.html) 132 sayfadan JSON-LD ile referans
alıyor, gövdeden ise hiç. Sonuç: sayfa iç bağlantı grafiğinde YETİM.

Bu ikisi farklı sinyaldir. Şemadaki "author.url" makine tarafı; gövdedeki
rel="author" bağlantısı hem tarayıcının yazar sayfasını bulmasını sağlar
hem de E-E-A-T'nin (deneyim/uzmanlık/otorite/güven) doğrulanabilir olmasını.
Yapay zekâ sistemleri "bunu kim yazmış, güvenilir mi" sorusunu yanıtlarken
izlenebilir bir yazar sayfası arar.

Kullanım:
    python3 scripts/link-author-bylines.py           # önizleme
    python3 scripts/link-author-bylines.py --apply
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "content", "scripts"}

AUTHOR_PAGE = "/yazarlar/furkan-mert.html"

# Ekip imzaları dilin kendi ekip/hakkımızda sayfasına gider
TEAM_PAGE = {
    "tr": "/ekip.html",
    "en": "/about.html",
    "ar": "/hakkimizda-ar.html",
    "ru": "/hakkimizda-ru.html",
}
TEAM_NAMES = {
    "Suu Ekibi": "tr", "Suu Team": "en", "فريق Suu": "ar", "Команда Suu": "ru",
}

FOUNDER = "Furkan Mert Fındıklı"


def lang_of(page: str) -> str:
    m = re.search(r'<html[^>]*\blang="([a-z]{2})', page)
    return m.group(1) if m else "tr"


def link_bylines(page: str) -> tuple[str, int]:
    n = 0

    # 1) <span><i class="fas fa-pen"></i> Furkan Mert Fındıklı</span>
    pattern = re.compile(
        r'(<span><i class="fas fa-pen"></i>\s*)(' + re.escape(FOUNDER) + r')(\s*</span>)')

    def repl_founder(m: re.Match) -> str:
        nonlocal n
        n += 1
        return f'{m.group(1)}<a href="{AUTHOR_PAGE}" rel="author">{m.group(2)}</a>{m.group(3)}'

    page = pattern.sub(repl_founder, page)

    # 2) Ekip imzası → ekip/hakkımızda sayfası
    lang = lang_of(page)
    for name, name_lang in TEAM_NAMES.items():
        target = TEAM_PAGE.get(lang) or TEAM_PAGE.get(name_lang)
        if not target:
            continue
        pat = re.compile(
            r'(<span><i class="fas fa-pen"></i>\s*)(' + re.escape(name) + r')(\s*</span>)')

        def repl_team(m: re.Match) -> str:
            nonlocal n
            n += 1
            return f'{m.group(1)}<a href="{target}" rel="author">{m.group(2)}</a>{m.group(3)}'

        page = pat.sub(repl_team, page)

    # 3) "· By Furkan Mert Fındıklı" biçimli satır içi imza
    pat = re.compile(r'(·\s*(?:By\s+)?)(' + re.escape(FOUNDER) + r')(?!\s*</a>)(\s*·)')

    def repl_inline(m: re.Match) -> str:
        nonlocal n
        n += 1
        return f'{m.group(1)}<a href="{AUTHOR_PAGE}" rel="author">{m.group(2)}</a>{m.group(3)}'

    page = pat.sub(repl_inline, page)
    return page, n


def main() -> int:
    apply = "--apply" in sys.argv
    touched, total = 0, 0

    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        try:
            page = original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        # zaten bağlanmışsa dokunma
        if 'rel="author"' in page:
            continue

        page, n = link_bylines(page)
        if n and page != original:
            touched += 1
            total += n
            if apply:
                path.write_text(page, encoding="utf-8")

    mode = "UYGULANDI" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"{touched} sayfada {total} yazar satırı bağlandı — {mode}")
    if not apply and total:
        print("Uygulamak için: python3 scripts/link-author-bylines.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
