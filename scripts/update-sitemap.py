#!/usr/bin/env python3
"""
Suu — Sitemap güncelleyici (kayıt defteri kaynaklı)

rebuild-sitemap.py mevcut sitemap'i baştan kuruyor ve kendi kopya küme
tablosunu taşıyordu (dördüncü gerçek kaynağı). Bu script onun yerine
CERRAHİ çalışır:

  1. content/page-registry.json'a göre eksik URL'leri EKLER
  2. Her URL'in xhtml:link hreflang açıklamalarını kayıt defterine göre YENİLER
  3. Mevcut <image:image> blokları, priority ve changefreq DOKUNULMADAN kalır
  4. llms.txt ailesini keşfedilebilir olsun diye listeler

Böylece bir yılda birikmiş image annotation'ları kaybolmaz.

Kullanım:
    python3 scripts/update-sitemap.py            # önizleme
    python3 scripts/update-sitemap.py --apply
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITEMAP = ROOT / "sitemap.xml"
REGISTRY = ROOT / "content" / "page-registry.json"
BASE = "https://suuapp.com"
TODAY = datetime.date.today().isoformat()

# noindex veya indekslenmemesi gereken sayfalar — sitemap'e girmez
EXCLUDE_PARTS = ("/404", "/admin.html", "/app/", "/makale.html",
                 "/yandex_", "og-image-template.html",
                 # Hediye kod kampanyası: noindex, bağlantı elle paylaşılıyor.
                 # Aramadan gelen rastgele trafik sınırlı kod havuzunu tüketmesin.
                 "/hediye-kod", "/gift-code", "/x9f4c2e7b")

RE_URL_BLOCK = re.compile(r"[ \t]*<url>(.*?)</url>\s*\n?", re.DOTALL)


def git_last_modified(rel: str) -> str | None:
    """Dosyaya dokunan son commit'in tarihi (YYYY-MM-DD).

    lastmod önceden dokunulmadan korunuyordu; sonuç olarak bu ay baştan yazılan
    sayfalar bile Mayıs tarihi ilan ediyordu (250 URL'nin 245'i). Tarayıcıya
    "burada yeni bir şey yok" demek, yeniden taramayı geciktiriyor ve
    "Keşfedildi / Tarandı - dizine eklenmemiş" satırlarını besliyor.
    Her build'de TODAY yazmak da yalan olurdu — git'teki gerçek tarih kullanılır.
    """
    import subprocess
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                             cwd=ROOT, capture_output=True, text=True, timeout=10)
        d = out.stdout.strip()
        return d if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else None
    except Exception:
        return None
RE_LOC = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")
RE_XHTML = re.compile(r"[ \t]*<xhtml:link[^>]*/?>[ \t]*\n?")
RE_LASTMOD = re.compile(r"(<lastmod>)([^<]*)(</lastmod>)")


def abs_url(path: str) -> str:
    return f"{BASE}/" if path == "/" else f"{BASE}/{path.lstrip('/')}"


def family_urls(variants: dict[str, str], kind: str, default: str) -> dict[str, str]:
    out = {}
    for lang, value in variants.items():
        rel = value if kind == "root" else (
            f"blog/{value}.html" if lang == default else f"blog/{lang}/{value}.html"
        )
        out[lang] = abs_url(rel)
    return out


def local_exists(url: str) -> bool:
    rel = url[len(BASE) + 1:] or "index.html"
    return (ROOT / (rel if rel else "index.html")).exists()


def build_cluster_map(reg: dict) -> dict[str, dict[str, str]]:
    """URL → { lang: URL } (hreflang açıklamaları için)"""
    default = reg["_default"]
    order = reg["_languages"]
    out: dict[str, dict[str, str]] = {}
    for kind in ("root", "blog"):
        for variants in reg[kind].values():
            urls = family_urls(variants, kind, default)
            urls = {l: u for l, u in urls.items() if local_exists(u)}
            if not urls:
                continue
            ordered = {l: urls[l] for l in order if l in urls}
            # Tek dilli sayfa da sitemap'e girmeli; sadece hreflang açıklaması
            # almaz (kendine tek referans anlamsız olurdu).
            for u in ordered.values():
                out[u] = ordered if len(ordered) > 1 else {}
    return out


def render_xhtml(cluster: dict[str, str], xdefault_lang: str) -> str:
    lines = []
    for lang, href in cluster.items():
        lines.append(f'        <xhtml:link rel="alternate" hreflang="{lang}" href="{href}"/>')
    # x-default hedefi _xdefault'tan gelir (URL yapısını süren _default'tan ayrı).
    xdefault = cluster.get(xdefault_lang) or next(iter(cluster.values()))
    lines.append(f'        <xhtml:link rel="alternate" hreflang="x-default" href="{xdefault}"/>')
    return "\n".join(lines) + "\n"


def main() -> int:
    apply = "--apply" in sys.argv

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    default = reg["_default"]
    xdefault_lang = reg.get("_xdefault", default)
    clusters = build_cluster_map(reg)

    xml = SITEMAP.read_text(encoding="utf-8")
    blocks = RE_URL_BLOCK.findall(xml)
    present = {RE_LOC.search(b).group(1) for b in blocks if RE_LOC.search(b)}

    refreshed = 0
    removed = 0

    def rewrite(match: re.Match) -> str:
        nonlocal refreshed, removed
        inner = match.group(1)
        loc_m = RE_LOC.search(inner)
        if not loc_m:
            return match.group(0)
        loc = loc_m.group(1)

        if any(x in loc for x in EXCLUDE_PARTS):
            removed += 1
            return ""

        # İndekslenemez dosya tipleri sitemap'te yer almaz (yukarıdaki nota bakın)
        if loc.endswith((".txt", ".json")):
            removed += 1
            return ""

        cleaned = RE_XHTML.sub("", inner)
        cluster = clusters.get(loc)
        if cluster:
            block = render_xhtml(cluster, xdefault_lang)
            # hreflang bloğunu <loc>'un hemen ardına koy
            cleaned = cleaned.replace(loc_m.group(0), loc_m.group(0) + "\n" + block.rstrip("\n"), 1)

        rel = loc[len(BASE) + 1:] or "index.html"
        real = git_last_modified(rel)
        if real:
            def _bump(m: re.Match) -> str:
                # lastmod yalnızca İLERİ gider — geriye çekmek sinyali bozar
                return m.group(1) + (real if real > m.group(2) else m.group(2)) + m.group(3)
            cleaned = RE_LASTMOD.sub(_bump, cleaned, count=1)

        new = f"    <url>{cleaned}</url>\n"
        if new != match.group(0):
            refreshed += 1
        return new

    xml_new = RE_URL_BLOCK.sub(rewrite, xml)

    # ── Eksik URL'leri ekle ──────────────────────────────────
    wanted: list[str] = []
    for url in clusters:
        if url not in present and not any(x in url for x in EXCLUDE_PARTS):
            wanted.append(url)

    # llms*.txt ve ai-plugin.json BİLEREK sitemap'e girmez.
    #
    # Sitemap indekslenebilir SAYFALARI bildirir. Düz metin ve JSON dosyaları
    # indekslenemez, dolayısıyla listelemek Search Console'da garantili
    # "Tarandı - şu anda dizine eklenmiş değil" satırı üretir ve tarama
    # bütçesini gerçek sayfalardan çalar. 2026-08-17'de Google'ın bildirdiği
    # 13 "tarandı, indekslenmedi" URL'sinden biri tam olarak llms-full.txt'ti.
    #
    # Keşif doğru mekanizmayla zaten sağlanıyor:
    #   robots.txt yorum bloğu + sayfa <head>'lerindeki
    #   <link rel="alternate" type="text/plain" href="/llms-*.txt">

    added_xml = ""
    for url in sorted(set(wanted)):
        cluster = clusters.get(url)
        hre = ("\n" + render_xhtml(cluster, xdefault_lang).rstrip("\n")) if cluster else ""
        prio = "1.0" if url == f"{BASE}/" else ("0.5" if url.endswith(".txt") else "0.8")
        added_xml += (
            f"    <url>\n"
            f"        <loc>{url}</loc>{hre}\n"
            f"        <lastmod>{TODAY}</lastmod>\n"
            f"        <changefreq>weekly</changefreq>\n"
            f"        <priority>{prio}</priority>\n"
            f"    </url>\n"
        )

    if added_xml:
        xml_new = xml_new.replace("</urlset>", added_xml + "</urlset>", 1)

    total = xml_new.count("<url>")
    print(f"mevcut: {len(present)} URL")
    print(f"hreflang açıklaması yenilenen: {refreshed}")
    print(f"çıkarılan (noindex): {removed}")
    print(f"eklenen: {len(set(wanted))}")
    for u in sorted(set(wanted)):
        print(f"  + {u}")
    print(f"\ntoplam: {total} URL")

    if apply:
        SITEMAP.write_text(xml_new, encoding="utf-8")
        print(f"\n{SITEMAP.name} yazıldı")
    else:
        print("\nÖNİZLEME — Uygulamak için: python3 scripts/update-sitemap.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
