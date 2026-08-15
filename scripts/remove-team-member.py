#!/usr/bin/env python3
"""
Suu — ekip üyesini siteden bütünüyle kaldır

Bir kişi ekipten ayrıldığında adı 20+ dosyaya yayılmış durumda olur:
görünür ekip kartı, JSON-LD Person düğümü, Organization employee dizisi,
meta etiketleri, SSS soruları ve blog yazarlığı. Bunların bir kısmı kalırsa
entity grafiği kırılır (var olmayan @id'ye referans) — yapay zekâlar için
en pahalı hata türü budur.

Bu script yapısal kısımları hallederi; düz metin (bio paragrafı, ekip
sayısı geçen cümle) elle düzeltilir çünkü her dilde farklı yazılır.

Yaptıkları:
  1. JSON-LD @graph içinden Person düğümünü siler
  2. Organization employee / member dizilerinden çıkarır
  3. Article author'ı devralan kişiye taşır (yazarsız Article olmaz)
  4. FAQPage içinden kişiyle ilgili soruyu siler
  5. meta description / keywords / og / twitter içinden adını temizler
  6. article:author meta'sını devralan kişiye çevirir
  7. Görünür byline'ı devralan kişiye çevirir
  8. Ekip kartı <div> bloğunu siler

Kullanım:
    python3 scripts/remove-team-member.py               # önizleme
    python3 scripts/remove-team-member.py --apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".github", ".claude", "node_modules", ".qodo"}

# ── Kaldırılan kişi ───────────────────────────────────────────────────────
TARGET_ID = "https://suuapp.com/#nisanur"
TARGET_NAMES = ["Nisanur Büyükbaş", "Nisanur Buyukbas", "Nisanur Buyukbas",
                "نيسانور بويوكباش", "Nisanur"]
TARGET_PHOTO = "assets/team/nisanur.jpg"

# ── İçeriği devralan kişi ─────────────────────────────────────────────────
HEIR = {
    "@type": "Person",
    "@id": "https://suuapp.com/#furkan",
    "name": "Furkan Mert Fındıklı",
    "url": "https://suuapp.com/yazarlar/furkan-mert.html",
    "jobTitle": "Founder & Developer",
    "affiliation": {
        "@type": "Organization",
        "@id": "https://suuapp.com/#organization",
        "name": "Suu",
        "url": "https://suuapp.com",
    },
}
HEIR_NAME = "Furkan Mert Fındıklı"

RE_LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.DOTALL)


def mentions(value: object) -> bool:
    """Bu JSON düğümü kaldırılan kişiyi mi anlatıyor?"""
    if isinstance(value, dict):
        if value.get("@id") == TARGET_ID:
            return True
        blob = json.dumps(value, ensure_ascii=False)
        return any(n in blob for n in TARGET_NAMES[:4])
    if isinstance(value, str):
        return any(n in value for n in TARGET_NAMES[:4])
    return False


def scrub_node(node: object) -> object:
    """Bir JSON-LD düğümünü kişiden arındır. None dönerse düğüm silinir."""
    if isinstance(node, list):
        out = []
        for item in node:
            cleaned = scrub_node(item)
            if cleaned is not None:
                out.append(cleaned)
        return out

    if not isinstance(node, dict):
        return node

    t = node.get("@type")

    # 1) Kişinin kendi Person düğümü → sil
    if t == "Person" and mentions(node):
        return None

    # 2) Organization içindeki rol kaydı → sil
    if t == "OrganizationRole" and mentions(node.get("member")):
        return None

    # 3) SSS'te kişiyle ilgili soru → sil
    if t == "Question" and mentions(node.get("name")):
        return None

    # 4) Article yazarı → devralan kişi
    if "author" in node and mentions(node["author"]):
        node["author"] = json.loads(json.dumps(HEIR))

    for key in ("employee", "employees", "member", "members", "founder"):
        if key in node:
            val = node[key]
            if isinstance(val, list):
                node[key] = [v for v in (scrub_node(v) for v in val) if v is not None]
            elif mentions(val):
                del node[key]
                continue

    for key, val in list(node.items()):
        if key in ("author",):
            continue
        cleaned = scrub_node(val)
        if cleaned is None:
            del node[key]
        else:
            node[key] = cleaned

    return node


def scrub_jsonld(page: str) -> tuple[str, int]:
    hits = 0

    def repl(m: re.Match) -> str:
        nonlocal hits
        open_t, block, close_t = m.groups()
        if not any(n in block for n in TARGET_NAMES[:4]) and TARGET_ID not in block:
            return m.group(0)
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            return m.group(0)
        cleaned = scrub_node(data)
        if cleaned is None:
            hits += 1
            return ""                       # düğümün tamamı kişiye aitti
        out = json.dumps(cleaned, ensure_ascii=False, indent=2)
        out = out.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
        hits += 1
        return f"{open_t}\n{out}\n    {close_t}"

    return RE_LD.sub(repl, page), hits


# Ekip kartı: fotoğrafı içeren en yakın <div class="team-card"> … </div>
def drop_team_card(page: str) -> tuple[str, bool]:
    # Fotoğraf yolu hem JSON-LD "image" alanında hem görünür kartta geçer.
    # Kartı olan geçişi bulmak için tüm eşleşmeler denenir.
    start = -1
    for m in re.finditer(re.escape(TARGET_PHOTO), page):
        cand = page.rfind('<div class="team-card"', 0, m.start())
        if cand != -1 and m.start() - cand < 2000:
            start = cand
            break
    if start == -1:
        return page, False
    # dengeli </div> ara
    depth, i = 0, start
    while i < len(page):
        nxt_open = page.find("<div", i)
        nxt_close = page.find("</div>", i)
        if nxt_close == -1:
            return page, False
        if nxt_open != -1 and nxt_open < nxt_close:
            depth += 1
            i = nxt_open + 4
        else:
            depth -= 1
            i = nxt_close + 6
            if depth == 0:
                break
    end = i
    line_start = page.rfind("\n", 0, start) + 1
    return page[:line_start] + page[end:].lstrip("\n"), True


META_KEYS = ("description", "keywords", "og:description", "og:title",
             "twitter:description", "twitter:title")


def scrub_meta(page: str) -> tuple[str, int]:
    """meta content içinden kişinin adını ve bağlacını temizle."""
    hits = 0

    def clean_value(v: str) -> str:
        for name in ("Nisanur Büyükbaş", "Nisanur Buyukbas"):
            # "A, B ve C (rol)" → "A ve B"
            v = re.sub(r"\s*,?\s*(?:ve|and|и|و)\s+" + re.escape(name) + r"\s*\([^)]*\)", "", v)
            v = re.sub(r"\s*,?\s*(?:ve|and|и|و)\s+" + re.escape(name), "", v)
            v = re.sub(r"\s*" + re.escape(name) + r"\s*\([^)]*\)\s*,?", "", v)
            v = re.sub(r"\s*,\s*" + re.escape(name), "", v)
            v = v.replace(name, "")
        v = re.sub(r"\s*,\s*,", ",", v)
        v = re.sub(r"\s{2,}", " ", v).strip().strip(",").strip()
        return v

    def repl(m: re.Match) -> str:
        nonlocal hits
        whole, key, val = m.group(0), m.group(1), m.group(2)
        if key not in META_KEYS or not any(n in val for n in TARGET_NAMES[:2]):
            return whole
        new = clean_value(val)
        if new == val:
            return whole
        hits += 1
        return whole.replace(val, new)

    page = re.sub(r'<meta (?:name|property)="([^"]+)" content="([^"]*)"', repl, page)

    # article:author → devralan
    new_page, n = re.subn(
        r'(<meta property="article:author" content=")[^"]*(")',
        rf"\1{HEIR_NAME}\2", page)
    if n and any(n0 in page for n0 in TARGET_NAMES[:2]):
        hits += n
    return new_page, hits


def scrub_byline(page: str) -> tuple[str, int]:
    total = 0
    for name in ("Nisanur Büyükbaş", "Nisanur Buyukbas"):
        page, n = re.subn(
            r'(<span><i class="fas fa-pen"></i>\s*)' + re.escape(name) + r'(\s*</span>)',
            rf"\1{HEIR_NAME}\2", page)
        total += n
        # "· By X ·" / "· X ·" biçimli satır içi byline'lar
        page, n = re.subn(r'(·\s*(?:By\s+)?)' + re.escape(name), rf"\1{HEIR_NAME}", page)
        total += n
    return page, total


def main() -> int:
    apply = "--apply" in sys.argv
    report: list[tuple[str, list[str]]] = []

    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        try:
            page = original = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if not any(n in page for n in TARGET_NAMES[:4]) and TARGET_PHOTO not in page:
            continue

        actions: list[str] = []

        page, dropped = drop_team_card(page)
        if dropped:
            actions.append("ekip kartı silindi")

        page, n = scrub_jsonld(page)
        if n:
            actions.append(f"{n} JSON-LD bloğu temizlendi")

        page, n = scrub_meta(page)
        if n:
            actions.append(f"{n} meta etiketi")

        page, n = scrub_byline(page)
        if n:
            actions.append(f"{n} byline devredildi")

        if page != original:
            report.append((str(rel), actions))
            if apply:
                path.write_text(page, encoding="utf-8")

    # humans.txt
    humans = ROOT / "humans.txt"
    if humans.exists():
        lines = humans.read_text(encoding="utf-8").splitlines(keepends=True)
        kept = [ln for ln in lines if not any(n in ln for n in TARGET_NAMES[:2])]
        if len(kept) != len(lines):
            report.append(("humans.txt", [f"{len(lines) - len(kept)} satır silindi"]))
            if apply:
                humans.write_text("".join(kept), encoding="utf-8")

    # content/suu-facts.json
    facts_path = ROOT / "content" / "suu-facts.json"
    if facts_path.exists():
        facts = json.loads(facts_path.read_text(encoding="utf-8"))
        team = facts.get("entities", {}).get("team")
        if isinstance(team, list):
            new_team = [m for m in team if not mentions(m)]
            if len(new_team) != len(team):
                facts["entities"]["team"] = new_team
                report.append(("content/suu-facts.json",
                               [f"ekip {len(team)} → {len(new_team)} kişi"]))
                if apply:
                    facts_path.write_text(
                        json.dumps(facts, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")

    for name, actions in report:
        print(f"  {name}")
        for a in actions:
            print(f"      · {a}")

    mode = "UYGULANDI" if apply else "ÖNİZLEME (yazılmadı)"
    print(f"\n{len(report)} dosya — {mode}")
    if not apply:
        print("Uygulamak için: python3 scripts/remove-team-member.py --apply")
    print("\nNOT: bio paragrafları ve 'üç kişiden oluşur' cümleleri elle düzeltilmeli.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
