#!/usr/bin/env python3
"""
Suu — Uzun meta description'ları cümle sınırında kırpar

Google masaüstünde ~160 karakter gösteriyor; daha uzunu kesiliyor ve kesilen
kısım genellikle farklılaştırıcı bilgi oluyordu (SEO denetimi, 2026-08-20 —
247 sayfanın 56'sı 180 karakteri aşıyordu).

Yaklaşım: yeniden YAZMAZ, KIRPAR. Sınırın altına sığan son tam cümlede keser,
böylece yazarın kendi cümleleri korunur ve yarım cümle kalmaz. İlk cümlesi
tek başına sınırı aşan sayfalara dokunmaz — orada insan kararı gerekiyor,
listeye yazılır.

Kullanım:
    python3 scripts/trim-descriptions.py            # önizleme
    python3 scripts/trim-descriptions.py --apply
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".qodo", ".github", "worker"}
LIMIT = 160        # hedef: Google'ın masaüstünde gösterdiği uzunluk
TRIGGER = 180      # bunun altındakiler zaten kabul edilebilir, dokunulmaz
FLOOR = 110        # bundan kısa bir sonuç iyileştirme değil, kayıp olur

# Latin, Arapça (؟ ۔) ve Devanagari (।) cümle sonları
SENT_END = re.compile(r"(?<=[.!?۔।؟])\s+")
RE_DESC = re.compile(r'(<meta name="description" content=")(.*?)("\s*/?>)', re.S)


def trim(text: str) -> str | None:
    """Sınıra sığan son tam cümleye kadar kırp; mümkün değilse None."""
    if len(text) <= LIMIT:
        return None
    parts = SENT_END.split(text)
    out = ""
    for p in parts:
        cand = (out + " " + p).strip() if out else p
        if len(cand) > LIMIT:
            break
        out = cand
    if not out or len(out) == len(text) or len(out) < FLOOR:
        return None
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    trimmed, skipped = [], []

    for path in sorted(ROOT.rglob("*.html")):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        m = RE_DESC.search(text)
        if not m:
            continue
        current = html.unescape(re.sub(r"\s+", " ", m.group(2))).strip()
        if len(current) <= TRIGGER:
            continue
        new = trim(current)
        rel = str(path.relative_to(ROOT))
        if new is None:
            skipped.append((rel, len(current)))
            continue
        trimmed.append((rel, len(current), len(new)))
        if apply:
            text = text[:m.start(2)] + html.escape(new, quote=True) + text[m.end(2):]
            path.write_text(text, encoding="utf-8")

    print(f"{len(trimmed)} açıklama kırpılacak")
    for rel, a, b in trimmed[:12]:
        print(f"  {a:4} → {b:3}  {rel}")
    if len(trimmed) > 12:
        print(f"  … ve {len(trimmed) - 12} tane daha")
    if skipped:
        print(f"\n{len(skipped)} sayfa atlandı (cümle sınırında {FLOOR}-{LIMIT} aralığına inilemiyor):")
        for rel, n in skipped:
            print(f"  {n:4}  {rel}")
        print("  → bunlar elle yeniden yazılmalı; kırpmak anlamı bozuyor")
    print("\nuygulandı" if apply else "\nÖNİZLEME — uygulamak için: --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
