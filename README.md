# Suu — Su, Kalori ve Egzersiz Takibi (Web Sitesi)

Suu'nun pazarlama ve SEO web sitesi. [suuapp.com](https://suuapp.com) adresinde canlı.

- **Kanonik ad:** Suu – Su Takibi, Kalori Sayacı ve Egzersiz Takibi
- **Tagline:** Su, Kalori ve Egzersiz — Tek Uygulamada

> **Tek doğruluk kaynağı:** [content/suu-facts.json](content/suu-facts.json). Uygulamaya dair her sayı, özellik ve platform bilgisi önce orada güncellenir; ardından `python3 scripts/check-facts.py` ile site taranır.

## Uygulama Hakkında

Suu artık sadece bir su takip uygulaması değil — **su takibi, kalori sayımı ve egzersiz takibini yapay zekâ ile birleştiren** bir sağlık ve fitness uygulaması. Furkan Mert Fındıklı tarafından tek başına (indie) Flutter ile geliştirilir; Android ve iOS'ta ücretsiz.

- **Google Play:** 4.9★ · 2.847 değerlendirme · **App Store:** puan/sayım teyit bekliyor (bkz. `suu-facts.json` → `_needs_confirmation`)
- **Uygulama dil desteği:** Türkçe, English, العربية, Deutsch, Italiano, Русский, हिन्दी (7 dil, RTL dahil)
- **Site dil desteği:** TR / EN / AR / RU canlı — DE / IT / HI yolda
- **Hedef pazar:** Türkiye, MENA, BDT, DACH, İtalya, Hindistan

## Özellikler — Üç Sütun

### 1. Su Takibi
- Kişiselleştirilmiş günlük su hedefi (yaş, kilo, aktivite, hava sıcaklığı bazlı)
- **91 içecek** + gerçek dehidrasyon faktörü; Starbucks ve kahve zinciri menüleri entegre
- Yenen besinlerin protein/sodyum değerine göre **sindirim suyu** hesabı
- Egzersize göre otomatik ek sıvı ihtiyacı; gün boyunca dinamik güncelleme
- **Suu Endeksi** (0–100 hidrasyon skoru), **Ana Beyin** (adaptif hedef)

### 2. Kalori ve Beslenme
- **Fotoğrafla kalori analizi (Premium):** yemek tanıma, porsiyon tahmini, kalori + makro çıkarımı. Görsel kalıcı saklanmaz.
- **Sesli/yazılı kayıt:** konuşarak öğün/içecek ekleme; AI katı-sıvı ayrımını otomatik yapar. Ses, cihazın işletim sistemi (Apple Speech / Android SpeechRecognizer) ile metne çevrilir — ses kaydı Suu backend'ine gönderilmez.
- Kalori, protein, karbonhidrat, yağ takibi ve otomatik makro hesaplama
- **1–100 beslenme puanı**, günlük denge görünümü
- **Limit:** günde 3 ücretsiz AI analizi; sınırsız analiz + fotoğraf = Premium

### 3. Egzersiz Takibi
- **~50 spor aktivitesi:** koşu, yürüyüş, bisiklet, fitness, yüzme, doğa yürüyüşü, kardiyo…
- Koşu/yürüyüş: mesafe, süre, tempo, ortalama hız, yakılan kalori
- Bisiklet: hız, ortalama hız, mesafe, irtifa, süre, yakılan kalori
- Her egzersiz su hedefini otomatik günceller

### Suu AI
Sohbet ederek su ekleme, içecek kaydetme, öğün oluşturma, egzersiz ekleme, beslenme analizi, hedef güncelleme, hatırlatıcı düzenleme.

### Platform
- **iOS:** Apple Health, **Siri** komutları, **Dynamic Island**, **Live Activities**, widget'lar
- **Android:** Google Health Connect, widget'lar
- **Apple Watch:** yakında — bugün Watch verisi Apple Health üzerinden Suu'ya akıyor ve su hedefini güncelliyor

