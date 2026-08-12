#!/usr/bin/env python3
"""
Suu — Ana sayfa üreticisi (7 dil, tek şablon)

Girdi:
    content/home/_template.html.j2   ortak şablon
    content/home/<lang>.json         dile özel metinler
    content/suu-facts.json           paylaşılan gerçekler (fiyat, link, sayı)

Çıktı:
    tr → index.html
    xx → hosgeldiniz-xx.html

Neden üretici: aynı sayfayı 7 dilde elle sürdürmek imkânsız. Bir bölüm
değişince şablon bir kez güncellenir, 7 dosya yeniden üretilir. Hreflang
kümesi ve JSON-LD de buradan çıkar — sapma olamaz.

Kullanım:
    python3 scripts/build-homepages.py            # önizleme (fark özeti)
    python3 scripts/build-homepages.py --apply
    python3 scripts/build-homepages.py --apply --lang tr,en
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print("HATA: jinja2 gerekli.  pip3 install jinja2", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "content" / "home"
FACTS = ROOT / "content" / "suu-facts.json"
BASE = "https://suuapp.com"

# lang → (çıktı dosyası, locale, yön)
TARGETS: dict[str, tuple[str, str, str]] = {
    "tr": ("index.html",            "tr_TR", "ltr"),
    "en": ("hosgeldiniz-en.html",   "en_US", "ltr"),
    "ar": ("hosgeldiniz-ar.html",   "ar_SA", "rtl"),
    "ru": ("hosgeldiniz-ru.html",   "ru_RU", "ltr"),
    "de": ("hosgeldiniz-de.html",   "de_DE", "ltr"),
    "it": ("hosgeldiniz-it.html",   "it_IT", "ltr"),
    "hi": ("hosgeldiniz-hi.html",   "hi_IN", "ltr"),
}


def page_url(lang: str) -> str:
    return f"{BASE}/" if lang == "tr" else f"{BASE}/{TARGETS[lang][0]}"


def build_jsonld(lang: str, data: dict, facts: dict) -> str:
    """Ana sayfanın @graph'ı. Sayılar suu-facts.json'dan, metinler dil dosyasından."""
    n = facts["numbers"]
    links = facts["links"]
    founder = facts["entities"]["founder"]
    langs = [l["code"] for l in facts["languages"]["supported"]]
    plans = {p["id"]: p for p in facts["pricing"]["plans"]}

    def app_node(os_name: str, platform: str, download: str, rating: str, features: list[str]) -> dict:
        return {
            "@type": ["MobileApplication", "HealthAndFitnessApplication"],
            "@id": f"{BASE}/#suuapp-{platform}",
            "name": facts["identity"]["store_title"].get(lang, facts["identity"]["store_title"]["en"]),
            "alternateName": "Suu",
            "operatingSystem": os_name,
            "applicationCategory": "HealthApplication",
            "url": page_url(lang),
            "downloadUrl": download,
            "installUrl": download,
            "inLanguage": langs,
            "author": {"@id": f"{BASE}/#furkan"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "screenshot": f"{BASE}/assets/screenshots/{platform}/{lang}/ana-ekran.webp",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": rating,
                "bestRating": "5",
                "ratingCount": str(n["rating_count"]),
            },
            "offers": [
                {"@type": "Offer", "name": data["pricing"]["plans"][0]["name"], "price": "0", "priceCurrency": facts["pricing"]["currency"]},
                {"@type": "Offer", "name": data["pricing"]["plans"][1]["name"], "price": str(plans["yearly"]["price_try"]), "priceCurrency": "TRY"},
                {"@type": "Offer", "name": "Premium", "price": str(plans["monthly"]["price_try"]), "priceCurrency": "TRY"},
                {"@type": "Offer", "name": "Family", "price": str(plans["family"]["price_try"]), "priceCurrency": "TRY"},
            ],
            "featureList": features,
            "additionalProperty": [
                {"@type": "PropertyValue", "name": "beverages", "value": str(n["beverages"])},
                {"@type": "PropertyValue", "name": "sportActivities", "value": str(n["sport_activities"])},
                {"@type": "PropertyValue", "name": "languages", "value": str(facts["languages"]["count"])},
                {"@type": "PropertyValue", "name": "freeAiAnalysesPerDay", "value": str(n["free_ai_analyses_per_day"])},
                {"@type": "PropertyValue", "name": "freeTrialDays", "value": str(n["free_trial_days"])},
                {"@type": "PropertyValue", "name": "appleWatch", "value": "coming soon"},
            ],
        }

    graph = [
        {
            "@type": "Organization",
            "@id": f"{BASE}/#organization",
            "name": "Suu",
            "url": BASE,
            "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/favicon-512.png", "width": 512, "height": 512},
            "email": links["support_email"],
            "founder": {"@id": f"{BASE}/#furkan"},
            "foundingLocation": {"@type": "Place", "name": "İstanbul, Türkiye"},
            "areaServed": ["TR", "SA", "AE", "KW", "QA", "RU", "DE", "IT", "IN", "US", "GB"],
            "sameAs": founder["sameAs"] + [links["app_store"], links["google_play"]],
        },
        {
            "@type": "Person",
            "@id": f"{BASE}/#furkan",
            "name": founder["name"],
            "birthDate": founder["birth_date"],
            "jobTitle": founder["role"],
            "url": founder["profile_page"],
            "homeLocation": {"@type": "Place", "name": founder["location"]},
            "knowsAbout": founder["expertise"],
            "sameAs": founder["sameAs"],
        },
        # Blog yazılarında yazar olarak geçen ikinci kişi — @id'nin çözülebilmesi
        # için kanonik düğümü burada tanımlı olmalı (inject-entity-ids.py #nisanur
        # referansı basıyor, karşılığı olmadan entity askıda kalırdı).
        {
            "@type": "Person",
            "@id": f"{BASE}/#nisanur",
            "name": "Nisanur Büyükbaş",
            "jobTitle": "Head of Growth & Marketing",
            "worksFor": {"@id": f"{BASE}/#organization"},
        },
        {
            "@type": "WebSite",
            "@id": f"{BASE}/#website",
            "url": BASE,
            "name": "Suu",
            "description": data["meta"]["description"],
            "inLanguage": lang,
            "publisher": {"@id": f"{BASE}/#organization"},
        },
        app_node("iOS 15.0+", "ios", links["app_store"], str(n["rating_app_store"]), data["schema"]["features_ios"]),
        app_node("Android 8.0+", "android", links["google_play"], str(n["rating_google_play"]), data["schema"]["features_android"]),
        {
            "@type": "WebPage",
            "@id": f"{page_url(lang)}#webpage",
            "url": page_url(lang),
            "name": data["meta"]["title"],
            "isPartOf": {"@id": f"{BASE}/#website"},
            "about": {"@id": f"{BASE}/#suuapp-ios"},
            "inLanguage": lang,
            "primaryImageOfPage": {"@type": "ImageObject", "url": f"{BASE}/assets/og-image.png"},
            "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".hero__title", ".hero__lead", ".answer-box"]},
        },
        {
            "@type": "FAQPage",
            "@id": f"{page_url(lang)}#faq",
            "about": {"@id": f"{BASE}/#suuapp-ios"},
            "inLanguage": lang,
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in data["faq"]["items"]
            ],
        },
    ]

    doc = {"@context": "https://schema.org", "@graph": graph}
    out = json.dumps(doc, ensure_ascii=False, indent=2)
    # <script> içine gömülüyor: HTML kaçışı yerine JSON kaçışı kullan —
    # aksi hâlde "</script>" dizisi bloğu erken kapatabilir.
    return out.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def available_langs() -> list[str]:
    """Yalnızca içerik dosyası olan diller. hreflang'in 404'e işaret etmesini
    engeller — yeni dil eklendiğinde küme kendiliğinden genişler."""
    return [code for code in TARGETS if (HOME / f"{code}.json").exists()]


def hreflang_cluster() -> list[dict]:
    return [{"code": code, "href": page_url(code)} for code in available_langs()]


def main() -> int:
    apply = "--apply" in sys.argv
    only = None
    if "--lang" in sys.argv:
        only = {c.strip() for c in sys.argv[sys.argv.index("--lang") + 1].split(",")}

    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    env = Environment(
        loader=FileSystemLoader(str(HOME)),
        undefined=StrictUndefined,        # eksik çeviri sessizce boş geçmesin
        trim_blocks=False,
        lstrip_blocks=False,
        autoescape=True,
    )
    template = env.get_template("_template.html.j2")

    built, skipped, changed = [], [], []

    for lang, (outfile, locale, direction) in TARGETS.items():
        if only and lang not in only:
            continue

        src = HOME / f"{lang}.json"
        if not src.exists():
            skipped.append(f"{lang} (content/home/{lang}.json yok)")
            continue

        data = json.loads(src.read_text(encoding="utf-8"))

        html = template.render(
            lang=lang,
            dir=direction,
            locale=locale,
            url=page_url(lang),
            og_locale_alternates=[TARGETS[c][1] for c in available_langs() if c != lang],
            hreflang=hreflang_cluster(),
            facts=facts,
            jsonld=build_jsonld(lang, data, facts),
            **data,
        )

        target = ROOT / outfile
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        if old != html:
            changed.append(outfile)
            if apply:
                target.write_text(html, encoding="utf-8")
        built.append(f"{lang} → {outfile} ({len(html) // 1024} KB)")

    for b in built:
        print(f"  {b}")
    for s in skipped:
        print(f"  atlandı: {s}")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(built)} sayfa üretildi, {len(changed)} tanesi değişti — {mode}")
    if changed:
        print("  değişen:", ", ".join(changed))
    if not apply and changed:
        print("\nUygulamak için: python3 scripts/build-homepages.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
