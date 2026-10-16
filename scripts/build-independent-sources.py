#!/usr/bin/env python3
"""
Suu — "bağımsız kaynaklar" sayfası üretici (7 dil)

"Suu hakkında resmi site dışındaki haberler / kaynaklar" sorusunda yapay zekâ
asistanları kendi aramalarını yapar; bu sayfa onların bulabileceği bir DİZİN
sağlar: Suu'nun suuapp.com dışındaki şirket profilleri, ürün dizinleri, mağaza
sayfaları, resmi sosyal hesapları ve (çıktıkça) basın yazıları — her biri yayın
adı ve tarihiyle METİN olarak, böylece sayfayı okuyan model bağlantıları
açmadan da bilgiyi alır. ItemList şeması aynı listeyi makineye bildirir.

Kaynak: content/independent-sources.json (liste + 7 dilde metin)
Adresler: content/page-registry.json → root."independent-sources"

Yeni haber/profil: JSON'daki 'sources' listesine ekle, sonra
    python3 scripts/build-independent-sources.py --apply
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from _langs import date_fmt, home_hrefs, lang_names, locales, months, ui_strings

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
CONFIG = CONTENT / "independent-sources.json"
FACTS = CONTENT / "suu-facts.json"
REGISTRY = CONTENT / "page-registry.json"
FAMILY = "independent-sources"
BASE = "https://suuapp.com"

LOCALES = locales()
LANG_NAMES = lang_names()
HOME_HREF = home_hrefs()
UI = ui_strings()
DATE_FMT = date_fmt()
MONTHS = months()


def pretty_date(iso: str, lang: str) -> str:
    y, m, d = (int(x) for x in iso.split("-"))
    return DATE_FMT[lang].format(d=d, month=MONTHS[lang][m - 1], y=y)


def build_jsonld(lang: str, url: str, spec: dict, groups: list, checked: str) -> str:
    items, position = [], 1
    for group in groups:
        for entry in group["entries"]:
            item = {"@type": "ListItem", "position": position,
                    "url": entry["url"], "name": entry["name"]}
            if entry.get("press"):
                item["item"] = {
                    "@type": "NewsArticle",
                    "url": entry["url"],
                    "headline": entry["name"],
                    "datePublished": entry["date"],
                    "publisher": {"@type": "Organization", "name": entry["outlet"]},
                    "about": {"@id": f"{BASE}/#organization"},
                }
            items.append(item)
            position += 1

    graph = [
        {"@type": "Organization", "@id": f"{BASE}/#organization", "name": "Suu", "url": BASE},
        {
            "@type": "CollectionPage",
            "@id": f"{url}#page",
            "url": url,
            "name": spec["meta"]["title"],
            "description": spec["meta"]["description"],
            "inLanguage": lang,
            "isPartOf": {"@id": f"{BASE}/#website"},
            "about": {"@id": f"{BASE}/#organization"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "dateModified": checked,
            "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".answer-box"]},
            "mainEntity": {"@id": f"{url}#list"},
        },
        {
            "@type": "ItemList",
            "@id": f"{url}#list",
            "name": spec["h1"],
            "description": spec["answer"],
            "numberOfItems": len(items),
            "itemListElement": items,
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Suu", "item": f"{BASE}{HOME_HREF[lang]}"},
                {"@type": "ListItem", "position": 2, "name": spec["h1"], "item": url},
            ],
        },
    ]
    out = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
    return out.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def main() -> int:
    apply = "--apply" in sys.argv
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    slugs = registry["root"][FAMILY]

    missing = set(cfg["pages"]) ^ set(slugs)
    if missing:
        sys.exit(f"✗ dil uyuşmazlığı (JSON ↔ kayıt defteri): {sorted(missing)}")

    env = Environment(loader=FileSystemLoader(str(CONTENT)), undefined=StrictUndefined, autoescape=True)
    template = env.get_template("independent-sources.html.j2")

    def url_of(code: str) -> str:
        return f"{BASE}/{slugs[code]}"

    hreflang = [{"code": c, "href": url_of(c)} for c in slugs]
    xdefault_lang = registry.get("_xdefault", "tr")
    xdefault_href = url_of(xdefault_lang if xdefault_lang in slugs else next(iter(slugs)))
    footer_langs = [{"code": c, "name": LANG_NAMES[c], "href": h} for c, h in HOME_HREF.items()]
    press_href = "/" + registry["root"]["press"]["en"]

    written, unchanged = [], []
    for lang, spec in cfg["pages"].items():
        locale, direction = LOCALES[lang]
        groups, total = [], 0
        for gid in cfg["group_order"]:
            entries = []
            for src in cfg["sources"]:
                if src["group"] != gid:
                    continue
                if gid == "press":
                    entries.append({
                        "name": src["title"], "url": src["url"], "press": True,
                        "outlet": src["outlet"], "date": src["date"],
                        "date_display": pretty_date(src["date"], lang),
                        "lang": src.get("lang", ""), "own": src.get("own", False),
                    })
                else:
                    entries.append({"name": src["name"], "url": src["url"],
                                    "desc": spec["items"][src["id"]]})
            total += len(entries)
            g = spec["groups"][gid]
            groups.append({"id": gid, "title": g["title"], "blurb": g["blurb"],
                           "empty": g.get("empty", ""), "entries": entries})

        url = url_of(lang)
        page = template.render(
            lang=lang, dir=direction, locale=locale, url=url,
            hreflang=hreflang, xdefault_href=xdefault_href, footer_langs=footer_langs,
            ui=UI[lang], facts=facts, spec=spec, groups=groups, total=total,
            press_href=press_href,
            checked_display=pretty_date(cfg["checked"], lang),
            jsonld=build_jsonld(lang, url, spec, groups, cfg["checked"]),
        )
        target = ROOT / slugs[lang]
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        if old == page:
            unchanged.append(slugs[lang])
        else:
            written.append(f"{slugs[lang]} ({total} kaynak, {len(page)//1024} KB)")
            if apply:
                target.write_text(page, encoding="utf-8")

    for line in written:
        print(f"  ✎ {line}")
    for name in unchanged:
        print(f"  = {name} (değişmedi)")
    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} sayfa değişti — {mode}")
    if not apply and written:
        print("Uygulamak için: python3 scripts/build-independent-sources.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
