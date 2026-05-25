#!/usr/bin/env python3
"""
Suu — Cannibal page redirect generator.

Bu sayfalar SEO açısından primary URL'lerle aynı niyete sahip ve
"keyword cannibalization" yaratıyor. Bunları minimal redirect HTML'iyle
overwrite ediyoruz:

  - <link rel="canonical">  →  primary URL'i işaret eder (signal birleşimi)
  - <meta http-equiv="refresh">  →  kullanıcıyı 0sn'de yönlendirir
  - <script> window.location.replace(...)  →  JS fallback
  - <meta name="robots" content="noindex, follow">  →  Google için açık talimat

GitHub Pages 301 yapamıyor; bu yaklaşım Google'ın "consolidation via
canonical" rehberine uygun. Eski içerik git history'de korunur.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"

# kaynak_slug : (hedef_url_path, başlık)
REDIRECTS = {
    "blog/en-iyi-su-takip-uygulamasi.html": (
        "/blog/su-takip-uygulamasi-neden-kullanmaliyim.html",
        "En İyi Su Takip Uygulaması",
    ),
    "blog/su-icince-kilo-verilir-mi.html": (
        "/blog/kilo-ve-su.html",
        "Su İçince Kilo Verilir mi?",
    ),
    "blog/yazin-ne-kadar-su-icmeli.html": (
        "/blog/gunluk-ne-kadar-su-icmeli.html",
        "Yazın Ne Kadar Su İçmeli?",
    ),
    "blog/yeterince-su-icip-icmedigini-anla.html": (
        "/blog/susuzluk-belirtileri.html",
        "Yeterince Su İçip İçmediğini Anla",
    ),
}

TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yönlendiriliyor — {title} | Suu</title>
    <link rel="canonical" href="{base}{target}">
    <meta name="robots" content="noindex, follow">
    <meta http-equiv="refresh" content="0; url={target}">
    <script>window.location.replace("{target}");</script>
    <style>
        body {{ font-family: -apple-system, sans-serif; max-width: 600px; margin: 80px auto; padding: 20px; color: #333; text-align: center; }}
        a {{ color: #4A90D9; font-weight: 600; }}
    </style>
</head>
<body>
    <h1>Yönlendiriliyor…</h1>
    <p>Bu sayfa taşındı. Otomatik olarak yönlendirilmediyseniz:</p>
    <p><a href="{target}">{base}{target}</a> sayfasını ziyaret edin.</p>
</body>
</html>
"""


def main() -> int:
    for src, (target, title) in REDIRECTS.items():
        path = ROOT / src
        if not path.exists():
            print(f"  ⚠ MISSING: {src}")
            continue
        path.write_text(TEMPLATE.format(base=BASE, target=target, title=title), encoding="utf-8")
        print(f"  ✓ {src} → {target}")
    print(f"\n{len(REDIRECTS)} kanibal sayfa minimal redirect'e dönüştürüldü.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
