#!/usr/bin/env python3
"""
!!! ESKİMİŞ — KULLANMAYIN !!!

Yerine:  python3 scripts/update-sitemap.py --apply

Neden kaldırıldı:
  • Kendi kopya CLUSTERS tablosunu taşıyordu — content/page-registry.json ile
    senkron olmayan dördüncü bir "gerçek kaynağı" idi ve zamanla sapmıştı.
  • Sitemap'i baştan kurarken bir yılda birikmiş <image:image> bloklarını
    siliyordu.

update-sitemap.py kayıt defterinden çalışır, mevcut zenginleştirmeleri korur
ve idempotenttir. Eski kodun tamamı git geçmişindedir:

    git show HEAD:scripts/rebuild-sitemap.py
"""
import sys

print(__doc__, file=sys.stderr)
raise SystemExit(1)
