#!/usr/bin/env python3
"""
Suu — Elle yazılmış blog yazılarından rehberlere bağlantı

content/guides/ rehberleri (yapay zekâ sorusu rehberleri) yeni ve iç bağlantı
almadan keşfedilmesi yavaş. Bu script, konu olarak komşu olan ELLE YAZILMIŞ
yazıların "İlgili yazılar" ızgarasına (.related-grid) rehber kartı ekler.

Eşleme kayıt defteri KÜMESİ üzerinden yapılır (slug kalıbıyla değil): kaynak
küme → hedef rehber kümesi. Böylece her dil kendiliğinden çözülür; bir dilde
kaynak ya da hedef sayfa yoksa o dil atlanır.

Güvenlik:
    · Üretilmiş sayfalar ("ÜRETİLMİŞ DOSYA") atlanır — onların bağlantıları
      JSON'daki `related` dizisinden gelir, buraya yazılanı sonraki build siler.
    · Hedefe zaten bağlantı varsa tekrar eklenmez (idempotent).
    · Izgaranın kapanış </div>'ı iç içe div'ler sayılarak bulunur
      (link-pillars.py'deki eski kalıp hatası burada tekrarlanmaz).

Kullanım:
    python3 scripts/link-guides.py            # önizleme
    python3 scripts/link-guides.py --apply
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "content" / "page-registry.json"
GUIDES = ROOT / "content" / "guides"
DEFAULT = "tr"
GENERATED_MARK = "ÜRETİLMİŞ DOSYA"

# Kaynak küme (elle yazılmış yazı) → bağlanacak rehber kümeleri
LINKS: dict[str, list[str]] = {
    # zorunlu: yamyamlık sınırları — eski yazı derin cevaba yönlendirir
    "kalori-acigi": ["neden-kilo-veremiyorum"],
    "kilo-ve-su": ["neden-kilo-veremiyorum", "gece-atistirmasini-birakmak"],
    "susuzluk-belirtileri": ["neden-hep-yorgunum"],
    # konu komşuları
    "su-ve-uyku-kalitesi": ["neden-hep-yorgunum", "gece-atistirmasini-birakmak"],
    "kahveyi-azaltmak": ["kolayi-birakmak"],
    "enerji-icecegi-kontrolu": ["kolayi-birakmak"],
    "kafein-seker-takibi": ["kolayi-birakmak"],
    "meyve-suyu-vs-su": ["kolayi-birakmak"],
    "su-icme-lig-sistemi": ["spora-usenmek"],
    "_en_water-tracking-gamification": ["spora-usenmek"],
    "egzersizde-kalori-yakimi": ["spora-usenmek"],
    "spor-ve-hidrasyon": ["spora-usenmek"],
    "fotografla-kalori-sayma": ["kalori-saymak-sikici"],
    "sesli-kalori-girisi": ["kalori-saymak-sikici"],
    "makro-hesaplama": ["kalori-saymak-sikici"],
}

TAG = {"tr": "Rehber", "en": "Guide", "ar": "دليل", "ru": "Руководство",
       "de": "Ratgeber", "it": "Guida", "uk": "Посібник"}

RE_DIV = re.compile(r"<div\b|</div>", re.IGNORECASE)
GRID_OPEN = '<div class="related-grid">'
RE_CARD_INDENT = re.compile(r"\n([ \t]*)<a [^>]*class=\"related-card\"")
RE_LI_INDENT = re.compile(r"\n([ \t]*)<li\b")
# Izgara yoksa: <div class="related"><ul>…</ul> listesi ya da link-pillars.py'nin
# kendi kendine yeten bloğu (işaretçisinden sonraki ilk </ul>)
LIST_ANCHORS = ('<div class="related">', "<!-- sütunlar arası bağlantı: scripts/link-pillars.py -->")


def list_close(page: str) -> int | None:
    """İlgili-yazılar listesinin </ul> indeksi; yoksa None."""
    for anchor in LIST_ANCHORS:
        start = page.find(anchor)
        if start == -1:
            continue
        end = page.find("</ul>", start)
        if end != -1:
            return end
    return None


def rel_path(lang: str, slug: str) -> Path:
    return ROOT / (f"blog/{slug}.html" if lang == DEFAULT else f"blog/{lang}/{slug}.html")


def grid_close(page: str) -> int | None:
    start = page.find(GRID_OPEN)
    if start == -1:
        return None
    depth = 0
    for m in RE_DIV.finditer(page, start):
        if m.group(0).lower().startswith("<div"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return m.start()
    return None


def guide_titles() -> dict[str, dict[str, str]]:
    """rehber kümesi → {dil: kısa başlık (og_title)}"""
    out: dict[str, dict[str, str]] = {}
    for p in sorted(GUIDES.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        out[d["cluster"]] = {l: pg["meta"]["og_title"] for l, pg in d["pages"].items()}
    return out


def main() -> int:
    apply = "--apply" in sys.argv
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))["blog"]
    titles = guide_titles()
    touched, added, skipped = 0, 0, []

    for src_cluster, targets in LINKS.items():
        src = reg.get(src_cluster, {})
        for lang, src_slug in src.items():
            path = rel_path(lang, src_slug)
            if not path.exists():
                continue
            page = original = path.read_text(encoding="utf-8")
            if GENERATED_MARK in page:
                continue
            for tgt_cluster in targets:
                tgt_slug = reg.get(tgt_cluster, {}).get(lang)
                title = titles.get(tgt_cluster, {}).get(lang)
                if not tgt_slug or not title or not rel_path(lang, tgt_slug).exists():
                    continue
                href = f"{tgt_slug}.html"
                if f'href="{href}"' in page:
                    continue
                close = grid_close(page)
                if close is not None:
                    grid = page[page.find(GRID_OPEN):close]
                    m = RE_CARD_INDENT.search(grid)
                    indent = m.group(1) if m else "            "
                    card = (f'\n{indent}<a href="{href}" class="related-card">'
                            f'<div class="tag">{html.escape(TAG[lang])}</div>'
                            f"<h4>{html.escape(title)}</h4></a>")
                else:
                    close = list_close(page)
                    if close is None:
                        skipped.append(f"{path.relative_to(ROOT)} (ilgili yazılar bölümü yok)")
                        break
                    block = page[:close]
                    m = None
                    for m in RE_LI_INDENT.finditer(block[-3000:]):
                        pass
                    indent = m.group(1) if m else "        "
                    card = f'\n{indent}<li><a href="{href}">{html.escape(title)}</a></li>'
                cut = close
                while cut > 0 and page[cut - 1] in " \t\n":
                    cut -= 1
                page = page[:cut] + card + page[cut:]
                added += 1
            if page != original:
                touched += 1
                print(f"  {path.relative_to(ROOT)}")
                if apply:
                    path.write_text(page, encoding="utf-8")

    print(f"\n{touched} sayfaya {added} rehber bağlantısı")
    for s in skipped:
        print(f"  ⚠ atlandı: {s}")
    print("UYGULANDI" if apply else "ÖNİZLEME (yazılmadı) — uygulamak için --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
