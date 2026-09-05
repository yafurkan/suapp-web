#!/usr/bin/env python3
"""
Suu — FAQPage şeması ile sayfa içeriğini hizala

Google kuralı: FAQPage işaretlemesindeki soru/cevaplar sayfada kullanıcıya
görünür olmalıdır. Denetimde 130 sayfada ihlal bulundu (check-faq-visibility.py).
İki farklı durum var ve her biri farklı yönde düzeltilir:

  A) Sayfada görünür SSS VAR ama şema onunla uyuşmuyor (50 sayfa)
     → ŞEMA sayfadan yeniden üretilir. Doğru kaynak sayfadır; kullanıcı ne
       görüyorsa arama motoruna da o söylenmelidir.

  B) Sayfada hiç görünür SSS YOK (80 sayfa)
     → Şemadaki soru/cevaplar SAYFAYA basılır. İçerik zaten yazılmış, sadece
       gösterilmiyordu; silmek yerine göstermek hem kuralı karşılar hem
       sayfaya gerçek içerik ekler.

Kullanım:
    python3 scripts/fix-faq-visibility.py               # önizleme
    python3 scripts/fix-faq-visibility.py --apply
    python3 scripts/fix-faq-visibility.py --only A      # sadece şema onarımı
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "content"}

RE_LD_BLOCK = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.DOTALL)
RE_STRIP = re.compile(r'<script.*?</script>|<style.*?</style>', re.DOTALL)
RE_TAGS = re.compile(r'<[^>]+>')
RE_WS = re.compile(r"\s+")

MARKER = "<!-- FAQ (auto-rendered from schema: scripts/fix-faq-visibility.py) -->"

# Sayfadaki görünür SSS kalıpları — soru/cevap çiftini yakalar
VISIBLE_PATTERNS = [
    re.compile(r'<div class="faq-question"[^>]*>(.*?)</div>\s*<div class="faq-answer"[^>]*>(.*?)</div>', re.DOTALL),
    re.compile(r'<summary[^>]*>(.*?)</summary>\s*<(?:div|p)[^>]*>(.*?)</(?:div|p)>', re.DOTALL),
    re.compile(r'<div class="faq-item"[^>]*>\s*<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>', re.DOTALL),
    re.compile(r'<h3 class="faq-q"[^>]*>(.*?)</h3>\s*<p class="faq-a"[^>]*>(.*?)</p>', re.DOTALL),
    re.compile(r'<div class="faq-q"[^>]*>(.*?)</div>\s*<div class="faq-a"[^>]*>(.*?)</div>', re.DOTALL),
    re.compile(r'<div class="faq-item"[^>]*>\s*<h4[^>]*>(.*?)</h4>\s*<p[^>]*>(.*?)</p>', re.DOTALL),
]

# Basılacak bloğun yerleştirileceği çapa, öncelik sırasıyla
ANCHORS = [
    '<section class="references"', '<div class="references"',
    '<section class="related"', '<div class="related"',
    '<div class="footer-nav"', '<nav class="footer-nav"',
    '<div class="related-grid"', '<div class="related-card"',
    "</article>", "</main>", "<footer",
]

FAQ_HEADINGS = {
    "tr": "Sık sorulan sorular", "en": "Frequently asked questions",
    "ar": "الأسئلة الشائعة", "ru": "Частые вопросы",
    "de": "Häufige Fragen", "it": "Domande frequenti", "hi": "अक्सर पूछे जाने वाले सवाल",
    "uk": "Часті запитання",
}


def clean(text: str) -> str:
    return RE_WS.sub(" ", html.unescape(RE_TAGS.sub("", text))).strip()


def visible_text(page: str) -> str:
    body = RE_STRIP.sub(" ", page)
    return RE_WS.sub(" ", html.unescape(RE_TAGS.sub(" ", body)))


def schema_faq(page: str) -> list[tuple[str, str]]:
    for _, block, _ in RE_LD_BLOCK.findall(page):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        nodes = data.get("@graph") if isinstance(data, dict) and "@graph" in data else [data]
        for node in nodes if isinstance(nodes, list) else [nodes]:
            if isinstance(node, dict) and node.get("@type") == "FAQPage":
                out = []
                for q in node.get("mainEntity", []):
                    name = q.get("name")
                    ans = (q.get("acceptedAnswer") or {}).get("text")
                    if isinstance(name, str) and isinstance(ans, str):
                        out.append((name, ans))
                return out
    return []


def visible_faq(page: str) -> list[tuple[str, str]]:
    for pattern in VISIBLE_PATTERNS:
        pairs = pattern.findall(page)
        if len(pairs) >= 2:
            return [(clean(q), clean(a)) for q, a in pairs if clean(q) and clean(a)]
    return []


def lang_of(page: str) -> str:
    m = re.search(r'<html[^>]*\blang="([a-z]{2})', page)
    return m.group(1) if m else "tr"


def rewrite_schema(page: str, pairs: list[tuple[str, str]]) -> str:
    """A) Şemayı sayfadaki görünür SSS'ten yeniden üret."""
    def repl(m: re.Match) -> str:
        open_tag, block, close_tag = m.groups()
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            return m.group(0)

        changed = False

        def fix(node):
            nonlocal changed
            if isinstance(node, dict) and node.get("@type") == "FAQPage":
                node["mainEntity"] = [
                    {"@type": "Question", "name": q,
                     "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in pairs
                ]
                changed = True
            return node

        if isinstance(data, dict) and "@graph" in data:
            data["@graph"] = [fix(n) for n in data["@graph"]]
        else:
            data = fix(data)

        if not changed:
            return m.group(0)
        out = json.dumps(data, ensure_ascii=False, indent=2)
        out = out.replace("<", "\\u003c").replace(">", "\\u003e")
        return f"{open_tag}\n{out}\n    {close_tag}"

    return RE_LD_BLOCK.sub(repl, page)


# Sayfada zaten bir SSS bulunduğunu gösteren işaretler — bunlardan biri
# varsa asla ikinci bir SSS bloğu basılmaz (çift içerik riski).
HAS_FAQ_HINTS = ("faq-item", "faq-question", "faq__item", "faq-q",
                 "<summary", 'id="faq"', 'class="faq"')


def render_faq(page: str, pairs: list[tuple[str, str]]) -> str | None:
    """B) Şemadaki SSS'i sayfaya bas."""
    if MARKER in page:
        return None
    # Kontrol yalnızca GÖVDEDE yapılır — <style> içindeki ".faq-item { }"
    # gibi CSS tanımları "sayfada SSS var" anlamına gelmez.
    markup = RE_STRIP.sub(" ", page)
    if any(h in markup for h in HAS_FAQ_HINTS):
        return None          # görünür SSS var ama kalıbı tanımadık — dokunma

    heading = FAQ_HEADINGS.get(lang_of(page), FAQ_HEADINGS["en"])
    items = []
    for q, a in pairs:
        items.append(
            '    <details style="border-bottom:1px solid rgba(128,128,128,.25)">\n'
            f'      <summary style="padding:14px 0;font-weight:600;cursor:pointer;list-style:none">{html.escape(q)}</summary>\n'
            f'      <div style="padding-bottom:14px;opacity:.85">{html.escape(a)}</div>\n'
            "    </details>"
        )

    block = (
        f"\n  {MARKER}\n"
        '  <section class="faq-rendered" style="max-width:760px;margin:40px auto;padding:0 20px">\n'
        f"    <h2>{html.escape(heading)}</h2>\n"
        + "\n".join(items)
        + "\n  </section>\n\n"
    )

    for anchor in ANCHORS:
        idx = page.find(anchor)
        if idx != -1:
            return page[:idx] + block + page[idx:]
    return None


def main() -> int:
    apply = "--apply" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].upper()

    fixed_a, fixed_b, skipped = [], [], []

    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        try:
            page = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        sq = schema_faq(page)
        if not sq:
            continue
        body = visible_text(page)
        if not [q for q, _ in sq if q[:40] not in body]:
            continue                      # zaten uyumlu

        vq = visible_faq(page)

        if vq and (only in (None, "A")):
            new = rewrite_schema(page, vq)
            if new != page:
                fixed_a.append(f"{rel}  (şema {len(sq)} → sayfadaki {len(vq)} soru)")
                if apply:
                    path.write_text(new, encoding="utf-8")
            continue

        if not vq and (only in (None, "B")):
            new = render_faq(page, sq)
            if new:
                fixed_b.append(f"{rel}  ({len(sq)} soru sayfaya basıldı)")
                if apply:
                    path.write_text(new, encoding="utf-8")
            else:
                skipped.append(f"{rel}  (çapa bulunamadı)")

    print(f"A) Şema sayfadan yeniden üretildi : {len(fixed_a)}")
    for x in fixed_a[:6]:
        print(f"     {x}")
    if len(fixed_a) > 6:
        print(f"     … ve {len(fixed_a) - 6} tane daha")

    print(f"\nB) SSS sayfaya basıldı            : {len(fixed_b)}")
    for x in fixed_b[:6]:
        print(f"     {x}")
    if len(fixed_b) > 6:
        print(f"     … ve {len(fixed_b) - 6} tane daha")

    if skipped:
        print(f"\n⚠ atlandı ({len(skipped)}) — elle bakılmalı:")
        for x in skipped[:10]:
            print(f"     {x}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(fixed_a) + len(fixed_b)} sayfa — {mode}")
    if not apply:
        print("Uygulamak için: python3 scripts/fix-faq-visibility.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
