#!/usr/bin/env python3
"""
Suu — Karşılaştırma ve kategori cevap sayfası üreticisi

Bunlar GEO/AEO'nun en yüksek getirili sayfaları: yapay zekâya "hangi kalori
uygulamasını kullanayım" diye sorulduğunda alıntılanan içerik türü.

Girdi:
    content/compare/<topic>.json        karşılaştırma sayfaları (konu başına tüm diller)
    content/guides/<topic>.json         rehberler: "yapay zekâya sorulan sağlık sorusu
                                        → cevap → Suu'da nereden takip edilir"
    content/compare/_template.html.j2   AEO formatlı şablon (ikisi için ortak;
                                        `kind` değişkeniyle dallanır)
    content/suu-facts.json              paylaşılan gerçekler
    content/page-registry.json          hreflang kümesi (inject-hreflang.py ile aynı kaynak)

Çıktı:
    blog/<slug>.html          (varsayılan dil)
    blog/<lang>/<slug>.html   (diğer diller)

Şablon zorunlu AEO formatını dayatır:
    cevap-önce kutusu → şeffaflık notu → karşılaştırma tablosu →
    analiz → karar → CTA → SSS → kaynaklar → ilgili yazılar

Kayıt defteri: hreflang bloğu content/page-registry.json → "blog" kümesinden
üretilir (inject-hreflang.py'nin yazdığıyla birebir aynı). Karma kümelerde
(ör. tr/en/ar/ru elle yazılmış, de/it/uk JSON'dan) şablon eskiden yalnızca
JSON'daki dilleri basıyor, inject-hreflang.py çalıştırılana kadar diğer diller
düşüyordu. Rehberler kümede kayıtlı olmak ZORUNDA; önce kayıt defterine ekleyin,
ardından build-i18n-map.py, update-sitemap.py.

Kullanım:
    python3 scripts/build-compare.py                    # önizleme
    python3 scripts/build-compare.py --apply
    python3 scripts/build-compare.py --apply --topic suu-vs-cal-ai
    python3 scripts/build-compare.py --diff             # değişen sayfaların farkı (yazmaz)
"""
from __future__ import annotations

import difflib
import html
import json
import re
import sys
from pathlib import Path

from _langs import date_fmt, locales, months, ui_strings

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    raise SystemExit("HATA: jinja2 gerekli.  pip3 install jinja2")

ROOT = Path(__file__).resolve().parents[1]
COMPARE = ROOT / "content" / "compare"
# Kaynak klasörü → sayfa türü. Rehberler ayrı klasörde: build-llms.py
# karşılaştırmaları content/compare/*.json'dan topluyor, rehberler oraya
# "Comparison Pages" olarak düşmemeli. Tür, JSON'daki bir bayrakla değil
# klasörle belirlenir — unutulabilecek bir alan yok.
SOURCES = {"compare": COMPARE, "guide": ROOT / "content" / "guides"}
FACTS = ROOT / "content" / "suu-facts.json"
REGISTRY = ROOT / "content" / "page-registry.json"
BASE = "https://suuapp.com"
DEFAULT = "tr"

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
LOCALES = locales()
UI = ui_strings()
MONTHS = months()
DATE_FMT = date_fmt()
OG_DIR = ROOT / "assets" / "og" / "blog"
DEFAULT_OG = f"{BASE}/assets/og-image.png"

# Rehber kaynaklarında aranan yerel sağlık otoriteleri (uyarı düzeyi). Bir
# sağlık rehberi yalnızca PubMed'e değil, okurun ülkesinin resmî kaynağına da
# dayanmalı — hem güven hem yerel arama sinyali.
LOCAL_AUTHORITIES = {
    "tr": ("saglik.gov.tr",),
    "en": ("nhs.uk", "cdc.gov", "nih.gov", "efsa.europa.eu", "who.int"),
    "ar": ("moh.gov.sa", "sfda.gov.sa", "emro.who.int", "mohap.gov.ae", "who.int"),
    "ru": ("rospotrebnadzor.ru", "minzdrav.gov.ru", "who.int"),
    "de": ("dge.de", "bioeg.de", "bzga.de", "gesund.bund.de", "rki.de", "degam.de"),
    "it": ("crea.gov.it", "salute.gov.it", "iss.it", "issalute.it", "sinu.it",   # issalute.it = ISS halk portalı
           "efsa.europa.eu"),                                                   # EFSA: AB gıda otoritesi, merkezi Parma
    "uk": ("moz.gov.ua", "phc.org.ua", "who.int"),
}


