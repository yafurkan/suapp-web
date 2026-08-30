#!/usr/bin/env python3
"""
Suu — Özel gün kutlama katmanını tüm sayfalara enjekte et

Tek satırlık <script src="/assets/js/special-days.js" defer> etiketini
analytics.js satırının hemen ardına koyar. Script'in kendisi hangi dilde,
hangi tarihte çalışacağına karar verir; sayfa tarafında koşul yoktur —
yılın 363 günü hiçbir istek atmaz, CSS bile yüklenmez.

Neden ayrı bir enjeksiyon: site 220+ statik HTML dosyası, ortak bir kabuk
şablonu yok. analytics.js zaten aynı yolla dağıtılmıştı, bu da aynı yerden
gider ki iki katman hep birlikte dursun.

Kullanım:
    python3 scripts/inject-special-days.py            # önizleme
    python3 scripts/inject-special-days.py --apply
    python3 scripts/inject-special-days.py --remove --apply   # geri al
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "scripts"}
# admin.html yönetim arayüzü, og-image-template render şablonu, yandex doğrulama
# dosyası, x9f4c2e7b.html hediye kod paneli — hepsi iç kullanım, kutlama görmez.
SKIP_FILES = {"admin.html", "og-image-template.html", "yandex_d8f56999642a8d54.html",
              "x9f4c2e7b.html"}

SNIPPET = '    <script src="/assets/js/special-days.js" defer></script>\n'

ANALYTICS_LINE = re.compile(r'^([ \t]*)<script src="/assets/js/analytics\.js" defer></script>[ \t]*\n',
                            re.MULTILINE)
ALREADY = re.compile(r'assets/js/special-days\.js')
# Geri alma: etiketi ve varsa önündeki girintiyi/ardındaki satır sonunu birlikte al
REMOVE_LINE = re.compile(r'[ \t]*<script src="/assets/js/special-days\.js"[^>]*></script>[ \t]*\n?')


def iter_html() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if path.name in SKIP_FILES:
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    apply = "--apply" in sys.argv
    remove = "--remove" in sys.argv

    stats = {"injected": 0, "removed": 0, "skipped": 0, "nohead": 0}
    changed: list[tuple[Path, str]] = []

    for path in iter_html():
        try:
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        text = original

        if remove:
            text, n = REMOVE_LINE.subn("", text)
            if n:
                stats["removed"] += n
                changed.append((path, f"kaldırıldı ×{n}"))
        elif ALREADY.search(text):
            stats["skipped"] += 1
        else:
            # 1. tercih: analytics.js satırının hemen altı (iki katman yan yana dursun)
            m = ANALYTICS_LINE.search(text)
            if m:
                text = text[:m.end()] + m.group(1) + SNIPPET.lstrip() + text[m.end():]
                stats["injected"] += 1
                changed.append((path, "analytics.js altına eklendi"))
            elif "</head>" in text:
                text = text.replace("</head>", SNIPPET + "</head>", 1)
                stats["injected"] += 1
                changed.append((path, "</head> öncesine eklendi"))
            else:
                stats["nohead"] += 1
                changed.append((path, "UYARI: </head> yok, atlandı"))

        if text != original and apply:
            path.write_text(text, encoding="utf-8")

    for path, action in changed:
        print(f"  {path.relative_to(ROOT)}  —  {action}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(
        f"\n{len(changed)} dosya değişti — {mode}\n"
        f"  eklendi     : {stats['injected']}\n"
        f"  kaldırıldı  : {stats['removed']}\n"
        f"  zaten vardı : {stats['skipped']}\n"
        f"  </head> yok : {stats['nohead']}"
    )
    if not apply and changed:
        bayrak = "--remove --apply" if remove else "--apply"
        print(f"\nUygulamak için: python3 scripts/inject-special-days.py {bayrak}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
