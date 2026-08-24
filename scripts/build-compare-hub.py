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

from _langs import date_fmt, home_hrefs, lang_names, locales, months, ui_strings

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
CONFIG = CONTENT / "compare-hub.json"
FACTS = CONTENT / "suu-facts.json"
REGISTRY = CONTENT / "page-registry.json"
BASE = "https://suuapp.com"

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
LOCALES = locales()
LANG_NAMES = lang_names()
HOME_HREF = home_hrefs()
UI = ui_strings()

DATE_FMT = date_fmt()
MONTHS = months()


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
    # x-default hedefi kayıt defterinden; şablon bunu eskiden kümenin İLK diline
    # (tr) sabitliyordu ve her build inject-hreflang.py'nin işini geri alıyordu.
    xdefault_lang = json.loads(REGISTRY.read_text(encoding="utf-8")).get("_xdefault", "tr")
    xdefault_href = page_url(xdefault_lang, cfg) if xdefault_lang in cfg["pages"] \
        else hreflang[0]["href"]
    # HOME_HREF üzerinden dönülüyor, LANG_NAMES üzerinden değil: dil tablosunda
    # olup karşılama sayfası henüz yazılmamış bir dil menüye 404 koymamalı.
    footer_langs = [{"code": code, "name": LANG_NAMES[code], "href": href}
                    for code, href in HOME_HREF.items()]

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
            xdefault_href=xdefault_href,
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