### Sosyal & Oyunlaştırma
- Arkadaş ligleri (haftalık, 4 kişiye kadar, iOS + Android çapraz platform)
- Sanal evcil hayvan, rozetler, streak'ler

### İstatistik & Raporlama
- 7 / 30 / 365 günlük grafikler
- PDF & CSV rapor dışa aktarımı (Premium)
- Hidrasyon skoru, Su Yolculuğu hikayesi

## Fiyatlandırma

- **Ücretsiz:** temel su-hidrasyon takibi + günde 3 AI analizi + Apple Health/Health Connect senkronu — her zaman ücretsiz
- **Premium:** sınırsız AI analizi, fotoğraflı yemek tanıma, dinamik sindirim suyu bildirimleri, gelişmiş makro/mikro istatistikleri, reklamsız, PDF/CSV rapor
- **Fiyat:** ₺1.200/yıl (%50 lansman indirimi, normal ₺2.400) · aylık ₺149 · aile planı ₺2.399/yıl (3 kişiye kadar) · 3 gün ücretsiz deneme · yerel para birimi otomatik

## Web Sitesi Yapısı

Çok dilli statik site. Ana sayfa dışında diğer dil sayfaları `-en`/`-ar`/`-ru` (ve yolda olan `-de`/`-it`/`-hi`) suffix'ini kullanır. Ana sayfa istisnası: `hosgeldiniz-*`.

**URL kuralı — kritik:** Mevcut URL'ler değiştirilmez. GitHub Pages 301 yönlendirme veremediği için dizin tabanlı (`/en/`, `/de/`) yapıya geçmek yıllık ~40.000 görüntülemenin dayandığı URL'leri kırardı.

**`_default` ile `_xdefault` ayrımı — kritik:** `content/page-registry.json` iki ayrı anahtar taşır ve karıştırılmamalıdır.

| Anahtar | Değer | Neyi sürer |
|---|---|---|
| `_default` | `tr` | **URL yapısı.** Türkçe blog yazıları `blog/<slug>.html`, diğerleri `blog/<lang>/<slug>.html`. Değiştirmek her URL'yi kırar. |
| `_xdefault` | `en` | **`hreflang="x-default"` hedefi.** Dil tercihi belirsiz kullanıcıya/crawler'a sunulacak sürüm. |

Bu ayrım olmadan 222 kümenin 220'si "varsayılan Suu = Türkçe" sinyali veriyordu. Yeni bir şablon yazarken x-default'u **sabit kodlamayın** — `xdefault_href` değişkenini kullanın, aksi hâlde her build `inject-hreflang.py`'nin işini geri alır.

```
/
├── index.html                    # Türkçe ana sayfa
├── hosgeldiniz-en|ar|ru.html     # EN / AR / RU ana sayfa
├── premium{,-en,-ar,-ru}.html    # Fiyatlandırma
├── ozellikler{,-en,-ar,-ru}.html # Özellikler
├── faq{,-en,-ar,-ru}.html        # SSS
├── kimler-icin / who-is-suu-for* # Kullanım senaryosu hub'ı
├── gizlilik-politikasi.html      # Gizlilik (tek URL, sekmeli çok dil)
├── kullanim-sartlari.html        # Kullanım Şartları (tek URL, sekmeli çok dil)
├── su-hesaplayici / water-calculator*  # Su hesaplama aracı
├── blog/                         # Türkçe blog (50 yazı)
│   ├── en/                       # İngilizce blog (50 yazı)
│   ├── ar/                       # Arapça blog (35 yazı)
│   └── ru/                       # Rusça blog (39 yazı)
├── content/suu-facts.json        # TEK DOĞRULUK KAYNAĞI
├── sitemap.xml · robots.txt
├── llms.txt · llms-full.txt      # AI asistan referans dosyaları (dil başına)
└── aso-store-listing.md          # Dahili ASO/mağaza metinleri (.gitignore — yayınlanmaz)
```

## Tek Kaynak Mimarisi

