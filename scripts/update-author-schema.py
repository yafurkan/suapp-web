#!/usr/bin/env python3
"""
Blog yazılarındaki author schema URL'sini LinkedIn'den internal
/yazarlar/furkan-mert.html sayfasına geçirir + LinkedIn'i sameAs'a taşır.

Google için: Article schema → author entity'si artık site içinde
çözülebilir bir Person URL'sine işaret eder (E-E-A-T cross-reference).
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "blog"
AUTHOR_URL = "https://suuapp.com/yazarlar/furkan-mert.html"
LINKEDIN = "https://www.linkedin.com/in/furkanfindikli/"

# Eski örüntüleri tanı: "author" objesinde url alanı LinkedIn'i gösteriyor
# Yeni: url → AUTHOR_URL, sameAs: [LINKEDIN]
RE_AUTHOR_BLOCK = re.compile(
    r'("author"\s*:\s*\{)([^}]*?)("\s*\})',
    re.DOTALL,
)


def transform_author(match: re.Match) -> str:
    head = match.group(1)
    body = match.group(2)
    tail = match.group(3)

    # url alanını LinkedIn'den AUTHOR_URL'e çek
    new_body, n_url = re.subn(
        r'"url"\s*:\s*"https://www\.linkedin\.com/in/furkanfindikli/?"',
        f'"url": "{AUTHOR_URL}"',
        body,
    )
    if n_url == 0:
        # author bloğunda LinkedIn url'i yok; dokunma
        return match.group(0)

    # sameAs zaten varsa dokunma; yoksa ekle
    if '"sameAs"' not in new_body:
        # sona ekle — virgülle ayrılı, tail'den önce
        new_body = new_body.rstrip()
        if not new_body.endswith(","):
            new_body += ","
        new_body += f'\n            "sameAs": ["{LINKEDIN}"]\n        '

    return head + new_body + tail


def process(path: Path) -> bool:
    html = path.read_text(encoding="utf-8")
    new_html, changed = RE_AUTHOR_BLOCK.subn(transform_author, html)
    if new_html != html:
        path.write_text(new_html, encoding="utf-8")
        return True
    return False


def main() -> int:
    edited = 0
    for path in sorted(BLOG_DIR.rglob("*.html")):
        if process(path):
            edited += 1
            print(f"  ✓ {path.relative_to(ROOT)}")
    print(f"\nGüncellenen: {edited} dosya")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
