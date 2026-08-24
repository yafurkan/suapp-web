#!/usr/bin/env python3
"""
Suu — IndexNow gönderimi (Bing, Yandex ve ortaklarına anında bildirim)

Anahtar dosyası siteye bir yıl önce konmuş ama bir kez bile ping atılmamıştı
(humans.txt: "NOT YET CONFIGURED"). Bu script onu devreye alır.

IndexNow tek bir çağrıyla katılımcı tüm motorlara dağıtır — Bing, Yandex,
Seznam, Naver. Google IndexNow kullanmaz; oraya sitemap + Search Console yolu
geçerlidir.

Kullanım:
    python3 scripts/indexnow-submit.py --changed        # git'te değişen HTML'ler
    python3 scripts/indexnow-submit.py --all            # sitemap'teki her URL
    python3 scripts/indexnow-submit.py --url /premium.html /index.html
    python3 scripts/indexnow-submit.py --changed --dry  # göndermeden listele
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "suuapp.com"
BASE = f"https://{HOST}"
ENDPOINT = "https://api.indexnow.org/IndexNow"
MAX_URLS = 10000          # IndexNow tek istek sınırı

# İndekslenmemesi gereken sayfalar — robots.txt ile tutarlı
EXCLUDE = ("admin.html", "app/index.html", "404", "makale.html",
           "yandex_", "og-image-template.html")


def find_key() -> tuple[str, str]:
    """Kök dizindeki <key>.txt dosyasını bul; içeriği anahtarla aynı olmalı."""
    for path in ROOT.glob("*.txt"):
        stem = path.stem
        if len(stem) != 32 or not all(c in "0123456789abcdef" for c in stem.lower()):
            continue
        content = path.read_text(encoding="utf-8").strip()
        if content == stem:
            return stem, f"{BASE}/{path.name}"
    raise SystemExit("HATA: IndexNow anahtar dosyası bulunamadı (kökte <32-hex>.txt).")


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise SystemExit("HATA: git çalıştırılamadı.")


def changed_urls() -> list[str]:
    """Değişen/eklenen HTML dosyaları.

    Çalışma ağacına bakar; ağaç temizse SON COMMIT'in diff'ine düşer.
    Bu düşüş şart: yayın akışı (README) bu script'i push'tan SONRA
    çağırıyor, o noktada değişiklikler artık commit'lenmiş oluyor ve
    yalnızca `git status`'a bakan bir sürüm hep "gönderilecek URL yok"
    diyordu — yani yeni sayfalar hiç bildirilmiyordu.
    """
    paths = []
    for line in _git("status", "--porcelain", "--", "*.html").splitlines():
        if line.startswith(" D") or line.startswith("D "):
            continue
        paths.append(line[3:].strip().strip('"'))

    if not paths:
        paths = _git("diff", "--name-only", "--diff-filter=d",
                     "HEAD~1", "HEAD", "--", "*.html").split()

    urls = []
    for path in paths:
        if not path.endswith(".html") or any(x in path for x in EXCLUDE):
            continue
        urls.append(to_url(path))
    return sorted(set(urls))


def sitemap_urls() -> list[str]:
    sm = ROOT / "sitemap.xml"
    if not sm.exists():
        raise SystemExit("HATA: sitemap.xml yok.")
    import re
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", sm.read_text(encoding="utf-8"))


def to_url(rel: str) -> str:
    rel = rel.lstrip("./")
    if rel == "index.html":
        return f"{BASE}/"
    return f"{BASE}/{rel}"


def submit(key: str, key_location: str, urls: list[str], dry: bool) -> int:
    if not urls:
        print("Gönderilecek URL yok.")
        return 0

    urls = urls[:MAX_URLS]
    print(f"{len(urls)} URL:")
    for u in urls[:25]:
        print(f"  {u}")
    if len(urls) > 25:
        print(f"  … ve {len(urls) - 25} tane daha")

    if dry:
        print("\n--dry — gönderilmedi.")
        return 0

    payload = json.dumps({
        "host": HOST,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT, data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    # macOS'ta sistem Python'ı kök sertifikaları görmüyor — certifi varsa onu kullan
    ctx = None
    try:
        import ssl, certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass

    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            code = resp.status
            body = resp.read().decode("utf-8", "replace")[:200]
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode("utf-8", "replace")[:200]
    except Exception as e:                       # ağ hatası
        print(f"\nGÖNDERİM BAŞARISIZ: {e}", file=sys.stderr)
        return 1

    # 200 = kabul edildi, 202 = kabul edildi (anahtar doğrulaması sürüyor)
    ok = code in (200, 202)
    print(f"\nHTTP {code} — {'kabul edildi' if ok else 'REDDEDİLDİ'}")
    if body.strip():
        print(f"yanıt: {body}")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    dry = "--dry" in args

    key, key_location = find_key()
    print(f"anahtar: {key[:8]}…  konum: {key_location}\n")

    if "--all" in args:
        urls = sitemap_urls()
    elif "--url" in args:
        i = args.index("--url")
        urls = [to_url(a) if not a.startswith("http") else a
                for a in args[i + 1:] if not a.startswith("--")]
    else:
        urls = changed_urls()

    return submit(key, key_location, urls, dry)


if __name__ == "__main__":
    sys.exit(main())
