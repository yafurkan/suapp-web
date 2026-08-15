#!/usr/bin/env python3
"""
Suu — sütunlar arası bağlantı (su → kalori/egzersiz)

Sitenin trafiği neredeyse tamamen SU sorgularından geliyor; kalori ve
egzersiz kümesi ise yeni ve otoritesi düşük. Ama 35 TR su yazısının
yalnızca 2'si kalori/egzersiz sayfalarına bağlanıyordu — yani sitenin
biriktirdiği otorite yeni sütunlara hiç akmıyor.

Bu script her su/genel yazısının mevcut "İlgili Yazılar" ızgarasına
konusuyla İLGİLİ en fazla iki kalori/egzersiz bağlantısı ekler. Bağlantı
seçimi yazının konusuna göre yapılır (spor yazısı → egzersiz kalorisi,
kilo yazısı → kalori açığı, içecek yazısı → kalori sayma).

Başlıklar hedef sayfanın kendi <title>'ından okunur; elle yazılmaz.

Kullanım:
    python3 scripts/link-pillars.py            # önizleme
    python3 scripts/link-pillars.py --apply
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MARKER = "<!-- sütunlar arası bağlantı: scripts/link-pillars.py -->"

# Yazının konusu → hedef sayfalar (öncelik sırasıyla, en fazla 2 kullanılır)
# Anahtar kelimeler slug üzerinde aranır.
ROUTES = {
    "tr": {
        "dir": "blog",
        "tag_calories": "Kalori",
        "tag_exercise": "Egzersiz",
        "rules": [
            (r"spor|egzersiz|aktivite|kosu|antren",
             [("egzersizde-kalori-yakimi.html", "exercise"),
              ("en-iyi-egzersiz-takip-uygulamasi.html", "exercise")]),
            (r"kilo|zayifla|kilo-ve-su|su-icince-kilo",
             [("kalori-acigi.html", "calories"),
              ("en-iyi-kalori-uygulamasi.html", "calories")]),
            (r"kahve|cay|icecek|enerji|meyve|alkol|kafein|seker",
             [("en-iyi-kalori-uygulamasi.html", "calories"),
              ("fotografla-kalori-sayma.html", "calories")]),
            (r"",
             [("su-kalori-egzersiz-tek-uygulama.html", "calories"),
              ("en-iyi-kalori-uygulamasi.html", "calories")]),
        ],
    },
    "en": {
        "dir": "blog/en",
        "tag_calories": "Calories",
        "tag_exercise": "Exercise",
        "rules": [
            (r"sport|exercise|activity|running|workout|hydration-and-exercise",
             [("calories-burned-exercise.html", "exercise"),
              ("best-workout-tracker-app.html", "exercise")]),
            (r"weight|lose|slim",
             [("calorie-deficit.html", "calories"),
              ("best-calorie-counting-app.html", "calories")]),
            (r"coffee|tea|juice|energy|alcohol|caffeine|sugar|drink",
             [("best-calorie-counting-app.html", "calories"),
              ("macro-calculation.html", "calories")]),
            (r"",
             [("water-calorie-exercise-one-app.html", "calories"),
              ("best-calorie-counting-app.html", "calories")]),
        ],
    },
}

# Bu sayfalar zaten kalori/egzersiz kümesinin parçası — kaynak olarak alınmaz
CLUSTER = {
    "tr": {"en-iyi-kalori-uygulamasi", "kalori-acigi", "makro-hesaplama",
           "fotografla-kalori-sayma", "egzersizde-kalori-yakimi", "sesli-kalori-girisi",
           "en-iyi-egzersiz-takip-uygulamasi", "kalori-ve-egzersiz-takibi-bir-arada",
           "ucretsiz-kalori-sayaci", "en-iyi-fotografla-kalori-uygulamasi",
           "su-kalori-egzersiz-tek-uygulama", "suu-vs-cal-ai", "suu-vs-myfitnesspal",
           "suu-vs-yazio"},
    "en": {"best-calorie-counting-app", "calorie-deficit", "macro-calculation",
           "photo-calorie-counting", "calories-burned-exercise", "voice-calorie-logging",
           "best-workout-tracker-app", "calorie-counter-with-exercise-tracker",
           "free-calorie-counter-app", "best-photo-calorie-app",
           "water-calorie-exercise-one-app", "suu-vs-cal-ai", "suu-vs-myfitnesspal",
           "suu-vs-yazio", "lifesum-vs-yazio", "yazio-vs-myfitnesspal",
           "cronometer-vs-yazio"},
}

RE_GRID = re.compile(r'(<div class="related-grid">)(.*?)(</div>\s*</div>)', re.DOTALL)
# İkinci kalıp: <div class="related"><h3>…</h3><ul><li>…</li></ul></div>
RE_LIST = re.compile(r'(<div class="related">.*?<ul>)(.*?)(</ul>)', re.DOTALL)

# Üçüncü durum: ilgili bölümü hiç yok → sona kendi bloğunu bas
STANDALONE_ANCHORS = ["</article>", "<footer", "</main>"]

HEADING = {"tr": "Kalori ve egzersiz tarafı", "en": "The calorie and exercise side"}


def page_title(path: Path) -> str:
    page = path.read_text(encoding="utf-8")
    m = re.search(r'<meta property="og:title" content="([^"]+)"', page)
    if not m:
        m = re.search(r"<title>(.*?)</title>", page, re.DOTALL)
    title = html.unescape(m.group(1)) if m else path.stem
    title = re.sub(r"\s*[|—–]\s*Suu.*$", "", title).strip()
    # kart başlığı kısa olmalı
    return title if len(title) <= 62 else title[:59].rsplit(" ", 1)[0] + "…"


def targets_for(slug: str, cfg: dict) -> list[tuple[str, str]]:
    for pattern, targets in cfg["rules"]:
        if not pattern or re.search(pattern, slug):
            return targets
    return []


def main() -> int:
    apply = "--apply" in sys.argv
    touched, links, skipped = 0, 0, []

    for lang, cfg in ROUTES.items():
        folder = ROOT / cfg["dir"]
        titles: dict[str, str] = {}

        for path in sorted(folder.glob("*.html")):
            slug = path.stem
            if slug in CLUSTER[lang]:
                continue

            page = original = path.read_text(encoding="utf-8")
            if MARKER in page:
                continue
            # Yönlendirme kabuğu — içeriği yok, bağlantı eklenmez
            if 'http-equiv="refresh"' in page:
                continue

            chosen = []
            for target, pillar in targets_for(slug, cfg):
                if not (folder / target).exists():
                    continue
                if f'href="{target}"' in page:      # zaten bağlı
                    continue
                if target not in titles:
                    titles[target] = page_title(folder / target)
                tag = cfg["tag_exercise"] if pillar == "exercise" else cfg["tag_calories"]
                chosen.append((target, tag, titles[target]))
                if len(chosen) == 2:
                    break

            if not chosen:
                continue

            # 1) Kart ızgarası varsa kart olarak ekle
            m = RE_GRID.search(page)
            if m:
                block = MARKER + "\n"
                for target, tag, title in chosen:
                    block += (
                        f'            <a href="{target}" class="related-card">\n'
                        f'                <div class="tag">{html.escape(tag)}</div>\n'
                        f'                <h4>{html.escape(title)}</h4>\n'
                        f"            </a>\n"
                    )
                page = page[:m.end(2)] + "\n" + block + page[m.end(2):]

            else:
                # 2) Madde listesi varsa <li> olarak ekle
                m = RE_LIST.search(page)
                if m:
                    block = "\n        " + MARKER + "\n"
                    for target, tag, title in chosen:
                        block += (f'        <li><a href="{target}">'
                                  f"{html.escape(title)}</a></li>\n")
                    page = page[:m.end(2)] + block + "    " + page[m.end(2):]

                else:
                    # 3) Hiç ilgili bölümü yok → kendi kendine yeten blok
                    items = "".join(
                        f'      <li style="margin-block-end:6px"><a href="{target}" '
                        f'style="color:#1E88E5;font-weight:600;text-decoration:none">'
                        f"{html.escape(title)}</a></li>\n"
                        for target, _tag, title in chosen)
                    block = (
                        f"\n{MARKER}\n"
                        '<div style="max-width:760px;margin:32px auto;padding:20px;'
                        'border-radius:10px;background:rgba(30,136,229,.06)">\n'
                        f'  <h3 style="font-size:1rem;margin:0 0 12px">{html.escape(HEADING[lang])}</h3>\n'
                        f'  <ul style="margin:0 0 0 20px;padding:0">\n{items}  </ul>\n'
                        "</div>\n\n"
                    )
                    for anchor in STANDALONE_ANCHORS:
                        idx = page.find(anchor)
                        if idx != -1:
                            page = page[:idx] + block + page[idx:]
                            break
                    else:
                        skipped.append(str(path.relative_to(ROOT)))
                        continue

            if page != original:
                touched += 1
                links += len(chosen)
                if apply:
                    path.write_text(page, encoding="utf-8")

    print(f"  {touched} sayfaya {links} sütunlar arası bağlantı")
    if skipped:
        print(f"  ⚠ ilgili-yazılar ızgarası olmayan {len(skipped)} sayfa atlandı:")
        for s in skipped[:8]:
            print(f"      {s}")
        if len(skipped) > 8:
            print(f"      … ve {len(skipped) - 8} tane daha")

    mode = "UYGULANDI" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{mode}")
    if not apply and touched:
        print("Uygulamak için: python3 scripts/link-pillars.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
