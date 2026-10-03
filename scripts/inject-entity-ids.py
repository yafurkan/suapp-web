#!/usr/bin/env python3
"""
Suu — Entity grafiği: JSON-LD düğümlerine kalıcı @id ekle

Sorun: 192 sayfa Organization ve Person nesnelerini kopyalıyordu, yalnızca
11'i @id ile referans veriyordu. Yapay zekâlar ve arama motorları için bu,
"Suu" adında 192 ayrı kuruluş gibi görünür — entity sinyali seyrelir.

NEDEN DÜĞÜMLERİ SİLMİYORUZ: Google, Article için publisher/author
özelliklerini SAYFADA bekler. Sadece {"@id": "..."} bırakmak, düğüm başka
sayfada tanımlı olduğu için zorunlu alanları kaybettirir. Doğru çözüm
mevcut düğümü olduğu gibi bırakıp ona kalıcı bir @id vermektir:
sayfa kendi kendine yeter, aynı zamanda tüm kopyalar tek kimlikte birleşir.

Eşlenen entity'ler:
    Organization "Suu"                → https://suuapp.com/#organization
    Person "Furkan Mert Fındıklı"     → https://suuapp.com/#furkan
    MobileApplication/SoftwareApplication "Suu" → PLATFORMA GÖRE:
        yalnız iOS sinyali (App Store URL'si / operatingSystem iOS)
                                      → https://suuapp.com/#suuapp-ios
        yalnız Android sinyali (Google Play URL'si / operatingSystem Android)
                                      → https://suuapp.com/#suuapp-android
        iki platform birden ya da hiç sinyal yok → DOKUNULMAZ (raporlanır)

NEDEN PLATFORMA GÖRE: eskiden her "Suu" uygulama düğümü #suuapp-ios'a
bağlanıyordu. Play bağlantılı, "Android + iOS" diyen ve Play puanını taşıyan
karma bir düğüm böylece iOS kimliğine yapışıyor; Google Play'in 4.9 / 2847
puanı App Store uygulamasınınmış gibi görünüyordu (bkz. suu-facts.json →
numbers._rating_comment). Karma düğüm iki kimliğe birden bölünemez; elle iki
platform düğümüne ayrılması gerekir — script tahmin yürütmez.

Kullanım:
    python3 scripts/inject-entity-ids.py            # önizleme
    python3 scripts/inject-entity-ids.py --apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"

SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "content"}
SKIP_FILES = {"og-image-template.html"}

RE_LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.DOTALL)

# (@type kümesi, name) → @id
ENTITY_IDS: list[tuple[set[str], str, str]] = [
    ({"Organization", "NewsMediaOrganization"}, "Suu", f"{BASE}/#organization"),
    ({"Person"}, "Furkan Mert Fındıklı", f"{BASE}/#furkan"),
]

# Uygulama düğümleri adla değil PLATFORMLA eşlenir (bkz. app_platform).
APP_TYPES = {"MobileApplication", "SoftwareApplication", "HealthAndFitnessApplication"}
APP_NAME = "Suu"
APP_IDS = {
    "ios": f"{BASE}/#suuapp-ios",
    "android": f"{BASE}/#suuapp-android",
}
AMBIGUOUS = "(dokunulmadı) platformu belirsiz/karma Suu uygulama düğümü"

IOS_HOSTS = ("apps.apple.com", "itunes.apple.com")
ANDROID_HOSTS = ("play.google.com",)
RE_IOS_OS = re.compile(r"(?i)\b(?:ios|ipados|watchos)\b")
RE_ANDROID_OS = re.compile(r"(?i)\bandroid\b")


def types_of(node: dict) -> set[str]:
    t = node.get("@type")
    if isinstance(t, str):
        return {t}
    if isinstance(t, list):
        return set(t)
    return set()


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def app_platform(node: dict) -> str | None:
    """Uygulama düğümünün platformu: "ios", "android" ya da None (belirsiz/karma).

    Sinyaller: mağaza URL'leri (url, downloadUrl, installUrl, sameAs ve
    offers[].url) ile operatingSystem. İki platformun sinyali birden varsa
    — örneğin operatingSystem ["Android", "iOS"] ya da hem App Store hem Play
    teklifi — düğüm karmadır ve None döner: tek bir kimliğe bağlanamaz.
    """
    urls: list[str] = []
    for key in ("url", "downloadUrl", "installUrl", "sameAs"):
        urls += _strings(node.get(key))
    offers = node.get("offers")
    for offer in offers if isinstance(offers, list) else [offers]:
        if isinstance(offer, dict):
            urls += _strings(offer.get("url"))
    os_text = " ".join(_strings(node.get("operatingSystem")))

    ios = any(h in u for u in urls for h in IOS_HOSTS) or bool(RE_IOS_OS.search(os_text))
    android = any(h in u for u in urls for h in ANDROID_HOSTS) or bool(RE_ANDROID_OS.search(os_text))
    if ios and not android:
        return "ios"
    if android and not ios:
        return "android"
    return None


def is_app_node(node: dict) -> bool:
    return node.get("name") == APP_NAME and bool(types_of(node) & APP_TYPES)


def match_id(node: dict) -> str | None:
    name = node.get("name")
    if not isinstance(name, str):
        return None
    tset = types_of(node)
    for types, expected, entity_id in ENTITY_IDS:
        if name == expected and tset & types:
            return entity_id
    if is_app_node(node):
        platform = app_platform(node)
        return APP_IDS[platform] if platform else None
    return None


def walk(obj, stats: dict, skipped: dict | None = None) -> object:
    """Ağacı gez, eşleşen düğümlere @id ekle (varsa dokunma).

    skipped: platformu belirlenemediği için BİLEREK atlanan uygulama
    düğümlerinin sayacı — yalnızca rapor içindir, dosyayı değiştirmez.
    """
    if skipped is None:
        skipped = {}
    if isinstance(obj, list):
        return [walk(x, stats, skipped) for x in obj]
    if not isinstance(obj, dict):
        return obj

    node = {k: walk(v, stats, skipped) for k, v in obj.items()}

    if "@id" not in node and is_app_node(node) and app_platform(node) is None:
        skipped[AMBIGUOUS] = skipped.get(AMBIGUOUS, 0) + 1

    entity_id = match_id(node)
    if entity_id and "@id" not in node:
        # @id'yi @type'ın hemen ardına koy — okunabilirlik için
        rebuilt: dict = {}
        for k, v in node.items():
            rebuilt[k] = v
            if k == "@type":
                rebuilt["@id"] = entity_id
        if "@type" not in rebuilt:
            rebuilt["@id"] = entity_id
        stats[entity_id] = stats.get(entity_id, 0) + 1
        return rebuilt

    return node


def process(html: str, stats: dict, skipped: dict | None = None) -> tuple[str, bool]:
    changed = False
    if skipped is None:
        skipped = {}

    def repl(m: re.Match) -> str:
        nonlocal changed
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)          # ayrıştırılamayanı ellemeyiz

        local: dict = {}
        new_data = walk(data, local, skipped)
        if not local:
            return m.group(0)

        for k, v in local.items():
            stats[k] = stats.get(k, 0) + v

        out = json.dumps(new_data, ensure_ascii=False, indent=2)
        out = out.replace("<", "\\u003c").replace(">", "\\u003e")
        changed = True
        return f"{open_tag}\n{out}\n    {close_tag}"

    return RE_LD.sub(repl, html), changed


def iter_html() -> list[Path]:
    files = []
    for p in ROOT.rglob("*.html"):
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if p.name in SKIP_FILES:
            continue
        files.append(p)
    return sorted(files)


def main() -> int:
    apply = "--apply" in sys.argv
    stats: dict[str, int] = {}
    touched: list[str] = []
    ambiguous_pages: list[str] = []

    for path in iter_html():
        try:
            html = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        skipped: dict[str, int] = {}
        new, changed = process(html, stats, skipped)
        if skipped:
            ambiguous_pages.append(str(path.relative_to(ROOT)))
        if changed and new != html:
            touched.append(str(path.relative_to(ROOT)))
            if apply:
                path.write_text(new, encoding="utf-8")

    print(f"{len(touched)} sayfada @id eklenecek\n")
    for entity_id, count in sorted(stats.items(), key=lambda kv: -kv[1]):
        print(f"  {count:>4} × {entity_id}")

    if ambiguous_pages:
        print(f"\n{len(ambiguous_pages)} sayfada {AMBIGUOUS} — elle iOS/Android "
              f"düğümlerine ayrılmalı:")
        for page in ambiguous_pages:
            print(f"    {page}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{mode}")
    if not apply and touched:
        print("Uygulamak için: python3 scripts/inject-entity-ids.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
