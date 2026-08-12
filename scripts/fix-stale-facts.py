#!/usr/bin/env python3
"""
Suu — Eskimiş gerçeklerin toplu düzeltmesi

content/suu-facts.json ile çelişen mekanik ifadeleri tüm sitede düzeltir:
  • içecek sayısı: "100+" → 91
  • dil sayısı:    "4 dil" → 7 dil (ve 4'lü dil listeleri → 7'li)

Apple Watch gibi ANLAMSAL düzeltmeler bu scriptin kapsamında DEĞİLDİR —
onlar cümle yeniden yazımı gerektirir, elle yapılır.

Kullanım:
    python3 scripts/fix-stale-facts.py            # önizleme (dosyaya yazmaz)
    python3 scripts/fix-stale-facts.py --apply    # uygula
    python3 scripts/fix-stale-facts.py --apply --only beverages
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCAN_SUFFIXES = {".html", ".txt", ".json"}
SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo", "scripts", "content", "donations"}
# README.md sitenin KENDİ yapısını anlatıyor (site hâlâ 4 dilde) — elle güncellenecek.
SKIP_FILES = {"README.md", "app-readme.md", "aso-store-listing.md", "donations.json"}


# ───────────────────────────────────────────────────────────
# Kural grupları — (regex, replacement)
# Sıra önemli: uzun/spesifik kalıplar önce gelir.
# ───────────────────────────────────────────────────────────
RULES: dict[str, list[tuple[str, str]]] = {
    "beverages": [
        # Türkçe
        (r"100\s*\+\s*İçecek", "91 İçecek"),
        (r"100\s*\+\s*içecek", "91 içecek"),
        (r"100['’]den fazla içecek", "91 içecek"),
        (r"100['’]ün üzerinde içecek", "91 içecek"),
        (r"100\s*farklı içecek", "91 farklı içecek"),
        # English
        (r"100\s*\+\s*Beverages?", "91 Beverages"),
        (r"100\s*\+\s*Drinks?", "91 Drinks"),
        (r"100\s*\+\s*beverages?", "91 beverages"),
        (r"100\s*\+\s*drinks?", "91 drinks"),
        (r"(?:over|more than)\s+100\s+beverage categories", "91 beverage categories"),
        (r"(?:over|more than)\s+100\s+beverages?", "91 beverages"),
        (r"(?:over|more than)\s+100\s+drinks?", "91 drinks"),
        # Arabic — "أكثر من 100 مشروب" / "100+ مشروب" → "91 مشروبًا"
        (r"أكثر من\s*100\s*مشروب", "91 مشروبًا"),
        (r"100\s*\+\s*مشروب", "91 مشروبًا"),
        # Russian — "более 100 напитков" → "91 напиток"
        (r"более\s*100\s*напитк\w*", "91 напиток"),
        (r"свыше\s*100\s*напитк\w*", "91 напиток"),
        (r"100\s*\+\s*напитк\w*", "91 напиток"),
    ],
    "languages": [
        # Uzun/spesifik listeler önce. (RTL) etiketi Arapça'ya aittir —
        # listeyi genişletirken Arapça'nın yanında kalmalı.
        (
            r"4 Dil Tam Yerelleştirme: Türkçe, İngilizce, Rusça, Arapça \(RTL\)",
            "7 Dil Tam Yerelleştirme: Türkçe, İngilizce, Arapça (RTL), Almanca, İtalyanca, Rusça, Hintçe",
        ),
        # Türkçe — hâl ekli biçimler (Arapça'da → Hintçe'de, ünlü uyumu)
        (
            r"Türkçe, İngilizce, Rusça (ve|ile) Arapça['’]da \(RTL\)",
            r"Türkçe, İngilizce, Arapça (RTL), Almanca, İtalyanca, Rusça \1 Hintçe'de",
        ),
        (
            r"Türkçe, İngilizce, Rusça (ve|ile) Arapça['’]da",
            r"Türkçe, İngilizce, Arapça, Almanca, İtalyanca, Rusça \1 Hintçe'de",
        ),
        # Türkçe — eksiz biçimler
        (
            r"Türkçe, İngilizce, Rusça (ve|ile) Arapça \(RTL\)",
            r"Türkçe, İngilizce, Arapça (RTL), Almanca, İtalyanca, Rusça \1 Hintçe",
        ),
        (
            r"Türkçe, İngilizce, Rusça \(Русский\) (ve|ile) Arapça \(العربية, RTL\)",
            r"Türkçe, İngilizce, Arapça (العربية, RTL), Almanca, İtalyanca, Rusça (Русский) \1 Hintçe",
        ),
        (
            r"Türkçe, İngilizce, Rusça \(Русский\), Arapça \(العربية, RTL\)",
            "Türkçe, İngilizce, Arapça (العربية, RTL), Almanca, İtalyanca, Rusça (Русский), Hintçe",
        ),
        (
            r"Türkçe, İngilizce, Rusça (ve|ile) Arapça",
            r"Türkçe, İngilizce, Arapça, Almanca, İtalyanca, Rusça \1 Hintçe",
        ),
        (
            r"Türkçe, İngilizce, Rusça, Arapça",
            "Türkçe, İngilizce, Arapça, Almanca, İtalyanca, Rusça, Hintçe",
        ),
        # English
        (
            r"Turkish, English, Russian (?:and|&) Arabic \(RTL\)",
            "Turkish, English, Arabic (RTL), German, Italian, Russian and Hindi",
        ),
        (
            r"Turkish, English, Russian (?:and|&) Arabic",
            "Turkish, English, Arabic, German, Italian, Russian and Hindi",
        ),
        (r"TR\s*/\s*EN\s*/\s*AR\s*/\s*RU", "TR/EN/AR/DE/IT/RU/HI"),
        (r"TR\s*\+\s*EN\s*\+\s*RU\s*\+\s*AR", "TR + EN + AR + DE + IT + RU + HI"),
        (r"\bRU, EN, TR, AR\b", "RU, EN, TR, AR, DE, IT, HI"),
        (r"\bEN, TR, RU, AR\b", "EN, TR, RU, AR, DE, IT, HI"),
        (r"\bAR وEN وTR وRU\b", "AR وEN وTR وRU وDE وIT وHI"),
        # Sayılar
        (r"\b4 Dil\b", "7 Dil"),
        (r"\b4 dilde\b", "7 dilde"),
        (r"\b4 dil\b", "7 dil"),
        (r"\b4 Languages\b", "7 Languages"),
        (r"\b4 languages\b", "7 languages"),
        (r"\b4 языках\b", "7 языках"),
        (r"\b4 языка\b", "7 языков"),
        (r"\b4 لغات\b", "7 لغات"),
        (r"بـ\s*4\s*لغات", "بـ 7 لغات"),
    ],
    # Apple Watch mağaza açıklamasında "Yakında". Aşağıdakiler ifade
    # düzeyinde düzeltmelerdir; tam cümle yeniden yazımı gereken yerler
    # (SSS cevapları, adanmış blog yazıları) elle düzeltilir.
    "applewatch": [
        # ── Türkçe ──────────────────────────────────────────
        (r"Apple Watch Standalone \(SwiftUI\) uygulaması", "Apple Watch uygulaması (yakında)"),
        (r"Standalone watchOS app built with SwiftUI", "Coming soon"),
        (
            r"Suu['’]nun bağımsız \(standalone\) Apple Watch uygulaması SwiftUI ile geliştirilmiştir\.",
            "Suu'nun Apple Watch uygulaması yakında geliyor.",
        ),
        (r"\*\*Apple Watch\*\* \(SwiftUI standalone app\)", "**Apple Watch** (yakında)"),
        (r"\*\*Apple Watch\*\* \(bağımsız watchOS uygulaması\)", "**Apple Watch** (yakında)"),
        (r"\*\*Apple Watch sahipleri:\*\* Bağımsız watchOS uygulaması", "**Apple Watch sahipleri:** watchOS uygulaması yakında"),
        (r"Bağımsız Apple Watch uygulaması \(standalone watchOS\)", "Apple Watch uygulaması (yakında)"),
        (r"\| Apple Watch uygulaması \| Evet \(standalone\) \|", "| Apple Watch uygulaması | Yakında |"),
        (r"SwiftUI \(Apple Watch standalone\)", "SwiftUI (Apple Watch — yakında)"),
        (r"Apple Watch \(standalone\)", "Apple Watch (yakında)"),
        (r"bağımsız \(standalone\) Apple Watch uygulaması", "Apple Watch uygulaması (yakında)"),
        (r"standalone Apple Watch uygulaması", "Apple Watch uygulaması (yakında)"),
        (r"bağımsız Apple Watch uygulaması", "Apple Watch uygulaması (yakında)"),
        # ── English ─────────────────────────────────────────
        (r"Apple Watch standalone app \(SwiftUI\)", "Apple Watch app (coming soon)"),
        (r"a genuine standalone Apple Watch app", "an Apple Watch app (coming soon)"),
        (r"[Ss]tandalone Apple Watch (app|experience)", r"Apple Watch \1 (coming soon)"),
        (r"full Apple Watch standalone app", "Apple Watch app (coming soon)"),
        (r"Apple Watch standalone", "Apple Watch (coming soon)"),
        (r"standalone watchOS app", "watchOS app (coming soon)"),
        # ── Русский ─────────────────────────────────────────
        (r"Автономное \(standalone\) приложение Apple Watch на SwiftUI", "Приложение Suu для Apple Watch (скоро)"),
        (r"отдельное приложение для Apple Watch, написанное на SwiftUI", "приложение для Apple Watch (скоро)"),
        (r"отдельным Apple Watch-приложением", "приложением для Apple Watch (скоро)"),
        (r"Apple Watch \(SwiftUI standalone\)", "Apple Watch (скоро)"),
        (r"\| Apple Watch \(standalone\) \| Да \|", "| Apple Watch | Скоро |"),
        (r"Apple Watch \(standalone\)", "Apple Watch (скоро)"),
        # ── العربية ─────────────────────────────────────────
        (r"\| تطبيق Apple Watch \| نعم \(مستقل\) \|", "| تطبيق Apple Watch | قريبًا |"),
        (r"تطبيق Apple Watch مستقل", "تطبيق Apple Watch (قريبًا)"),
    ],
}


def iter_files() -> list[Path]:
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


def main() -> int:
    apply = "--apply" in sys.argv
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    groups = {k: v for k, v in RULES.items() if only is None or k == only}
    if not groups:
        print(f"Bilinmeyen grup: {only}. Seçenekler: {', '.join(RULES)}", file=sys.stderr)
        return 2

    compiled = {
        name: [(re.compile(pat), rep) for pat, rep in rules]
        for name, rules in groups.items()
    }

    total_subs = 0
    touched: list[tuple[Path, int]] = []

    for path in iter_files():
        try:
            original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        text = original
        file_subs = 0
        for rules in compiled.values():
            for pattern, replacement in rules:
                text, n = pattern.subn(replacement, text)
                file_subs += n

        if file_subs:
            total_subs += file_subs
            touched.append((path, file_subs))
            if apply:
                path.write_text(text, encoding="utf-8")

    for path, n in touched:
        print(f"  {n:>3}×  {path.relative_to(ROOT)}")

    mode = "uygulandı" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(touched)} dosyada {total_subs} değişiklik — {mode}")
    if not apply and total_subs:
        print("Uygulamak için: python3 scripts/fix-stale-facts.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
