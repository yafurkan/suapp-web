#!/usr/bin/env python3
"""
Inject SpeakableSpecification into Article JSON-LD on blog posts.
Targets the headline (h1), the intro section, and h2 subheadings — common patterns
across the blog templates. Idempotent.
"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"

SPEAKABLE_FRAGMENT = '''"speakable": {
            "@type": "SpeakableSpecification",
            "cssSelector": [".hero h1", ".intro", "h2", ".benefit-content p", ".phase-card p"]
        }'''


def find_article_block(html: str) -> tuple[int, int, str] | None:
    pattern = re.compile(
        r'<script type="application/ld\+json">\s*(\{.*?\})\s*</script>',
        re.DOTALL,
    )
    for m in pattern.finditer(html):
        block = m.group(1)
        if re.search(r'"@type"\s*:\s*"(Article|BlogPosting|NewsArticle)"', block):
            return m.start(1), m.end(1), block
    return None


def has_speakable(block: str) -> bool:
    return bool(re.search(r'"speakable"\s*:', block))


def inject_speakable(block: str) -> str:
    if has_speakable(block):
        return block
    last_brace = block.rfind("}")
    if last_brace == -1:
        return block
    head = block[:last_brace].rstrip()
    if not head.endswith(","):
        head += ","
    return head + "\n        " + SPEAKABLE_FRAGMENT + "\n    }"


def process_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    found = find_article_block(html)
    if not found:
        return "skip-no-article"
    start, end, block = found
    if has_speakable(block):
        return "skip-already-speakable"
    new_block = inject_speakable(block)
    new_html = html[:start] + new_block + html[end:]
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
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["", "en", "ar", "ru"]
    main(targets)
