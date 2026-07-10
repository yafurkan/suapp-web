# Suu — Kalori ve Su Takibi (Web Sitesi)

Suu'nun pazarlama ve SEO web sitesi. [suuapp.com](https://suuapp.com) adresinde canlı.

- **Kanonik ad:** Suu - Kalori ve Su Takibi
- **Tagline:** Su, Kalori ve Sağlık Rehberi

## Uygulama Hakkında

Suu artık sadece bir su takip uygulaması değil — **yapay zeka tabanlı beslenme, kalori ve hidrasyon asistanı**. Furkan Mert Fındıklı tarafından tek başına (indie) Flutter ile geliştirilir; Android ve iOS'ta ücretsiz.

- **Google Play:** 4.9★ · 2.800+ değerlendirme · **App Store:** 5.0★
- **Dil desteği:** Türkçe, İngilizce, Rusça, Arapça (4 dil, tam yerelleştirme + RTL)
- **Hedef pazar:** Türkiye, MENA, BDT

## Özellikler

### Yapay Zeka Beslenme (yeni yön)
- **Sesli kayıt:** konuşarak öğün/içecek ekleme; AI katı-sıvı ayrımını otomatik yapar. Ses, cihazın işletim sistemi (Apple Speech / Android SpeechRecognizer) ile metne çevrilir — ses kaydı Suu backend'ine gönderilmez.
- **Fotoğraflı kalori analizi (Premium):** Google Gemini API ile yemek tanıma, porsiyon tahmini, kalori + makro çıkarımı. Görsel kalıcı saklanmaz.
- **Kalori & makro takibi:** kalori, protein, karbonhidrat, yağ, sodyum → Apple HealthKit / Google Health Connect (Dietary oku + yaz).
- **1–100 beslenme puanı**, günlük denge görünümü.
- **Limit:** günde 3 ücretsiz AI analizi (sesli/yazılı); sınırsız analiz + fotoğraf = Premium.

### Hidrasyon
- Kişiselleştirilmiş günlük su hedefi (boy, kilo, cinsiyet, aktivite, hava durumu bazlı)
- **91 içecek** + gerçek dehidrasyon faktörü; Starbucks ve kahve zinciri menüleri entegre
- **Suu Endeksi** (0–100 hidrasyon skoru), **Ana Beyin** (adaptif hedef)
- Akıllı bildirimler: yemek sonrası sindirim suyu, gece dehidrasyonuna karşı sabah "ilk yudum"

### Platform
- **Apple Watch** (bağımsız watchOS uygulaması), **Siri** komutları, **Dynamic Island**, kilit/ana ekran widget'ları
- Apple HealthKit + Google Health Connect (çift yönlü senkron)

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

Çok dilli statik site. Ana sayfa dışında EN/AR/RU sayfaları `-en`/`-ar`/`-ru` suffix'i kullanır (ana sayfa istisnası: `hosgeldiniz-*`).

```
/
├── index.html                    # Türkçe ana sayfa
├── hosgeldiniz-en|ar|ru.html     # EN / AR / RU ana sayfa
├── premium{,-en,-ar,-ru}.html    # Fiyatlandırma (4 dil)
├── ozellikler{,-en,-ar,-ru}.html # Özellikler (4 dil)
├── faq{,-en,-ar,-ru}.html        # SSS (4 dil)
├── kimler-icin / who-is-suu-for* # Kullanım senaryosu hub'ı (4 dil)
├── gizlilik-politikasi.html      # Gizlilik (tek URL, 4 dil sekmeli)
├── kullanim-sartlari.html        # Kullanım Şartları (tek URL, 4 dil sekmeli)
├── su-hesaplayici / water-calculator*  # Su hesaplama aracı (4 dil)
├── blog/                         # Türkçe blog (42 yazı)
│   ├── en/                       # İngilizce blog (39 yazı)
│   ├── ar/                       # Arapça blog (35 yazı)
│   └── ru/                       # Rusça blog (39 yazı)
├── sitemap.xml · robots.txt
├── llms.txt · llms-full.txt      # AI asistan referans dosyaları (4 dil)
└── aso-store-listing.md          # Dahili ASO/mağaza metinleri (.gitignore — yayınlanmaz)
```

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
