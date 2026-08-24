#!/usr/bin/env python3
"""
Suu — dil başına RSS beslemesi

Beslemenin iki işi var: (1) içerik toplayıcıların ve bazı yapay zekâ
getiricilerinin yeni yazıları keşfetmesi, (2) tazelik sinyali — sitenin
düzenli güncellendiğini makine tarafında da göstermek.

Girdiler yazının kendi meta verisinden okunur (başlık, açıklama, yayın
tarihi, yazar); besleme elle sürdürülmez.

Kullanım:
    python3 scripts/build-feeds.py            # önizleme
    python3 scripts/build-feeds.py --apply
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

from _langs import feeds
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"
MAX_ITEMS = 40

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
FEEDS = feeds()


def meta(page: str, *keys: str) -> str:
    for k in keys:
        m = re.search(rf'<meta (?:name|property)="{re.escape(k)}" content="([^"]*)"', page)
        if m and m.group(1).strip():
            return html.unescape(m.group(1)).strip()
    return ""


def title_of(page: str) -> str:
    t = meta(page, "og:title")
    if not t:
        m = re.search(r"<title>(.*?)</title>", page, re.DOTALL)
        t = html.unescape(m.group(1)).strip() if m else ""
    return re.sub(r"\s*[|—–]\s*Suu.*$", "", t).strip()


def published_of(page: str) -> datetime:
    raw = meta(page, "article:published_time", "article:modified_time")
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw or "")
    if m:
        return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                        tzinfo=timezone.utc)
    return datetime(2026, 1, 1, tzinfo=timezone.utc)


def main() -> int:
    apply = "--apply" in sys.argv
    now = datetime.now(timezone.utc)
    written = []

    for lang, cfg in FEEDS.items():
        folder = ROOT / cfg["dir"]
        if not folder.exists():
            continue

        entries = []
        for path in folder.glob("*.html"):
            page = path.read_text(encoding="utf-8", errors="ignore")
            if 'http-equiv="refresh"' in page or "noindex" in page:
                continue
            title = title_of(page)
            if not title:
                continue
            entries.append({
                "title": title,
                "url": f"{BASE}/{cfg['dir']}/{path.name}",
                "desc": meta(page, "description", "og:description"),
                "date": published_of(page),
                "author": meta(page, "article:author") or "Furkan Mert Fındıklı",
            })

        entries.sort(key=lambda e: e["date"], reverse=True)
        entries = entries[:MAX_ITEMS]

        items = []
        for e in entries:
            items.append(
                "    <item>\n"
                f"      <title>{escape(e['title'])}</title>\n"
                f"      <link>{escape(e['url'])}</link>\n"
                f"      <guid isPermaLink=\"true\">{escape(e['url'])}</guid>\n"
                f"      <description>{escape(e['desc'])}</description>\n"
                f"      <dc:creator>{escape(e['author'])}</dc:creator>\n"
                f"      <pubDate>{format_datetime(e['date'])}</pubDate>\n"
                "    </item>"
            )

        feed_url = f"{BASE}/{cfg['out']}"
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"'
            ' xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            "  <channel>\n"
            f"    <title>{escape(cfg['title'])}</title>\n"
            f"    <link>{BASE}/{cfg['index']}</link>\n"
            f"    <description>{escape(cfg['desc'])}</description>\n"
            f"    <language>{cfg['lang']}</language>\n"
            f"    <lastBuildDate>{format_datetime(now)}</lastBuildDate>\n"
            f'    <atom:link href="{feed_url}" rel="self" type="application/rss+xml"/>\n'
            + "\n".join(items) + "\n"
            "  </channel>\n"
            "</rss>\n"
        )

        target = ROOT / cfg["out"]
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        # lastBuildDate her çalıştırmada değişir; gerçek fark var mı diye
        # o satır dışlanarak karşılaştırılır (gereksiz commit üretmesin).
        strip = lambda s: re.sub(r"<lastBuildDate>.*?</lastBuildDate>", "", s)
        if strip(old) == strip(xml):
            print(f"  = {cfg['out']} ({len(entries)} yazı, değişmedi)")
            continue

        written.append(f"{cfg['out']} ({len(entries)} yazı, {len(xml)//1024} KB)")
        if apply:
            target.write_text(xml, encoding="utf-8")

    for line in written:
        print(f"  ✎ {line}")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} besleme değişti — {mode}")
    if not apply and written:
        print("Uygulamak için: python3 scripts/build-feeds.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
