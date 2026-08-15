#!/usr/bin/env python3
"""
Suu — beslenme/hidrasyon/egzersiz sözlüğü üretici

"TDEE nedir", "makro ne demek", "MET değeri nasıl hesaplanır" — tanım
soruları yapay zekâ asistanlarının en sık yanıtladığı sorgu tipidir ve
yanıt genellikle 40-60 kelimelik tek bir paragraftan doğrudan alıntılanır.
Sitede bu formatta tek bir sayfa bile yoktu.

DefinedTermSet + DefinedTerm şeması bu yapıyı makineye açıkça bildirir:
"bu sayfa bir terimler kümesidir, şu terim şu anlama gelir". Sayfadaki
<dl> yapısı da aynı bilgiyi kullanıcıya görünür biçimde verir — şema ile
görünür içerik birebir aynı olmalıdır.

Sözlük mevcut uzun yazıların yerine geçmez: her terim, varsa, ilgili
ayrıntılı yazıya bağlanır. Böylece küme içi bağlantı da güçlenir.

Kullanım:
    python3 scripts/build-glossary.py            # önizleme
    python3 scripts/build-glossary.py --apply
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
CONFIG = CONTENT / "glossary.json"
FACTS = CONTENT / "suu-facts.json"
BASE = "https://suuapp.com"

LOCALES = {"tr": ("tr_TR", "ltr"), "en": ("en_US", "ltr")}

LANG_NAMES = {"tr": "Türkçe", "en": "English", "ar": "العربية", "ru": "Русский",
              "de": "Deutsch", "it": "Italiano", "hi": "हिन्दी"}

HOME_HREF = {"tr": "/", "en": "/hosgeldiniz-en.html",
             "ar": "/hosgeldiniz-ar.html", "ru": "/hosgeldiniz-ru.html",
             "de": "/hosgeldiniz-de.html", "it": "/hosgeldiniz-it.html",
             "hi": "/hosgeldiniz-hi.html"}

UI = {
    "tr": {"skip": "İçeriğe geç", "blog": "Blog", "cta": "Ücretsiz İndir",
           "short_answer": "Kısa cevap:", "back_to_blog": "Bloga dön",
           "updated_label": "Güncelleme:", "terms_word": "terim",
           "index_label": "Terim dizini", "langs_label": "Dil seçimi",
           "hub_href": "/karsilastirmalar.html", "hub_label": "Karşılaştırmalar",
           "cta_head": "Bu sayıları elle hesaplama",
           "cta_sub": "Suu; günlük kalori, makro ve su hedefini senin verinden hesaplar. iOS ve Android'de ücretsiz.",
           "home_href": "/", "blog_href": "/blog.html"},
    "en": {"skip": "Skip to content", "blog": "Blog", "cta": "Download Free",
           "short_answer": "Short answer:", "back_to_blog": "Back to blog",
           "updated_label": "Updated:", "terms_word": "terms",
           "index_label": "Term index", "langs_label": "Choose language",
           "hub_href": "/comparisons.html", "hub_label": "Comparisons",
           "cta_head": "Stop working these numbers out by hand",
           "cta_sub": "Suu calculates your daily calorie, macro and water targets from your own data. Free on iOS and Android.",
           "home_href": "/hosgeldiniz-en.html", "blog_href": "/blog-en.html"},
}

MONTHS = {
    "tr": ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
           "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
}


def slugify(text: str) -> str:
    tr = str.maketrans("çğıöşüÇĞIİÖŞÜ", "cgiosuCGIIOSU")
    text = text.translate(tr).lower()
    text = re.sub(r"\(.*?\)", " ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def pretty_date(iso: str, lang: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    month = MONTHS[lang][m - 1]
    return f"{month} {d}, {y}" if lang == "en" else f"{d} {month} {y}"


def article_title(rel_path: str) -> str:
    """Bağlantı metni yazının kendi başlığından — elle yazılmaz."""
    page = (ROOT / rel_path).read_text(encoding="utf-8")
    m = re.search(r'<meta property="og:title" content="([^"]+)"', page)
    if not m:
        m = re.search(r"<title>(.*?)</title>", page, re.DOTALL)
    title = html.unescape(m.group(1)) if m else rel_path
    return re.sub(r"\s*[|—–]\s*Suu.*$", "", title).strip()


def page_url(lang: str, cfg: dict) -> str:
    return f"{BASE}/{cfg['pages'][lang]['outfile']}"


def build_jsonld(lang: str, cfg: dict, spec: dict, terms: list, facts: dict) -> str:
    url = page_url(lang, cfg)
    founder = facts["entities"]["founder"]
    set_id = f"{url}#termset"

    term_nodes = []
    for t in terms:
        node = {
            "@type": "DefinedTerm",
            "@id": f"{url}#{t['anchor']}",
            "name": t["term"],
            "description": t["definition"],
            "inDefinedTermSet": {"@id": set_id},
            "url": f"{url}#{t['anchor']}",
        }
        if t.get("abbr"):
            node["alternateName"] = t["abbr"]
        term_nodes.append(node)

    graph = [
        {"@type": "Organization", "@id": f"{BASE}/#organization",
         "name": "Suu", "url": BASE},
        {"@type": "Person", "@id": f"{BASE}/#furkan", "name": founder["name"],
         "url": founder["profile_page"], "jobTitle": founder["role"]},
        {
            "@type": "DefinedTermSet",
            "@id": set_id,
            "name": spec["h1"],
            "description": spec["meta"]["description"],
            "inLanguage": lang,
            "url": url,
            "hasDefinedTerm": [{"@id": n["@id"]} for n in term_nodes],
        },
        *term_nodes,
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
            "dateModified": cfg["updated"],
            "speakable": {"@type": "SpeakableSpecification",
                          "cssSelector": [".answer-box"]},
            "mainEntity": {"@id": set_id},
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
    template = env.get_template("glossary.html.j2")

    langs = list(cfg["pages"])
    hreflang = [{"code": c, "href": page_url(c, cfg)} for c in langs]
    footer_langs = [{"code": c, "name": LANG_NAMES[c], "href": HOME_HREF[c]}
                    for c in LANG_NAMES]

    written, unchanged = [], []

    for lang, spec in cfg["pages"].items():
        locale, direction = LOCALES[lang]

        terms = []
        for raw in spec["terms"]:
            # StrictUndefined kullanıldığı için isteğe bağlı alanlar
            # şablona ulaşmadan önce burada tanımlanır.
            t = {"abbr": None, "formula": None, "see_also": None,
                 "see_also_title": None, **raw}
            t["anchor"] = slugify(t["term"])
            if t["see_also"]:
                t["see_also_title"] = article_title(t["see_also"])
            terms.append(t)

        anchors = [t["anchor"] for t in terms]
        if len(set(anchors)) != len(anchors):
            print(f"  ✗ {lang}: çakışan çapa — {sorted(anchors)}")
            return 1

        page = template.render(
            lang=lang, dir=direction, locale=locale,
            url=page_url(lang, cfg),
            hreflang=hreflang, footer_langs=footer_langs,
            ui=UI[lang], facts=facts,
            badge=spec["badge"], h1=spec["h1"], meta=spec["meta"],
            answer=spec["answer"], intro=spec["intro"],
            terms=terms,
            see_also_label=spec["see_also_label"],
            formula_label=spec["formula_label"],
            updated_display=pretty_date(cfg["updated"], lang),
            jsonld=build_jsonld(lang, cfg, spec, terms, facts),
        )

        target = ROOT / spec["outfile"]
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        if old == page:
            unchanged.append(spec["outfile"])
        else:
            written.append(f"{spec['outfile']} ({len(terms)} terim, {len(page)//1024} KB)")
            if apply:
                target.write_text(page, encoding="utf-8")

    for line in written:
        print(f"  ✎ {line}")
    for name in unchanged:
        print(f"  = {name} (değişmedi)")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} sayfa değişti — {mode}")
    if not apply and written:
        print("Uygulamak için: python3 scripts/build-glossary.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
