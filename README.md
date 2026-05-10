# Suu — Su Takip Uygulaması Web Sitesi

Suu'nun pazarlama ve SEO web sitesi. [suuapp.com](https://suuapp.com) adresinde canlı.

## Uygulama Hakkında

Suu, Türkiye kökenli sosyal su takip uygulaması. Android ve iOS için ücretsiz.

- **Google Play:** 4.9★ · 2.800+ değerlendirme
- **App Store:** 5.0★
- **Dil desteği:** Türkçe, Arapça, Rusça, İngilizce
- **Hedef pazar:** Türkiye ve MENA

## Mevcut Özellikler

### Temel
- Kişiselleştirilmiş günlük su hedefi (boy, kilo, cinsiyet, aktivite bazlı)
- 100+ içecek kategorisi — kahve, çay, ayran, meyve suyu, spor içeceği dahil
- Her içeceğin dehidratasyon faktörü otomatik hesaplanıyor
- Ücretsiz deneme süresi mevcut

### Kahve Zinciri Entegrasyonu (Rakiplerde Yok)
Starbucks, Nevada Coffee, Greenwich Coffee menüleri Suu'ya özel entegre edilmiş. Kullanıcı içtiği ürünü seçince kafein içeriğine göre ekstra su ihtiyacı anında hesaplanıyor.

### Sosyal
- Arkadaşlarla haftalık lig sistemi (4 kişiye kadar)
- iOS + Android çapraz platform lig
- Arkadaş takibi (günlük tüketim, streak, hedef ilerleme)
- Günlük su içme davetleri

### iOS Özel
- Dynamic Island desteği (iPhone 14 Pro+)
- Kilit ekranı widget (iOS 16+)
- Ana ekran widget
- Apple Health (HealthKit) entegrasyonu

### Android
- Google Health Connect entegrasyonu
- Ana ekran widget
- Özelleştirilebilir bildirimler

### İstatistik & Raporlama
- Günlük / haftalık / aylık / yıllık grafikler
- Hidrasyon skoru (0–100)
- PDF rapor export (WaterMinder ve Hydro Coach'ta bu özellik yok)
- Streak takibi

### Monetizasyon
- Aylık plan
- Yıllık plan
- Aile planı
- Ücretsiz deneme mevcut

## Bilinen Eksikler / Gelecek Roadmap

| Eksik | Etki | Durum |
|-------|------|-------|
| Apple Watch / Wear OS desteği | Yüksek — rakiplerin çoğu sunuyor, kullanıcı bağlılığını etkiliyor | Roadmap |
| Özelleştirilebilir içecek ekleme | Orta — kullanıcı kendi içeceğini tanımlayamıyor | Roadmap |
| Sesli asistan (Siri / Google Assistant) | Orta | Roadmap |
| Tek seferlik satın alma seçeneği | Orta — Türkiye'de aboneliğe dirençli kullanıcı segmenti var | Roadmap |
| Kamera tabanlı içecek tanıma | Yüksek — "gerçek hidrasyon" felsefesiyle uyumlu güçlü differentiator | Roadmap |

## Teknik Borçlar (Uygulama Tarafı)

- Duplicate auth implementasyonu
- Aşırı büyük dosyalar
- Firebase App Check eksikliği
- Firestore yazma verimsizlikleri — launch anında tüm kullanıcıları etkiliyor

## Web Sitesi Yapısı

```
/
├── hosgeldiniz.html        # Türkçe ana sayfa
├── hosgeldiniz-en.html     # İngilizce ana sayfa
├── hosgeldiniz-ar.html     # Arapça ana sayfa
├── blog/                   # Türkçe blog (13 yazı)
│   ├── en/                 # İngilizce blog (12 yazı)
│   └── ar/                 # Arapça blog (12 yazı)
├── ozellikler.html         # Özellikler sayfası
├── faq.html                # SSS
├── su-hesaplayici.html     # Su hesaplama aracı
├── starbucks-dehidrasyon.html  # Starbucks dehidrasyon hesabı (TR)
├── starbucks-dehydration.html  # Starbucks dehydration calculator (EN)
├── sitemap.xml
├── robots.txt
├── llms.txt                # AI asistan referans dosyası
└── llms-full.txt           # Detaylı AI referans dosyası
```

## Teknoloji

- HTML5, CSS3, Vanilla JavaScript
- GitHub Pages (otomatik deploy)
- Microsoft Clarity (kullanıcı analitik)

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
