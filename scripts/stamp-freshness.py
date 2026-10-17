#!/usr/bin/env python3
"""
Suu — Blog tazelik tarihleri: içerik GERÇEKTEN değişince dateModified kendiliğinden ilerler

Yapay zekâ aramaları ve Google güncel içeriği öne çıkarır; tarihi yazının
JSON-LD dateModified'ından, article:modified_time'dan, görünür "Güncelleme"
satırından ve sitemap lastmod'undan okur. Bu tarihler eskiden elle tutuluyordu:
339 yazının 227'sinde güncelleme tarihi yayın tarihiyle aynı kalmıştı, gerçek
düzenlemeler bile tarihe yansımıyordu.

Bu script tarihi İÇERİKTEN türetir — takvimden değil:

  1. Her yazının OKUNAN metni çıkarılır. Menü, alt bilgi, tarih satırı,
     script/stil ve toplu script'lerin eklediği blokları (ilgili yazılar,
     sütunlar arası bağlantı, CTA) sayılmaz. Hreflang/analitik/şema
     enjeksiyonu gibi toplu işler bu yüzden "değişiklik" sayılmaz —
     2026-08-17'de 235 URL'nin 228'ine aynı lastmod'u basan hata buydu.
  2. Metin, content/freshness.json'daki son tarihlenmiş haliyle karşılaştırılır.
     En az 25 kelime ya da metnin %2'si değiştiyse "güncellendi" sayılır.
     Daha küçük düzeltmeler (yazım, tek rakam) tarih ilerletmez ama birikir.
  3. Yeni tarih = metni bugünkü hâline getiren commit'in tarihi
     (Europe/Istanbul). "Bugün" değil: hesap ne zaman yapılırsa yapılsın aynı
     sonucu verir, tarih kendiliğinden ileri kaymaz.
  4. Elle yazılmış yazıda: JSON-LD dateModified, article:modified_time ve
     görünür "Güncelleme: …" satırı. Üretilmiş yazıda (build-compare.py):
     tarih kayıt defterine yazılır, sayfayı üretici yeniden basar.
     Ardından sitemap lastmod ve blog indekslerinin şemasındaki tarih eşitlenir.

İçerik değişmeden tarih ASLA ilerlemez. Elle ileri alınmış tarihe dokunulmaz;
geri düşmüş tarih kayıt defterindekine döndürülür.

Yayın akışı (deploy.yml) her push'ta --apply ile çalıştırır ve sonucu depoya
geri yazar; elle çalıştırmak gerekmez.

Kullanım:
    python3 scripts/stamp-freshness.py                  # önizleme
    python3 scripts/stamp-freshness.py --apply
    python3 scripts/stamp-freshness.py --explain blog/kalori-acigi.html
    python3 scripts/stamp-freshness.py --report [--days 180]   # eskiyen yazılar (Markdown)
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

from _langs import date_fmt, months, ui_strings

ROOT = Path(__file__).resolve().parents[1]
BLOG = ROOT / "blog"
MANIFEST = ROOT / "content" / "freshness.json"
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://suuapp.com"
TZ = ZoneInfo("Europe/Istanbul")
GENERATED_MARK = "ÜRETİLMİŞ DOSYA"

MIN_WORDS = 25          # bu kadar kelime değişmeden tarih ilerlemez
MIN_RATIO = 0.02        # uzun yazıda eşik metnin %2'si
HISTORY = 60            # tarih için geriye bakılan en fazla commit

MONTHS = months()
DATE_FMT = date_fmt()
UI = ui_strings()

RE_DATE_MODIFIED = re.compile(r'("dateModified"\s*:\s*")(\d{4}-\d{2}-\d{2})([^"]*")')
RE_MOD_META = re.compile(r'(<meta property="article:modified_time" content=")([^"]*)(")')
RE_PUB_META = re.compile(r'<meta property="article:published_time" content="[^"]*">')
RE_META_DIV = re.compile(r'(<div class="meta">)(.*?)(</div>)', re.S)
RE_LANG = re.compile(r'<html[^>]*\blang="([a-z]{2})')


# ── okunan metin ─────────────────────────────────────────────
SKIP_TAGS = {"head", "script", "style", "noscript", "svg", "template", "iframe",
             "nav", "header", "footer", "form", "button", "select", "textarea"}
# Toplu script'lerin ya da şablonun eklediği, yazının kendisi olmayan bloklar
# "cards": üretilmiş sayfalarda (build-compare.py şablonu) "ilgili sayfalar" ızgarası —
# yeni rehber eklendikçe tüm kümeye kart eklenir; yazının kendisi değil.
SKIP_CLASSES = {"meta", "related", "related-grid", "related-card", "cards", "breadcrumb",
                "breadcrumbs", "cta-box", "trial-banner", "sticky-cta",
                "sticky-download-bar", "share", "lang-switcher"}
# Metin çıkarma kuralı değişince artır: kayıttaki özetler önceki hâllerden
# yeniden hesaplanır, tarihlere dokunulmaz.
RULES = 2
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "source", "track", "wbr"}


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.skip = 0           # atlanan alt ağacın içindeki derinlik
        self.skip_next = False  # link-pillars işaretinden sonraki ilk öğe
        self.body = False
        self.words: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.body = True
        if tag in VOID:
            return
        cls = set((dict(attrs).get("class") or "").split())
        starts = self.skip == 0 and (tag in SKIP_TAGS or bool(cls & SKIP_CLASSES) or self.skip_next)
        self.skip_next = False
        self.stack.append(tag)
        if self.skip or starts:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in VOID or tag not in self.stack:
            return
        while self.stack:                  # kapanmamış <p>/<li> vb. tolere edilir
            t = self.stack.pop()
            if self.skip:
                self.skip -= 1
            if t == tag:
                break

    def handle_comment(self, data):
        if "link-pillars" in data:         # "<!-- sütunlar arası bağlantı: scripts/link-pillars.py -->"
            self.skip_next = True

    def handle_data(self, data):
        if self.body and not self.skip:
            self.words.extend(data.split())


def words_of(html: str) -> list[str]:
    p = _Text()
    p.feed(html)
    p.close()
    return p.words


def text_hash(words: list[str]) -> str:
    return hashlib.sha1(" ".join(words).encode("utf-8")).hexdigest()


def changed_words(old: list[str], new: list[str]) -> int:
    sm = difflib.SequenceMatcher(None, old, new, autojunk=False)
    return sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal")


def threshold(total: int) -> int:
    return max(MIN_WORDS, int(total * MIN_RATIO + 0.5))


# ── git ──────────────────────────────────────────────────────
def git(*args: str, partial: bool = False) -> bytes | None:
    """partial: hata koduyla bitse de çıktıyı kullan — sığ klonda `git log`
    geçmişin sınırına gelince hata verir ama o noktaya kadarki çıktı doğrudur."""
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if r.returncode == 0 or (partial and r.stdout):
        return r.stdout
    return None


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def has_object(sha: str) -> bool:
    return git("cat-file", "-e", sha) is not None


def blob_text(sha: str) -> str | None:
    out = git("cat-file", "-p", sha)
    return out.decode("utf-8", "replace") if out is not None else None


def head_blob(rel: str) -> str | None:
    out = git("rev-parse", f"HEAD:{rel}")
    return out.decode().strip() if out else None


def today() -> str:
    return dt.datetime.now(TZ).date().isoformat()


def last_text_change(rel: str, cur: list[str]) -> str:
    """Metni bugünkü hâline getiren commit'in tarihi (İstanbul).

    Yeniden eskiye yürünür; metni hâlâ aynı olan en eski commit bu metni
    getirendir. HEAD bile farklıysa (henüz commit'lenmemiş düzenleme) bugün.
    Geçmiş hiç okunamazsa "bugün" DEĞİL son commit'in tarihi: "bugün" her
    çalıştırmada ilerler, tarihi kendiliğinden kaydırırdı."""
    lines = (git("log", f"-n{HISTORY}", "--format=%H %cI", "--", rel, partial=True) or b"").decode().splitlines()
    if not lines:
        head = git("log", "-1", "--format=%cI", partial=True)
        print(f"  ⚠ {rel}: git geçmişi okunamadı — son commit'in tarihi kullanıldı", file=sys.stderr)
        return istanbul(head.decode().strip()) if head else today()
    found = None
    for line in lines:
        sha, when = line.split(" ", 1)
        content = git("show", f"{sha}:{rel}")
        if content is None or words_of(content.decode("utf-8", "replace")) != cur:
            break
        found = when
    return istanbul(found) if found else today()


def istanbul(iso_time: str) -> str:
    return dt.datetime.fromisoformat(iso_time).astimezone(TZ).date().isoformat()


# ── tarih yazma ──────────────────────────────────────────────
def display_date(lang: str, iso: str) -> str:
    y, m, d = iso.split("-")
    return DATE_FMT[lang].format(d=int(d), month=MONTHS[lang][int(m) - 1], y=y)


def page_lang(rel: str, html: str) -> str:
    m = RE_LANG.search(html)
    if m and m.group(1) in DATE_FMT:
        return m.group(1)
    parts = Path(rel).parts
    return parts[1] if len(parts) == 3 and parts[1] in DATE_FMT else "tr"


def page_date(html: str) -> str | None:
    m = RE_DATE_MODIFIED.search(html)
    return m.group(2) if m else None


def published_date(html: str) -> str | None:
    m = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
    return m.group(1) if m else None


# Elle yazılmış "Güncelleme: 29 Eylül 2026" / "Updated September 29, 2026"
_LABELS = sorted({re.escape(UI[l]["updated_label"].rstrip(":")) for l in UI if "updated_label" in UI[l]}
                 | {"Updated"}, key=len, reverse=True)
RE_MANUAL_UPDATED = re.compile(r"(?:" + "|".join(_LABELS) + r"):?\s*[^·<]+?(?=\s*·|\s*<|\s*$)")


def visible_line(html: str, lang: str, iso: str) -> str:
    """Görünür tarih satırına (div.meta) "Güncelleme: …" ekler ya da yeniler."""
    m = RE_META_DIV.search(html)
    if not m:
        return html
    label = UI[lang]["updated_label"]
    mark = (f'<span class="meta-updated" data-freshness>{label} '
            f'<time datetime="{iso}">{display_date(lang, iso)}</time></span>')
    inner = m.group(2)
    if "data-freshness" in inner:
        inner = re.sub(r'<span class="meta-updated" data-freshness>.*?</span>', mark, inner, count=1, flags=re.S)
    elif RE_MANUAL_UPDATED.search(inner):
        inner = RE_MANUAL_UPDATED.sub(mark, inner, count=1)
    elif "<span" in inner:                      # <span>📅 tarih</span><span>…</span> biçimi
        end = inner.find("</span>") + len("</span>")
        indent = re.match(r"\s*", inner).group(0) or "\n        "
        inner = inner[:end] + indent + mark + inner[end:]
    elif " · " in inner:                         # "tarih · yazar · süre" biçimi
        i = inner.find(" · ")
        inner = inner[:i] + " · " + mark + inner[i:]
    else:
        return html
    return html[:m.start(2)] + inner + html[m.end(2):]


def stamp_html(html: str, lang: str, iso: str) -> str:
    html = RE_DATE_MODIFIED.sub(lambda m: m.group(1) + iso + m.group(3), html)
    if RE_MOD_META.search(html):
        html = RE_MOD_META.sub(lambda m: m.group(1) + iso + m.group(3), html, count=1)
    else:
        pm = RE_PUB_META.search(html)
        if pm:
            indent = html[html.rfind("\n", 0, pm.start()) + 1:pm.start()]
            html = html[:pm.end()] + f'\n{indent}<meta property="article:modified_time" content="{iso}">' + html[pm.end():]
    pub = published_date(html)
    if pub is None or iso > pub:
        html = visible_line(html, lang, iso)
    return html


def stamp_sitemap(dates: dict[str, str]) -> int:
    if not dates or not SITEMAP.exists():
        return 0
    xml = SITEMAP.read_text(encoding="utf-8")
    n = 0
    for rel, iso in dates.items():
        loc = re.escape(f"{BASE}/{rel}")
        new, k = re.subn(r"(<loc>" + loc + r"</loc>(?:(?!</url>).)*?<lastmod>)[^<]*(</lastmod>)",
                         lambda m: m.group(1) + iso + m.group(2), xml, count=1, flags=re.S)
        if k and new != xml:
            xml, n = new, n + 1
    SITEMAP.write_text(xml, encoding="utf-8")
    return n


def stamp_indexes(dates: dict[str, str]) -> int:
    """Blog indekslerinin (blog*.html) Blog.blogPost şemasında yalnızca o yazının
    dateModified'ı. İndeksi baştan üretmek (build-blog-index.py) tarihle ilgisiz
    bekleyen işleri de uygulardı (küçük resim üretimi vb.); burada yalnızca tarih değişir."""
    n = 0
    for index in sorted(ROOT.glob("blog*.html")):
        text = index.read_text(encoding="utf-8")
        new = text
        for rel, iso in dates.items():
            url = re.escape(f"{BASE}/{rel}")
            new = re.sub(r'("url":\s*"' + url + r'"[^{}]*?"dateModified":\s*")[^"]+(")',
                         lambda m: m.group(1) + iso + m.group(2), new)
            new = re.sub(r'("dateModified":\s*")[^"]+("[^{}]*?"url":\s*"' + url + r'")',
                         lambda m: m.group(1) + iso + m.group(2), new)
        if new != text:
            index.write_text(new, encoding="utf-8")
            n += 1
    return n


# ── kayıt defteri ────────────────────────────────────────────
def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {
        "_comment": "scripts/stamp-freshness.py tarafından tutulur — elle düzenlemeyin. "
                    "Her yazı: son tarihlenmiş metnin özeti (text), o hâlin git blob'u (blob) "
                    "ve güncelleme tarihi (modified). Üretilmiş yazılarda build-compare.py "
                    "bu tarihi okur.",
        "rules": RULES,
        "pages": {},
    }


def refresh_rules(man: dict) -> int:
    """Kural değiştiyse özetleri kayıtlı blob'lardan yeniden hesapla (tarih değişmez)."""
    if man.get("rules") == RULES:
        return 0
    n = 0
    for rel, e in man["pages"].items():
        old = blob_text(e["blob"])
        if old is not None:
            e["text"] = text_hash(words_of(old))
            n += 1
    man["rules"] = RULES
    return n


def save_manifest(man: dict) -> None:
    man["pages"] = dict(sorted(man["pages"].items()))
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def blog_pages() -> list[Path]:
    return sorted(p for p in BLOG.rglob("*.html")
                  if '"dateModified"' in p.read_text(encoding="utf-8", errors="replace"))


def baseline_blob(rel: str, data: bytes) -> str:
    """Bu hâlin git'te bulunan blob'u — sonraki ölçümler buradan okunur."""
    sha = blob_sha(data)
    return sha if has_object(sha) else (head_blob(rel) or sha)


# ── ana akış ─────────────────────────────────────────────────
def run(apply: bool) -> int:
    man = load_manifest()
    rehashed = refresh_rules(man)
    pages = man["pages"]
    added, stamped, restored, honored, small = [], [], [], [], []
    sitemap_dates: dict[str, str] = {}
    regen = False

    current = blog_pages()
    # Silinen ya da yönlendirmeye çevrilen yazılar kayıttan düşer (raporu kirletmesin)
    alive = {p.relative_to(ROOT).as_posix() for p in current}
    gone = [rel for rel in pages if rel not in alive]
    for rel in gone:
        del pages[rel]

    for path in current:
        rel = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        html = data.decode("utf-8")
        words = words_of(html)
        cur = page_date(html)
        generated = GENERATED_MARK in html
        entry = pages.get(rel)

        if entry is None:                          # ilk kez: mevcut durum başlangıç olur, tarih değişmez
            pages[rel] = {"text": text_hash(words), "blob": baseline_blob(rel, data), "modified": cur}
            added.append(rel)
            continue

        if text_hash(words) == entry["text"]:
            if cur and cur > entry["modified"]:    # elle ileri alınmış: saygı duy
                entry["modified"] = cur
                honored.append(rel)
            elif cur and cur < entry["modified"]:  # geri düşmüş (yeniden üretim, geri alma): düzelt
                restored.append((rel, cur, entry["modified"]))
                sitemap_dates[rel] = entry["modified"]
                if generated:
                    regen = True
                elif apply:
                    path.write_text(stamp_html(html, page_lang(rel, html), entry["modified"]), encoding="utf-8")
            continue

        old = blob_text(entry["blob"])
        if old is None:
            print(f"  ⚠ {rel}: önceki hâli git'te yok ({entry['blob'][:8]}) — ölçülemedi, atlandı", file=sys.stderr)
            continue
        old_words = words_of(old)
        n = changed_words(old_words, words)
        if n < threshold(len(old_words)):
            small.append((rel, n, threshold(len(old_words))))
            continue

        new = max(cur or "", last_text_change(rel, words), entry["modified"])
        stamped.append((rel, cur, new, n))
        pages[rel] = {"text": text_hash(words), "blob": baseline_blob(rel, data), "modified": new}
        if new != cur:
            sitemap_dates[rel] = new
            if generated:
                regen = True
            elif apply:
                path.write_text(stamp_html(html, page_lang(rel, html), new), encoding="utf-8")

    # ── özet ──
    for rel, cur, new, n in stamped:
        print(f"  ✎ {rel:<60} {cur} → {new}   ({n} kelime değişti)")
    for rel, cur, want in restored:
        print(f"  ↺ {rel:<60} {cur} → {want}   (geri düşmüştü)")
    for rel, n, t in small:
        print(f"  · {rel:<60} {n} kelime < eşik {t} — tarih aynı kalır")
    if rehashed:
        print(f"  ⟳ metin kuralı değişti: {rehashed} özet yeniden hesaplandı (tarihlere dokunulmadı)")
    if added:
        print(f"  + kayıt defterine eklenen yazı: {len(added)} (tarihlerine dokunulmadı)")
    if honored:
        print(f"  = elle ileri alınmış tarih kabul edildi: {len(honored)}")
    if gone:
        print(f"  − artık yazı olmayan kayıt silindi: {len(gone)}")

    if apply:
        save_manifest(man)
        if regen:
            regenerate()
        n = stamp_sitemap(sitemap_dates)
        k = stamp_indexes(sitemap_dates)
        print(f"\n{len(stamped)} yazının tarihi ilerledi, {len(restored)} düzeltildi; "
              f"sitemap'te {n} satır, {k} blog indeksi.")
    else:
        print(f"\n{len(stamped)} yazının tarihi ilerleyecek, {len(restored)} düzeltilecek  (yazmak için --apply)")
    return 0


def regenerate() -> None:
    """Üretilmiş yazıları kayıt defterindeki tarihlerle yeniden bas."""
    if importlib.util.find_spec("jinja2") is None:
        print("  ⚠ jinja2 yok — üretilmiş yazılar basılamadı: pip install jinja2 && "
              "python3 scripts/build-compare.py --apply", file=sys.stderr)
        return
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build-compare.py"), "--apply"],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)


def explain(rel: str) -> int:
    man = load_manifest()
    refresh_rules(man)
    entry = man["pages"].get(rel)
    html = (ROOT / rel).read_text(encoding="utf-8")
    words = words_of(html)
    print(f"{rel}\n  okunan metin: {len(words)} kelime, sayfadaki dateModified: {page_date(html)}")
    if not entry:
        print("  kayıt defterinde yok — ilk çalıştırmada eklenir")
        return 0
    print(f"  kayıt defteri: {entry['modified']} (blob {entry['blob'][:8]})")
    if text_hash(words) == entry["text"]:
        print("  metin son tarihlenmiş hâliyle aynı")
        return 0
    old = blob_text(entry["blob"])
    if old is None:
        print("  önceki hâl git'te yok")
        return 1
    ow = words_of(old)
    n, t = changed_words(ow, words), threshold(len(ow))
    print(f"  değişen: {n} kelime, eşik: {t} → {'TARİH İLERLER' if n >= t else 'tarih aynı kalır'}")
    if n >= t:
        print(f"  yeni tarih: {max(page_date(html) or '', last_text_change(rel, words), entry['modified'])}")
    sm = difflib.SequenceMatcher(None, ow, words, autojunk=False)
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op != "equal":
            print(f"   {op:7} −「{' '.join(ow[i1:i2])[:90]}」 +「{' '.join(words[j1:j2])[:90]}」")
    return 0


def report(days: int) -> int:
    """Uzun süredir içeriği değişmemiş yazılar — Markdown (aylık rapor konusu)."""
    man = {rel: e for rel, e in load_manifest()["pages"].items() if (ROOT / rel).exists()}
    cutoff = (dt.datetime.now(TZ).date() - dt.timedelta(days=days)).isoformat()
    old = sorted((e["modified"], rel) for rel, e in man.items() if e.get("modified") and e["modified"] < cutoff)
    by_lang: dict[str, list[tuple[str, str]]] = {}
    for mod, rel in old:
        parts = Path(rel).parts
        lang = parts[1] if len(parts) == 3 else "tr"
        by_lang.setdefault(lang, []).append((mod, rel))
    print(f"## {days} gündür içeriği değişmemiş yazılar: {len(old)} / {len(man)}\n")
    print("Bu yazıların tarihi ancak içerikleri gerçekten güncellenirse ilerler "
          "(en az 25 kelime ya da metnin %2'si). Önce trafiği yüksek olanlardan başlayın.\n")
    for lang in sorted(by_lang, key=lambda l: -len(by_lang[l])):
        print(f"<details><summary><b>{lang.upper()}</b> — {len(by_lang[lang])} yazı</summary>\n")
        for mod, rel in by_lang[lang]:
            print(f"- `{mod}` [{rel}]({BASE}/{rel})")
        print("\n</details>\n")
    if not old:
        print("Hepsi güncel. 🎉")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--explain", metavar="DOSYA")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--days", type=int, default=180)
    a = ap.parse_args()
    if a.explain:
        return explain(a.explain)
    if a.report:
        return report(a.days)
    return run(a.apply)


if __name__ == "__main__":
    raise SystemExit(main())
