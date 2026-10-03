#!/usr/bin/env python3
"""
Suu — açık / koyu tema düğmesini tasarım sistemi sayfalarına enjekte et

Koyu tema assets/css/suu.css'te token'larla zaten var (sistem tercihine göre
açılır, <html data-theme="light|dark"> sistem tercihini ezer). Eksik olan,
ziyaretçinin bunu elle seçebilmesiydi. Her suu.css sayfasına iki satır girer:

  1. viewport meta'sının hemen altına, temayı İLK BOYAMADAN ÖNCE uygulayan
     tek satırlık satır içi script — yoksa koyu seçmiş ziyaretçi her sayfada
     bir an açık tema görür.
  2. lang-switcher.js'in hemen altına /assets/js/theme.js — düğmeyi dil
     seçicinin yanına yerleştirir ve seçimi localStorage'da saklar.

Yalnızca suu.css'i yükleyen sayfalar: eski blog yazıları (satır içi sabit
renkler) koyu temayı desteklemiyor, oraya düğme koymak boş bir buton olurdu.

Aynı iki satır dört şablonda da birebir durur — content/compare/_template.html.j2,
content/home/_template.html.j2, content/compare-hub.html.j2, content/glossary.html.j2 —
böylece yeniden üretilen sayfalar düğmeyi kaybetmez. Bu script elle yazılmış
sayfalar (press.html) ve henüz yeniden üretilmemiş çıktılar içindir; idempotenttir.

Kullanım:
    python3 scripts/inject-theme-toggle.py            # önizleme
    python3 scripts/inject-theme-toggle.py --apply
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "scripts", "content"}

# Şablonlardaki satırlarla BİREBİR aynı olmalı (bkz. docstring).
PREPAINT = ("<script>(function(){try{var t=localStorage.getItem('suu-theme');"
            "if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t)}"
            "catch(e){}})();</script>")
TAG = '<script src="/assets/js/theme.js?v=1" defer></script>'

USES_DS = re.compile(r'href="/assets/css/suu\.css')
VIEWPORT = re.compile(r'^([ \t]*)<meta name="viewport"[^>]*>[ \t]*\n', re.MULTILINE)
SWITCHER = re.compile(r'^([ \t]*)<script src="/lang-switcher\.js[^"]*" defer></script>[ \t]*\n',
                      re.MULTILINE)


def iter_html() -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        out.append(path)
    return out


def patch(text: str) -> tuple[str, list[str]]:
    notes = []
    if "localStorage.getItem('suu-theme')" not in text:
        m = VIEWPORT.search(text)
        if not m:
            notes.append("viewport meta yok — boyama öncesi script eklenemedi")
        else:
            line = f"{m.group(1)}{PREPAINT}\n"
            text = text[:m.end()] + line + text[m.end():]
    if "/assets/js/theme.js" not in text:
        m = SWITCHER.search(text)
        if not m:
            notes.append("lang-switcher.js yok — theme.js eklenemedi")
        else:
            line = f"{m.group(1)}{TAG}\n"
            text = text[:m.end()] + line + text[m.end():]
    return text, notes


def main() -> int:
    apply = "--apply" in sys.argv
    changed, skipped, problems = [], 0, []
    for path in iter_html():
        old = path.read_text(encoding="utf-8")
        if not USES_DS.search(old):
            skipped += 1
            continue
        new, notes = patch(old)
        rel = path.relative_to(ROOT)
        problems += [f"{rel}: {n}" for n in notes]
        if new != old:
            changed.append(rel)
            if apply:
                path.write_text(new, encoding="utf-8")

    for rel in changed:
        print(f"  ✎ {rel}")
    for p in problems:
        print(f"  ⚠ {p}")
    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(changed)} sayfa değişti, {skipped} sayfa suu.css kullanmıyor (atlandı) — {mode}")
    if changed and not apply:
        print("Uygulamak için: python3 scripts/inject-theme-toggle.py --apply")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
