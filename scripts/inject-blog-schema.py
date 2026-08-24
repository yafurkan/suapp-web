#!/usr/bin/env python3
"""
Inject Article schema (JSON-LD) into blog posts that lack it.
Reads <title>, <meta name="description">, canonical URL, og:image, html lang from each post.
Idempotent: skips files that already contain @type: Article or @type: BlogPosting.
"""
import re
import sys
from pathlib import Path

from _langs import blog_targets

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = PROJECT_ROOT / "blog"

LANG_PUBLISH_DATE = {
    "tr": "2026-03-15",
    "en": "2026-03-30",
    "ar": "2026-04-15",
    "ru": "2026-05-07",
}

LANG_AUTHOR_TITLE = {
    "tr": "Indie Developer & Suu Kurucusu",
    "en": "Indie Developer & Founder of Suu",
    "ar": "مطور مستقل ومؤسس Suu",
    "ru": "Indie-разработчик и основатель Suu",
}


def extract(pattern: str, html: str, group: int = 1) -> str | None:
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    return m.group(group).strip() if m else None


def has_article_schema(html: str) -> bool:
    return bool(
        re.search(
            r'"@type"\s*:\s*"(Article|BlogPosting|NewsArticle)"',
            html,
        )
    )


def build_article_schema(
    *, headline: str, description: str, image: str, url: str, lang: str, date: str
) -> str:
    headline_safe = headline.replace('"', '\\"')
    description_safe = description.replace('"', '\\"')
    author_title = LANG_AUTHOR_TITLE.get(lang, "Indie Developer & Founder of Suu")
    return f"""    <script type="application/ld+json">
    {{
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "{headline_safe}",
        "description": "{description_safe}",
        "image": "{image}",
        "datePublished": "{date}",
        "dateModified": "{date}",
        "inLanguage": "{lang}",
        "author": {{
            "@type": "Person",
            "name": "Furkan Mert Fındıklı",
            "url": "https://www.linkedin.com/in/furkanfindikli/",
            "jobTitle": "{author_title}",
            "affiliation": {{"@type": "Organization", "name": "Suu", "url": "https://suuapp.com"}}
        }},
        "publisher": {{
            "@type": "Organization",
            "name": "Suu",
            "url": "https://suuapp.com",
            "logo": {{"@type": "ImageObject", "url": "https://suuapp.com/assets/favicon.svg"}}
        }},
        "mainEntityOfPage": "{url}"
    }}
    </script>
"""


def process_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8")
    if has_article_schema(html):
        return "skip-already-has-article"

    lang = extract(r'<html\s+lang="([^"]+)"', html) or "en"
    title = extract(r"<title>([^<]+)</title>", html)
    if not title:
        return "skip-no-title"
    title = re.sub(r"\s*\|\s*Suu\s*$", "", title).strip()

    description = extract(r'<meta\s+name="description"\s+content="([^"]+)"', html)
    if not description:
        return "skip-no-description"

    canonical = extract(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
    if not canonical:
        return "skip-no-canonical"

    og_image = (
        extract(r'<meta\s+property="og:image"\s+content="([^"]+)"', html)
        or "https://suuapp.com/assets/og-image.png"
    )

    date = LANG_PUBLISH_DATE.get(lang, "2026-04-01")
    schema_block = build_article_schema(
        headline=title,
        description=description,
        image=og_image,
        url=canonical,
        lang=lang,
        date=date,
    )

    if "</head>" not in html:
        return "skip-no-head-close"

    new_html = html.replace("</head>", schema_block + "</head>", 1)
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
