#!/usr/bin/env python3
"""
Suu — Blog OG görseli üretici.

Kullanım:
    # Eksik olan tüm OG görsellerini üret
    python3 scripts/generate-og.py

    # Belirli bir yazı için
    python3 scripts/generate-og.py blog/yeni-yazi.html

    # Tüm yazıları yeniden üret (mevcut PNG'leri ezer)
    python3 scripts/generate-og.py --force

    # PNG üret ve aynı zamanda yazının og:image / twitter:image / Article
    # schema'sını güncelle (yeni yazılar için tavsiye edilir)
    python3 scripts/generate-og.py --update-meta

Bağımlılıklar:
    pip3 install Pillow arabic_reshaper python-bidi

Notlar:
    - Dil yazı yolundan tespit edilir (/blog/en/, /blog/ar/, /blog/ru/, diğerleri TR).
    - Başlık <h1>'den çekilir.
    - Çıktı: assets/og/blog/{slug}.png  (TR)
              assets/og/blog/{lang}-{slug}.png (EN/AR/RU)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError as e:
    sys.exit(f"Eksik bağımlılık: {e.name}\n"
             "Yükleme: pip3 install Pillow arabic_reshaper python-bidi")


# === Yapılandırma =========================================================

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://suuapp.com"
OG_DIR = ROOT / "assets" / "og" / "blog"
BLOG_DIR = ROOT / "blog"

# Fontlar
LATIN_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
LATIN_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"
AR_FONT = "/System/Library/Fonts/SFArabic.ttf"

# Görsel boyutları (FB/Twitter/LinkedIn standardı)
W, H = 1200, 630

# Tagline (her dil için)
TAGLINES = {
    "tr": "Su Takip · AI Sağlık Asistanı",
    "en": "Water Tracker · AI Health Assistant",
    "ar": "تتبع الماء · مساعد صحي بالذكاء الاصطناعي",
    "ru": "Трекер воды · ИИ-помощник по здоровью",
}


# === Görsel üretimi =======================================================

def _is_arabic(ch: str) -> bool:
    cp = ord(ch)
    return (
        (0x0600 <= cp <= 0x06FF)
        or (0x0750 <= cp <= 0x077F)
        or (0x08A0 <= cp <= 0x08FF)
        or (0xFB50 <= cp <= 0xFDFF)
        or (0xFE70 <= cp <= 0xFEFF)
    )


def _gradient(c1, c2):
    img = Image.new("RGB", (W, H), c1)
    d = ImageDraw.Draw(img)
    for y in range(H):
        r = y / H
        d.line(
            [(0, y), (W, y)],
            fill=(
                int(c1[0] * (1 - r) + c2[0] * r),
                int(c1[1] * (1 - r) + c2[1] * r),
                int(c1[2] * (1 - r) + c2[2] * r),
            ),
        )
    return img


def _draw_drop(d, cx, cy, size, color=(255, 255, 255, 230)):
    r = size // 2
    d.ellipse([cx - r, cy - r // 3, cx + r, cy + r + r // 3], fill=color)
    d.polygon(
        [(cx, cy - size), (cx - r, cy + r // 3), (cx + r, cy + r // 3)],
        fill=color,
    )


def _measure_mixed(draw, text, ar_font, latin_font):
    total = 0
    for ch in text:
        font = ar_font if _is_arabic(ch) else latin_font
        bbox = draw.textbbox((0, 0), ch, font=font)
        total += bbox[2] - bbox[0]
    return total


def _draw_mixed(draw, x, y, text, ar_font, latin_font, fill):
    cur = x
    for ch in text:
        font = ar_font if _is_arabic(ch) else latin_font
        draw.text((cur, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), ch, font=font)
        cur += bbox[2] - bbox[0]


def _wrap_mixed(text, draw, ar_font, latin_font, max_w):
    words = text.split(" ")
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if _measure_mixed(draw, test, ar_font, latin_font) <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _wrap_latin(text, draw, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        b = draw.textbbox((0, 0), test, font=font)
        if b[2] - b[0] <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def make_og_image(title: str, output_path: Path, lang: str = "tr") -> None:
    """Bir blog yazısı için 1200x630 OG görseli üretir."""
    if lang == "ar":
        title = get_display(arabic_reshaper.reshape(title))

    # Background gradient + overlay highlights
    img = _gradient((74, 144, 217), (41, 182, 246))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse([-200, -200, 600, 600], fill=(255, 255, 255, 25))
    od.ellipse([800, 300, 1500, 1000], fill=(255, 255, 255, 18))
    img = Image.alpha_composite(img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(img)

    is_rtl = lang == "ar"

    # Brand bar
    if is_rtl:
        draw.rectangle([W - 8, 0, W, H], fill=(255, 255, 255, 180))
    else:
        draw.rectangle([0, 0, 8, H], fill=(255, 255, 255, 180))

    # Brand "Suu" + drop (her zaman Latin font)
    brand_font = ImageFont.truetype(LATIN_BOLD, 48)
    if is_rtl:
        _draw_drop(draw, W - 75, 95, 28)
        bbox = draw.textbbox((0, 0), "Suu", font=brand_font)
        tw = bbox[2] - bbox[0]
        draw.text((W - 105 - tw, 70), "Suu", font=brand_font, fill=(255, 255, 255))
    else:
        _draw_drop(draw, 75, 95, 28)
        draw.text((105, 70), "Suu", font=brand_font, fill=(255, 255, 255))

    # Başlık
    if lang == "ar":
        size = 64
        ar_f = ImageFont.truetype(AR_FONT, size)
        latin_f = ImageFont.truetype(LATIN_BOLD, size)
        lines = _wrap_mixed(title, draw, ar_f, latin_f, W - 160)
        while len(lines) > 4 and size > 36:
            size -= 4
            ar_f = ImageFont.truetype(AR_FONT, size)
            latin_f = ImageFont.truetype(LATIN_BOLD, size)
            lines = _wrap_mixed(title, draw, ar_f, latin_f, W - 160)
        line_h = size + 12
        total_h = len(lines) * line_h
        start_y = (H - total_h) // 2
        for i, ln in enumerate(lines):
            y = start_y + i * line_h
            tw = _measure_mixed(draw, ln, ar_f, latin_f)
            x = W - 80 - tw
            _draw_mixed(draw, x + 2, y + 2, ln, ar_f, latin_f, (0, 0, 0, 80))
            _draw_mixed(draw, x, y, ln, ar_f, latin_f, (255, 255, 255))
    else:
        size = 64
        tf = ImageFont.truetype(LATIN_BOLD, size)
        lines = _wrap_latin(title, draw, tf, W - 160)
        while len(lines) > 4 and size > 36:
            size -= 4
            tf = ImageFont.truetype(LATIN_BOLD, size)
            lines = _wrap_latin(title, draw, tf, W - 160)
        line_h = size + 12
        total_h = len(lines) * line_h
        start_y = (H - total_h) // 2
        for i, ln in enumerate(lines):
            y = start_y + i * line_h
            draw.text((82, y + 2), ln, font=tf, fill=(0, 0, 0, 80))
            draw.text((80, y), ln, font=tf, fill=(255, 255, 255))

    # Footer (tagline + URL)
    tagline = TAGLINES[lang]
    if lang == "ar":
        tagline = get_display(arabic_reshaper.reshape(tagline))
        ar_tag = ImageFont.truetype(AR_FONT, 28)
        latin_tag = ImageFont.truetype(LATIN_REG, 28)
        tw = _measure_mixed(draw, tagline, ar_tag, latin_tag)
        _draw_mixed(draw, W - 80 - tw, H - 90, tagline, ar_tag, latin_tag,
                    (255, 255, 255, 220))
        url_f = ImageFont.truetype(LATIN_REG, 28)
        bbox = draw.textbbox((0, 0), "suuapp.com", font=url_f)
        tw = bbox[2] - bbox[0]
        draw.text((W - 80 - tw, H - 50), "suuapp.com", font=url_f,
                  fill=(255, 255, 255, 200))
    else:
        tag_f = ImageFont.truetype(LATIN_REG, 28)
        draw.text((80, H - 90), tagline, font=tag_f, fill=(255, 255, 255, 220))
        draw.text((80, H - 50), "suuapp.com", font=tag_f, fill=(255, 255, 255, 200))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, "PNG", optimize=True)


# === Yardımcılar ==========================================================

def detect_lang(path: Path) -> str:
    p = str(path)
    if "/blog/en/" in p:
        return "en"
    if "/blog/ar/" in p:
        return "ar"
    if "/blog/ru/" in p:
        return "ru"
    return "tr"


def extract_title(html_path: Path) -> str | None:
    content = html_path.read_text(encoding="utf-8")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", content, re.DOTALL)
    if not m:
        return None
    return re.sub(r"<[^>]+>", "", m.group(1)).strip()


def og_path_for(html_path: Path) -> Path:
    lang = detect_lang(html_path)
    slug = html_path.stem + ".png"
    name = f"{lang}-{slug}" if lang != "tr" else slug
    return OG_DIR / name


def og_url_for(html_path: Path) -> str:
    return f"{BASE_URL}/assets/og/blog/{og_path_for(html_path).name}"


def update_meta_tags(html_path: Path) -> dict:
    """og:image, twitter:image ve Article schema image alanlarını günceller."""
    url = og_url_for(html_path)
    content = html_path.read_text(encoding="utf-8")
    original = content
    changes = {"og": 0, "twitter": 0, "schema": 0}

    content, n = re.subn(
        r'(<meta\s+property="og:image"\s+content=")[^"]*(")',
        rf"\g<1>{url}\g<2>", content,
    )
    changes["og"] = n

    content, n = re.subn(
        r'(<meta\s+name="twitter:image"\s+content=")[^"]*(")',
        rf"\g<1>{url}\g<2>", content,
    )
    changes["twitter"] = n

    # Article schema: "image": "https://..."
    content, n = re.subn(
        r'("image":\s*")https://suuapp\.com/assets/og[^"]*(")',
        rf"\g<1>{url}\g<2>", content,
    )
    changes["schema"] = n

    if content != original:
        html_path.write_text(content, encoding="utf-8")
    return changes


# === CLI ==================================================================

def collect_targets(args) -> list[Path]:
    if args.path:
        p = (ROOT / args.path).resolve()
        if not p.exists():
            sys.exit(f"Dosya bulunamadı: {args.path}")
        return [p]
    return sorted(BLOG_DIR.rglob("*.html"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?",
                    help="Belirli bir blog yazısının yolu (opsiyonel)")
    ap.add_argument("--force", action="store_true",
                    help="Mevcut PNG'leri yeniden üret")
    ap.add_argument("--update-meta", action="store_true",
                    help="Yazının og:image / twitter:image / schema'sını güncelle")
    args = ap.parse_args()

    targets = collect_targets(args)

    stats = {"generated": 0, "skipped": 0, "meta_updated": 0, "errors": []}

    for html in targets:
        rel = html.relative_to(ROOT)
        title = extract_title(html)
        if not title:
            stats["errors"].append(f"{rel}: <h1> bulunamadı")
            continue

        lang = detect_lang(html)
        out = og_path_for(html)

        if out.exists() and not args.force:
            stats["skipped"] += 1
        else:
            try:
                make_og_image(title, out, lang)
                stats["generated"] += 1
                print(f"  ✓ {out.name}")
            except Exception as e:
                stats["errors"].append(f"{rel}: {e}")
                continue

        if args.update_meta:
            try:
                ch = update_meta_tags(html)
                if any(ch.values()):
                    stats["meta_updated"] += 1
                    print(f"    meta güncellendi: og={ch['og']} tw={ch['twitter']} schema={ch['schema']}")
            except Exception as e:
                stats["errors"].append(f"{rel} (meta): {e}")

    print()
    print(f"Üretildi:  {stats['generated']}")
    print(f"Atlandı (zaten var): {stats['skipped']}")
    if args.update_meta:
        print(f"Meta güncellendi: {stats['meta_updated']}")
    if stats["errors"]:
        print(f"\nHatalar ({len(stats['errors'])}):")
        for e in stats["errors"]:
            print(f"  ✗ {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
