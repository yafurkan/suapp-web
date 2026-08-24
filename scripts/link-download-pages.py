#!/usr/bin/env python3
"""
Suu — Blog alt gezinmesine indirme sayfası bağlantısı ekler

İndirme sayfaları (indir.html, download*.html) 247 sayfalık iç bağlantı
grafiğinin dibindeydi: her biri 1 bağlantı alıyordu, oysa anasayfa 173
(SEO denetimi, 2026-08-20). Sebep yapısal — sitedeki 421 indirme CTA'sı
/app device-redirect'ine gidiyor, o da robots.txt'de Disallow.

/app'e DOKUNULMAZ: tek dokunuşla doğru mağazaya götürmek dönüşüm için
doğru olan; robots'ta engellenmesi de doğru, çünkü içerik değil yönlendirici.
Eksik olan, indekslenebilir indirme sayfasına giden iç bağlantıydı.

Bu script blog yazılarının .footer-nav bloğuna sayfanın DİLİNE uygun
indirme sayfası bağlantısı ekler. Mağaza butonları ve CTA kutuları
değiştirilmez.

Kullanım:
    python3 scripts/link-download-pages.py            # önizleme
    python3 scripts/link-download-pages.py --apply
"""
from __future__ import annotations

import re
import sys
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"

# dil → (indekslenebilir indirme sayfası, bağlantı metni)
TARGET = {
    "tr": ("/indir.html", "Ücretsiz İndir"),
    "en": ("/download.html", "Download Free"),
    "ru": ("/download-ru.html", "Скачать бесплатно"),
    "ar": ("/download-ar.html", "تحميل مجاني"),
}

RE_LANG = re.compile(r'<html[^>]*\slang="([^"]+)"', re.I)

# Sitede üç ayrı blog alt bilgi şablonu var; üçü de ayrı ele alınır.
RE_FOOTER_NAV = re.compile(r'(<div class="footer-nav">.*?)(\s*</div>)', re.S)
RE_FOOTER_BOTTOM = re.compile(
    r'(<div class="footer__bottom"[^>]*>.*?)(\s*</div>)', re.S)
RE_FOOTER_PLAIN = re.compile(
    r'(<footer>\s*<p>.*?<a href="/">[^<]*</a>)(\s*&nbsp;)', re.S)


def insert(text: str, href: str, label: str) -> str | None:
    """Bulunan ilk alt bilgi şablonuna bağlantıyı ekler."""
    m = RE_FOOTER_NAV.search(text)
    if m:
        link = f'\n        <a href="{href}"><i class="fas fa-download"></i> {label}</a>'
        return text[:m.end(1)] + link + text[m.start(2):]

    m = RE_FOOTER_BOTTOM.search(text)
    if m:
        link = f'\n            <p class="small mb-0"><a href="{href}">{label}</a></p>'
        return text[:m.end(1)] + link + text[m.start(2):]

    m = RE_FOOTER_PLAIN.search(text)
    if m:
        link = f'\n        <a href="{href}">{label}</a>'
        return text[:m.end(1)] + " &nbsp;" + link + text[m.start(2):]

    return None


def main() -> int:
    apply = "--apply" in sys.argv
    added, skipped = collections.Counter(), collections.Counter()

    for path in sorted(BLOG.rglob("*.html")):
        text = path.read_text(encoding="utf-8", errors="replace")
        lang_m = RE_LANG.search(text)
        lang = (lang_m.group(1).split("-")[0].lower() if lang_m else "")
        if lang not in TARGET:
            skipped["dil eşleşmedi"] += 1
            continue
        href, label = TARGET[lang]
        if f'href="{href}"' in text:
            skipped["zaten var"] += 1
            continue
        new_text = insert(text, href, label)
        if new_text is None:
            skipped["alt bilgi şablonu tanınmadı"] += 1
            continue
        added[lang] += 1
        if apply:
            path.write_text(new_text, encoding="utf-8")

    total = sum(added.values())
    print(f"{total} blog yazısına indirme bağlantısı eklenecek")
    for lang, n in sorted(added.items()):
        print(f"  {lang}: {n:3}  → {TARGET[lang][0]}")
    if skipped:
        print("\natlanan:")
        for k, n in skipped.items():
            print(f"  {k}: {n}")
    print("\nuygulandı" if apply else "\nÖNİZLEME — uygulamak için: --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
