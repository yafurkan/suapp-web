#!/usr/bin/env python3
"""
Suu — Hreflang cluster injector

Tüm blog yazılarına bidirectional hreflang etiketleri ekler:
  tr / en / ar / ru / x-default

Mevcut <link rel="alternate" hreflang="..."> etiketlerini siler,
ardından kümeyi yeniden enjekte eder. Self-canonical link'i korur.

Çıktı: Düzenlenen dosya sayısı + kapsam raporu.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_DIR = ROOT / "blog"
BASE = "https://suuapp.com"

# ───────────────────────────────────────────────────────────
# Cluster table — TR slug → (EN, AR, RU)
# AR or RU = None demek o dilde yazı yok demek;
# hreflang etiketi o dil için atlanır.
# ───────────────────────────────────────────────────────────
CLUSTERS: dict[str, dict[str, str | None]] = {
    # TR slug : { en, ar, ru }
    "afrika-su-kuyusu-bagis-programi":     {"en": "africa-water-well-donation-program",  "ar": "barnamaj-tabarru-abar-almae-afriqia", "ru": "programma-pozhertvovanij-kolodtsy-afrika"},
    "aktivite-bazli-su-takibi":            {"en": "activity-based-water-tracking",       "ar": "almae-walnashat-aljasadi",            "ru": "voda-po-aktivnosti"},
    "alkol-sonrasi-hidrasyon":             {"en": "post-alcohol-hydration",              "ar": "tarteeb-baad-alkohol",                "ru": "gidratatsiya-posle-alkogolya"},
    "apple-watch-su-takibi":               {"en": "apple-watch-water-tracking",          "ar": None,                                  "ru": "apple-watch-voda"},
    "cay-hidrasyon":                       {"en": "tea-hydration",                       "ar": "tarteeb-asshay",                      "ru": "chai-i-gidratatsiya"},
    "emzirmede-su-ihtiyaci":               {"en": "hydration-while-breastfeeding",       "ar": "almae-walrida",                       "ru": "voda-i-kormlenie"},
    "enerji-icecegi-kontrolu":             {"en": "energy-drink-control",                "ar": "tahakum-mashroob-attaqa",             "ru": "kontrol-energetikov"},
    "gunde-kac-kahve":                     {"en": "how-many-cups-coffee",                "ar": "kam-fanjan-qahwa",                    "ru": "skolko-kofe-v-den"},
    "gunluk-ne-kadar-su-icmeli":           {"en": "how-much-water-should-i-drink",       "ar": "kam-litr-mae-yawmiyan",               "ru": "skolko-vody-pit-v-den"},
    "hamilelikte-su-ihtiyaci":             {"en": "hydration-during-pregnancy",          "ar": "almae-walhml",                        "ru": "voda-i-beremennost"},
    "hidrasyon-skoru-nedir":               {"en": "hydration-score-explained",           "ar": None,                                  "ru": "otsenka-gidratatsii"},
    "kafein-seker-takibi":                 {"en": "caffeine-sugar-tracking",             "ar": "alkafayin-walsukar",                  "ru": "kofein-i-sahar"},
    "kahve-cay-su-sayar-mi":               {"en": "coffee-tea-hydration",                "ar": "alqahwa-walshay-walmae",              "ru": "kofe-chay-i-voda"},
    "kahveyi-azaltmak":                    {"en": "quit-coffee-guide",                   "ar": "taqlil-alqahwa",                      "ru": "kak-sokratit-kofe"},
    "kilo-ve-su":                          {"en": "water-and-weight-loss",               "ar": "almae-walidara-alwazn",               "ru": "voda-i-pohudenie"},
    "meyve-suyu-vs-su":                    {"en": "juice-vs-water",                      "ar": "aaseer-am-mae",                       "ru": "sok-ili-voda"},
    "sabah-su-icmenin-faydalari":          {"en": "morning-water-benefits",              "ar": "fawaid-shurb-almae-sabahan",          "ru": "voda-utrom"},
    "sesli-komutla-su-ekleme":             {"en": "siri-water-tracking",                 "ar": None,                                  "ru": "siri-voda"},
    "spor-ve-hidrasyon":                   {"en": "hydration-and-exercise",              "ar": "arriyada-waltartib",                  "ru": "sport-i-gidratatsiya"},
    "su-icme-aliskanlik":                  {"en": "water-drinking-habits",               "ar": "adat-shurb-almae",                    "ru": "privychka-pit-vodu"},
    "su-icme-lig-sistemi":                 {"en": "water-challenge-with-friends",        "ar": "nadhari-almae-maa-asdiqa",            "ru": "vodnyi-challenge-s-druzyami"},
    "su-icmenin-faydalari":                {"en": "benefits-of-drinking-water",          "ar": "fawaid-shurb-almae",                  "ru": "polza-pitia-vody"},
    "su-takip-uygulamasi-neden-kullanmaliyim": {"en": "best-water-tracking-app",         "ar": "afdal-tatbiq-mae",                    "ru": "luchshee-prilozhenie-dlya-vody"},
    "su-ve-bobrek-sagligi":                {"en": "water-and-kidney-health",             "ar": "almae-wasihhat-alkulaa",              "ru": "voda-i-zdorove-pochek"},
    "su-ve-cilt-sagligi":                  {"en": "water-and-skin-health",               "ar": "almae-walsihha-aljildiyya",           "ru": "voda-i-zdorove-kozhi"},
    "su-ve-uyku-kalitesi":                 {"en": "water-and-sleep",                     "ar": "almae-wannawm",                       "ru": "voda-i-son"},
    "susuzluk-belirtileri":                {"en": "signs-of-dehydration",                "ar": "alamat-aljafaf",                      "ru": "priznaki-obezvozhivaniya"},
    "suu-evcil-hayvan-mini-oyunlar":       {"en": "pet-companion-mini-games",            "ar": "hayawan-aleef-aleab-mini",            "ru": "domashnij-pitomec-mini-igry"},
}

# EN-only / RU-only — TR'de eşi olmayan yazılar (gamification gibi)
# Bu yazılarda x-default = EN, ve tr atlanır.
EXTRA = {
    # en_slug : { ar, ru }
    "water-tracking-gamification": {"ar": None, "ru": "geymifikatsiya-vody"},
}

# Kanibal kabul edilen TR yazıları — bunlar 301-like JS redirect olacak.
# Hreflang inject'ten ÇIKAR.
CANNIBAL_TR = {
    "en-iyi-su-takip-uygulamasi",       # → su-takip-uygulamasi-neden-kullanmaliyim
    "su-icince-kilo-verilir-mi",        # → kilo-ve-su
    "yazin-ne-kadar-su-icmeli",         # → gunluk-ne-kadar-su-icmeli (yaz alt-niyeti)
    "yeterince-su-icip-icmedigini-anla", # → susuzluk-belirtileri
}


def url_for(lang: str, slug: str) -> str:
    if lang == "tr":
        return f"{BASE}/blog/{slug}.html"
    return f"{BASE}/blog/{lang}/{slug}.html"


def build_cluster(tr_slug: str | None, en_slug: str, ar_slug: str | None, ru_slug: str | None) -> list[tuple[str, str]]:
    """Returns [(hreflang, href)] pairs to inject."""
    pairs: list[tuple[str, str]] = []
    if tr_slug:
        pairs.append(("tr", url_for("tr", tr_slug)))
    pairs.append(("en", url_for("en", en_slug)))
    if ar_slug:
        pairs.append(("ar", url_for("ar", ar_slug)))
    if ru_slug:
        pairs.append(("ru", url_for("ru", ru_slug)))
    # x-default: TR yoksa EN'i koy; varsa TR'yi göster
    default = pairs[0][1]
    pairs.append(("x-default", default))
    return pairs


RE_HREFLANG = re.compile(
    r'\s*<link\s+rel=["\']alternate["\']\s+hreflang=["\'][^"\']+["\']\s+href=["\'][^"\']+["\']\s*/?>\s*\n?',
    re.IGNORECASE,
)
RE_HREFLANG_FLIP = re.compile(
    r'\s*<link\s+hreflang=["\'][^"\']+["\']\s+rel=["\']alternate["\']\s+href=["\'][^"\']+["\']\s*/?>\s*\n?',
    re.IGNORECASE,
)
RE_CANONICAL = re.compile(
    r'(<link\s+rel=["\']canonical["\']\s+href=["\'][^"\']+["\']\s*/?>)',
    re.IGNORECASE,
)


def render_block(pairs: list[tuple[str, str]]) -> str:
    lines = ["", "    <!-- Hreflang cluster (auto-injected) -->"]
    for lang, href in pairs:
        lines.append(f'    <link rel="alternate" hreflang="{lang}" href="{href}">')
    return "\n".join(lines) + "\n"


def inject(html: str, pairs: list[tuple[str, str]]) -> tuple[str, bool]:
    """Remove all existing hreflang links, insert new block after canonical."""
    new_html = RE_HREFLANG.sub("\n", html)
    new_html = RE_HREFLANG_FLIP.sub("\n", new_html)
    # collapse 3+ newlines
    new_html = re.sub(r"\n{3,}", "\n\n", new_html)
    block = render_block(pairs)

    if RE_CANONICAL.search(new_html):
        new_html = RE_CANONICAL.sub(r"\1" + block, new_html, count=1)
    else:
        # canonical yoksa <head> sonuna ekle
        new_html = new_html.replace("</head>", block + "</head>", 1)

    return new_html, new_html != html


def process_file(path: Path, pairs: list[tuple[str, str]]) -> bool:
    html = path.read_text(encoding="utf-8")
    new_html, changed = inject(html, pairs)
    if changed:
        path.write_text(new_html, encoding="utf-8")
    return changed


def main() -> int:
    edited = 0
    skipped = 0
    cannibal_seen = []

    for tr_slug, langs in CLUSTERS.items():
        en_slug = langs["en"]
        ar_slug = langs["ar"]
        ru_slug = langs["ru"]
        pairs = build_cluster(tr_slug, en_slug, ar_slug, ru_slug)

        # TR
        tr_path = BLOG_DIR / f"{tr_slug}.html"
        if tr_path.exists():
            if process_file(tr_path, pairs):
                edited += 1
                print(f"  ✓ {tr_path.relative_to(ROOT)}")
            else:
                skipped += 1
        else:
            print(f"  ⚠ MISSING TR: {tr_path}")

        # EN
        en_path = BLOG_DIR / "en" / f"{en_slug}.html"
        if en_path.exists():
            if process_file(en_path, pairs):
                edited += 1
                print(f"  ✓ {en_path.relative_to(ROOT)}")
            else:
                skipped += 1
        else:
            print(f"  ⚠ MISSING EN: {en_path}")

        # AR
        if ar_slug:
            ar_path = BLOG_DIR / "ar" / f"{ar_slug}.html"
            if ar_path.exists():
                if process_file(ar_path, pairs):
                    edited += 1
                    print(f"  ✓ {ar_path.relative_to(ROOT)}")
                else:
                    skipped += 1
            else:
                print(f"  ⚠ MISSING AR: {ar_path}")

        # RU
        if ru_slug:
            ru_path = BLOG_DIR / "ru" / f"{ru_slug}.html"
            if ru_path.exists():
                if process_file(ru_path, pairs):
                    edited += 1
                    print(f"  ✓ {ru_path.relative_to(ROOT)}")
                else:
                    skipped += 1
            else:
                print(f"  ⚠ MISSING RU: {ru_path}")

    # EXTRA (TR'siz, EN-only kümeler)
    for en_slug, langs in EXTRA.items():
        ar_slug = langs["ar"]
        ru_slug = langs["ru"]
        pairs = build_cluster(None, en_slug, ar_slug, ru_slug)
        en_path = BLOG_DIR / "en" / f"{en_slug}.html"
        if en_path.exists():
            if process_file(en_path, pairs):
                edited += 1
                print(f"  ✓ {en_path.relative_to(ROOT)}")
        if ru_slug:
            ru_path = BLOG_DIR / "ru" / f"{ru_slug}.html"
            if ru_path.exists():
                if process_file(ru_path, pairs):
                    edited += 1
                    print(f"  ✓ {ru_path.relative_to(ROOT)}")

    # Kanibal TR yazılar — kontrol et, varlığını rapor et
    for slug in CANNIBAL_TR:
        p = BLOG_DIR / f"{slug}.html"
        if p.exists():
            cannibal_seen.append(p.relative_to(ROOT))

    print()
    print(f"=== Özet ===")
    print(f"  Düzenlenen dosya : {edited}")
    print(f"  Değişmeyen       : {skipped}")
    print(f"  Kanibal (sonra redirect olacak): {len(cannibal_seen)}")
    for c in cannibal_seen:
        print(f"     {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
