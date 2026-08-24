#!/usr/bin/env python3
"""
Suu — Bağış makbuzları sayfası üretici

Kaynak: donations.json  (bağış widget'ıyla AYNI kaynak)

Neden var: 5 indekslenmiş sayfa /donations/receipts/ adresine bağlantı
veriyordu ama dizinde index.html yoktu; GitHub Pages 404 döndürüyordu
(SEO denetimi, 2026-08-20). Bağlantı bir şeffaflık vaadinin parçası —
tıklayan kullanıcı makbuzu görebilmeli.

donations.json robots.txt'de Disallow olduğu için veri sayfaya GÖMÜLÜR;
istemci tarafı fetch kullanılmaz, aksi hâlde tarayıcılar boş sayfa görür.

Kullanım:
    python3 scripts/build-receipts-page.py            # önizleme
    python3 scripts/build-receipts-page.py --apply
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "donations.json"
OUT = ROOT / "donations" / "receipts" / "index.html"
URL = "https://suuapp.com/donations/receipts/"

MONTHS = {
    "01": "Ocak", "02": "Şubat", "03": "Mart", "04": "Nisan",
    "05": "Mayıs", "06": "Haziran", "07": "Temmuz", "08": "Ağustos",
    "09": "Eylül", "10": "Ekim", "11": "Kasım", "12": "Aralık",
}


def pretty_date(ym: str) -> str:
    try:
        y, m = ym.split("-")
        return f"{MONTHS.get(m, m)} {y}"
    except ValueError:
        return ym


def build(data: dict) -> str:
    receipts = sorted(data["receipts"], key=lambda r: r["date"], reverse=True)
    total = data["totalAmount"]
    cur = data["baseCurrency"]
    updated = data["lastUpdated"]

    rows = []
    for r in receipts:
        date = html.escape(pretty_date(r["date"]))
        charity = html.escape(r["charity"])
        amount = f"{r['amount']:,}".replace(",", ".")
        if r.get("url"):
            doc = (f'<a href="{html.escape(r["url"])}">Dekontu gör'
                   f'<span class="sr">— {charity}</span></a>')
        else:
            doc = '<span class="pending">Dekont yüklenmedi</span>'
        rows.append(
            f'        <tr>\n'
            f'          <td>{date}</td>\n'
            f'          <td>{charity}</td>\n'
            f'          <td class="num">₺{amount}</td>\n'
            f'          <td>{doc}</td>\n'
            f'        </tr>'
        )
    tbody = "\n".join(rows)
    total_fmt = f"{total:,}".replace(",", ".")

    return f"""<!doctype html>
