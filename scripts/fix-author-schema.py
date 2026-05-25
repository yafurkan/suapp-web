#!/usr/bin/env python3
"""
update-author-schema.py bir regex bug'ı nedeniyle nested 'affiliation'
objesini yanlış yerden kesip JSON-LD'yi bozdu. Bu script bozuk pattern'i
güvenli ve idempotent şekilde düzeltir.

Bozuk:
    "affiliation": {"@type": "Organization", "name": "Suu", "url": "https://suuapp.com,
                "sameAs": ["https://www.linkedin.com/in/furkanfindikli/"]
            "}
            },

İstenen (affiliation düzgün kapanır, sameAs author seviyesinde kalır):
    "affiliation": {"@type": "Organization", "name": "Suu", "url": "https://suuapp.com"},
                "sameAs": ["https://www.linkedin.com/in/furkanfindikli/"]
            },
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "blog"

BROKEN_RE = re.compile(
    r'"affiliation":\s*\{"@type":\s*"Organization",\s*"name":\s*"Suu",\s*"url":\s*"https://suuapp\.com,\s*\n'
    r'(\s*)"sameAs":\s*\[\s*"https://www\.linkedin\.com/in/furkanfindikli/?"\s*\]\s*\n'
    r'\s*"\}\s*\n'
    r'(\s*)\},'
)


def repair(html: str) -> tuple[str, int]:
    def _sub(m: re.Match) -> str:
        sameAs_indent = m.group(1)
        close_indent = m.group(2)
        return (
            '"affiliation": {"@type": "Organization", "name": "Suu", "url": "https://suuapp.com"},\n'
            f'{sameAs_indent}"sameAs": ["https://www.linkedin.com/in/furkanfindikli/"]\n'
            f'{close_indent}}},'
        )

    new_html, n = BROKEN_RE.subn(_sub, html)
    return new_html, n


def main() -> int:
    fixed = 0
    failed = 0
    for path in sorted(BLOG_DIR.rglob("*.html")):
        html = path.read_text(encoding="utf-8")
        new_html, n = repair(html)
        if n == 0:
            continue
        path.write_text(new_html, encoding="utf-8")
        fixed += 1

        # Doğrulama: tüm JSON-LD blokları parse edilebilir mi?
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', new_html, re.DOTALL):
            try:
                json.loads(m.group(1))
            except Exception as e:
                failed += 1
                print(f"  ❌ {path.relative_to(ROOT)}: JSON-LD invalid ({e})")
                break
        else:
            print(f"  ✓ {path.relative_to(ROOT)}")

    print(f"\nOnarılan dosya: {fixed}")
    print(f"Hâlâ bozuk    : {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
