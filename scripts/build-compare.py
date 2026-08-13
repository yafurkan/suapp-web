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

import json
import sys
from pathlib import Path

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

LOCALES = {"tr": ("tr_TR", "ltr"), "en": ("en_US", "ltr"), "ar": ("ar_SA", "rtl"),
           "de": ("de_DE", "ltr"), "it": ("it_IT", "ltr"), "ru": ("ru_RU", "ltr"),
           "hi": ("hi_IN", "ltr")}

# Sayfa iskeleti metinleri — konudan bağımsız
UI = {
    "tr": {"skip": "İçeriğe geç", "blog": "Blog", "compare": "Karşılaştırma", "pricing": "Fiyatlandırma",
           "cta": "Ücretsiz İndir", "short_answer": "Kısa cevap:", "faq_head": "Sık sorulan sorular",
           "references": "Kaynaklar", "related": "İlgili yazılar", "back_to_blog": "Bloga dön",
           "published_label": "Yayın:", "read_time": "dakika okuma",
           "home_href": "/", "blog_href": "/blog.html"},
    "en": {"skip": "Skip to content", "blog": "Blog", "compare": "Comparison", "pricing": "Pricing",
           "cta": "Download Free", "short_answer": "Short answer:", "faq_head": "Frequently asked questions",
           "references": "References", "related": "Related articles", "back_to_blog": "Back to blog",
           "published_label": "Published:", "read_time": "min read",
           "home_href": "/hosgeldiniz-en.html", "blog_href": "/blog-en.html"},
    "ar": {"skip": "تخطَّ إلى المحتوى", "blog": "المدونة", "compare": "المقارنة", "pricing": "الأسعار",
           "cta": "تنزيل مجاني", "short_answer": "الإجابة المختصرة:", "faq_head": "الأسئلة الشائعة",
           "references": "المصادر", "related": "مقالات ذات صلة", "back_to_blog": "العودة إلى المدونة",
           "published_label": "النشر:", "read_time": "دقيقة قراءة",
           "home_href": "/hosgeldiniz-ar.html", "blog_href": "/blog-ar.html"},
    "ru": {"skip": "Перейти к содержимому", "blog": "Блог", "compare": "Сравнение", "pricing": "Цены",
           "cta": "Скачать бесплатно", "short_answer": "Короткий ответ:", "faq_head": "Частые вопросы",
           "references": "Источники", "related": "Похожие статьи", "back_to_blog": "Назад в блог",
           "published_label": "Опубликовано:", "read_time": "мин чтения",
           "home_href": "/hosgeldiniz-ru.html", "blog_href": "/blog-ru.html"},
    "de": {"skip": "Zum Inhalt springen", "blog": "Blog", "compare": "Vergleich", "pricing": "Preise",
           "cta": "Gratis laden", "short_answer": "Kurze Antwort:", "faq_head": "Häufige Fragen",
           "references": "Quellen", "related": "Verwandte Artikel", "back_to_blog": "Zurück zum Blog",
           "published_label": "Veröffentlicht:", "read_time": "Min. Lesezeit",
           "home_href": "/hosgeldiniz-de.html", "blog_href": "/blog-en.html"},
    "it": {"skip": "Vai al contenuto", "blog": "Blog", "compare": "Confronto", "pricing": "Prezzi",
           "cta": "Scarica gratis", "short_answer": "Risposta breve:", "faq_head": "Domande frequenti",
           "references": "Fonti", "related": "Articoli correlati", "back_to_blog": "Torna al blog",
           "published_label": "Pubblicato:", "read_time": "min di lettura",
           "home_href": "/hosgeldiniz-it.html", "blog_href": "/blog-en.html"},
    "hi": {"skip": "मुख्य सामग्री पर जाएँ", "blog": "ब्लॉग", "compare": "तुलना", "pricing": "क़ीमत",
           "cta": "मुफ़्त डाउनलोड", "short_answer": "संक्षिप्त उत्तर:", "faq_head": "अक्सर पूछे जाने वाले सवाल",
           "references": "स्रोत", "related": "संबंधित लेख", "back_to_blog": "ब्लॉग पर वापस",
           "published_label": "प्रकाशित:", "read_time": "मिनट पढ़ें",
           "home_href": "/hosgeldiniz-hi.html", "blog_href": "/blog-en.html"},
}


def rel_path(lang: str, slug: str) -> str:
    return f"blog/{slug}.html" if lang == DEFAULT else f"blog/{lang}/{slug}.html"


def abs_url(lang: str, slug: str) -> str:
    return f"{BASE}/{rel_path(lang, slug)}"


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
            "dateModified": data["published"],
            "inLanguage": lang,
            "mainEntityOfPage": url,
            "author": {"@id": f"{BASE}/#furkan"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "about": {"@id": f"{BASE}/#suuapp-ios"},
            "speakable": {"@type": "SpeakableSpecification",
                          "cssSelector": [".answer-box", "h1", "h2", ".verdict p"]},
        },
        {
            "@type": "ItemList",
            "@id": f"{url}#itemlist",
            "name": page["table"]["head"],
            "inLanguage": lang,
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": len(apps),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "item": a} for i, a in enumerate(apps, 1)
            ],
        },
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