def rel_path(lang: str, slug: str) -> str:
    return f"blog/{slug}.html" if lang == DEFAULT else f"blog/{lang}/{slug}.html"


def abs_url(lang: str, slug: str) -> str:
    return f"{BASE}/{rel_path(lang, slug)}"


def display_date(lang: str, iso: str) -> str:
    y, m, d = iso.split("-")
    return DATE_FMT[lang].format(d=int(d), month=MONTHS[lang][int(m) - 1], y=y)


def og_image_url(lang: str, page: dict, kind: str) -> str:
    """Açık `og_image` > (rehberde) diskte üretilmiş görsel > genel görsel.
    Karşılaştırma sayfaları açık alan verilmedikçe genel görselde kalır —
    mevcut 45 sayfanın çıktısı değişmesin."""
    if page.get("og_image"):
        return BASE + page["og_image"]
    if kind == "guide":
        name = (page["slug"] if lang == DEFAULT else f"{lang}-{page['slug']}") + ".png"
        if (OG_DIR / name).exists():
            return f"{BASE}/assets/og/blog/{name}"
    return DEFAULT_OG


def validate_guide(topic: str, lang: str, page: dict) -> tuple[list[str], list[str]]:
    """Rehber sözleşmesi. Hata → build durur; uyarı → yazdırılır."""
    errors, warns = [], []
    where = f"{topic}[{lang}]"
    for key in ("table", "ranked"):
        if key in page:
            errors.append(f"{where}: rehberde '{key}' olmaz (ItemList/uygulama sıralaması üretir)")
    for key in ("health_note", "in_app", "answer", "faq", "references", "related", "about"):
        if key not in page:
            errors.append(f"{where}: '{key}' eksik")
    if errors:
        return errors, warns
    steps = page["in_app"].get("steps", [])
    if len(steps) < 3:
        errors.append(f"{where}: in_app en az 3 adım ister ({len(steps)})")
    for i, st in enumerate(steps, 1):
        if not st.get("feature") or not st.get("solves") or not (
                st.get("where") or (st.get("where_ios") and st.get("where_android"))):
            errors.append(f"{where}: in_app adım {i} → feature + solves + where (veya where_ios/where_android)")
    for key, n in (("faq", 4), ("references", 2), ("related", 3)):
        if len(page[key]) < n:
            errors.append(f"{where}: '{key}' en az {n} öğe ister ({len(page[key])})")
    if not page["health_note"].get("body"):
        errors.append(f"{where}: health_note.body boş")
    if lang == "uk":
        blob = json.dumps(page, ensure_ascii=False)
        if "/blog/ru/" in blob:
            errors.append(f"{where}: Ukraynaca sayfa Rusça sayfaya bağlantı veriyor")
    hosts = LOCAL_AUTHORITIES.get(lang, ())
    if hosts and not any(h in r["href"] for r in page["references"] for h in hosts):
        warns.append(f"{where}: yerel sağlık otoritesi kaynağı yok ({', '.join(hosts)})")
    if len(page["meta"]["title"]) > 60:
        warns.append(f"{where}: title {len(page['meta']['title'])} karakter (>60)")
    if len(page["meta"]["description"]) > 160:
        warns.append(f"{where}: description {len(page['meta']['description'])} karakter (>160)")
    return errors, warns


def registry_cluster(reg: dict, slugs: dict) -> dict | None:
    """JSON'daki {dil: slug} çiftlerinin HEPSİNİ içeren blog kümesi."""
    for cluster in reg["blog"].values():
        if all(cluster.get(l) == s for l, s in slugs.items()):
            return cluster
    return None


def hreflang_pairs(reg: dict, cluster: dict | None, slugs: dict, langs: list) -> tuple[list, str]:
    """inject-hreflang.py ile birebir aynı mantık: kayıt defteri dil sırası,
    x-default → _xdefault dili, yoksa varsayılan dil, yoksa ilk dil.
    Kümesi olmayan ya da tek dilli sayfada JSON'daki diller kullanılır
    (inject-hreflang.py tek dilli kümelere dokunmaz)."""
    xdefault_lang = reg.get("_xdefault", DEFAULT)
    if cluster and len(cluster) >= 2:
        pairs = [{"code": l, "href": abs_url(l, cluster[l])}
                 for l in reg["_languages"] if l in cluster]
        by = {p["code"]: p["href"] for p in pairs}
        x = by.get(xdefault_lang) or by.get(reg.get("_default", DEFAULT)) or pairs[0]["href"]
        return pairs, x
    pairs = [{"code": l, "href": abs_url(l, slugs[l])} for l in langs]
    x = (abs_url(xdefault_lang, slugs[xdefault_lang]) if xdefault_lang in slugs
         else abs_url(langs[0], slugs[langs[0]]))
    return pairs, x


