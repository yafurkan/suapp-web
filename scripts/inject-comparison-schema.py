#!/usr/bin/env python3
"""
Suu — Karşılaştırma ve derleme sayfalarına ItemList şeması

Bu sayfalar ("Suu vs X", "en iyi X uygulaması") AI alıntısı ve zengin sonuç
kazanma ihtimali en yüksek sayfalar — ama hiçbirinde ItemList yoktu.

POLİTİKA NOTU: Suu'nun kendi sitesinde kendi ürününe Review/AggregateRating
basmak Google'ın "self-serving review" kuralına takılır. Onun yerine Suu,
ana sayfadaki mağaza kaynaklı düğüme @id ile bağlanır
(https://suuapp.com/#suuapp-ios) — puan oradan miras alınır, yeni bir
öz-değerlendirme üretilmez. Rakipler için hiç puan basılmaz.

Kullanım:
    python3 scripts/inject-comparison-schema.py            # önizleme
    python3 scripts/inject-comparison-schema.py --apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"
SUU_ID = f"{BASE}/#suuapp-ios"

MARKER = "<!-- ItemList schema (auto-injected: scripts/inject-comparison-schema.py) -->"

# Rakip uygulama künyeleri — sadece kimlik, puan YOK
APPS = {
    "Suu":           {"os": "iOS, Android", "id": SUU_ID},
    "MyFitnessPal":  {"os": "iOS, Android", "url": "https://www.myfitnesspal.com/"},
    "Yazio":         {"os": "iOS, Android", "url": "https://www.yazio.com/"},
    "Lifesum":       {"os": "iOS, Android", "url": "https://lifesum.com/"},
    "Cronometer":    {"os": "iOS, Android", "url": "https://cronometer.com/"},
    "WaterMinder":   {"os": "iOS, Android", "url": "https://waterminder.com/"},
    "Hydro Coach":   {"os": "Android",      "url": "https://hydrocoach.app/"},
    "Plant Nanny":   {"os": "iOS, Android", "url": "https://plantnanny.app/"},
}

# sayfa → (dil, liste adı, sıralı uygulamalar)
PAGES: dict[str, tuple[str, str, list[str]]] = {}


def _add(pathmap: dict[str, str], name: dict[str, str], apps: list[str]) -> None:
    for lang, rel in pathmap.items():
        PAGES[rel] = (lang, name[lang], apps)


# ── Kafa kafaya karşılaştırmalar ─────────────────────────────
_add(
    {"tr": "blog/suu-vs-myfitnesspal.html", "en": "blog/en/suu-vs-myfitnesspal.html",
     "ar": "blog/ar/suu-vs-myfitnesspal.html", "ru": "blog/ru/suu-vs-myfitnesspal.html"},
    {"tr": "Suu ve MyFitnessPal karşılaştırması",
     "en": "Suu vs MyFitnessPal comparison",
     "ar": "مقارنة بين Suu و MyFitnessPal",
     "ru": "Сравнение Suu и MyFitnessPal"},
    ["Suu", "MyFitnessPal"],
)
_add(
    {"tr": "blog/suu-vs-yazio.html", "en": "blog/en/suu-vs-yazio.html",
     "ar": "blog/ar/suu-vs-yazio.html", "ru": "blog/ru/suu-vs-yazio.html"},
    {"tr": "Suu ve Yazio karşılaştırması",
     "en": "Suu vs Yazio comparison",
     "ar": "مقارنة بين Suu و Yazio",
     "ru": "Сравнение Suu и Yazio"},
    ["Suu", "Yazio"],
)

# ── Derlemeler (sıralı liste — 1. sıra Suu) ──────────────────
_add(
    {"tr": "blog/en-iyi-kalori-uygulamasi.html", "en": "blog/en/best-calorie-counting-app.html",
     "ar": "blog/ar/afdal-tatbiq-hisab-suerat.html",
     "ru": "blog/ru/luchshee-prilozhenie-podscheta-kalorij.html"},
    {"tr": "En iyi kalori sayma uygulamaları",
     "en": "Best calorie counting apps",
     "ar": "أفضل تطبيقات حساب السعرات",
     "ru": "Лучшие приложения для подсчёта калорий"},
    ["Suu", "MyFitnessPal", "Yazio", "Lifesum", "Cronometer"],
)
_add(
    {"tr": "blog/su-takip-uygulamasi-neden-kullanmaliyim.html",
     "en": "blog/en/best-water-tracking-app.html",
     "ar": "blog/ar/afdal-tatbiq-mae.html",
     "ru": "blog/ru/luchshee-prilozhenie-dlya-vody.html"},
    {"tr": "En iyi su takip uygulamaları",
     "en": "Best water tracking apps",
     "ar": "أفضل تطبيقات تتبع الماء",
     "ru": "Лучшие приложения для отслеживания воды"},
    ["Suu", "WaterMinder", "Hydro Coach", "Plant Nanny"],
)


def app_node(name: str) -> dict:
    meta = APPS[name]
    if "id" in meta:
        # Suu — ana sayfadaki mağaza kaynaklı düğüme bağlan, yeni puan üretme
        return {"@type": "SoftwareApplication", "@id": meta["id"], "name": name}
    return {
        "@type": "SoftwareApplication",
        "name": name,
        "applicationCategory": "HealthApplication",
        "operatingSystem": meta["os"],
        "url": meta["url"],
    }


def build(page_url: str, lang: str, list_name: str, apps: list[str]) -> str:
    doc = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{page_url}#itemlist",
        "name": list_name,
        "inLanguage": lang,
        "itemListOrder": "https://schema.org/ItemListOrderDescending" if len(apps) > 2 else "https://schema.org/ItemListUnordered",
        "numberOfItems": len(apps),
        "itemListElement": [
            {"@type": "ListItem", "position": i, "item": app_node(name)}
            for i, name in enumerate(apps, start=1)
        ],
    }
    body = json.dumps(doc, ensure_ascii=False, indent=2)
    body = body.replace("<", "\\u003c").replace(">", "\\u003e")
    return f'    {MARKER}\n    <script type="application/ld+json">\n{body}\n    </script>\n'


RE_EXISTING = re.compile(
    r'[ \t]*' + re.escape(MARKER) + r'\s*<script type="application/ld\+json">.*?</script>[ \t]*\n?',
    re.DOTALL,
)


def main() -> int:
    apply = "--apply" in sys.argv
    changed, missing, skipped = [], [], 0

    for rel, (lang, list_name, apps) in sorted(PAGES.items()):
        path = ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue

        html = path.read_text(encoding="utf-8")
        html = RE_EXISTING.sub("", html)          # idempotent — eskiyi çıkar

        page_url = f"{BASE}/{rel}"
        block = build(page_url, lang, list_name, apps)

        if "</head>" not in html:
            missing.append(f"{rel} (</head> yok)")
            continue

        new = html.replace("</head>", block + "</head>", 1)
        original = path.read_text(encoding="utf-8")
        if new == original:
            skipped += 1
            continue

        changed.append(f"{rel}  ({len(apps)} uygulama, {lang})")
        if apply:
            path.write_text(new, encoding="utf-8")

    for c in changed:
        print(f"  ✓ {c}")
    for m in missing:
        print(f"  ⚠ bulunamadı: {m}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(changed)} sayfa güncellenecek, {skipped} zaten güncel — {mode}")
    if not apply and changed:
        print("Uygulamak için: python3 scripts/inject-comparison-schema.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
