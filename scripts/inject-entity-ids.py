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
    MobileApplication/SoftwareApplication "Suu" → https://suuapp.com/#suuapp-ios

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
    ({"MobileApplication", "SoftwareApplication", "HealthAndFitnessApplication"},
     "Suu", f"{BASE}/#suuapp-ios"),
]


def types_of(node: dict) -> set[str]:
    t = node.get("@type")
    if isinstance(t, str):
        return {t}
    if isinstance(t, list):
        return set(t)
    return set()


def match_id(node: dict) -> str | None:
    name = node.get("name")
    if not isinstance(name, str):
        return None
    tset = types_of(node)
    for types, expected, entity_id in ENTITY_IDS:
        if name == expected and tset & types:
            return entity_id
    return None


def walk(obj, stats: dict) -> object:
    """Ağacı gez, eşleşen düğümlere @id ekle (varsa dokunma)."""
    if isinstance(obj, list):
        return [walk(x, stats) for x in obj]
    if not isinstance(obj, dict):
        return obj

    node = {k: walk(v, stats) for k, v in obj.items()}

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


def process(html: str, stats: dict) -> tuple[str, bool]:
    changed = False

    def repl(m: re.Match) -> str:
        nonlocal changed
        open_tag, body, close_tag = m.group(1), m.group(2), m.group(3)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return m.group(0)          # ayrıştırılamayanı ellemeyiz

        local: dict = {}
        new_data = walk(data, local)
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

    for path in iter_html():
        try:
            html = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new, changed = process(html, stats)
        if changed and new != html:
            touched.append(str(path.relative_to(ROOT)))
            if apply:
                path.write_text(new, encoding="utf-8")

    print(f"{len(touched)} sayfada @id eklenecek\n")
    for entity_id, count in sorted(stats.items(), key=lambda kv: -kv[1]):
        print(f"  {count:>4} × {entity_id}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{mode}")
    if not apply and touched:
        print("Uygulamak için: python3 scripts/inject-entity-ids.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
