#!/usr/bin/env python3
"""
Suu — Ölçüm katmanını tüm sayfalara enjekte et

Yaptıkları:
  1. Ölü GA gtag bloğunu siler (GA_MEASUREMENT_ID placeholder'ı)
  2. Sayfa içine kopyalanmış Clarity bloklarını siler
  3. Yerine tek satırlık <script src="/assets/js/analytics.js" defer> koyar

Neden: Clarity 221 sayfanın sadece 42'sindeydi (blogun tamamı ölçümsüzdü),
GA ise hiç veri toplamıyordu. Tek dosyaya taşıyınca ölçüm ID'si değişince
221 dosya değil bir dosya güncellenir.

Kullanım:
    python3 scripts/inject-analytics.py            # önizleme
    python3 scripts/inject-analytics.py --apply
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "scripts"}
# admin.html yönetim arayüzü, og-image-template render şablonu, yandex doğrulama dosyası
SKIP_FILES = {"admin.html", "og-image-template.html", "yandex_d8f56999642a8d54.html"}

SNIPPET = '    <script src="/assets/js/analytics.js" defer></script>\n'

# Ölü GA bloğu: yorum satırı (varsa) + gtag script'i + config script'i
GA_BLOCK = re.compile(
    r"[ \t]*(?:<!--[^>]*(?:Google Analytics|GA4)[^>]*-->\s*)?"
    r"[ \t]*<script[^>]*googletagmanager\.com/gtag/js[^>]*>\s*</script>\s*"
    r"(?:[ \t]*<script>\s*window\.dataLayer.*?</script>\s*)?",
    re.IGNORECASE | re.DOTALL,
)

# Sayfaya kopyalanmış Clarity bloğu
CLARITY_BLOCK = re.compile(
    r"[ \t]*(?:<!--[^>]*[Cc]larity[^>]*-->\s*)?"
    r"[ \t]*<script[^>]*>\s*\(function\(c,l,a,r,i,t,y\).*?</script>\s*",
    re.DOTALL,
)

ALREADY = re.compile(r'assets/js/analytics\.js')


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

    stats = {"ga_removed": 0, "clarity_removed": 0, "injected": 0, "skipped": 0}
    changed: list[tuple[Path, list[str]]] = []

    for path in iter_html():
        try:
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        text = original
        actions: list[str] = []

        text, n = GA_BLOCK.subn("", text)
        if n:
            stats["ga_removed"] += n
            actions.append(f"ölü GA ×{n}")

        text, n = CLARITY_BLOCK.subn("", text)
        if n:
            stats["clarity_removed"] += n
            actions.append(f"inline Clarity ×{n}")

        if ALREADY.search(text):
            stats["skipped"] += 1
        elif "</head>" in text:
            text = text.replace("</head>", SNIPPET + "</head>", 1)
            stats["injected"] += 1
            actions.append("analytics.js eklendi")
        else:
            actions.append("UYARI: </head> yok, atlandı")

        if text != original:
            changed.append((path, actions))
            if apply:
                path.write_text(text, encoding="utf-8")

    for path, actions in changed:
        print(f"  {path.relative_to(ROOT)}  —  {', '.join(actions)}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(
        f"\n{len(changed)} dosya değişti — {mode}\n"
        f"  ölü GA bloğu silindi : {stats['ga_removed']}\n"
        f"  inline Clarity silindi: {stats['clarity_removed']}\n"
        f"  analytics.js eklendi : {stats['injected']}\n"
        f"  zaten vardı          : {stats['skipped']}"
    )
    if not apply and changed:
        print("\nUygulamak için: python3 scripts/inject-analytics.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
