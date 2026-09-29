#!/usr/bin/env python3
"""
Suu — Gerçek denetleyicisi (fact checker)

content/suu-facts.json tek doğruluk kaynağıdır. Bu script sitedeki
tüm dosyaları tarayıp bu kaynakla ÇELİŞEN iddiaları raporlar.

Neden önemli: yapay zekâ asistanları birden fazla kaynağı karşılaştırır.
Sitede "Apple Watch var" yazarken mağazada "yakında" yazıyorsa, model
her iki kaynağa da güvenmez — GEO'da en pahalı hata budur.

Kullanım:
    python3 scripts/check-facts.py            # tüm site
    python3 scripts/check-facts.py index.html # tek dosya
    python3 scripts/check-facts.py --quiet    # sadece hata sayısı

Çıkış kodu: 'error' seviyesinde bulgu varsa 1, yoksa 0.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FACTS_PATH = ROOT / "content" / "suu-facts.json"

SCAN_SUFFIXES = {".html", ".txt", ".json", ".md"}
SKIP_DIRS = {".git", ".github", ".claude", ".kilo", "node_modules", ".qodo", "scripts", "content", "donations"}
SKIP_FILES = {"app-readme.md", "aso-store-listing.md", "cache-bust.txt", "donations.json"}

ERROR, WARN = "error", "warn"


# ───────────────────────────────────────────────────────────
# Kurallar
#
# pattern  : aranan (eski/çelişkili) ifade
# unless   : (isteğe bağlı) aynı satırda geçerse bulgu sayılmaz — dürüst
#            "henüz yok / planlanıyor" cümlelerini yanlış alarmdan ayırır
# message  : neyin yanlış olduğu
# fix      : ne yazması gerektiği
#
# FILE_RULES satır değil dosya düzeyinde çalışır: "şu dosyada şu OLMALI".
# ───────────────────────────────────────────────────────────
def build_rules(facts: dict) -> list[dict]:
    beverages = facts["numbers"]["beverages"]
    lang_count = facts["languages"]["count"]
    watch = facts["platform_matrix"]["apple_watch"]["ios"]

    rules: list[dict] = [
        {
            "id": "beverages-count",
            "severity": ERROR,
            "pattern": re.compile(
                r"(?i)\b100\s*\+?\s*(?:farkl[ıi]\s+)?"
                r"(?:i[çc]ecek|beverage|drink|напитк|مشروب)",
            ),
            "message": "Eski içecek sayısı ('100+')",
            "fix": f"{beverages} içecek",
        },
        {
            "id": "language-count",
            "severity": ERROR,
            "pattern": re.compile(
                r"(?i)\b4\s*(?:farkl[ıi]\s+)?(?:dil(?:de|i|e)?|languages?|языках?|لغات)\b"
            ),
            "message": "Eski dil sayısı ('4 dil')",
            "fix": f"{lang_count} dil",
        },
        {
            "id": "language-list",
            "severity": ERROR,
            "pattern": re.compile(
                r"(?i)T[üu]rk[çc]e,?\s*[İI]ngilizce,?\s*(?:ve\s*)?Rus[çc]a(?:,?\s*(?:ve\s*)?Arap[çc]a)?"
                r"|Turkish,?\s*English,?\s*Russian\s*(?:and|&)\s*Arabic"
            ),
            "message": "Eski dil listesi (yalnızca 4 dil sayılıyor)",
            "fix": "Türkçe, English, العربية, Deutsch, Italiano, Русский, हिन्दी",
        },
        {
            "id": "ga-placeholder",
            "severity": ERROR,
            "pattern": re.compile(r"GA_MEASUREMENT_ID"),
            "message": "Google Analytics placeholder — hiç veri toplamıyor",
            "fix": "gerçek GA4 ölçüm ID'si (G-XXXXXXXXXX) veya bloğu tamamen kaldır",
        },
        {
            # 2026-09-14: Suu iki kişilik bağımsız ekip (entities.team). "Tek geliştirici"
            # iddiası hem ekip sayfalarıyla hem dış kaynaklardaki ekip anlatımıyla çelişir.
            "id": "solo-developer-claim",
            "severity": ERROR,
            "pattern": re.compile(
                r"(?i)single-handedly|built by one developer|by a single developer|as a solo developer|"
                r"tek başına geliştir|tek geliştiricisi|bireysel olarak geliştiril|"
                r"بواسطة مطور واحد|يطوّره مطوّر واحد|одним разработчиком|делает один разработчик|"
                r"eines einzelnen Entwicklers|da un solo sviluppatore|один розробник"
            ),
            "message": "'Tek geliştirici' iddiası — Suu iki kişilik bağımsız ekip",
            "fix": "küçük bağımsız ekip (Furkan Mert Fındıklı + Mert Öz)",
        },
        {
            # Uygulama arayüzü 7 dil: tr en ar de it ru hi. Ukraynaca YALNIZCA sitede.
            # Dürüst "henüz yok / planlanıyor / İngilizce arayüz" cümleleri serbest.
            "id": "ukrainian-ui-claim",
            "severity": ERROR,
            "pattern": re.compile(
                r"(?i)(?:застосун\w*|додат\w*|інтерфейс\w*|\bapp\b|\bUI\b)[^.<\n]{0,60}(?:українськ\w*|in Ukrainian)"
                r"|(?:українськ\w*|\bUkrainian\b)[^.<\n]{0,40}(?:інтерфейс\w*|локалізац\w*|interface|locali[sz]ation)"
            ),
            "unless": re.compile(r"(?i)в планах|поки що|ще не|наразі не|незабаром|немає|planned|not yet|coming"),
            "message": "Uygulamanın Ukraynaca arayüzü var gibi anlatılıyor — arayüz Ukraynaca DEĞİL",
            "fix": "Українська локалізація в планах; поки що зручно користуватися англійською версією інтерфейсу",
        },
        {
            # Uygulama kataloğu: filtre kahve 0.8, Türk kahvesi 0.7, espresso 0.5
            # (suu-facts.json → beverage_hydration). Sitenin eski "kahve 0.60 / ~%60" değeri yanlış.
            "id": "coffee-hydration-stale",
            "severity": ERROR,   # 2026-09-27 site temizlendi; geri gelirse yayın durur
            "pattern": re.compile(
                r"(?i)(?:coffee|kahve|кофе|قهوة|kaffee|caff[èe]|кава)[^<\n]{0,80}?"
                r"(?:0[.,]60\b|~\s?%\s?60\b|~\s?60\s?%|%60\b)"
                r"|factor:\s?0\.60"
            ),
            "message": "Eski kahve hidrasyon katsayısı (0.60 / ~%60)",
            "fix": f"filtre kahve {facts['beverage_hydration']['factors']['filter_coffee']}, "
                   f"Türk kahvesi {facts['beverage_hydration']['factors']['turkish_coffee']}, "
                   f"espresso {facts['beverage_hydration']['factors']['espresso']}",
        },
        {
            # Alkol katsayısı iOS (1.0) ve Android (-0.2/-0.4/-0.8) arasında farklı —
            # uygulamada eşitlenene kadar sayı yayınlanmaz (beverage_hydration.alcohol).
            "id": "alcohol-negative-factor",
            "severity": ERROR,   # 2026-09-27 site temizlendi; geri gelirse yayın durur
            "pattern": re.compile(
                r"(?i)(?:alcohol|alkol|алкогол\w*|الكحول|alkohol|alcol|пиво|beer|bira|wine|şarap|вино)"
                r"[^<\n]{0,80}?[-−–]\s?0[.,][2-8]\b"
            ),
            "message": "Alkol için negatif hidrasyon katsayısı yazılmış — platformlar arasında farklı, yayınlanmamalı",
            "fix": "niteliksel anlatım: alkol su hedefini 10 ml saf alkol başına +250 ml artırır",
        },
    ]

    # Apple Watch: mağaza açıklaması "yakında" diyorsa, "var" iddiaları hatadır.
    if watch == "coming_soon":
        rules += [
            {
                "id": "apple-watch-standalone",
                "severity": ERROR,
                "pattern": re.compile(
                    r"(?i)(?:standalone|ba[ğg][ıi]ms[ıi]z|independent|отдельн\w*|مستقل)"
                    r"[^.<\n]{0,60}Apple\s*Watch"
                    r"|Apple\s*Watch[^.<\n]{0,60}"
                    r"(?:standalone|ba[ğg][ıi]ms[ıi]z|independent|отдельн\w*|مستقل)"
                ),
                "message": "Apple Watch 'bağımsız uygulama var' iddiası",
                "fix": "Apple Watch desteği — yakında",
            },
            {
                "id": "apple-watch-mention",
                "severity": WARN,
                "pattern": re.compile(r"(?i)apple\s*watch|watchOS"),
                "message": "Apple Watch geçiyor — 'yakında' olarak işaretlendiğinden gözden geçir",
                "fix": "mevcut bir özellikmiş gibi anlatılmadığından emin ol",
            },
        ]
    elif watch == "yes":
        # Watch uygulaması yayında: "yakında / geliştiriliyor / henüz yok" iddiaları artık yanlış.
        rules += [
            {
                "id": "apple-watch-stale-soon",
                "severity": ERROR,
                "pattern": re.compile(
                    r"(?i)(?:apple\s*watch|watchos)[^.<\n]{0,90}"
                    r"(?:coming\s*soon|in\s+development|on\s+the\s+way|not\s+(?:yet\s+)?released|no\s+(?:dedicated\s+)?(?:apple\s*)?watch\s+app\s+yet|"
                    r"yakında|yolda|geliştiriliyor|henüz\s+(?:yok|adanmış|özel)|"
                    r"in\s+arbeit|noch\s+aussteht|noch\s+keine|demnächst|in\s+arrivo|deve\s+ancora|non\s+ha\s+ancora|"
                    r"в\s+разработке|пока\s+нет|скоро\s+выйдет|قيد\s+التطوير|لم\s+يصدر|قريبًا|"
                    r"у\s+розробці|поки\s+немає|ще\s+попереду|незабаром|जल्द|अभी\s+नहीं)"
                    r"|(?:coming\s*soon|in\s+development|yakında|in\s+arbeit|in\s+arrivo|в\s+разработке|قيد\s+التطوير|у\s+розробці)"
                    r"[^.<\n]{0,60}(?:apple\s*watch|watchos)"
                ),
                "message": "Apple Watch uygulaması yayında ama metin 'yakında / geliştiriliyor' diyor",
                "fix": "Apple Watch uygulaması mevcut — su, sesli öğün, GPS'li antrenman",
            },
            {
                # Sesli öğün analizi iPhone'da tamamlanır; su/antrenman kuyruğa alınıp
                # eşitlenir. "Bağımsız / standalone" abartı (bkz. suu-facts device_integrations).
                "id": "apple-watch-standalone-claim",
                "severity": WARN,
                "pattern": re.compile(
                    r"(?i)(?:standalone|автономн\w*|eigenständig\w*|bağımsız)[^.<\n]{0,40}(?:apple\s*watch|watchos)"
                    r"|(?:apple\s*watch|watchos)[^.<\n]{0,20}(?:standalone|автономн\w*)"
                ),
                "message": "Apple Watch uygulaması 'bağımsız/standalone' diye anlatılıyor",
                "fix": "su ve antrenman iPhone yanında olmasa da saatte kaydedilir, sonra eşitlenir; sesli öğün analizi iPhone'da tamamlanır",
            },
        ]

    # Kilit ekranı widget'ı yok: yalnızca ana ekran widget'ı (küçük/orta/büyük) +
    # kilit ekranında Live Activity. 2026-09-29'da 7 dilde "Home and Lock Screen
    # widgets" iddiası bulunup düzeltildi. Olumsuz cümleler ve rakip hücreleri hariç.
    if facts["platform_matrix"].get("lock_screen_widgets", {}).get("ios") == "no":
        rules.append({
            "id": "lock-screen-widget-claim",
            "severity": ERROR,
            "pattern": re.compile(
                r"(?i)lock[- ]?screen\s+widget|home\s*(?:/|and)\s*lock[- ]?screen\s+widget"
                r"|kilit\s+ekran[ıi]\s+(?:ve\s+ana\s+ekran\s+)?widget"
                r"|виджет\w*\s+(?:на\s+)?(?:главн\w*\s+)?экран\w*\s+блокировки|экран\w*\s+блокировки\s+трёх"
                r"|ودجات\s+شاشة\s+القفل|وشاشة\s+القفل\s+بثلاثة"
                r"|Sperrbildschirm-?\s*(?:und\s+Homescreen-)?Widgets|widget\s+(?:della\s+)?schermata\s+di\s+blocco"
                r"|віджет\w*\s+на\s+(?:заблокованому|екрані\s+блокування)|लॉक\s+स्क्रीन\s+(?:और\s+होम\s+स्क्रीन\s+)?विजेट"
            ),
            "unless": re.compile(
                r"(?i)\bno\b|isn't|\byok|нет\b|немає|لا\s+توجد|gibt\s+es\s+nicht|non\s+ci\s+sono|नहीं"
                r"|WaterMinder|Waterllama|Hydro\s+Coach"
            ),
            "message": "Suu'da kilit ekranı widget'ı yok (yalnızca ana ekran widget'ı + Live Activity)",
            "fix": "ana ekran widget'ı (küçük/orta/büyük; iOS 17+ tek dokunuşla su) — kilit ekranında Live Activity",
        })

    return rules


# Dosya düzeyi kurallar: seçilen dosyalarda bir işaretin BULUNMASI gerekir.
FILE_RULES: list[dict] = [
    {
        # content/guides/ rehberleri sağlık sorusu cevaplıyor: her biri görünür bir
        # "tıbbi tavsiye değildir / sağlık uzmanına danış" bloğu taşımalı (Play Sağlık
        # İçerikleri politikasıyla aynı ilke).
        "id": "guide-health-note",
        "severity": ERROR,
        "applies": re.compile(r"Kaynak: content/guides/"),
        "requires": re.compile(r'class="[^"]*\bhealth-note\b'),
        "message": "Rehber sayfasında sağlık notu (health-note) yok",
        "fix": "content/guides/<konu>.json → pages.<lang>.health_note",
    },
]


def iter_files(explicit: list[str]) -> list[Path]:
    if explicit:
        return [ROOT / p for p in explicit]

    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts[:-1]):
            continue
        if path.name in SKIP_FILES:
            continue
        files.append(path)
    return sorted(files)


def scan(path: Path, rules: list[dict]) -> list[tuple[dict, int, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    hits: list[tuple[dict, int, str]] = []
    for rule in FILE_RULES:
        if rule["applies"].search(text) and not rule["requires"].search(text):
            hits.append((rule, 1, "(dosya düzeyi)"))
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule in rules:
            match = rule["pattern"].search(line)
            if match and rule.get("unless") and rule["unless"].search(line):
                continue
            if match:
                snippet = line.strip()
                if len(snippet) > 110:
                    start = max(0, match.start() - 40)
                    snippet = "…" + snippet[start : start + 110] + "…"
                hits.append((rule, lineno, snippet))
    return hits


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv

    if not FACTS_PATH.exists():
        print(f"HATA: {FACTS_PATH.relative_to(ROOT)} bulunamadı.", file=sys.stderr)
        return 2

    facts = json.loads(FACTS_PATH.read_text(encoding="utf-8"))
    rules = build_rules(facts)

    # rule_id → [(dosya, satır, parça)]
    findings: dict[str, list[tuple[Path, int, str]]] = {}
    for path in iter_files(args):
        for rule, lineno, snippet in scan(path, rules):
            findings.setdefault(rule["id"], []).append((path, lineno, snippet))

    by_id = {r["id"]: r for r in rules + FILE_RULES}
    errors = sum(
        len(v) for k, v in findings.items() if by_id[k]["severity"] == ERROR
    )
    warns = sum(len(v) for k, v in findings.items() if by_id[k]["severity"] == WARN)

    if not quiet:
        for rule in rules + FILE_RULES:
            hits = findings.get(rule["id"])
            if not hits:
                continue
            tag = "HATA" if rule["severity"] == ERROR else "UYARI"
            print(f"\n[{tag}] {rule['message']}  ({len(hits)} bulgu)")
            print(f"       → olması gereken: {rule['fix']}")
            shown = hits if rule["severity"] == ERROR else hits[:15]
            for path, lineno, snippet in shown:
                print(f"       {path.relative_to(ROOT)}:{lineno}  {snippet}")
            if len(hits) > len(shown):
                print(f"       … ve {len(hits) - len(shown)} tane daha")

        pending = facts.get("_needs_confirmation") or []
        if pending:
            print(f"\n[BEKLEYEN] suu-facts.json içinde teyit bekleyen {len(pending)} madde:")
            for item in pending:
                print(f"       • {item}")

    print(f"\nÖzet: {errors} hata, {warns} uyarı.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