<html lang="tr">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Bağış Dekontları — Suu Şeffaflık Kaydı</title>
    <meta name="description" content="Suu Premium gelirinden yapılan bağışların banka dekontları. Hangi kuruma, hangi tarihte, ne kadar gönderildi — tamamı açık kayıt." />

    <meta property="og:title" content="Bağış Dekontları — Suu Şeffaflık Kaydı" />
    <meta property="og:description" content="Suu Premium gelirinden yapılan bağışların banka dekontları, tarih ve tutarlarıyla birlikte." />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="{URL}" />
    <meta property="og:image" content="https://suuapp.com/assets/og-image.png" />
    <meta property="og:site_name" content="Suu" />
    <meta property="og:locale" content="tr_TR" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Bağış Dekontları — Suu Şeffaflık Kaydı" />
    <meta name="twitter:description" content="Suu Premium gelirinden yapılan bağışların banka dekontları." />
    <meta name="twitter:image" content="https://suuapp.com/assets/og-image.png" />

    <link rel="canonical" href="{URL}" />

    <link rel="icon" href="/favicon.ico" sizes="any" />
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />

    <style>
      :root {{
        --ink: #16202b; --muted: #5b6b7a; --line: #e2e8ee;
        --bg: #ffffff; --panel: #f6f9fb; --accent: #2f7fa8;
      }}
      @media (prefers-color-scheme: dark) {{
        :root {{
          --ink: #e6edf3; --muted: #9aabb9; --line: #253340;
          --bg: #0e151c; --panel: #141d26; --accent: #6bb6d8;
        }}
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0; padding: 0 20px 64px; background: var(--bg); color: var(--ink);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif;
        line-height: 1.65;
      }}
      .wrap {{ max-width: 720px; margin: 0 auto; }}
      header {{ padding: 56px 0 24px; }}
      .back {{
        display: inline-block; font-size: 14px; color: var(--muted);
        text-decoration: none; margin-bottom: 20px;
      }}
      .back:hover {{ color: var(--accent); }}
      h1 {{ font-size: clamp(26px, 5vw, 34px); line-height: 1.2; margin: 0 0 12px; }}
      .lede {{ color: var(--muted); margin: 0 0 24px; max-width: 34em; }}
      .en {{ font-size: 14px; color: var(--muted); font-style: italic; }}
      .total {{
        display: flex; flex-wrap: wrap; gap: 4px 28px; align-items: baseline;
        background: var(--panel); border: 1px solid var(--line);
        border-radius: 8px; padding: 16px 18px; margin: 0 0 32px;
      }}
      .total .big {{ font-size: 26px; font-weight: 700; }}
      .total .lbl {{ font-size: 14px; color: var(--muted); }}
      .tablewrap {{ overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }}
      table {{ border-collapse: collapse; width: 100%; min-width: 480px; }}
      th, td {{ text-align: left; padding: 12px 14px; border-bottom: 1px solid var(--line); }}
      th {{
        font-size: 12px; text-transform: uppercase; letter-spacing: .06em;
        color: var(--muted); font-weight: 600; background: var(--panel);
      }}
      tbody tr:last-child td {{ border-bottom: none; }}
      td.num {{ font-variant-numeric: tabular-nums; white-space: nowrap; }}
      td a {{ color: var(--accent); }}
      .pending {{ color: var(--muted); font-size: 14px; }}
      .sr {{
        position: absolute; width: 1px; height: 1px; overflow: hidden;
        clip: rect(0 0 0 0); white-space: nowrap;
      }}
      .note {{ font-size: 14px; color: var(--muted); margin-top: 20px; }}
      footer {{
        margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--line);
        font-size: 13px; color: var(--muted);
      }}
      a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; }}
    </style>
    <script src="/assets/js/analytics.js" defer></script>
  </head>
  <body>
    <div class="wrap">
      <header>
        <a class="back" href="/">← suuapp.com</a>
        <h1>Bağış dekontları</h1>
        <p class="lede">
          Suu Premium gelirinden yapılan bağışların banka dekontları.
          Hangi kuruma, hangi tarihte, ne kadar gönderildi — hepsi burada.
        </p>
        <p class="en">Bank transfer receipts for donations funded by Suu Premium revenue.</p>
      </header>

      <div class="total">
        <span class="big">₺{total_fmt}</span>
        <span class="lbl">bugüne kadar bağışlanan toplam · son güncelleme {updated}</span>
      </div>

      <div class="tablewrap">
        <table>
          <thead>
            <tr>
              <th scope="col">Tarih</th>
              <th scope="col">Kurum</th>
              <th scope="col">Tutar</th>
              <th scope="col">Dekont</th>
            </tr>
          </thead>
          <tbody>
{tbody}
          </tbody>
        </table>
      </div>

      <p class="note">
        Dekontlarda kişisel bilgiler (hesap numarası, adres) karartılmıştır.
        Bir kayıtla ilgili sorunuz olursa
        <a href="mailto:destek@suuapp.com">destek@suuapp.com</a> adresine yazabilirsiniz.
      </p>

      <footer>© Suu · <a href="/">suuapp.com</a></footer>
    </div>
  </body>
</html>
"""


def main() -> int:
    apply = "--apply" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    page = build(data)

    old = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if old == page:
        print(f"{OUT.relative_to(ROOT)} zaten güncel")
        return 0

    print(f"{OUT.relative_to(ROOT)} — {len(data['receipts'])} makbuz, {len(page)} bayt")
    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(page, encoding="utf-8")
        print("uygulandı")
    else:
        print("ÖNİZLEME (yazılmadı) — uygulamak için: --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
