#!/usr/bin/env python3
"""Hediye kodlarını D1'e yüklenecek SQL'e çevirir.

Kaynaklar:
  iOS     — App Store offer kodları (.xlsx, "Tek Seferlik Kod" sütunu)
  Android — Google Play promo kodları (.csv, "Promotion code" sütunu)

Neden ayrı bir script: kodlar repoya ASLA girmemeli (repo herkese açık ve
GitHub Pages'te yayınlanıyor). Bu script kaynak dosyaları İndirilenler'den
okur, çıktıyı worker/seed-codes.sql'e yazar; o dosya .gitignore'da.

Kullanım:
    python3 scripts/gift-codes-import.py                 # önizleme
    python3 scripts/gift-codes-import.py --apply         # SQL'i yaz
    python3 scripts/gift-codes-import.py --ios-skip 35 --apply

Sonra:
    cd worker && npx wrangler d1 execute suu-gift-codes --remote --file=./seed-codes.sql
"""

from __future__ import annotations

import argparse
import csv
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOWNLOADS = pathlib.Path.home() / "Downloads"
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
VALID_CODE = re.compile(r"^[A-Z0-9]{8,32}$")


def read_xlsx_codes(path: pathlib.Path) -> list[str]:
    """Sıra No / Tek Seferlik Kod tablosundan kodları dosya sırasıyla okur."""
    with zipfile.ZipFile(path) as z:
        sheet = z.read("xl/worksheets/sheet1.xml")
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            sroot = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(NS + "t"))
                      for si in sroot.iter(NS + "si")]

    def cell_value(c) -> str:
        inline = c.find(NS + "is/" + NS + "t")
        if inline is not None:
            return inline.text or ""
        v = c.find(NS + "v")
        if v is None:
            return ""
        if c.get("t") == "s" and shared:
            try:
                return shared[int(v.text)]
            except (ValueError, IndexError):
                return ""
        return v.text or ""

    codes: list[str] = []
    for row in ET.fromstring(sheet).iter(NS + "row"):
        cells = {re.sub(r"\d", "", c.get("r") or ""): cell_value(c)
                 for c in row.iter(NS + "c")}
        if not cells.get("A", "").strip().isdigit():
            continue                      # başlık ve açıklama satırları
        code = cells.get("B", "").strip().upper()
        if code:
            codes.append(code)
    return codes


def read_csv_codes(path: pathlib.Path) -> list[str]:
    """Google Play Console export'u — tek sütun, ilk satır başlık."""
    codes: list[str] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for i, row in enumerate(csv.reader(fh)):
            if not row or not row[0].strip():
                continue
            value = row[0].strip().upper()
            if i == 0 and not VALID_CODE.match(value):
                continue                  # "PROMOTION CODE" başlığı
            codes.append(value)
    return codes


def clean(codes: list[str], label: str) -> list[str]:
    """Geçersizleri ve tekrarları ayıklar, sırayı korur."""
    seen: set[str] = set()
    out: list[str] = []
    bad = dupe = 0
    for c in codes:
        if not VALID_CODE.match(c):
            bad += 1
            continue
        if c in seen:
            dupe += 1
            continue
        seen.add(c)
        out.append(c)
    if bad or dupe:
        print(f"  {label}: {bad} geçersiz, {dupe} tekrar eden kod atlandı")
    return out


def sql_for(rows: list[tuple[str, str, int, str]]) -> str:
    """INSERT OR IGNORE — script iki kez çalışırsa kod ÇOĞALMAZ."""
    # BEGIN/COMMIT YAZILMAZ: uzak D1 açık transaction ifadelerini reddediyor
    # ("please use the state.storage.transaction() API instead"). Her INSERT
    # zaten kendi başına atomik; INSERT OR IGNORE de tekrarı zararsız kılıyor.
    lines = ["-- Suu hediye kodları — ÜRETİLMİŞ DOSYA, GİT'E EKLEME.",
             "-- Üretim: python3 scripts/gift-codes-import.py --apply"]
    for i in range(0, len(rows), 200):
        chunk = rows[i:i + 200]
        lines.append("INSERT OR IGNORE INTO codes (code, platform, seq, batch) VALUES")
        values = [f"  ('{c}', '{p}', {s}, '{b}')" for c, p, s, b in chunk]
        lines.append(",\n".join(values) + ";")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ios", type=pathlib.Path,
                    default=DOWNLOADS / "Suu_Kurumsal_Mesajli_Kodlar.xlsx")
    ap.add_argument("--android", type=pathlib.Path,
                    default=DOWNLOADS / "promotion_codes.csv")
    ap.add_argument("--ios-skip", type=int, default=35,
                    help="elle dağıtılmış ilk N iOS kodu atlanır (varsayılan 35)")
    ap.add_argument("--android-skip", type=int, default=0)
    ap.add_argument("--batch", default="2026-08")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "worker" / "seed-codes.sql")
    ap.add_argument("--apply", action="store_true", help="SQL dosyasını yaz")
    args = ap.parse_args()

    rows: list[tuple[str, str, int, str]] = []

    for label, path, reader, skip in (
        ("ios", args.ios, read_xlsx_codes, args.ios_skip),
        ("android", args.android, read_csv_codes, args.android_skip),
    ):
        if not path.exists():
            print(f"⚠  {label}: dosya yok, atlanıyor → {path}")
            continue
        codes = clean(reader(path), label)
        kept = codes[skip:]
        print(f"{label:8s} {len(codes):4d} kod okundu · ilk {skip} atlandı · "
              f"{len(kept):4d} havuza girecek  ({path.name})")
        if kept:
            print(f"         ilk: {kept[0]}  ·  son: {kept[-1]}")
        for offset, code in enumerate(kept):
            rows.append((code, label, skip + offset + 1, f"{label}-{args.batch}"))

    if not rows:
        print("Hiç kod bulunamadı — dosya yollarını kontrol et.", file=sys.stderr)
        return 1

    print(f"\nTOPLAM {len(rows)} kod → {args.out}")

    if not args.apply:
        print("\n(önizleme — yazmak için --apply ekle)")
        return 0

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(sql_for(rows), encoding="utf-8")
    print(f"✓ yazıldı: {args.out}  ({args.out.stat().st_size // 1024} KB)")
    print("\nŞimdi D1'e yükle:")
    print("  cd worker && npx wrangler d1 execute suu-gift-codes --remote --file=./seed-codes.sql")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
