#!/usr/bin/env python3
"""
Enrich Article JSON-LD with `keywords` (from <meta name="keywords">) and `wordCount`
(from <body> text content). Idempotent.
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


def count_words(html: str) -> int:
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.IGNORECASE | re.DOTALL)
    if not body_match:
        return 0
    body = body_match.group(1)
    # Strip <script> and <style> blocks
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.IGNORECASE | re.DOTALL)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.IGNORECASE | re.DOTALL)
    # Remove all tags
    text = re.sub(r"<[^>]+>", " ", body)
    # Decode minimal entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    words = re.findall(r"\S+", text)
    return len(words)


def find_article_block(html: str) -> tuple[int, int, str] | None:
    """Find the Article JSON-LD script block. Returns (start, end, content)."""
    # Match <script type="application/ld+json">...</script> blocks containing "Article"
    pattern = re.compile(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        re.DOTALL,
    )
    for m in pattern.finditer(html):
        block = m.group(1)
        if re.search(r'"@type"\s*:\s*"(Article|BlogPosting|NewsArticle)"', block):
            return m.start(1), m.end(1), block
    return None


def has_keywords(block: str) -> bool:
    return bool(re.search(r'"keywords"\s*:', block))


def has_word_count(block: str) -> bool:
    return bool(re.search(r'"wordCount"\s*:', block))


def inject_fields(block: str, *, keywords: str | None, word_count: int) -> str:
    additions = []
    if keywords and not has_keywords(block):
        kw_safe = keywords.replace('"', '\\"').strip()
        additions.append(f'"keywords": "{kw_safe}"')
    if word_count > 0 and not has_word_count(block):
        additions.append(f'"wordCount": {word_count}')

    if not additions:
        return block

    # Insert just before the final `}`
    last_brace = block.rfind("}")
    if last_brace == -1:
        return block
    head = block[:last_brace].rstrip()
    if not head.endswith(","):
        head += ","
    return head + "\n        " + ",\n        ".join(additions) + "\n    }"


def process_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    found = find_article_block(html)
    if not found:
        return "skip-no-article"
    start, end, block = found

    if has_keywords(block) and has_word_count(block):
        return "skip-already-enriched"

    keywords = extract(r'<meta\s+name="keywords"\s+content="([^"]+)"', html)
    word_count = count_words(html)

    new_block = inject_fields(block, keywords=keywords, word_count=word_count)
    if new_block == block:
        return "skip-no-additions"

    new_html = html[:start] + new_block + html[end:]
    path.write_text(new_html, encoding="utf-8")
    return "enriched"


def main(target_dirs: list[str]) -> None:
    counts: dict[str, int] = {}
    for d in target_dirs:
        sub = BLOG_DIR / d if d else BLOG_DIR
        for f in sorted(sub.glob("*.html")):
            result = process_file(f)
            counts[result] = counts.get(result, 0) + 1
        print(f"--- {d or 'tr (root)'} done ---")
    print("\n=== Total ===")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else blog_targets()
    main(targets)
