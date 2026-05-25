#!/usr/bin/env python3
"""
Sitemap rebuilder — Suu.

Yapar:
  1. Mevcut sitemap.xml'i parse eder.
  2. Kanibal kabul edilen URL'leri çıkarır.
  3. Her blog URL'i için hreflang annotation'ı ekler/günceller
     (inject-hreflang.py'deki CLUSTERS ile aynı).
  4. lastmod'u bugüne çeker (zorlanmaz; sadece kayıp olanlara).
  5. Çıktı: temizlenmiş + zenginleştirilmiş sitemap.xml

Notlar:
  - <changefreq> ve <priority> Google'da artık etkisiz ama tutmakta sakınca yok.
  - image:image blokları korunur.
  - llms.txt zaten sitemap'te değildi (robots.txt'de referans) — değişmedi.
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://suuapp.com"
TODAY = datetime.date.today().isoformat()

# inject-hreflang.py ile aynı küme
CLUSTERS = {
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

EXTRA = {
    "water-tracking-gamification": {"ar": None, "ru": "geymifikatsiya-vody"},
}

# Sitemap'ten ÇIKARILACAK URL'ler (kanibal blog yazıları)
# Not: hosgeldiniz-en/ar/ru.html SİTEMAP'TE KALIR — bunlar gerçek
# multi-lang landing page'ler, self-canonical ve indekslenmeli.
EXCLUDE_URLS = {
    f"{BASE}/blog/en-iyi-su-takip-uygulamasi.html",
    f"{BASE}/blog/su-icince-kilo-verilir-mi.html",
    f"{BASE}/blog/yazin-ne-kadar-su-icmeli.html",
    f"{BASE}/blog/yeterince-su-icip-icmedigini-anla.html",
    f"{BASE}/makale.html",
}


def url_for(lang: str, slug: str) -> str:
    if lang == "tr":
        return f"{BASE}/blog/{slug}.html"
    return f"{BASE}/blog/{lang}/{slug}.html"


def build_cluster(tr_slug: str | None, en_slug: str, ar_slug: str | None, ru_slug: str | None) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if tr_slug:
        pairs.append(("tr", url_for("tr", tr_slug)))
    pairs.append(("en", url_for("en", en_slug)))
    if ar_slug:
        pairs.append(("ar", url_for("ar", ar_slug)))
    if ru_slug:
        pairs.append(("ru", url_for("ru", ru_slug)))
    default = pairs[0][1]
    pairs.append(("x-default", default))
    return pairs


# loc → hreflang cluster lookup
URL_CLUSTER: dict[str, list[tuple[str, str]]] = {}
for tr_slug, langs in CLUSTERS.items():
    pairs = build_cluster(tr_slug, langs["en"], langs["ar"], langs["ru"])
    URL_CLUSTER[url_for("tr", tr_slug)] = pairs
    URL_CLUSTER[url_for("en", langs["en"])] = pairs
    if langs["ar"]:
        URL_CLUSTER[url_for("ar", langs["ar"])] = pairs
    if langs["ru"]:
        URL_CLUSTER[url_for("ru", langs["ru"])] = pairs

for en_slug, langs in EXTRA.items():
    pairs = build_cluster(None, en_slug, langs["ar"], langs["ru"])
    URL_CLUSTER[url_for("en", en_slug)] = pairs
    if langs["ru"]:
        URL_CLUSTER[url_for("ru", langs["ru"])] = pairs


# ───────────────────────────────────────────────────────────
# Sitemap parse + rewrite (regex-based, namespace'leri korur)
# ───────────────────────────────────────────────────────────
RE_URL_BLOCK = re.compile(r"<url>(.*?)</url>", re.DOTALL)
RE_LOC = re.compile(r"<loc>([^<]+)</loc>")
RE_HREFLANG_LINE = re.compile(
    r'\s*<xhtml:link\s+rel="alternate"\s+hreflang="[^"]+"\s+href="[^"]+"\s*/>\s*\n',
)
RE_LASTMOD = re.compile(r"<lastmod>[^<]+</lastmod>")


def rewrite_block(block_inner: str) -> str | None:
    """Returns None if the URL should be excluded; else returns rewritten block content."""
    m = RE_LOC.search(block_inner)
    if not m:
        return block_inner
    loc = m.group(1).strip()

    if loc in EXCLUDE_URLS:
        return None

    # lastmod: kanonik blog URL'lerinde TODAY ile değiştir;
    # statik sayfalarda olduğu gibi bırak.
    new_block = block_inner
    if loc in URL_CLUSTER:
        if RE_LASTMOD.search(new_block):
            new_block = RE_LASTMOD.sub(f"<lastmod>{TODAY}</lastmod>", new_block, count=1)
        else:
            new_block = new_block.replace(
                f"<loc>{loc}</loc>",
                f"<loc>{loc}</loc>\n        <lastmod>{TODAY}</lastmod>",
                1,
            )

    # Mevcut xhtml:link satırlarını sil
    new_block = RE_HREFLANG_LINE.sub("\n", new_block)

    # Eğer bu loc için bir cluster varsa, hreflang'leri ekle
    if loc in URL_CLUSTER:
        pairs = URL_CLUSTER[loc]
        cluster_xml = []
        for lang, href in pairs:
            cluster_xml.append(
                f'        <xhtml:link rel="alternate" hreflang="{lang}" href="{href}" />'
            )
        cluster_str = "\n" + "\n".join(cluster_xml) + "\n"
        # priority'den sonra ekle; yoksa loc'tan sonra
        if "<priority>" in new_block:
            new_block = re.sub(
                r"(</priority>)",
                r"\1" + cluster_str,
                new_block,
                count=1,
            )
        elif "</lastmod>" in new_block:
            new_block = re.sub(
                r"(</lastmod>)",
                r"\1" + cluster_str,
                new_block,
                count=1,
            )

    # Çoklu boş satırları temizle
    new_block = re.sub(r"\n{3,}", "\n\n", new_block)
    return new_block


def main() -> int:
    sitemap = SITEMAP.read_text(encoding="utf-8")

    excluded = 0
    rewritten = 0
    new_parts: list[str] = []
    pos = 0
    for m in RE_URL_BLOCK.finditer(sitemap):
        new_parts.append(sitemap[pos : m.start()])
        block_inner = m.group(1)
        result = rewrite_block(block_inner)
        if result is None:
            excluded += 1
        else:
            if result != block_inner:
                rewritten += 1
            new_parts.append(f"<url>{result}</url>")
        pos = m.end()
    new_parts.append(sitemap[pos:])

    new_sitemap = "".join(new_parts)
    # Bayat boş <url>...</url> arası newline temizliği
    new_sitemap = re.sub(r"\n{3,}", "\n\n", new_sitemap)

    SITEMAP.write_text(new_sitemap, encoding="utf-8")

    # Stats
    url_count = new_sitemap.count("<url>")
    print(f"Sitemap rebuilt — {SITEMAP.relative_to(ROOT)}")
    print(f"  Toplam URL : {url_count}")
    print(f"  Çıkarılan  : {excluded}")
    print(f"  Yeniden yazılan blok: {rewritten}")
    print(f"  lastmod (cluster) : {TODAY}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
