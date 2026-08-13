#!/usr/bin/env python3
"""
Suu — FAQPage şeması görünürlük denetimi

Google'ın yapılandırılmış veri kuralı: FAQPage işaretlemesindeki soru ve
cevaplar SAYFADA KULLANICIYA GÖRÜNÜR olmalıdır. Görünmeyen içerik için
FAQPage kullanmak, en iyi ihtimalle işaretlemenin yok sayılmasına, en kötü
ihtimalle manuel işleme yol açar.

Bu script her sayfada FAQPage şemasındaki soruların görünür gövdede geçip
geçmediğini denetler.

Kullanım:
    python3 scripts/check-faq-visibility.py
    python3 scripts/check-faq-visibility.py --list   # dosya dosya döküm
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "content"}

RE_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
RE_STRIP = re.compile(r'<script.*?</script>|<style.*?</style>', re.DOTALL)
RE_TAGS = re.compile(r'<[^>]+>')

# Eşleşme için sorunun ilk N karakteri aranır — tam eşleşme şart değil,
# sayfada biçimlendirme farkı olabilir.
PREFIX = 40


def visible_text(page: str) -> str:
    body = RE_STRIP.sub(" ", page)
    body = html.unescape(RE_TAGS.sub(" ", body))
    return re.sub(r"\s+", " ", body)


def faq_questions(page: str) -> list[str]:
    out: list[str] = []
    for block in RE_LD.findall(page):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        nodes = data.get("@graph") if isinstance(data, dict) and "@graph" in data else [data]
        for node in nodes if isinstance(nodes, list) else [nodes]:
            if isinstance(node, dict) and node.get("@type") == "FAQPage":
                for q in node.get("mainEntity", []):
                    name = q.get("name")
                    if isinstance(name, str):
                        out.append(name)
    return out


def main() -> int:
    show_list = "--list" in sys.argv

    clean, broken, partial = [], [], []

    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        try:
            page = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        questions = faq_questions(page)
        if not questions:
            continue

        body = visible_text(page)
        missing = [q for q in questions if q[:PREFIX] not in body]

        if not missing:
            clean.append((str(rel), len(questions)))
        elif len(missing) == len(questions):
            broken.append((str(rel), len(questions)))
        else:
            partial.append((str(rel), len(missing), len(questions)))

    total = len(clean) + len(broken) + len(partial)
    print(f"{total} sayfada FAQPage şeması var\n")
    print(f"  ✓ tamamı görünür : {len(clean)}")
    print(f"  ⚠ kısmen görünmez: {len(partial)}")
    print(f"  ✗ hiçbiri görünmez: {len(broken)}")

    if broken:
        print(f"\n✗ TAMAMEN GÖRÜNMEZ ({len(broken)}) — Google kuralı ihlali:")
        for rel, n in (broken if show_list else broken[:15]):
            print(f"    {rel}  ({n} soru)")
        if not show_list and len(broken) > 15:
            print(f"    … ve {len(broken) - 15} tane daha (--list ile tümü)")

    if partial:
        print(f"\n⚠ KISMEN GÖRÜNMEZ ({len(partial)}):")
        for rel, m, n in (partial if show_list else partial[:10]):
            print(f"    {rel}  ({m}/{n} soru görünmüyor)")
        if not show_list and len(partial) > 10:
            print(f"    … ve {len(partial) - 10} tane daha")

    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
