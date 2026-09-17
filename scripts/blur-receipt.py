#!/usr/bin/env python3
"""
Suu — Dekont tutar alanı bulanıklaştırıcı

Neden var: 2026-09-18'den beri sitede bağış tutarı yayınlanmıyor; bağış
"hedefin %kaçı" olarak anlatılıyor (bkz. scripts/build-donations.py).
Dekont görseli hâlâ yayınlanıyor — kurum ve tarih açık kalıyor — ama tutar
sütunu geri döndürülemez biçimde siliniyor.

Yöntem: tutar metni mozaiklenip bulanıklaştırılır, üstüne HER SATIRDA AYNI
ölçüde tek bir yumuşak iz konur. Aynı ölçü önemli: satıra göre değişen bir
bulanık iz, rakam sayısını yani tutarın büyüklüğünü ele verir.

Kullanım:
    python3 scripts/blur-receipt.py donations/receipts/yeni.webp           # önizleme
    python3 scripts/blur-receipt.py donations/receipts/yeni.webp --apply   # yerine yaz
    ... --from-x 1246        # tutar sütunu otomatik bulunamazsa sol sınırı elle ver
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

DARK = 150          # bu değerden koyu pikseller "metin" sayılır
ROW_GAP = 12        # bu kadar boş satır iki kaydı ayırır
PAD_X, PAD_Y = 34, 16
PILL_W, PILL_H = 132, 26
PILL_RIGHT_PAD = 24


def text_rows(mask, x0: int) -> list[tuple[int, int]]:
    """Sağ sütundaki metin bantlarını (y0, y1) olarak döndür."""
    width = len(mask[0])
    rows, run, gap = [], None, 0
    for y, line in enumerate(mask):
        has_text = any(line[x] for x in range(x0, width))
        if has_text:
            if run is None:
                run = [y, y]
            run[1] = y
            gap = 0
        elif run is not None:
            gap += 1
            if gap > ROW_GAP:
                rows.append((run[0], run[1]))
                run = None
    if run is not None:
        rows.append((run[0], run[1]))
    return rows


def detect_column(mask) -> int | None:
    """Tutar sütununun sol sınırını tahmin et: en sağdaki metin öbeği."""
    width = len(mask[0])
    cols = [any(line[x] for line in mask) for x in range(width)]
    groups, start = [], None
    for x, filled in enumerate(cols):
        if filled and start is None:
            start = x
        elif not filled and start is not None:
            if x - start > 4:
                groups.append((start, x))
            start = None
    if start is not None:
        groups.append((start, width))
    if not groups:
        return None
    # Son öbek tutar sütunu; sütun içindeki boşlukları birleştirmek için
    # 60px'den yakın komşu öbekleri aynı sütun say.
    left = groups[-1][0]
    for a, b in reversed(groups[:-1]):
        if left - b < 60:
            left = a
        else:
            break
    return left


def looks_processed(px, width: int, height: int, x_from: int) -> bool:
    """Seçilen sütunun sağında zaten bulanık iz var mı? (ikinci kez çalıştırma koruması)

    Aranan şey bu scriptin bıraktığı iz: uzun, düz bir orta gri şerit. Yazının
    kenar yumuşatması da gri üretir ama art arda 50 pikselden uzun sürmez.
    """
    for y in range(height):
        run = 0
        for x in range(x_from, width):
            if 165 <= px[x, y] <= 200:
                run += 1
                if run >= 50:
                    return True
            else:
                run = 0
    return False


def blur_amounts(path: Path, from_x: int | None, apply: bool) -> int:
    im = Image.open(path).convert("RGB")
    gray = im.convert("L")
    px = gray.load()
    mask = [[px[x, y] < DARK for x in range(im.width)] for y in range(im.height)]

    x0 = from_x if from_x is not None else detect_column(mask)
    if x0 is None:
        print("tutar sütunu bulunamadı — --from-x ile sol sınırı verin")
        return 1

    if from_x is None and looks_processed(px, im.width, im.height, x0 + 40):
        print(f"x={x0} sütununun sağında zaten bulanık iz var — bu dekont işlenmiş "
              f"görünüyor. Yine de gerekiyorsa --from-x ile sınırı elle verin.")
        return 1

    bands = text_rows(mask, x0)
    if not bands:
        print(f"x={x0} sağında metin yok — ya zaten bulanık ya da sınır yanlış")
        return 1

    boxes = []
    for y0, y1 in bands:
        boxes.append((
            max(0, x0 - PAD_X), max(0, y0 - PAD_Y),
            im.width, min(im.height, y1 + PAD_Y),
        ))

    for box in boxes:
        w, h = box[2] - box[0], box[3] - box[1]
        region = im.crop(box)
        small = region.resize((max(1, w // 24), max(1, h // 24)), Image.BILINEAR)
        region = small.resize((w, h), Image.NEAREST).filter(ImageFilter.GaussianBlur(9))
        region = Image.blend(region, Image.new("RGB", (w, h), (255, 255, 255)), 0.82)
        draw = ImageDraw.Draw(region)
        x1 = w - PILL_RIGHT_PAD
        y_top = (h - PILL_H) // 2
        draw.rounded_rectangle([x1 - PILL_W, y_top, x1, y_top + PILL_H],
                               radius=7, fill=(176, 182, 190))
        im.paste(region.filter(ImageFilter.GaussianBlur(6)), box)

    print(f"{path} — sütun x≥{x0}, {len(boxes)} tutar alanı bulanıklaştırıldı")
    for b in boxes:
        print(f"  {b}")

    if apply:
        im.save(path, "WEBP", quality=90, method=6)
        print("uygulandı (dosyanın üzerine yazıldı)")
    else:
        preview = path.with_name(path.stem + "-blur-preview.webp")
        im.save(preview, "WEBP", quality=90, method=6)
        print(f"ÖNİZLEME: {preview} — onaylarsan: --apply")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Dekonttaki tutar sütununu bulanıklaştırır.")
    parser.add_argument("image", type=Path, help="dekont görseli (webp/png/jpg)")
    parser.add_argument("--from-x", type=int, default=None,
                        help="tutar sütununun sol sınırı (otomatik bulunamazsa)")
    parser.add_argument("--apply", action="store_true", help="dosyanın üzerine yaz")
    ns = parser.parse_args()
    if not ns.image.exists():
        print(f"dosya yok: {ns.image}")
        return 1
    return blur_amounts(ns.image, ns.from_x, ns.apply)


if __name__ == "__main__":
    sys.exit(main())
