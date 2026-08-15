#!/usr/bin/env python3
"""
Suu — karşılaştırma merkezi (hub) üretici

"En iyi kalori uygulaması hangisi?" türü sorularda yapay zekâ asistanları
tek tek yazılardan çok, konuyu bir arada tutan DERLEME sayfalarını alıntılar:
bir sayfada birden fazla seçenek, hepsi aynı ölçütlerle değerlendirilmiş.
ItemList şeması bu yapıyı makineye açıkça bildirir.

Hub aynı zamanda iç bağlantı sorununu çözer: 15+ karşılaştırma sayfası şu an
yalnızca blog indeksinden bağlanıyor; hub bunları konu kümelerine ayırarak
ikinci bir bağlantı katmanı kurar ve küme otoritesini yoğunlaştırır.

Başlık ve açıklamalar hub'da TEKRAR YAZILMAZ — her giriş kendi sayfasının
<title> ve meta description'ından okunur. Sayfa güncellenince hub da güncellenir.

Kullanım:
    python3 scripts/build-compare-hub.py            # önizleme
    python3 scripts/build-compare-hub.py --apply
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
CONFIG = CONTENT / "compare-hub.json"
FACTS = CONTENT / "suu-facts.json"
BASE = "https://suuapp.com"

LOCALES = {"tr": ("tr_TR", "ltr"), "en": ("en_US", "ltr"),
           "ar": ("ar_SA", "rtl"), "ru": ("ru_RU", "ltr")}

LANG_NAMES = {"tr": "Türkçe", "en": "English", "ar": "العربية", "ru": "Русский",
              "de": "Deutsch", "it": "Italiano", "hi": "हिन्दी"}

HOME_HREF = {"tr": "/", "en": "/hosgeldiniz-en.html",
             "ar": "/hosgeldiniz-ar.html", "ru": "/hosgeldiniz-ru.html",
             "de": "/hosgeldiniz-de.html", "it": "/hosgeldiniz-it.html",
             "hi": "/hosgeldiniz-hi.html"}

UI = {
    "tr": {"skip": "İçeriğe geç", "blog": "Blog", "pricing": "Fiyatlandırma",
           "cta": "Ücretsiz İndir", "short_answer": "Kısa cevap:",
           "back_to_blog": "Bloga dön", "updated_label": "Güncelleme:",
           "comparisons_word": "karşılaştırma", "langs_label": "Dil seçimi",
           "cta_head": "Üçünü tek uygulamada takip et",
           "cta_sub": "Su, kalori ve egzersiz birbirine bağlı çalışır. iOS ve Android'de ücretsiz.",
           "glossary_href": "/sozluk.html", "glossary_label": "Sözlük",
           "home_href": "/", "blog_href": "/blog.html"},
    "en": {"skip": "Skip to content", "blog": "Blog", "pricing": "Pricing",
           "cta": "Download Free", "short_answer": "Short answer:",
           "back_to_blog": "Back to blog", "updated_label": "Updated:",
           "comparisons_word": "comparisons", "langs_label": "Choose language",
           "cta_head": "Track all three in one app",
           "cta_sub": "Water, calories and exercise working as one system. Free on iOS and Android.",
           "glossary_href": "/glossary.html", "glossary_label": "Glossary",
           "home_href": "/hosgeldiniz-en.html", "blog_href": "/blog-en.html"},
    "ar": {"skip": "تخطَّ إلى المحتوى", "blog": "المدونة", "pricing": "الأسعار",
           "cta": "تنزيل مجاني", "short_answer": "الإجابة المختصرة:",
           "back_to_blog": "العودة إلى المدونة", "updated_label": "التحديث:",
           "comparisons_word": "مقارنة", "langs_label": "اختيار اللغة",
           "cta_head": "تابع الثلاثة في تطبيق واحد",
           "cta_sub": "الماء والسعرات والتمارين كنظام واحد. مجاناً على iOS وAndroid.",
           "home_href": "/hosgeldiniz-ar.html", "blog_href": "/blog-ar.html"},
    "ru": {"skip": "Перейти к содержимому", "blog": "Блог", "pricing": "Цены",
           "cta": "Скачать бесплатно", "short_answer": "Короткий ответ:",
           "back_to_blog": "Назад в блог", "updated_label": "Обновлено:",
           "comparisons_word": "сравнений", "langs_label": "Выбор языка",
           "cta_head": "Отслеживайте всё три в одном приложении",
           "cta_sub": "Вода, калории и тренировки как единая система. Бесплатно на iOS и Android.",
           "home_href": "/hosgeldiniz-ru.html", "blog_href": "/blog-ru.html"},
}

DATE_FMT = {
    "tr": "{d} {month} {y}", "en": "{month} {d}, {y}",
    "ar": "{d} {month} {y}", "ru": "{d} {month} {y}",
}
MONTHS = {
    "tr": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
           "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو",
           "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля",
           "августа", "сентября", "октября", "ноября", "декабря"],
}


def page_meta(rel_path: str) -> tuple[str, str]:
    """Girişin başlığını ve açıklamasını sayfanın KENDİSİNDEN oku."""
    page = (ROOT / rel_path).read_text(encoding="utf-8")

    m = re.search(r'<meta property="og:title" content="([^"]+)"', page)
    if m:
        title = m.group(1)
    else:
        m = re.search(r"<title>(.*?)</title>", page, re.DOTALL)
        title = m.group(1) if m else rel_path
    title = re.sub(r"\s*[|—–]\s*Suu.*$", "", html.unescape(title)).strip()

    m = re.search(r'<meta name="description" content="([^"]+)"', page)
    desc = html.unescape(m.group(1)).strip() if m else ""
    if len(desc) > 190:
        desc = desc[:187].rsplit(" ", 1)[0] + "…"
    return title, desc


def slugify(text: str) -> str:
    tr = str.maketrans("çğıöşüÇĞIİÖŞÜ", "cgiosuCGIIOSU")
    text = text.translate(tr).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "grup"


def pretty_date(iso: str, lang: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return DATE_FMT[lang].format(d=d, month=MONTHS[lang][m - 1], y=y)


def page_url(lang: str, cfg: dict) -> str:
    return f"{BASE}/{cfg['pages'][lang]['outfile']}"


def build_jsonld(lang: str, cfg: dict, spec: dict, groups: list, facts: dict) -> str:
    url = page_url(lang, cfg)
    founder = facts["entities"]["founder"]

    items = []
    position = 1
    for group in groups:
        for entry in group["entries"]:
            items.append({
                "@type": "ListItem",
                "position": position,
                "url": f"{BASE}/{entry['rel']}",
                "name": entry["title"],
            })
            position += 1

    graph = [
        {
            "@type": "Organization",
            "@id": f"{BASE}/#organization",
            "name": "Suu",
            "url": BASE,
        },
        {
            "@type": "Person",
            "@id": f"{BASE}/#furkan",
            "name": founder["name"],
            "url": founder["profile_page"],
            "jobTitle": founder["role"],
        },
        {
            "@type": "CollectionPage",
            "@id": f"{url}#page",
            "url": url,
            "name": spec["meta"]["title"],
            "description": spec["meta"]["description"],
            "inLanguage": lang,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "author": {"@id": f"{BASE}/#furkan"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "dateModified": cfg["published"],
            "speakable": {
                "@type": "SpeakableSpecification",
                "cssSelector": [".answer-box"],
            },
            "mainEntity": {"@id": f"{url}#list"},
        },
        {
            "@type": "ItemList",
            "@id": f"{url}#list",
            "name": spec["h1"],
            "description": spec["answer"],
            "numberOfItems": len(items),
            "itemListOrder": "https://schema.org/ItemListOrderAscending",
            "itemListElement": items,
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Suu",
                 "item": f"{BASE}{HOME_HREF[lang]}"},
                {"@type": "ListItem", "position": 2, "name": spec["h1"], "item": url},
            ],
        },
    ]

    out = json.dumps({"@context": "https://schema.org", "@graph": graph},
                     ensure_ascii=False, indent=2)
    return out.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def main() -> int:
    apply = "--apply" in sys.argv

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))

    env = Environment(loader=FileSystemLoader(str(CONTENT)),
                      undefined=StrictUndefined, autoescape=True)
    template = env.get_template("compare-hub.html.j2")

    langs = list(cfg["pages"])
    hreflang = [{"code": code, "href": page_url(code, cfg)} for code in langs]
    footer_langs = [{"code": code, "name": LANG_NAMES[code], "href": HOME_HREF[code]}
                    for code in LANG_NAMES]

    written, unchanged = [], []

    for lang, spec in cfg["pages"].items():
        locale, direction = LOCALES[lang]

        groups, total = [], 0
        for group in spec["groups"]:
            entries = []
            for rel in group["pages"]:
                title, desc = page_meta(rel)
                entries.append({"rel": rel, "href": f"/{rel}",
                                "title": title, "description": desc})
            total += len(entries)
            groups.append({"title": group["title"], "blurb": group["blurb"],
                           "accent": group["accent"], "entries": entries,
                           "anchor": slugify(group["title"])})

        page = template.render(
            lang=lang, dir=direction, locale=locale,
            url=page_url(lang, cfg),
            hreflang=hreflang,
            footer_langs=footer_langs,
            ui=UI[lang],
            facts=facts,
            badge=spec["badge"], h1=spec["h1"], meta=spec["meta"],
            answer=spec["answer"], intro=spec["intro"],
            disclosure=spec["disclosure"],
            groups=groups, total=total,
            published_display=pretty_date(cfg["published"], lang),
            jsonld=build_jsonld(lang, cfg, spec, groups, facts),
        )

        target = ROOT / spec["outfile"]
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        if old == page:
            unchanged.append(spec["outfile"])
        else:
            written.append(f"{spec['outfile']} ({total} giriş, {len(page)//1024} KB)")
            if apply:
                target.write_text(page, encoding="utf-8")

    for line in written:
        print(f"  ✎ {line}")
    for name in unchanged:
        print(f"  = {name} (değişmedi)")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} sayfa değişti — {mode}")
    if not apply and written:
        print("Uygulamak için: python3 scripts/build-compare-hub.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
