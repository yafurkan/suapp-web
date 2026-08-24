#!/usr/bin/env python3
"""
Inject missing Twitter Card meta tags into blog posts.
Open Graph tags are already present across the blog set; this script only fills
the Twitter Card gap. Idempotent.
"""
import re
import sys
from pathlib import Path

from _langs import blog_targets

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"


def extract(pattern: str, html: str, group: int = 1) -> str | None:
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return m.group(group).strip() if m else None


def has_twitter(html: str) -> bool:
    return bool(re.search(r'<meta\s+name="twitter:card"', html, re.IGNORECASE))


def build_twitter_block(*, title: str, description: str, image: str) -> str:
    title_e = title.replace('"', "&quot;")
    desc_e = description.replace('"', "&quot;")
    return f"""    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@SuuTakip">
    <meta name="twitter:title" content="{title_e}">
    <meta name="twitter:description" content="{desc_e}">
    <meta name="twitter:image" content="{image}">
"""


def process_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    if has_twitter(html):
        return "skip-already-has-twitter"

    title = extract(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
    if not title:
        title = extract(r"<title>([^<]+)</title>", html)
        if title:
            title = re.sub(r"\s*\|\s*Suu\s*$", "", title).strip()
    if not title:
        return "skip-no-title"

    description = extract(r'<meta\s+property="og:description"\s+content="([^"]+)"', html) or extract(
        r'<meta\s+name="description"\s+content="([^"]+)"', html
    )
    if not description:
        return "skip-no-description"

    image = extract(r'<meta\s+property="og:image"\s+content="([^"]+)"', html) or "https://suuapp.com/assets/og-image.png"

    block = build_twitter_block(title=title, description=description, image=image)

    og_locale_match = re.search(r'(<meta\s+property="og:locale"[^>]*>)', html, re.IGNORECASE)
    canonical_match = re.search(r'(<link\s+rel="canonical"[^>]*>)', html, re.IGNORECASE)
    if og_locale_match:
        insert_pos = og_locale_match.end()
    elif canonical_match:
        insert_pos = canonical_match.end()
    else:
        return "skip-no-anchor"

    new_html = html[:insert_pos] + "\n" + block + html[insert_pos:]
    path.write_text(new_html, encoding="utf-8")
    return "injected"


def main(target_dirs: list[str]) -> None:
    counts: dict[str, int] = {}
    for d in target_dirs:
        sub = BLOG_DIR / d if d else BLOG_DIR
        for f in sorted(sub.glob("*.html")):
            result = process_file(f)
            counts[result] = counts.get(result, 0) + 1
    print("=== Total ===")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else blog_targets()
    main(targets)
