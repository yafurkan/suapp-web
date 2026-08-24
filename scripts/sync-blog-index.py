#!/usr/bin/env python3
"""
Suu — blog indeksine eksik yazıları ekle

Yeni bir blog yazısı dosya olarak eklendiğinde dil indeksine (blog.html,
blog-en.html …) elle kart eklenmezse sayfa YETİM kalır: hiçbir yerden iç
bağlantı almaz. Sitemap'te olması yetmez — tarayıcılar da yapay zekâ
getiricileri de bağlantı grafiğini izler, bağlantısız sayfayı düşük
öncelikli sayar ve çoğu zaman hiç getirmez.

Bu script her dilin yazı klasörünü indeksiyle karşılaştırır, eksik olanlar
için kartı yazının kendi meta verisinden (başlık, açıklama, yayın tarihi)
üretir ve gridin başına ekler.

Kullanım:
    python3 scripts/sync-blog-index.py              # önizleme
    python3 scripts/sync-blog-index.py --apply
"""
from __future__ import annotations

import html
import re
import sys
from datetime import date
from pathlib import Path

from _langs import blog_langs, blog_topics, months, read_more

ROOT = Path(__file__).resolve().parents[1]

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
# blog_langs() yalnızca indeks dosyası VE yazı klasörü diskte olan dilleri
# döndürür — yeni bir dilin blogunu açmak için burayı düzenlemek gerekmez.
LANGS = blog_langs()
READ_MORE = read_more()
MONTHS = months()

# Konu anahtarı → (regex, emoji, gradyan, dil tablosundaki etiket anahtarı).
# Kalıplar tüm dillerin slug'larını kapsamalı; etiketler content/languages.json'da.
TOPIC_LABELS = blog_topics()
TOPICS = [
    (r"vs|karsilastir|karşılaştır|versus|vergleich|confronto|porivn", "⚖️", "#0072C6,#43A047", "comparison"),
    (r"egzersiz|workout|exercise|antren|allenamento|sport|trenuvan", "🏃", "#2E9E4F,#66BB6A", "exercise"),
    (r"kalori|calorie|makro|macro|beslenme|nutrition|kalorien", "🔥", "#F57C00,#FFB74D", "calories"),
    (r"foto|photo", "📸", "#7B1FA2,#BA68C8", "photo"),
    (r"ucretsiz|ücretsiz|free|gratis|besplatn", "🎁", "#00897B,#4DB6AC", "free"),
    (r"", "💧", "#1E88E5,#42A5F5", "guide"),
]


def meta(page: str, *keys: str) -> str:
    for k in keys:
        m = re.search(
            rf'<meta (?:name|property)="{re.escape(k)}" content="([^"]*)"', page)
        if m and m.group(1).strip():
            return html.unescape(m.group(1)).strip()
    return ""


def title_of(page: str) -> str:
    t = meta(page, "og:title", "twitter:title")
    if not t:
        m = re.search(r"<title>(.*?)</title>", page, re.DOTALL)
        t = html.unescape(m.group(1)).strip() if m else ""
    # "Başlık | Suu" / "Başlık — Suu" kuyruğunu at
    return re.sub(r"\s*[|—–]\s*Suu.*$", "", t).strip()


def topic_of(slug: str, lang: str) -> tuple[str, str, str]:
    labels = TOPIC_LABELS.get(lang, TOPIC_LABELS["en"])
    for pattern, emoji, grad, key in TOPICS:
        if not pattern or re.search(pattern, slug, re.IGNORECASE):
            return emoji, grad, labels[key]
    return "💧", "#1E88E5,#42A5F5", labels["guide"]


def pretty_date(iso: str, lang: str) -> str:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    d = date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else date.today()
    month = MONTHS[lang][d.month - 1]
    if lang == "en":
        return f"{month} {d.day}, {d.year}"
    return f"{d.day} {month} {d.year}"


def card_tr(link: str, t: str, ex: str, emoji: str, grad: str, dt: str) -> str:
    g1, g2 = grad.split(",")
    return f"""                    <article class="article-card">
                        <div class="article-image">
                            <div class="article-placeholder" style="font-size:2.5rem;background:linear-gradient(135deg,{g1},{g2});color:#fff;">{emoji}</div>
                            <div class="article-date">{dt}</div>
                        </div>
                        <div class="article-content">
                            <h3 class="article-title">{html.escape(t)}</h3>
                            <p class="article-excerpt">{html.escape(ex)}</p>
                            <a href="{link}" class="read-more">{READ_MORE['tr']} <i class="fas fa-arrow-right"></i></a>
                        </div>
                    </article>
"""


def card_std(lang: str, link: str, t: str, ex: str, emoji: str, grad: str, tag: str) -> str:
    g1, g2 = grad.split(",")
    return f"""        <article class="article-card">
            <div class="article-thumb" style="background:linear-gradient(135deg,{g1},{g2});color:white;">{emoji}</div>
            <div class="article-body">
                <div class="article-tag">{html.escape(tag)}</div>
                <h3>{html.escape(t)}</h3>
                <p>{html.escape(ex)}</p>
                <a href="{link}" class="read-more">{READ_MORE[lang]} <i class="fas fa-arrow-right"></i></a>
            </div>
        </article>

"""


GRID_ANCHORS = [
    '<div class="articles-grid" id="articlesGrid">\n                    <!-- Static blog posts -->\n',
    '<div class="articles-grid" id="articlesGrid">\n',
    '<div class="articles-grid">\n',
]


def main() -> int:
    apply = "--apply" in sys.argv
    total = 0

    for lang, (index_name, post_dir, prefix) in LANGS.items():
        index_path = ROOT / index_name
        if not index_path.exists():
            continue
        index = index_path.read_text(encoding="utf-8")

        posts = sorted((ROOT / post_dir).glob("*.html"))
        missing = [p for p in posts if p.name not in index]
        if not missing:
            print(f"  {index_name:14s} ✓ eksik yok")
            continue

        cards = []
        for post in missing:
            page = post.read_text(encoding="utf-8")
            t = title_of(page)
            ex = meta(page, "description", "og:description")
            if len(ex) > 165:
                ex = ex[:162].rsplit(" ", 1)[0] + "…"
            emoji, grad, tag = topic_of(post.stem, lang)
            published = meta(page, "article:published_time")
            link = prefix + post.name
            if lang == "tr":
                cards.append(card_tr(link, t, ex, emoji, grad,
                                     pretty_date(published, lang)))
            else:
                cards.append(card_std(lang, link, t, ex, emoji, grad, tag))

        block = "".join(cards)
        for anchor in GRID_ANCHORS:
            pos = index.find(anchor)
            if pos != -1:
                cut = pos + len(anchor)
                index = index[:cut] + block + index[cut:]
                break
        else:
            print(f"  {index_name:14s} ✗ grid çapası bulunamadı — atlandı")
            continue

        print(f"  {index_name:14s} + {len(missing)} kart")
        for post in missing:
            print(f"        · {post.name}")
        total += len(missing)
        if apply:
            index_path.write_text(index, encoding="utf-8")

    mode = "UYGULANDI" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{total} kart — {mode}")
    if not apply and total:
        print("Uygulamak için: python3 scripts/sync-blog-index.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
