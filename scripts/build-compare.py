#!/usr/bin/env python3
"""
Suu — Karşılaştırma ve kategori cevap sayfası üreticisi

Bunlar GEO/AEO'nun en yüksek getirili sayfaları: yapay zekâya "hangi kalori
uygulamasını kullanayım" diye sorulduğunda alıntılanan içerik türü.

Girdi:
    content/compare/<topic>.json        konu başına tüm diller
    content/compare/_template.html.j2   AEO formatlı şablon
    content/suu-facts.json              paylaşılan gerçekler

Çıktı:
    blog/<slug>.html          (varsayılan dil)
    blog/<lang>/<slug>.html   (diğer diller)

Şablon zorunlu AEO formatını dayatır:
    cevap-önce kutusu → şeffaflık notu → karşılaştırma tablosu →
    analiz → karar → CTA → SSS → kaynaklar → ilgili yazılar

Üretim sonrası kayıt defterine eklemeyi unutmayın:
    content/page-registry.json → "blog" bölümü
    ardından build-i18n-map.py, inject-hreflang.py, update-sitemap.py

Kullanım:
    python3 scripts/build-compare.py                    # önizleme
    python3 scripts/build-compare.py --apply
    python3 scripts/build-compare.py --apply --topic suu-vs-cal-ai
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from _langs import locales, ui_strings

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    raise SystemExit("HATA: jinja2 gerekli.  pip3 install jinja2")

ROOT = Path(__file__).resolve().parents[1]
COMPARE = ROOT / "content" / "compare"
FACTS = ROOT / "content" / "suu-facts.json"
REGISTRY = ROOT / "content" / "page-registry.json"
BASE = "https://suuapp.com"
DEFAULT = "tr"

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
LOCALES = locales()
UI = ui_strings()


def rel_path(lang: str, slug: str) -> str:
    return f"blog/{slug}.html" if lang == DEFAULT else f"blog/{lang}/{slug}.html"


def abs_url(lang: str, slug: str) -> str:
    return f"{BASE}/{rel_path(lang, slug)}"


RE_TAGS = re.compile(r"<[^>]+>")


def plain(text: str) -> str:
    """Şema alanları düz metin ister; gövde metinleri <strong> vb. içerebiliyor."""
    return html.unescape(RE_TAGS.sub("", text)).strip()


def build_jsonld(lang: str, topic: str, data: dict, page: dict, facts: dict, url: str) -> str:
    founder = facts["entities"]["founder"]
    # Tablo iki biçimden birinde olabilir:
    #   klasik  → Suu ilk sütun + competitors listesi
    #   genel   → columns listesi (rakip-vs-rakip; Suu sonda olabilir)
    names = page["table"].get("columns")
    if not names:
        names = ["Suu"] + page["table"]["competitors"]
    apps = []
    for name in names:
        if name == "Suu":
            apps.append({"@type": "SoftwareApplication", "@id": f"{BASE}/#suuapp-ios", "name": "Suu"})
        else:
            apps.append({"@type": "SoftwareApplication", "name": name,
                         "applicationCategory": "HealthApplication"})

    # ItemList iki kaynaktan gelebilir. "ranked" bloğu varsa sayfa gerçek bir
    # SIRALAMA sunuyor (1. en iyi) ve şema onu yansıtmalı — tablodan üretilen
    # liste yalnızca sütun sırası, sıralama değil. İkisini birden basmak tek
    # sayfada çelişen iki ItemList demek olurdu.
    ranked = page.get("ranked")
    if ranked:
        item_list = {
            "@type": "ItemList",
            "@id": f"{url}#itemlist",
            "name": ranked["head"],
            "inLanguage": lang,
            "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "numberOfItems": len(ranked["items"]),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": it["name"],
                 "item": ({"@type": "SoftwareApplication", "@id": f"{BASE}/#suuapp-ios",
                           "name": "Suu", "description": plain(it["body"])}
                          if it["name"] == "Suu" else
                          {"@type": "SoftwareApplication", "name": it["name"],
                           "applicationCategory": "HealthApplication",
                           "description": plain(it["body"])})}
                for i, it in enumerate(ranked["items"], 1)
            ],
        }
    else:
        item_list = {
            "@type": "ItemList",
            "@id": f"{url}#itemlist",
            "name": page["table"]["head"],
            "inLanguage": lang,
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": len(apps),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "item": a} for i, a in enumerate(apps, 1)
            ],
        }

    graph = [
        # Organization ve Person düğümleri sayfada TAM olarak bulunmalı —
        # Article için publisher.name ve publisher.logo zorunludur, çıplak
        # {"@id": ...} referansı başka sayfadaki düğümü çözmez.
        {
            "@type": "Organization",
            "@id": f"{BASE}/#organization",
            "name": "Suu",
            "url": BASE,
            "logo": {"@type": "ImageObject", "url": f"{BASE}/assets/favicon-512.png"},
        },
        {
            "@type": "Person",
            "@id": f"{BASE}/#furkan",
            "name": founder["name"],
            "url": founder["profile_page"],
            "jobTitle": founder["role"],
            "worksFor": {"@id": f"{BASE}/#organization"},
            "sameAs": founder["sameAs"],
        },
        {
            "@type": "Article",
            "@id": f"{url}#article",
            "headline": page["h1"],
            "description": page["meta"]["description"],
            "image": f"{BASE}/assets/og-image.png",
            "datePublished": data["published"],
            # Tazelik sinyali: elle yazılmış sayfayı boru hattına taşımak veya
            # rakip tablosunu güncellemek yayın tarihini değiştirmez, ama
            # dateModified'ı değiştirmelidir. Yoksa "2026 karşılaştırması"
            # diyen bir sayfa arama motoruna aylar önce donmuş görünür.
            "dateModified": data.get("modified", data["published"]),
            "inLanguage": lang,
            "mainEntityOfPage": url,
            "author": {"@id": f"{BASE}/#furkan"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "about": {"@id": f"{BASE}/#suuapp-ios"},
            "speakable": {"@type": "SpeakableSpecification",
                          "cssSelector": [".answer-box", "h1", "h2", ".verdict p"]},
        },
        item_list,
        {
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "inLanguage": lang,
            "mainEntity": [
                {"@type": "Question", "name": q["q"],
                 "acceptedAnswer": {"@type": "Answer", "text": q["a"]}}
                for q in page["faq"]
            ],
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Suu", "item": BASE + UI[lang]["home_href"]},
                {"@type": "ListItem", "position": 2, "name": UI[lang]["blog"], "item": BASE + UI[lang]["blog_href"]},
                {"@type": "ListItem", "position": 3, "name": page["h1"], "item": url},
            ],
        },
    ]
    out = json.dumps({"@context": "https://schema.org", "@graph": graph},
                     ensure_ascii=False, indent=2)
    return out.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def main() -> int:
    apply = "--apply" in sys.argv
    only = None
    if "--topic" in sys.argv:
        only = sys.argv[sys.argv.index("--topic") + 1]

    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    # x-default hedefi kayıt defterinden gelir. Şablon bunu eskiden kümenin İLK
    # diline (tr) sabitliyordu, yani her --apply çalıştırması
    # inject-hreflang.py'nin yazdığı doğru x-default'u geri alıyordu — README'nin
    # "x-default'u sabit kodlamayın" kuralının tam olarak ihlali.
    xdefault_lang = json.loads(REGISTRY.read_text(encoding="utf-8")).get("_xdefault", DEFAULT)
    env = Environment(loader=FileSystemLoader(str(COMPARE)), undefined=StrictUndefined,
                      autoescape=True)
    template = env.get_template("_template.html.j2")

    topics = sorted(p.stem for p in COMPARE.glob("*.json"))
    if only:
        topics = [t for t in topics if t == only]
        if not topics:
            print(f"Konu bulunamadı: {only}", file=sys.stderr)
            return 2

    written, registry_lines = [], []

    for topic in topics:
        data = json.loads((COMPARE / f"{topic}.json").read_text(encoding="utf-8"))
        langs = [l for l in LOCALES if l in data["pages"]]
        slugs = {l: data["pages"][l]["slug"] for l in langs}

        registry_lines.append(f'    "{slugs[DEFAULT] if DEFAULT in slugs else slugs[langs[0]]}": '
                              + json.dumps({l: slugs[l] for l in langs}, ensure_ascii=False) + ",")

        for lang in langs:
            page = data["pages"][lang]
            url = abs_url(lang, page["slug"])
            locale, direction = LOCALES[lang]

            ctx = {
                "lang": lang, "dir": direction, "locale": locale, "url": url, "topic": topic,
                "facts": facts, "ui": UI[lang],
                "published": data["published"],
                "published_display": data["published"],
                "read_minutes": 6,
                "hreflang": [{"code": l, "href": abs_url(l, slugs[l])} for l in langs],
                "xdefault_href": abs_url(xdefault_lang, slugs[xdefault_lang])
                if xdefault_lang in slugs else abs_url(langs[0], slugs[langs[0]]),
                "jsonld": build_jsonld(lang, topic, data, page, facts, url),
            }
            ctx.update(page)          # sayfa değerleri varsayılanları ezer
            html = template.render(**ctx)

            target = ROOT / rel_path(lang, page["slug"])
            old = target.read_text(encoding="utf-8") if target.exists() else ""
            status = "güncel" if old == html else ("yeni" if not old else "güncellendi")
            print(f"  {rel_path(lang, page['slug']):<52} {len(html)//1024:>3} KB  {status}")
            written.append(target)
            if apply and old != html:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(html, encoding="utf-8")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} sayfa — {mode}")
    if registry_lines:
        print("\ncontent/page-registry.json → \"blog\" bölümüne eklenecek satırlar:")
        for line in registry_lines:
            print(line)
    if not apply:
        print("\nUygulamak için: python3 scripts/build-compare.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
