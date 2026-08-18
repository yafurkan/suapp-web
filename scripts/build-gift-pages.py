#!/usr/bin/env python3
"""
Suu — Hediye kod sayfası üreticisi (7 dil, tek şablon)

Girdi:
    content/gift/_template.html.j2   ortak şablon (animasyon + form + sonuç)
    content/gift/<lang>.json         dile özel metinler
    content/gift/config.json         Worker adresi, Turnstile anahtarı
    content/suu-facts.json           mağaza bağlantıları

    content/partners/<slug>.json     sponsorluk sayfaları (isteğe bağlı)

Çıktı:
    tr → hediye-kod.html      en → gift-code.html
    ar → gift-code-ar.html    ru → gift-code-ru.html
    de → gift-code-de.html    it → gift-code-it.html
    hi → gift-code-hi.html
    sponsorluklar → <slug>/index.html   (örn. dahacommunity/index.html)

Sponsorluk sayfaları AYNI şablonu kullanır, ayrı bir kopyasını değil: formda
veya güvenlik akışında bir düzeltme yapılınca iki yerde düzeltmek gerekmesin.
Sponsor dosyası yalnızca değişen metinleri yazar, gerisi dil dosyasından gelir.

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
PARTNERS = ROOT / "content" / "partners"
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


# Suu'nun kendi hero degradesi. Sponsor kendi rengini getirebilir.
DEFAULT_THEME = {"from": "#01A5F7", "mid": "#0B6FD0", "to": "#063C7A"}


def deep_merge(base: dict, over: dict) -> dict:
    """Sponsor dosyası yalnızca DEĞİŞEN anahtarları yazsın diye."""
    out = dict(base)
    for key, value in over.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


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

    def render(*, lang, c, out_path, page_url, alternates, lang_links, partner, theme):
        runtime = {"stock": c["stock"], "form": c["form"], "result": c["result"], "errors": c["errors"]}
        html = template.render(
            lang=lang,
            dir=TARGETS[lang][2],
            locale=TARGETS[lang][1],
            c=c,
            partner=partner,
            theme=theme,
            page_url=page_url,
            xdefault_url=alternates[0][1] if len(alternates) == 1 else f"{BASE}/{TARGETS[XDEFAULT][0]}",
            alternates=alternates,
            lang_links=lang_links,
            api_base=cfg["apiBase"].rstrip("/"),
            turnstile_key=cfg["turnstileSiteKey"],
            app_store=links["app_store"],
            google_play=links["google_play"],
            app_store_id=links["app_store_id"],
            copy_json=esc(json.dumps(runtime, ensure_ascii=False, separators=(",", ":"))),
        )
        if not html.endswith("\n"):
            html += "\n"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        old = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
        state = "aynı" if old == html else ("yeni" if not old else "güncellendi")
        if old != html and args.apply:
            out_path.write_text(html, encoding="utf-8")
        return html, state, old != html

    wanted = [l.strip() for l in args.lang.split(",") if l.strip()] or list(TARGETS)
    changed = 0

    for lang in wanted:
        if lang not in TARGETS:
            print(f"⚠  bilinmeyen dil: {lang}")
            continue
        out_name = TARGETS[lang][0]
        c = json.loads((GIFT / f"{lang}.json").read_text(encoding="utf-8"))
        html, state, diff = render(
            lang=lang, c=c, out_path=ROOT / out_name, page_url=f"{BASE}/{out_name}",
            alternates=[(code, f"{BASE}/{TARGETS[code][0]}") for code in TARGETS],
            lang_links=[(code, f"/{TARGETS[code][0]}", TARGETS[code][3]) for code in TARGETS],
            partner=None, theme=DEFAULT_THEME,
        )
        changed += diff
        print(f"{lang:3s} → {out_name:22s} {len(html)//1024:3d} KB  {state}")

    # ── sponsorluk sayfaları ──
    for pf in sorted(PARTNERS.glob("*.json")):
        if pf.name.startswith("_"):
            continue
        data = json.loads(pf.read_text(encoding="utf-8"))
        slug = data["slug"]
        for lang in data.get("langs", ["tr"]):
            base = json.loads((GIFT / f"{lang}.json").read_text(encoding="utf-8"))
            c = deep_merge(base, data.get("copy", {}).get(lang, {}))
            rel = f"{slug}/index.html" if lang == data.get("langs", ["tr"])[0] else f"{slug}/{lang}.html"
            url = f"{BASE}/{slug}/" if rel.endswith("index.html") else f"{BASE}/{rel}"
            partner = {"slug": slug, "name": data["name"], "short": data.get("short", data["name"]),
                       "logo": data["logo"]}
            html, state, diff = render(
                lang=lang, c=c, out_path=ROOT / rel, page_url=url,
                alternates=[(lang, url)],
                # Sponsor sayfasında genel dil menüsü gösterilmez: kullanıcıyı
                # iş birliği sayfasından çıkarıp markasız sayfaya atardı.
                lang_links=[],
                partner=partner, theme=deep_merge(DEFAULT_THEME, data.get("theme", {})),
            )
            changed += diff
            print(f"{lang:3s} → {rel:22s} {len(html)//1024:3d} KB  {state}   [{data['name']}]")

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
