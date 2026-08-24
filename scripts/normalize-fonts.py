#!/usr/bin/env python3
"""
Suu — Google Fonts istek URL'lerini tek biçime indirger

Site 18 farklı Google Fonts URL'i istiyordu; her varyant ayrı bir CSS
önbellek girdisi demek, dolayısıyla sayfa geçişlerinde stil dosyası yeniden
indiriliyordu (SEO denetimi, 2026-08-20).

ÖLÇÜLDÜ: Inter değişken (variable) bir font — wght@300;400;500;600;700 ile
wght@300..900 AYNI 7 woff2 dosyasını döndürüyor. Yani font dosyaları zaten
paylaşılıyordu; kazanç yalnızca CSS isteğinde. Küçük ama bedava.

Değişken font aralığı (`..`) kullanılan aileler tek URL'e indirgenir.
Tajawal DEĞİŞKEN DEĞİL — aralık sözdizimi 400 döndürüyor, o yüzden
Tajawal içeren URL'lere dokunulmaz.

Kullanım:
    python3 scripts/normalize-fonts.py            # önizleme
    python3 scripts/normalize-fonts.py --apply
"""
from __future__ import annotations

import re
import sys
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".qodo", ".github", "worker"}

# Değişken font aralıkları — hepsi Google Fonts'ta 200 döndürüyor (doğrulandı)
AXIS = {
    "Inter": "Inter:wght@300..900",
    "Noto+Sans+Arabic": "Noto+Sans+Arabic:wght@300..800",
    "Noto+Sans+Devanagari": "Noto+Sans+Devanagari:wght@400..800",
}
# Sıra sabit: farklı sayfalarda aynı aile kümesi hep aynı URL'i üretsin
ORDER = ["Inter", "Noto+Sans+Arabic", "Noto+Sans+Devanagari"]

RE_URL = re.compile(r'https://fonts\.googleapis\.com/css2\?[^"\']+')


def canonical(url: str) -> str | None:
    fams = re.findall(r"family=([^&]+)", url)
    names = [f.split(":")[0] for f in fams]
    if any(n not in AXIS for n in names):
        return None          # Tajawal vb. — dokunma
    ordered = [n for n in ORDER if n in names]
    if not ordered:
        return None
    q = "&".join(f"family={AXIS[n]}" for n in ordered)
    return f"https://fonts.googleapis.com/css2?{q}&display=swap"


def main() -> int:
    apply = "--apply" in sys.argv
    edited, before, after = [], collections.Counter(), collections.Counter()

    for path in sorted(ROOT.rglob("*.html")):
        if any(p in SKIP_DIRS for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "fonts.googleapis.com/css2" not in text:
            continue
        for u in RE_URL.findall(text):
            before[u] += 1

        def sub(m: re.Match) -> str:
            return canonical(m.group(0)) or m.group(0)

        new = RE_URL.sub(sub, text)
        for u in RE_URL.findall(new):
            after[u] += 1
        if new != text:
            edited.append(str(path.relative_to(ROOT)))
            if apply:
                path.write_text(new, encoding="utf-8")

    print(f"{len(edited)} sayfa güncellenecek")
    print(f"benzersiz URL: {len(before)} → {len(after)}")
    print("\nsonuçtaki URL'ler:")
    for u, n in after.most_common():
        print(f"  {n:4}×  {u}")
    print("\nuygulandı" if apply else "\nÖNİZLEME — uygulamak için: --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
