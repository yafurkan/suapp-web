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
SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "scripts", "content", "donations"}
SKIP_FILES = {"app-readme.md", "aso-store-listing.md", "cache-bust.txt", "donations.json"}

ERROR, WARN = "error", "warn"


# ───────────────────────────────────────────────────────────
# Kurallar
#
# pattern  : aranan (eski/çelişkili) ifade
# message  : neyin yanlış olduğu
# fix      : ne yazması gerektiği
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

    return rules


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
    for lineno, line in enumerate(text.splitlines(), start=1):
        for rule in rules:
            match = rule["pattern"].search(line)
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

    by_id = {r["id"]: r for r in rules}
    errors = sum(
        len(v) for k, v in findings.items() if by_id[k]["severity"] == ERROR
    )
    warns = sum(len(v) for k, v in findings.items() if by_id[k]["severity"] == WARN)

    if not quiet:
        for rule in rules:
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