RE_TAGS = re.compile(r"<[^>]+>")


def plain(text: str) -> str:
    """Şema alanları düz metin ister; gövde metinleri <strong> vb. içerebiliyor."""
    return html.unescape(RE_TAGS.sub("", text)).strip()


def build_jsonld(lang: str, topic: str, data: dict, page: dict, facts: dict, url: str,
                 kind: str = "compare", image: str = DEFAULT_OG) -> str:
    founder = facts["entities"]["founder"]
    if kind == "guide":
        return _guide_jsonld(lang, data, page, facts, url, image)
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
    return _dump_graph(graph)


def _dump_graph(graph: list) -> str:
    out = json.dumps({"@context": "https://schema.org", "@graph": graph},
                     ensure_ascii=False, indent=2)
    return out.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _guide_jsonld(lang: str, data: dict, page: dict, facts: dict, url: str, image: str) -> str:
    """Rehber şeması: Article + FAQPage + BreadcrumbList. ItemList YOK — rehber
    bir uygulama sıralaması değil; tablo sütunlarını SoftwareApplication diye
    işaretlemek yanıltıcı yapılandırılmış veri olurdu. Uygulama, `mentions`
    ile iki mağaza düğümüne bağlanır (asıl tanımları ana sayfada)."""
    founder = facts["entities"]["founder"]
    graph = [
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
            "image": image,
            # Sayfa düzeyinde `published`: mevcut bir yazı rehber boru hattına
            # taşındığında her dilin ASIL yayın tarihi korunur (ör. EN 03-22, RU 05-07).
            "datePublished": page.get("published", data["published"]),
            "dateModified": data.get("modified", data["published"]),
            "inLanguage": lang,
            "mainEntityOfPage": url,
            "author": {"@id": f"{BASE}/#furkan"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "about": [dict({"@type": "Thing", "name": a["name"]},
                           **({"sameAs": a["sameAs"]} if a.get("sameAs") else {}))
                      for a in page["about"]],
            "mentions": [{"@id": f"{BASE}/#suuapp-ios"}, {"@id": f"{BASE}/#suuapp-android"}],
            "citation": [{"@type": "CreativeWork", "name": r["label"], "url": r["href"]}
                         for r in page["references"]],
            "speakable": {"@type": "SpeakableSpecification",
                          "cssSelector": [".answer-box", "h1", ".in-app", ".verdict p"]},
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
    return _dump_graph(graph)


def main() -> int:
    apply = "--apply" in sys.argv
    show_diff = "--diff" in sys.argv
    only = None
    if "--topic" in sys.argv:
        only = sys.argv[sys.argv.index("--topic") + 1]

    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    # x-default hedefi kayıt defterinden gelir. Şablon bunu eskiden kümenin İLK
    # diline (tr) sabitliyordu, yani her --apply çalıştırması
    # inject-hreflang.py'nin yazdığı doğru x-default'u geri alıyordu — README'nin
    # "x-default'u sabit kodlamayın" kuralının tam olarak ihlali.
    # Hreflang artık doğrudan kümeden geliyor (bkz. hreflang_pairs).
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    env = Environment(loader=FileSystemLoader(str(COMPARE)), undefined=StrictUndefined,
                      autoescape=True)
    template = env.get_template("_template.html.j2")

    # (konu, tür, kaynak dosya) — konu adı iki klasörde çakışamaz: --topic ve
    # HTML'deki "Kaynak:" yorumu tek anlamlı kalmalı.
    sources: dict[str, tuple[str, Path]] = {}
    for kind, folder in SOURCES.items():
        for p in sorted(folder.glob("*.json")) if folder.exists() else []:
            if p.stem in sources:
                print(f"HATA: '{p.stem}' hem {sources[p.stem][1].parent.name}/ hem "
                      f"{folder.name}/ klasöründe", file=sys.stderr)
                return 2
            sources[p.stem] = (kind, p)
    topics = sorted(sources)
    if only:
        topics = [t for t in topics if t == only]
        if not topics:
            print(f"Konu bulunamadı: {only}", file=sys.stderr)
            return 2

    written, registry_lines, problems, notes = [], [], [], []

    for topic in topics:
        kind, src = sources[topic]
        data = json.loads(src.read_text(encoding="utf-8"))
        langs = [l for l in LOCALES if l in data["pages"]]
        slugs = {l: data["pages"][l]["slug"] for l in langs}
        cluster = registry_cluster(reg, slugs)
        if kind == "guide":
            # Rehberin kümesi açıkça yazılır (kısmi JSON'lar — ör. yalnızca de/it/uk —
            # mevcut bir kümeye katılır) ve kayıt defterinde OLMAK zorunda.
            declared = reg["blog"].get(data.get("cluster", ""))
            if not declared or any(declared.get(l) != s for l, s in slugs.items()):
                problems.append(f"{topic}: kayıt defterinde '{data.get('cluster')}' kümesi yok ya da "
                                f"slug'lar uyuşmuyor — önce content/page-registry.json → blog")
                continue
            cluster = declared
        hreflang, xdefault_href = hreflang_pairs(reg, cluster, slugs, langs)

        registry_lines.append(f'    "{slugs[DEFAULT] if DEFAULT in slugs else slugs[langs[0]]}": '
                              + json.dumps({l: slugs[l] for l in langs}, ensure_ascii=False) + ",")

        for lang in langs:
            page = data["pages"][lang]
            url = abs_url(lang, page["slug"])
            locale, direction = LOCALES[lang]
            if page.get("kind", kind) != kind or data.get("kind", kind) != kind:
                problems.append(f"{topic}[{lang}]: 'kind' klasörle çelişiyor ({src.parent.name}/)")
                continue
            if kind == "guide":
                errs, warns = validate_guide(topic, lang, page)
                notes += warns
                if errs:
                    problems += errs
                    continue
            og_url = og_image_url(lang, page, kind)

            ctx = {
                "lang": lang, "dir": direction, "locale": locale, "url": url, "topic": topic,
                "facts": facts, "ui": UI[lang],
                "published": data["published"],
                "published_display": data["published"],
                "read_minutes": 6,
                "hreflang": hreflang,
                "xdefault_href": xdefault_href,
                "jsonld": build_jsonld(lang, topic, data, page, facts, url, kind, og_url),
                "source_rel": f"content/{src.parent.name}/{topic}.json",
                "og_image_url": og_url,
                "cta_src": f"guide-{topic}" if kind == "guide" else "compare-body",
            }
            if kind == "guide":
                page_published = page.get("published", data["published"])
                ctx["published_display"] = display_date(lang, page_published)
                ctx["modified_iso"] = data.get("modified", data["published"])
                ctx["modified_display"] = (display_date(lang, data["modified"])
                                           if data.get("modified") and data["modified"] != page_published
                                           else "")
            ctx.update(page)          # sayfa değerleri varsayılanları ezer
            ctx["kind"] = kind        # tür klasörden gelir; JSON ezemez
            html = template.render(**ctx)

            target = ROOT / rel_path(lang, page["slug"])
            old = target.read_text(encoding="utf-8") if target.exists() else ""
            status = "güncel" if old == html else ("yeni" if not old else "güncellendi")
            print(f"  {rel_path(lang, page['slug']):<52} {len(html)//1024:>3} KB  {status}")
            if show_diff and old and old != html:
                sys.stdout.writelines(difflib.unified_diff(
                    old.splitlines(keepends=True), html.splitlines(keepends=True),
                    fromfile=f"a/{rel_path(lang, page['slug'])}",
                    tofile=f"b/{rel_path(lang, page['slug'])}", n=1))
            written.append(target)
            if apply and old != html:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(html, encoding="utf-8")

    for n in notes:
        print(f"  ⚠ {n}")
    if problems:
        print(f"\n{len(problems)} HATA — bu sayfalar üretilmedi:", file=sys.stderr)
        for pr in problems:
            print(f"  ✗ {pr}", file=sys.stderr)
    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} sayfa — {mode}")
    if registry_lines:
        print("\ncontent/page-registry.json → \"blog\" bölümüne eklenecek satırlar:")
        for line in registry_lines:
            print(line)
    if not apply:
        print("\nUygulamak için: python3 scripts/build-compare.py --apply")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