Sitenin üç ayrı gerçek kaynağı vardı (lang-switcher'ın `PAGE_MAP`'i, hreflang script'inin `CLUSTERS`'ı, sitemap script'inin kendi kopyası) ve zamanla birbirinden saptı. Artık hepsi iki dosyadan besleniyor:

| Kaynak | Besledikleri |
|---|---|
| `content/suu-facts.json` | JSON-LD, `llms.txt` ailesi, `ai-plugin.json`, sayfa metinleri, `check-facts.py` |
| `content/page-registry.json` | dil seçici, hreflang, sitemap |

Ek olarak `content/home/<lang>.json` (7 dil) ana sayfaların ve `llms.txt` ailesinin metinlerini taşır.

## Bakım Scriptleri

Repo'nun build sistemi `scripts/` altındaki Python dosyalarıdır (CI'da değil, elle çalıştırılır). Hepsi önce **önizleme** yapar; yazmak için `--apply` gerekir ve hepsi idempotenttir.

```bash
# Doğruluk
python3 scripts/check-facts.py              # suu-facts.json ile çelişen iddiaları tara
python3 scripts/fix-stale-facts.py --apply  # mekanik düzeltmeler (sayı, dil listesi)

# Üretim
python3 scripts/build-homepages.py --apply          # 7 dilde ana sayfa
python3 scripts/build-i18n-map.py --apply           # i18n-map.json + lang-switcher.js
python3 scripts/build-llms.py --apply               # llms.txt ailesi (7 dil × 2)
python3 scripts/build-compare.py --apply            # karşılaştırma/kategori cevap sayfaları
python3 scripts/build-feeds.py --apply              # RSS beslemeleri (dil başına, son 40)

# Enjeksiyon
python3 scripts/inject-hreflang.py --apply          # hreflang kümesi
python3 scripts/inject-comparison-schema.py --apply # karşılaştırma sayfalarına ItemList
python3 scripts/inject-analytics.py --apply         # ölçüm parçacığı
python3 scripts/update-sitemap.py --apply           # sitemap (image blokları korunur)
python3 scripts/sync-blog-index.py --apply          # blog indeksine eksik KARTLARI ekle
python3 scripts/sync-blog-schema.py --apply         # blog indeksinin Blog.blogPost ŞEMASINI eşitle
python3 scripts/generate-og.py                      # blog OG görselleri

# Yayın sonrası
python3 scripts/indexnow-submit.py --changed        # Bing + Yandex'e anında bildirim

# Rapor
python3 scripts/check-screenshots.py --missing      # eksik ekran görüntüleri
```

**Tipik yayın akışı:**
```bash
python3 scripts/build-homepages.py --apply && \
python3 scripts/build-compare.py --apply && \
python3 scripts/build-i18n-map.py --apply && \
python3 scripts/build-llms.py --apply && \
python3 scripts/inject-hreflang.py --apply && \
python3 scripts/sync-blog-index.py --apply && \
python3 scripts/sync-blog-schema.py --apply && \
python3 scripts/update-sitemap.py --apply && \
python3 scripts/build-feeds.py --apply && \
python3 scripts/check-facts.py && \
python3 scripts/check-faq-visibility.py
git push origin main
python3 scripts/indexnow-submit.py --all
```

**Sıra önemli:** `inject-hreflang.py`, sayfa üreten her script'ten SONRA çalışmalı — `build-compare.py` ve `build-compare-hub.py` sayfayı baştan yazdığı için enjekte edilmiş hreflang bloğunu düşürür. `sync-blog-schema.py` de `sync-blog-index.py`'den sonra gelir (biri kart, diğeri `Blog.blogPost` şeması).

## Teknoloji

- HTML5, CSS3, Vanilla JavaScript
- GitHub Pages (otomatik deploy)
- Microsoft Clarity (kullanıcı analitiği)

## Deploy

`main` branch'e push → GitHub Actions otomatik deploy eder → suuapp.com'da canlı.

```bash
git push origin main
```

GitHub Pages'i manuel yeniden etkinleştirmek için:
```bash
export GITHUB_TOKEN=ghp_...
./scripts/enable-pages.sh
```
