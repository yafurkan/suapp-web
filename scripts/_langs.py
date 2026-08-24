#!/usr/bin/env python3
"""
Suu — dil tablosu erişimi (paylaşılan modül)

Kaynak: content/languages.json

Bu modülden önce dil bağımlı her sabit 12'den fazla script'te ayrı ayrı
yazılıydı: build-compare'in LOCALES + UI'ı, build-compare-hub'ın LANG_NAMES +
HOME_HREF'i, sync-blog-index'in LANGS + READ_MORE + MONTHS'u, build-feeds'in
FEEDS'i… README'nin "Tek Kaynak Mimarisi" bölümü bu sapmanın iki kez
yaşandığını anlatıyor; DE/IT/UK eklerken üçüncüsü olacaktı.

Fonksiyonlar bilerek ESKİ SÖZLÜK BİÇİMLERİNİ döndürüyor. Böylece her
tüketici script'te değişen tek şey sabitin tanımı oluyor, kullanıldığı
yerlerin hiçbiri değişmiyor — refactor'ün doğruluğu builder'ları önizleme
modunda çalıştırıp "0 değişiklik" görmekle kanıtlanabiliyor.

Kullanım:
    from _langs import locales, ui_strings, blog_langs, feeds
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "content" / "languages.json"


@lru_cache(maxsize=1)
def table() -> dict[str, dict]:
    """dil kodu → tüm alanlar."""
    return json.loads(TABLE_PATH.read_text(encoding="utf-8"))["languages"]


def order() -> list[str]:
    """Kayıt defterindeki dil sırası — çıktıların sırası buna bağlı."""
    return list(table())


def published() -> list[str]:
    """Arkasında gerçek içerik olan diller.

    Yayında OLMAYAN bir dil hreflang kümesine girmez ve blog/besleme
    üretimine katılmaz: tek karşılama sayfasından ibaret bir dile hreflang
    vermek boş bir kümeye işaret etmek demekti (2026-08-20'de de/it/hi
    tam olarak bu yüzden park edildi).
    """
    return [k for k, v in table().items() if v.get("published")]


def field(name: str, langs: list[str] | None = None) -> dict[str, object]:
    t = table()
    return {k: t[k][name] for k in (langs or t) if t[k].get(name) is not None}


# ── Eski sözlük biçimleri ────────────────────────────────────────────────

def locales(langs: list[str] | None = None) -> dict[str, tuple[str, str]]:
    """dil → (og:locale, yazım yönü)"""
    t = table()
    return {k: (t[k]["locale"], t[k]["dir"]) for k in (langs or t)}


def lang_names() -> dict[str, str]:
    return field("native_name")  # type: ignore[return-value]


def home_hrefs(existing_only: bool = True) -> dict[str, str]:
    """dil → karşılama sayfası yolu.

    Varsayılan olarak yalnızca dosyası DİSKTE OLAN diller. Altbilgideki dil
    menüsü bu haritadan üretiliyor; tabloya bir dil eklemek, henüz sayfası
    yazılmamışken menüye 404 koymamalı.
    """
    out = field("home_href")
    if not existing_only:
        return out  # type: ignore[return-value]
    return {k: v for k, v in out.items()
            if v == "/" or (ROOT / str(v).lstrip("/")).exists()}  # type: ignore[return-value]


def home_files() -> dict[str, tuple[str, str, str]]:
    """dil → (çıktı dosyası, og:locale, yazım yönü) — build-homepages biçimi.

    home_hrefs()'in aksine DİSK KONTROLÜ YAPMAZ: burada amaç sayfayı üretmek,
    var olanı listelemek değil. build-homepages zaten content/home/<lang>.json
    yoksa dili atlıyor.
    """
    t = table()
    return {k: (("index.html" if v["home_href"] == "/" else v["home_href"].lstrip("/")),
                v["locale"], v["dir"]) for k, v in t.items()}


def ui_strings() -> dict[str, dict[str, str]]:
    return {k: dict(v["ui"]) for k, v in table().items()}


def months() -> dict[str, list[str]]:
    return field("months")  # type: ignore[return-value]


def date_fmt() -> dict[str, str]:
    return field("date_fmt")  # type: ignore[return-value]


def read_more() -> dict[str, str]:
    return field("read_more")  # type: ignore[return-value]


def blog_topics() -> dict[str, dict[str, str]]:
    """dil → blog kartı konu rozeti etiketleri."""
    return {k: dict(v["blog_topics"]) for k, v in table().items() if v.get("blog_topics")}


def blog_langs(with_bcp47: bool = False) -> dict[str, tuple]:
    """dil → (indeks dosyası, yazı klasörü, bağlantı öneki[, inLanguage])

    Yalnızca HEM indeks dosyası HEM yazı klasörü diskte var olan diller.
    Kasıtlı: yeni bir dilin blog'unu açmak için blog-<lang>.html kabuğunu
    ve blog/<lang>/ klasörünü oluşturmak yeterli — hiçbir script
    düzenlenmiyor.
    """
    out = {}
    for k, v in table().items():
        index, folder = v.get("blog_index"), v.get("blog_dir")
        if not index or not folder:
            continue
        if not (ROOT / index).exists() or not (ROOT / folder).is_dir():
            continue
        row = (index, folder, folder.rstrip("/") + "/")
        out[k] = row + (v["bcp47"],) if with_bcp47 else row
    return out


def blog_targets() -> list[str]:
    """inject-*.py ailesinin varsayılan hedef listesi.

    Biçim eski hâliyle aynı: varsayılan dil "" (blog/ kökü), diğerleri kendi
    kodlarıyla (blog/<lang>/). Eskiden bu liste beş script'te ["", "en", "ar",
    "ru"] olarak sabitti; yeni bir dil eklenince o dilin yazıları şema
    enjeksiyonu almadan SESSİZCE atlanıyordu.
    """
    return [""] + [k for k in blog_langs() if k != "tr"]


def feeds() -> dict[str, dict[str, str]]:
    """build-feeds.py'nin beklediği biçim; blog_langs ile aynı diller."""
    t = table()
    return {
        k: {"dir": t[k]["blog_dir"], "out": t[k]["feed"], "index": t[k]["blog_index"],
            "title": t[k]["feed_title"], "lang": t[k]["bcp47"], "desc": t[k]["feed_desc"]}
        for k in blog_langs()
    }
