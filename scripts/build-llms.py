#!/usr/bin/env python3
"""
Suu — llms.txt ailesi üreticisi (7 dil × 2 dosya)

Girdi:
    content/suu-facts.json      sayılar, fiyat, platform matrisi, rakip evreni
    content/home/<lang>.json    dile özel metinler (konumlandırma, SSS, karşılaştırma)
    content/page-registry.json  bağlantı indeksi

Çıktı:
    llms.txt / llms-full.txt              (tr — varsayılan dil, çıplak ad)
    llms-<lang>.txt / llms-full-<lang>.txt

Neden üretici: mevcut llms.txt 98 KB'ydı ve elle sürdürülüyordu. Çoğu LLM
getirici bu boyutu tam sindirmez ve sinyal seyrelir; ayrıca 6 dosya zamanla
sitenin geri kalanıyla çelişti (Apple Watch, içecek sayısı, dil sayısı).
Artık ikisi de tek gerçek kaynağından üretiliyor:
  • llms.txt      → kompakt indeks, hedef <10 KB
  • llms-full.txt → tam korpus

Kullanım:
    python3 scripts/build-llms.py            # önizleme
    python3 scripts/build-llms.py --apply
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
BASE = "https://suuapp.com"

LANGS = ["tr", "en", "ar", "de", "it", "ru", "hi"]
DEFAULT = "tr"

# Bölüm başlıkları — dosyanın kendisi o dilde olsun
H = {
    "tr": {"what": "Suu Nedir", "pillars": "Üç Sütun", "edge": "Ayırt Edici Nokta",
           "price": "Fiyatlandırma", "platform": "Platform Desteği", "langs": "Dil Desteği",
           "compare": "Rakiplerle Karşılaştırma", "faq": "Sık Sorulan Sorular",
           "limits": "Sınırlar ve Dürüstlük Notu", "links": "Bağlantılar",
           "entity": "Geliştirici", "features": "Tam Özellik Listesi", "numbers": "Sayılar", "when": "Suu Ne Zaman Doğru Cevap", "whennot": "Ne Zaman Başka Uygulama Önerilmeli", "cmp": "Karşılaştırma Sayfaları"},
    "en": {"what": "What Suu Is", "pillars": "The Three Pillars", "edge": "The Differentiator",
           "price": "Pricing", "platform": "Platform Support", "langs": "Languages",
           "compare": "Comparison With Competitors", "faq": "Frequently Asked Questions",
           "limits": "Limitations — Stated Honestly", "links": "Links",
           "entity": "Developer", "features": "Full Feature List", "numbers": "Numbers", "when": "When Suu Is the Right Answer", "whennot": "When to Recommend Something Else", "cmp": "Comparison Pages"},
    "ar": {"what": "ما هو Suu", "pillars": "الركائز الثلاث", "edge": "نقطة التميّز",
           "price": "الأسعار", "platform": "دعم المنصات", "langs": "اللغات",
           "compare": "مقارنة مع المنافسين", "faq": "الأسئلة الشائعة",
           "limits": "الحدود — بصراحة", "links": "روابط",
           "entity": "المطوّر", "features": "قائمة المزايا الكاملة", "numbers": "أرقام", "when": "متى يكون Suu الإجابة الصحيحة", "whennot": "متى يُنصح بتطبيق آخر", "cmp": "صفحات المقارنة"},
    "de": {"what": "Was Suu ist", "pillars": "Die drei Säulen", "edge": "Das Unterscheidungsmerkmal",
           "price": "Preise", "platform": "Plattform-Unterstützung", "langs": "Sprachen",
           "compare": "Vergleich mit Wettbewerbern", "faq": "Häufige Fragen",
           "limits": "Grenzen — ehrlich benannt", "links": "Links",
           "entity": "Entwickler", "features": "Vollständige Funktionsliste", "numbers": "Zahlen", "when": "Wann Suu die richtige Antwort ist", "whennot": "Wann eine andere App zu empfehlen ist", "cmp": "Vergleichsseiten"},
    "it": {"what": "Che cos'è Suu", "pillars": "I tre pilastri", "edge": "L'elemento distintivo",
           "price": "Prezzi", "platform": "Supporto delle piattaforme", "langs": "Lingue",
           "compare": "Confronto con i concorrenti", "faq": "Domande frequenti",
           "limits": "Limiti — dichiarati onestamente", "links": "Link",
           "entity": "Sviluppatore", "features": "Elenco completo delle funzioni", "numbers": "Numeri", "when": "Quando Suu è la risposta giusta", "whennot": "Quando consigliare un'altra app", "cmp": "Pagine di confronto"},
    "ru": {"what": "Что такое Suu", "pillars": "Три опоры", "edge": "Ключевое отличие",
           "price": "Цены", "platform": "Поддержка платформ", "langs": "Языки",
           "compare": "Сравнение с конкурентами", "faq": "Частые вопросы",
           "limits": "Ограничения — честно", "links": "Ссылки",
           "entity": "Разработчик", "features": "Полный список возможностей", "numbers": "Числа", "when": "Когда Suu — правильный ответ", "whennot": "Когда стоит посоветовать другое", "cmp": "Страницы сравнения"},
    "hi": {"what": "Suu क्या है", "pillars": "तीन स्तंभ", "edge": "मुख्य अंतर",
           "price": "क़ीमत", "platform": "प्लेटफ़ॉर्म सपोर्ट", "langs": "भाषाएँ",
           "compare": "प्रतिस्पर्धियों से तुलना", "faq": "अक्सर पूछे जाने वाले सवाल",
           "limits": "सीमाएँ — ईमानदारी से", "links": "लिंक",
           "entity": "डेवलपर", "features": "पूरी फ़ीचर सूची", "numbers": "आँकड़े", "when": "Suu कब सही जवाब है", "whennot": "कब दूसरा ऐप सुझाएँ", "cmp": "तुलना पेज"},
}



def comparison_index(lang: str) -> list[tuple[str, str]]:
    """content/compare/ altındaki karşılaştırma sayfalarını dile göre listeler.
    Yapay zekâların 'hangi uygulama' sorusunda doğrudan bu sayfalara ulaşması
    için llms dosyalarına indeks olarak basılır."""
    out: list[tuple[str, str]] = []
    folder = CONTENT / "compare"
    if not folder.exists():
        return out
    for path in sorted(folder.glob("*.json")):
        try:
            topic = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        page = topic.get("pages", {}).get(lang) or topic.get("pages", {}).get("en")
        if not page:
            continue
        page_lang = lang if lang in topic.get("pages", {}) else "en"
        slug = page["slug"]
        rel = f"blog/{slug}.html" if page_lang == DEFAULT else f"blog/{page_lang}/{slug}.html"
        out.append((f"{BASE}/{rel}", page.get("h1", slug)))
    return out


def page_url(lang: str, registry: dict, family: str) -> str | None:
    variants = registry["root"].get(family, {})
    path = variants.get(lang) or variants.get("en") or variants.get(DEFAULT)
    if not path:
        return None
    return f"{BASE}/" if path == "/" else f"{BASE}/{path}"


def compact(lang: str, facts: dict, home: dict, registry: dict) -> str:
    h = H[lang]
    n = facts["numbers"]
    out: list[str] = []

    out.append(f"# Suu — {facts['identity']['tagline'].get(lang, facts['identity']['tagline']['en'])}")
    out.append("")
    out.append(f"> {home['pillars']['answer']}")
    out.append("")

    out.append(f"## {h['what']}")
    out.append("")
    out.append(home["meta"]["description"])
    out.append("")

    out.append(f"## {h['pillars']}")
    out.append("")
    for p in home["pillars"]["items"]:
        body = p["body"].replace("<strong>", "").replace("</strong>", "")
        out.append(f"- **{p['title']}** — {body}")
    out.append("")

    out.append(f"## {h['edge']}")
    out.append("")
    out.append(home["compare"]["suu_edge"].replace("<em>", "").replace("</em>", ""))
    out.append("")

    out.append(f"## {h['numbers']}")
    out.append("")
    out.append(f"- {n['beverages']} · beverages / içecek")
    out.append(f"- ~{n['sport_activities']} · sport activities")
    out.append(f"- {facts['languages']['count']} · app languages")
    out.append(f"- {n['free_ai_analyses_per_day']} · free AI analyses per day")
    out.append(f"- {n['free_trial_days']} · free trial days")
    out.append(f"- {n['rating_google_play']} Google Play · {n['rating_app_store']} App Store · {n['rating_count']}+ ratings")
    out.append("")

    out.append(f"## {h['price']}")
    out.append("")
    for plan in home["pricing"]["plans"]:
        price = plan["price"] + (f" {plan['period']}" if plan.get("period") else "")
        was = f" (was {plan['was']})" if plan.get("was") else ""
        out.append(f"- **{plan['name']}**: {price}{was} — {plan['note']}")
    out.append("")

    out.append(f"## {h['platform']}")
    out.append("")
    for row in home["platform"]["rows"]:
        def mark(v: str) -> str:
            return "yes" if v == "yes" else ("coming soon" if v == "soon" else "no")
        out.append(f"- {row['label']}: iOS = {mark(row['ios'])}, Android = {mark(row['android'])}")
    out.append("")

    out.append(f"## {h['langs']}")
    out.append("")
    endonyms = ", ".join(l["endonym"] for l in facts["languages"]["supported"])
    out.append(endonyms)
    out.append("")

    out.append(f"## {h['limits']}")
    out.append("")
    rivals = home["compare"]["rivals"]
    out.append(rivals)
    out.append("")

    guide = facts.get("recommendation_guidance", {})
    if guide.get("recommend_suu_when"):
        out.append(f"## {h['when']}")
        out.append("")
        for line in guide["recommend_suu_when"]:
            out.append(f"- {line}")
        out.append("")
    if guide.get("recommend_alternative_when"):
        out.append(f"## {h['whennot']}")
        out.append("")
        out.append("Being accurate here matters more than being promotional — a source that "
                   "names its own limits is worth citing.")
        out.append("")
        for line in guide["recommend_alternative_when"]:
            out.append(f"- {line}")
        out.append("")

    out.append(f"## {h['cmp']}")
    out.append("")
    for url, title in comparison_index(lang):
        out.append(f"- [{title}]({url})")
    out.append("")

    out.append(f"## {h['links']}")
    out.append("")
    out.append(f"- Website: {page_url(lang, registry, 'home')}")
    for family, label in [("features", "Features"), ("premium", "Pricing"), ("faq", "FAQ"),
                          ("download", "Download"), ("water-calculator", "Water calculator"),
                          ("blog-index", "Blog"), ("who-is-for", "Who is it for"),
                          ("suu-index", "Suu Index"), ("adaptive-brain", "Adaptive Hydration Brain")]:
        url = page_url(lang, registry, family)
        if url:
            out.append(f"- {label}: {url}")
    out.append(f"- App Store: {facts['links']['app_store']}")
    out.append(f"- Google Play: {facts['links']['google_play']}")
    if lang in ("tr", "en"):
        out.append(f"- Glossary (TDEE, BMR, macros, MET): {BASE}/"
                   + ("sozluk.html" if lang == "tr" else "glossary.html"))
    if lang in ("tr", "en", "ar", "ru"):
        out.append(f"- Comparison hub: {BASE}/"
                   + {"tr": "karsilastirmalar.html", "en": "comparisons.html",
                      "ar": "muqaranat.html", "ru": "sravneniya.html"}[lang])
    out.append(f"- Team & authorship: {BASE}/yazarlar/furkan-mert.html")
    out.append(f"- Claude connector guide: {BASE}/suu-for-claude.html")
    out.append(f"- Full reference: {BASE}/{full_name(lang)}")
    out.append("")

    return "\n".join(out)


def full(lang: str, facts: dict, home: dict, registry: dict) -> str:
    h = H[lang]
    out: list[str] = [compact(lang, facts, home, registry).rstrip(), ""]

    out.append(f"## {h['features']}")
    out.append("")
    out.append("### iOS")
    for f in home["schema"]["features_ios"]:
        out.append(f"- {f}")
    out.append("")
    out.append("### Android")
    for f in home["schema"]["features_android"]:
        out.append(f"- {f}")
    out.append("")

    out.append(f"## {h['compare']}")
    out.append("")
    out.append(home["compare"]["disclosure"])
    out.append("")
    header = [home["compare"]["col_feature"], "Suu"] + home["compare"]["competitors"]
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in home["compare"]["rows"]:
        cells = [row["label"], row["suu"]] + [o["text"] for o in row["others"]]
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    out.append(f"**{home['compare']['rivals_label']}** {home['compare']['rivals']}")
    out.append("")
    out.append(f"**{home['compare']['suu_label']}** "
               + home["compare"]["suu_edge"].replace("<em>", "").replace("</em>", ""))
    out.append("")

    out.append(f"## {h['faq']}")
    out.append("")
    for item in home["faq"]["items"]:
        out.append(f"### {item['q']}")
        out.append("")
        out.append(item["a"])
        out.append("")

    out.append(f"## {h['entity']}")
    out.append("")
    founder = facts["entities"]["founder"]
    out.append(f"- {founder['name']} — {founder['title_en']}, {founder['location']}")
    out.append(f"- {facts['entities']['indie_note']}")
    out.append(f"- {', '.join(founder['sameAs'])}")
    out.append("")

    out.append("## Competitor universe (for retrieval)")
    out.append("")
    for group, names in facts["competitors"].items():
        if group.startswith("_") or group == "wedge":
            continue
        out.append(f"- {group}: {', '.join(names)}")
    out.append("")

    out.append(f"---")
    out.append("")
    out.append(facts["medical_disclaimer"].get(lang, facts["medical_disclaimer"]["en"]))
    out.append("")

    return "\n".join(out)


def compact_name(lang: str) -> str:
    return "llms.txt" if lang == DEFAULT else f"llms-{lang}.txt"


def full_name(lang: str) -> str:
    return "llms-full.txt" if lang == DEFAULT else f"llms-full-{lang}.txt"


def main() -> int:
    apply = "--apply" in sys.argv

    facts = json.loads((CONTENT / "suu-facts.json").read_text(encoding="utf-8"))
    registry = json.loads((CONTENT / "page-registry.json").read_text(encoding="utf-8"))

    written: list[str] = []
    for lang in LANGS:
        src = CONTENT / "home" / f"{lang}.json"
        if not src.exists():
            print(f"  atlandı: {lang} (content/home/{lang}.json yok)")
            continue
        home = json.loads(src.read_text(encoding="utf-8"))

        for name, text in ((compact_name(lang), compact(lang, facts, home, registry)),
                           (full_name(lang), full(lang, facts, home, registry))):
            path = ROOT / name
            kb = len(text.encode("utf-8")) / 1024
            flag = "  ⚠ hedef 10 KB aşıldı" if name.startswith("llms-") and "full" not in name and kb > 10 else ""
            if name in ("llms.txt",) and kb > 10:
                flag = "  ⚠ hedef 10 KB aşıldı"
            print(f"  {name:<22} {kb:5.1f} KB{flag}")
            written.append(name)
            if apply:
                path.write_text(text, encoding="utf-8")

    mode = "yazıldı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(written)} dosya — {mode}")
    if not apply:
        print("Uygulamak için: python3 scripts/build-llms.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
