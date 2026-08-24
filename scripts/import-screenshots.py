#!/usr/bin/env python3
"""
Suu — Ekran görüntüsü içe aktarıcı

Ham PNG/JPG ekran görüntülerini WebP'ye çevirip doğru klasöre yerleştirir.
Amaç: dosya adı/format/klasör derdi olmadan sadece görselleri bırakabilmek.

KULLANIM — 3 adım:

  1. Görselleri şu klasöre bırakın (PNG, JPG veya WebP fark etmez):

        assets/screenshots/_inbox/ios/
        assets/screenshots/_inbox/android/

     Dosya adı, ekranın slug'ı olmalı. Büyük harf, boşluk ve Türkçe karakter
     sorun değil — otomatik düzeltilir:

        "Kalori Foto Analiz.png"  →  kalori-foto-analiz.webp
        "kosu detay.PNG"          →  kosu-detay.webp

     Farklı dilde ekran varsa dosya adının sonuna dil kodu ekleyin:

        "ana-ekran-en.png"        →  ios/en/ana-ekran.webp

  2. Çalıştırın:

        python3 scripts/import-screenshots.py            # önizleme
        python3 scripts/import-screenshots.py --apply

  3. Kapsamı kontrol edin:

        python3 scripts/check-screenshots.py

Geçerli slug listesi ve teknik gereksinimler:
    assets/screenshots/README.md
"""
from __future__ import annotations

import re
import shutil
import sys
import unicodedata
from pathlib import Path

from _langs import order

try:
    from PIL import Image
except ImportError:
    raise SystemExit("HATA: Pillow gerekli.  pip3 install Pillow")

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "assets" / "screenshots"
INBOX = SHOTS / "_inbox"

# Dil tablosu: content/languages.json (bkz. scripts/_langs.py)
LANGS = set(order())
PLATFORMS = {"ios", "android"}
SOURCE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".heic"}

WEBP_QUALITY = 82
MAX_WIDTH = 1200          # telefon çerçevesinde bundan büyüğü gereksiz

VALID_SLUGS = {
    "ana-ekran", "kalori-foto-analiz", "makro-detay", "suu-ai-sohbet",
    "egzersiz-liste", "kosu-detay", "bisiklet-detay", "su-ekleme",
    "sesli-giris", "icecek-secimi", "istatistik", "hikaye-paylasim",
    "evcil-hayvan", "hatirlatma", "gun-challenge", "basarilar", "profil",
    "dynamic-island", "live-activity", "widget", "siri", "widget-android",
    "egzersiz-gecmis", "lig-siralamasi", "kilit-ekrani",
}

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(name: str) -> str:
    name = name.translate(TR_MAP)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return re.sub(r"-{2,}", "-", name)


def parse(stem: str) -> tuple[str, str]:
    """dosya adı → (slug, dil). Sonda dil kodu varsa ayırır."""
    slug = slugify(stem)
    parts = slug.rsplit("-", 1)
    if len(parts) == 2 and parts[1] in LANGS:
        return parts[0], parts[1]
    return slug, "tr"


def convert(src: Path, dst: Path, apply: bool) -> str:
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > MAX_WIDTH:
            ratio = MAX_WIDTH / im.width
            im = im.resize((MAX_WIDTH, round(im.height * ratio)), Image.LANCZOS)
        size = f"{im.width}×{im.height}"
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            im.save(dst, "WEBP", quality=WEBP_QUALITY, method=6)
    return size


def main() -> int:
    apply = "--apply" in sys.argv

    if not INBOX.exists():
        for p in PLATFORMS:
            (INBOX / p).mkdir(parents=True, exist_ok=True)
        print(f"Gelen kutusu oluşturuldu:\n  {(INBOX / 'ios').relative_to(ROOT)}\n"
              f"  {(INBOX / 'android').relative_to(ROOT)}\n\n"
              "Görselleri buraya bırakıp scripti tekrar çalıştırın.")
        return 0

    imported, unknown, empty = [], [], True

    for platform in sorted(PLATFORMS):
        folder = INBOX / platform
        if not folder.exists():
            continue
        for src in sorted(folder.iterdir()):
            if src.is_dir() or src.suffix.lower() not in SOURCE_EXT:
                continue
            empty = False
            slug, lang = parse(src.stem)

            if slug not in VALID_SLUGS:
                unknown.append((src.name, slug))
                continue

            dst = SHOTS / platform / lang / f"{slug}.webp"
            before = src.stat().st_size / 1024
            try:
                size = convert(src, dst, apply)
            except Exception as e:
                unknown.append((src.name, f"okunamadı: {e}"))
                continue
            after = dst.stat().st_size / 1024 if apply and dst.exists() else 0
            imported.append(
                f"  {src.name:<34} → {platform}/{lang}/{slug}.webp   "
                f"{size}  {before:.0f}→{after:.0f} KB" if apply else
                f"  {src.name:<34} → {platform}/{lang}/{slug}.webp   {size}"
            )
            if apply:
                src.unlink()          # işlenen dosyayı kutudan çıkar

    if empty:
        print("Gelen kutusu boş.\n")
        print("Görselleri şuraya bırakın:")
        print(f"  {(INBOX / 'ios').relative_to(ROOT)}/")
        print(f"  {(INBOX / 'android').relative_to(ROOT)}/")
        print("\nDosya adı ekranın slug'ı olsun (ör. kalori-foto-analiz.png).")
        print("Geçerli slug listesi: assets/screenshots/README.md")
        return 0

    for line in imported:
        print(line)

    if unknown:
        print(f"\n{len(unknown)} dosya tanınmadı (slug listesinde yok):")
        for name, slug in unknown:
            print(f"  {name}  →  '{slug}'")
        print("\nGeçerli slug'lar:")
        for s in sorted(VALID_SLUGS):
            print(f"  {s}")

    mode = "içe aktarıldı" if apply else "ÖNİZLEME (dosya yazılmadı)"
    print(f"\n{len(imported)} görsel — {mode}")
    if not apply and imported:
        print("Uygulamak için: python3 scripts/import-screenshots.py --apply")
    elif apply:
        print("\nKapsamı görmek için: python3 scripts/check-screenshots.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
