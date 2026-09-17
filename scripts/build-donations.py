#!/usr/bin/env python3
"""
Suu — Bağış verisi üretici (tutar → yüzde)

Neden var: Siteye para tutarı çıkmıyor (2026-09-18 kararı). Tutar yayınlamak
projenin finansal büyüklüğünü/yükünü ilan etmek gibi okunuyordu; bağış vaadi
"ne kadar" değil "hedefin ne kadarı" üzerinden anlatılıyor.

Akış:
    donations.private.json  (gitignore — gerçek TL tutarları, sadece yerelde)
        ↓  bu script
    donations.json          (public — SADECE yüzde, tutar yok)
        ↓  scripts/build-receipts-page.py
    donations/receipts/index.html

donations.json'daki `translations` bloğu elle yönetilir; bu script ona
dokunmaz, yalnızca sayısal alanları tazeler.

Kullanım:
    python3 scripts/build-donations.py            # önizleme
    python3 scripts/build-donations.py --apply    # yaz + dekont sayfasını üret
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "donations.private.json"
PUBLIC = ROOT / "donations.json"
RECEIPTS_BUILDER = ROOT / "scripts" / "build-receipts-page.py"


def pct(amount: float, goal: float) -> float:
    """Hedefin yüzdesi — tek ondalık, 0.1 altı katkılar 0.1 olarak görünür."""
    if goal <= 0:
        return 0.0
    raw = amount / goal * 100
    value = round(raw, 1)
    if raw > 0 and value == 0.0:
        return 0.1
    return value


def build(private: dict, public: dict) -> dict:
    goal = private["goalAmount"]
    receipts = []
    total = 0.0
    for r in private["receipts"]:
        total += r["amount"]
        entry = {
            "date": r["date"],
            "charity": r["charity"],
            "sharePercent": pct(r["amount"], goal),
        }
        if r.get("url"):
            entry["url"] = r["url"]
        receipts.append(entry)

    out = {
        "progressPercent": min(100.0, pct(total, goal)),
        "lastUpdated": private["lastUpdated"],
        "receipts": receipts,
        # Elle yönetilen blok — olduğu gibi taşınır.
        "translations": public.get("translations", {}),
    }
    return out


def guard(data: dict) -> list[str]:
    """Public dosyada para kokan bir alan kalmadığından emin ol."""
    banned = {"amount", "totalAmount", "goalAmount", "baseCurrency", "rates", "currencyByLang"}
    hits = []

    def walk(node, path="$"):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in banned:
                    hits.append(f"{path}.{k}")
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(data)
    return hits


def main() -> int:
    apply = "--apply" in sys.argv

    if not PRIVATE.exists():
        print(f"HATA: {PRIVATE.name} yok. Gerçek tutarlar orada tutuluyor "
              f"(gitignore'da). Örnek için git geçmişine değil, README'ye bak.")
        return 1

    private = json.loads(PRIVATE.read_text(encoding="utf-8"))
    public_old = json.loads(PUBLIC.read_text(encoding="utf-8")) if PUBLIC.exists() else {}
    data = build(private, public_old)

    leaks = guard(data)
    if leaks:
        print("HATA: public veride tutar alanı kaldı → " + ", ".join(leaks))
        return 1

    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    old = PUBLIC.read_text(encoding="utf-8") if PUBLIC.exists() else None

    print(f"ilerleme %{data['progressPercent']:g} · {len(data['receipts'])} dekont "
          f"· son güncelleme {data['lastUpdated']}")
    for r in data["receipts"]:
        print(f"  {r['date']}  {r['charity']}  +%{r['sharePercent']:g}"
              + ("" if r.get("url") else "  (dekont yüklenmedi)"))

    if old == text:
        print("donations.json zaten güncel")
    elif apply:
        PUBLIC.write_text(text, encoding="utf-8")
        print("donations.json yazıldı")
    else:
        print("ÖNİZLEME (yazılmadı) — uygulamak için: --apply")

    if apply:
        subprocess.run([sys.executable, str(RECEIPTS_BUILDER), "--apply"], check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
