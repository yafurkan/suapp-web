#!/usr/bin/env python3
"""
Suu — Ekran görüntüsü kapsam raporu

assets/screenshots/README.md'deki çekim listesine göre hangi ekranların
hangi platform/dil kombinasyonunda eksik olduğunu gösterir.

Kullanım:
    python3 scripts/check-screenshots.py            # özet
    python3 scripts/check-screenshots.py --missing  # eksiklerin tam listesi
"""
from __future__ import annotations

import sys
from pathlib import Path

from _langs import order

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "assets" / "screenshots"

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
LANGS = order()
PLATFORMS = ["ios", "android"]

REQUIRED = [
    "ana-ekran", "kalori-foto-analiz", "makro-detay", "suu-ai-sohbet",
    "egzersiz-liste", "kosu-detay", "bisiklet-detay", "su-ekleme",
]
RECOMMENDED = [
    "sesli-giris", "icecek-secimi", "istatistik",
    "hikaye-paylasim", "evcil-hayvan", "hatirlatma",
]
IOS_ONLY = ["dynamic-island", "live-activity", "widget", "siri"]


def exists(platform: str, lang: str, screen: str) -> bool:
    return (SHOTS / platform / lang / f"{screen}.webp").is_file()


def main() -> int:
    show_missing = "--missing" in sys.argv
    missing: list[str] = []

    print(f"{'Ekran':<22}", end="")
    for p in PLATFORMS:
        print(f"{p:<32}", end="")
    print()
    print(f"{'':<22}", end="")
    for _ in PLATFORMS:
        print("".join(f"{l:<4}" for l in LANGS) + "    ", end="")
    print()
    print("─" * 88)

    groups = [("ZORUNLU", REQUIRED), ("ÖNERİLEN", RECOMMENDED), ("iOS-ÖZEL", IOS_ONLY)]

    for label, screens in groups:
        print(f"\n{label}")
        for screen in screens:
            print(f"  {screen:<20}", end="")
            for platform in PLATFORMS:
                if label == "iOS-ÖZEL" and platform == "android":
                    print(f"{'—':<32}", end="")
                    continue
                for lang in LANGS:
                    ok = exists(platform, lang, screen)
                    print(f"{'✓' if ok else '·':<4}", end="")
                    if not ok and lang == "tr":
                        missing.append(f"{platform}/{lang}/{screen}.webp")
                print("    ", end="")
            print()

    total_tr = sum(
        1
        for label, screens in groups
        for screen in screens
        for platform in PLATFORMS
        if not (label == "iOS-ÖZEL" and platform == "android")
    )
    have_tr = total_tr - len(missing)

    print("\n" + "─" * 88)
    print(f"Türkçe (temel dil) kapsamı: {have_tr}/{total_tr}")
    print("✓ = var   · = yok (dil yoksa TR'ye, TR de yoksa placeholder'a düşer)")

    if show_missing and missing:
        print(f"\nEksik Türkçe görseller ({len(missing)}):")
        for m in missing:
            print(f"  assets/screenshots/{m}")
    elif missing:
        print(f"\nTam liste için: python3 scripts/check-screenshots.py --missing")

    return 0


if __name__ == "__main__":
    sys.exit(main())
