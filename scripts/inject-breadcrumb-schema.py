#!/usr/bin/env python3
"""
Inject BreadcrumbList schema into blog posts that lack it.
Idempotent: skips files that already contain @type: BreadcrumbList.
"""
import re
import sys
from pathlib import Path

from _langs import blog_targets

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"

LANG_LABELS = {
    "tr": {
        "home": ("Ana Sayfa", "https://suuapp.com/"),
        "blog": ("Blog", "https://suuapp.com/blog.html"),
    },
    "en": {
        "home": ("Home", "https://suuapp.com/hosgeldiniz-en.html"),
        "blog": ("Blog", "https://suuapp.com/blog-en.html"),
    },
    "ar": {
        "home": ("الرئيسية", "https://suuapp.com/hosgeldiniz-ar.html"),
        "blog": ("المدونة", "https://suuapp.com/blog-ar.html"),
    },
    "ru": {
        "home": ("Главная", "https://suuapp.com/hosgeldiniz-ru.html"),
        "blog": ("Блог", "https://suuapp.com/blog-ru.html"),
    },
}


def extract(pattern: str, html: str, group: int = 1) -> str | None:
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return m.group(group).strip() if m else None


def has_breadcrumb(html: str) -> bool:
    return bool(re.search(r'"@type"\s*:\s*"BreadcrumbList"', html))


def build_breadcrumb_schema(*, lang: str, title: str, url: str) -> str:
    labels = LANG_LABELS.get(lang, LANG_LABELS["en"])
    home_name, home_url = labels["home"]
    blog_name, blog_url = labels["blog"]
    title_safe = title.replace('"', '\\"')
    return f"""    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{"@type": "ListItem", "position": 1, "name": "{home_name}", "item": "{home_url}"}},
            {{"@type": "ListItem", "position": 2, "name": "{blog_name}", "item": "{blog_url}"}},
            {{"@type": "ListItem", "position": 3, "name": "{title_safe}", "item": "{url}"}}
        ]
    }}
    </script>
"""


def process_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    if has_breadcrumb(html):
        return "skip-already-has-breadcrumb"

    lang = extract(r'<html\s+lang="([^"]+)"', html) or "en"
    title = extract(r"<title>([^<]+)</title>", html)
    if not title:
        return "skip-no-title"
    title = re.sub(r"\s*\|\s*Suu\s*$", "", title).strip()

    canonical = extract(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
    if not canonical:
        return "skip-no-canonical"

    schema = build_breadcrumb_schema(lang=lang, title=title, url=canonical)

    if "</head>" not in html:
        return "skip-no-head-close"

    new_html = html.replace("</head>", schema + "</head>", 1)
    path.write_text(new_html, encoding="utf-8")
    return "injected"


def main(target_dirs: list[str]) -> None:
    counts: dict[str, int] = {}
    for d in target_dirs:
        sub = BLOG_DIR / d if d else BLOG_DIR
        for f in sorted(sub.glob("*.html")):
            result = process_file(f)
            counts[result] = counts.get(result, 0) + 1
            print(f"  {result}: {f.relative_to(PROJECT_ROOT)}")
        print(f"--- {d or 'tr (root)'} subtotals ---")
    print("\n=== Total ===")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else blog_targets()
    main(targets)
