#!/usr/bin/env python3
"""
Suu — Hediye kod sayfası üreticisi (7 dil, tek şablon)

Girdi:
    content/gift/_template.html.j2   ortak şablon (animasyon + form + sonuç)
    content/gift/<lang>.json         dile özel metinler
    content/gift/config.json         Worker adresi, Turnstile anahtarı
    content/suu-facts.json           mağaza bağlantıları

Çıktı:
    tr → hediye-kod.html      en → gift-code.html
    ar → gift-code-ar.html    ru → gift-code-ru.html
    de → gift-code-de.html    it → gift-code-it.html
    hi → gift-code-hi.html

Sayfalar noindex: kampanya bağlantısı elle paylaşılıyor, arama sonuçlarından
gelen rastgele trafiğin sınırlı kod havuzunu tüketmesini istemiyoruz.

Kullanım:
    python3 scripts/build-gift-pages.py            # önizleme
    python3 scripts/build-gift-pages.py --apply
    python3 scripts/build-gift-pages.py --apply --lang tr,en
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    print("HATA: jinja2 gerekli.  pip3 install jinja2", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[1]
GIFT = ROOT / "content" / "gift"
FACTS = ROOT / "content" / "suu-facts.json"
BASE = "https://suuapp.com"
XDEFAULT = "en"

# lang → (çıktı dosyası, locale, yön, dilin kendi adı)
TARGETS: dict[str, tuple[str, str, str, str]] = {
    "tr": ("hediye-kod.html",    "tr_TR", "ltr", "Türkçe"),
    "en": ("gift-code.html",     "en_US", "ltr", "English"),
    "ar": ("gift-code-ar.html",  "ar_SA", "rtl", "العربية"),
    "ru": ("gift-code-ru.html",  "ru_RU", "ltr", "Русский"),
    "de": ("gift-code-de.html",  "de_DE", "ltr", "Deutsch"),
    "it": ("gift-code-it.html",  "it_IT", "ltr", "Italiano"),
    "hi": ("gift-code-hi.html",  "hi_IN", "ltr", "हिन्दी"),
}


def esc(raw: str) -> str:
    """</script> kaçışı — gömülü JSON bloğu HTML'i kapatmasın."""
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--lang", default="", help="virgülle: tr,en")
    args = ap.parse_args()

    cfg = json.loads((GIFT / "config.json").read_text(encoding="utf-8"))
    facts = json.loads(FACTS.read_text(encoding="utf-8"))
    links = facts["links"]

    if "BURAYA" in cfg["apiBase"]:
        print("⚠  content/gift/config.json → apiBase hâlâ yer tutucu. "
              "Worker'ı deploy edip adresi yaz, sonra bu script'i tekrar çalıştır.")
    if "BURAYA" in cfg["turnstileSiteKey"]:
        print("⚠  content/gift/config.json → turnstileSiteKey yer tutucu. "
              "Turnstile olmadan bot koruması devre dışı kalır.")

    env = Environment(loader=FileSystemLoader(str(GIFT)), undefined=StrictUndefined,
                      trim_blocks=False, lstrip_blocks=False)
    template = env.get_template("_template.html.j2")

    wanted = [l.strip() for l in args.lang.split(",") if l.strip()] or list(TARGETS)
    changed = 0

    for lang in wanted:
        if lang not in TARGETS:
            print(f"⚠  bilinmeyen dil: {lang}")
            continue
        out_name, locale, direction, _ = TARGETS[lang]
        c = json.loads((GIFT / f"{lang}.json").read_text(encoding="utf-8"))

        # Tarayıcıdaki JS'in ihtiyacı olan metinler — şablonun ikinci kopyası değil,
        # yalnızca çalışma anında lazım olan bölümler.
        runtime = {"stock": c["stock"], "form": c["form"], "result": c["result"], "errors": c["errors"]}

        html = template.render(
            lang=lang,
            dir=direction,
            locale=locale,
            c=c,
            page_url=f"{BASE}/{out_name}",
            xdefault_url=f"{BASE}/{TARGETS[XDEFAULT][0]}",
            alternates=[(code, f"{BASE}/{TARGETS[code][0]}") for code in TARGETS],
            lang_links=[(code, f"/{TARGETS[code][0]}", TARGETS[code][3]) for code in TARGETS],
            api_base=cfg["apiBase"].rstrip("/"),
            turnstile_key=cfg["turnstileSiteKey"],
            app_store=links["app_store"],
            google_play=links["google_play"],
            app_store_id=links["app_store_id"],
            copy_json=esc(json.dumps(runtime, ensure_ascii=False, separators=(",", ":"))),
        )
        if not html.endswith("\n"):
            html += "\n"

        target = ROOT / out_name
        old = target.read_text(encoding="utf-8") if target.exists() else ""
        state = "aynı" if old == html else ("yeni" if not old else "güncellendi")
        if old != html:
            changed += 1
            if args.apply:
                target.write_text(html, encoding="utf-8")
        print(f"{lang:3s} → {out_name:22s} {len(html)//1024:3d} KB  {state}")

    # Panel de aynı Worker'a bakar — adres iki yerde elle tutulursa kaçınılmaz sapar.
    panel = ROOT / cfg["adminPage"]
    if panel.exists():
        text = panel.read_text(encoding="utf-8")
        fixed = re.sub(r'(var API = ")[^"]*(")', r"\g<1>" + cfg["apiBase"].rstrip("/") + r"\g<2>", text)
        if fixed != text:
            changed += 1
            if args.apply:
                panel.write_text(fixed, encoding="utf-8")
            print(f"    {cfg['adminPage']:22s}        panel adresi güncellendi")

    print(f"\n{changed} dosya {'yazıldı' if args.apply else 'değişecek'}"
          f"{'' if args.apply else '  (yazmak için --apply)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
