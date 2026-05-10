<div align="center">

# 💧 SuuApp - Akıllı Su Takip Uygulaması

<img src="assets/images/logos/suu_logo.png" width="150" alt="SuuApp Logo" />

**Sağlıklı yaşam için günlük su tüketimi takip uygulaması**

[![Flutter](https://img.shields.io/badge/Flutter-3.27%2B-02569B?logo=flutter)](https://flutter.dev)
[![Dart](https://img.shields.io/badge/Dart-3.8%2B-0175C2?logo=dart)](https://dart.dev)
[![Firebase](https://img.shields.io/badge/Firebase-Enabled-FFCA28?logo=firebase)](https://firebase.google.com)
[![iOS](https://img.shields.io/badge/iOS-16.0%2B-000000?logo=apple)](https://www.apple.com/ios)
[![Android](https://img.shields.io/badge/Android-API%2021%2B-3DDC84?logo=android)](https://www.android.com)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

[Özellikler](#-özellikler) • [Kurulum](#-kurulum) • [Mimari](#-mimari) • [Geliştirme](#-geliştirme)

</div>

---

## 📖 İçindekiler

- [Hakkında](#-hakkında)
- [Özellikler](#-özellikler)
- [Teknoloji Stack](#-teknoloji-stack)
- [Kurulum](#-kurulum)
- [Mimari](#-mimari)
- [Proje Yapısı](#-proje-yapısı)
- [Geliştirme](#-geliştirme)
- [Test](#-test)
- [Deployment](#-deployment)
- [Lisans](#-lisans)

---

## 🌟 Hakkında

**SuuApp**, günlük su tüketimi takibini kolaylaştıran, yapay zeka destekli akıllı bir mobil uygulamadır. Kullanıcıların sağlıklı hidrasyon alışkanlıkları geliştirmesine yardımcı olur.

### Ana Hedefler

- ✅ Günlük su tüketimini kolay ve eğlenceli hale getirmek
- ✅ Kişiselleştirilmiş su içme hedefleri belirlemek
- ✅ Akıllı bildirimlerle düzenli hatırlatmalar sağlamak
- ✅ Apple HealthKit entegrasyonu
- ✅ Apple Watch ve Widget desteği ile her yerden erişim
- ✅ Gamification ile motivasyonu artırmak
- ✅ Onboarding akışıyla kişiselleştirilmiş başlangıç deneyimi
- ✅ Premium abonelik sistemi (Paywall)

---

## 🚀 Özellikler

### 💧 Su Takip & İçecek Ekleme Sistemi

- **Hızlı Ekleme Butonları**: Favori içeceklerinizi tek dokunuşla ekleyin
- **Detaylı İçecek Seçici**: 20+ içecek kategorisi (su, kahve, çay, meyve suyu vb.)
- **Marka Logoları**: Starbucks, Greenwich, Nevada gibi popüler markalar için özel ikonlar
- **Günlük Hedef Takibi**: Kişiselleştirilmiş günlük su hedeflerinizi takip edin
- **Geçmiş İstatistikler**: Haftalık, aylık ve yıllık tüketim grafikleri
- **Ses Efektleri**: İçecek ekleme ve hedef tamamlama için ses geri bildirimi
- **Kaynak Takibi**: Her kayıt `source` alanıyla etiketlenir (`manual` / `widget` / `siri` / `voice`)

#### Bileşik Hidrasyon Modeli

Her içecek eklendiğinde iki ayrı değer hesaplanır ve `WaterIntakeModel`'e kaydedilir:

**1. Gerçek hidrasyon (`actualHydration`)**
```
actualHydration = miktar (ml) × hydrationFactor
```
| İçecek | hydrationFactor |
|--------|----------------|
| Su | 1.0 |
| Bitki çayı | 0.9 |
| Kahve | 0.8 |
| Enerji içeceği | 0.5 |
| Alkollü içecek | −0.5 (dehidrasyon) |

**2. Ekstra su ihtiyacı (`extraWaterNeed`)**

İçecekteki şeker, kafein ve alkol vücudun ek su tüketmesine neden olur. Bu miktar otomatik hesaplanır ve günlük hedefe eklenir:

```
Şeker etkisi:  her 10g şeker       → +100ml ekstra su
Kafein etkisi: içecek hacminin %20  → ekstra su
Alkol etkisi:  her 10ml saf alkol   → +250ml ekstra su
```

**Örnek — 350ml Enerji İçeceği (12g şeker/100ml, 32mg kafein/100ml):**
```
actualHydration = 350 × 0.5  = 175ml  (hidrasyon katkısı)
şeker etkisi    = (350/100 × 12) / 10 × 100  = 420ml
kafein etkisi   = 350 × 0.2             = 70ml
extraWaterNeed  = 490ml  → günlük hedefe eklenir
```

Kullanıcıya içecek seçme diyaloğunda:
- `extraWaterNeed > 0` ise uyarı kartı gösterilir ("+490ml ekstra su içmeniz önerilir")
- `extraWaterNeed == 0` ise yeşil onay kartı ("Doğrudan su ihtiyacınızı karşılar")

#### Hızlı İçme Dedektörü (`RapidDrinkingDetector`)

- Son 30 dakika içinde **3+** ekleme → uyarı popup tetiklenir
- **2 saat** global cooldown; günde **en fazla 3** kez gösterilir

### 🧮 Hidrasyon Hedef Hesaplama (`HydrationGoalService`)

Onboarding'den toplanan verilerle kişiselleştirilmiş günlük hedef hesaplanır. Adım adım çarpımlı formül:

```
1. temel          = ağırlık(kg) × 35 ml/kg
2. aktivite       = temel × aktivity_factor
3. sebze düz.     = adım2 × (1 + veggie_adjustment)
4. şekerli düz.   = adım3 × (1 + sugary_adjustment)
5. gebelik/emzirme= adım4 + pregnancy_addition_ml   (yalnızca kadın)
6. clamp          = [1500 ml … 6000 ml]
7. yuvarlama      = en yakın 50 ml'ye
```

**Katsayı tabloları (`HydrationFactors`):**

| Aktivite | Çarpan |
|----------|--------|
| Düşük (masa başı) | ×1.00 |
| Orta | ×1.12 (+%12) |
| Yüksek | ×1.25 (+%25) |

| Sebze/Meyve Tüketimi | Düzeltme |
|----------------------|---------|
| Nadir | 0 |
| Günlük | −%2 |
| Sık | −%5 |

| Şekerli İçecek Tüketimi | Düzeltme |
|-------------------------|---------|
| Neredeyse hiç | 0 |
| Nadir | +%4 |
| Günlük | +%8 |
| Sık | +%12 |

**Gebelik / Emzirme Eki** *(kaynak: IOM 2004 DRI raporu, yalnızca kadın cinsiyetinde)*

| Durum | Ek miktar |
|-------|-----------|
| Yok | +0 ml |
| Gebe | +300 ml |
| Emziriyor | +700 ml |

**Hedef güncelleme tetikleyicileri** — Profil değişikliklerinde hedef otomatik yeniden hesaplanır:
- Kilo değişimi
- Aktivite seviyesi değişimi
- Sebze/şekerli içecek tüketimi değişimi
- Gebelik durumu değişimi

**Kullanıcı hedefleri için ek öneri** (`getRecommendedDailyIncrease`):

| Hedef | Ek öneri |
|-------|----------|
| Kilo verme | +250 ml |
| Cilt sağlığı | +200 ml |
| Sindirim | +150 ml |
| Genel hidrasyon | +300 ml |
| Toplam (max) | +500 ml |

> ⚠️ Tüm hesaplamalar genel kılavuzlara dayalı tahmindir; tıbbi tavsiye değildir. Sağlık sorunları için doktora danışılmalıdır.

### 🎯 Onboarding & Kişiselleştirme

- **Adım Adım Onboarding**: Cinsiyet, yaş, boy, kilo, aktivite seviyesi, beslenme alışkanlıkları girişi
- **Hedef Hesaplama**: Kullanıcı verilerine göre otomatik günlük hedef belirleme
- **İzin Ekranları**: Bildirim ve konum erişimi için açıklayıcı izin akışı
- **Sağlık İzni Ekranı**: HealthKit erişimi için açıklayıcı izin akışı
- **Mikro Rıza Ekranı**: GDPR uyumlu veri kullanım onayı
- **Analiz Ekranı**: Kullanıcı verilerini işleme animasyonu
- **Paywall Entegrasyonu**: Onboarding sonunda premium teklifi

### 🔔 Akıllı Bildirim Sistemi

- **Aralık Bildirimleri**: Belirlediğiniz saatlerde düzenli hatırlatmalar
- **Günlük Bildirimler**: Sabah, öğle ve akşam özel mesajlar
- **İlerleme Kontrolleri**: Hedefinize ne kadar yakın olduğunuzu bildiren akıllı mesajlar
- **Çakışma Önleme**: 30 dakika içinde birden fazla bildirim gelmez
- **Özelleştirilebilir**: Bildirim saatleri, sesler ve günleri özelleştirin
- **Çok Dil Desteği**: Türkçe, İngilizce ve Arapça bildirimler

#### Bildirim Motoru — 3 Katmanlı Mimari

```
NotificationStateEvaluator
  → Güncel tüketim + saat → ProgressStatus
     (onTrack | behind | criticallyBehind | completed | noGoal)
       │
       ▼
NotificationContentFactory
  → ProgressStatus + Locale (TR/EN/AR) → başlık + gövde metni
  → Sabah / öğle / akşam / gece tonuna göre farklı mesaj seti
  → Hedef tamamlandıysa bildirim içeriği üretilmez
       │
       ▼
NotificationConflictResolver
  → Tüm zamanlanmış bildirimleri tarih sırasına dizer
  → 30 dakikalık çakışma penceresi: düşük öncelikli bildirim SUPPRESS edilir
  → Öncelik sırası: Günlük/İlerleme > Aralık
```

**İlerleme durumu zamanlamaya göre:**

| Saat | Beklenen tüketim | Durum |
|------|-----------------|-------|
| 00-08 | %10 | onTrack |
| 08-12 | %30 | behind / onTrack |
| 12-18 | %60 | behind / onTrack |
| 18-22 | %85 | behind / onTrack |
| 22-00 | %100 | criticallyBehind (20:00+ ve <%50 ise) |

- **`NotificationOptimizationService`**: Firebase'den kullanıcı etkileşim verisi (son 1000 aktivite) çekerek bildirim zamanlarını ML benzeri algoritmayla kişiselleştirir
- **Otomatik durdurma**: Günlük hedef tamamlanınca o günkü tüm bildirimler iptal edilir

### 🍎 Sağlık Entegrasyon Sistemi

#### Mimari

```
EnhancedHealthSyncService   ← Orkestratör
  ├── HealthKitService       ← iOS only
  ├── GoogleFitService       ← Android only
  └── WearableService        ← Apple Watch, Wear OS, Fitbit, Garmin…
```

Her platformda ilgili servis devreye girer; diğeri hiç başlatılmaz (`HealthFeatureFlags` ile kontrol).

---

#### iOS — Apple HealthKit (`HealthKitService`)

**İzin akışı — Apple gizlilik tasarımı**

iOS'ta `requestAuthorization()` her zaman `true` döndürür (Apple kullanıcının kararını uygulamaya bildirmez). Gerçek durum `checkActualPermission()` ile ayrıca sorgulanır:

```
hasPermissions() → true   → izin verilmiş
               → false  → reddedilmiş
               → null   → iOS bilgi vermedi (gizlilik)
                           → SharedPreferences'taki istek bayrağına bak
```

**Okunan veri tipleri:**

| HealthKit Tipi | İzin | Kullanım |
|----------------|------|---------|
| `WATER` | READ + WRITE | Su tüketimi kaydı / okuma |
| `STEPS` | READ | Adım → günlük hedef ayarı |
| `ACTIVE_ENERGY_BURNED` | READ | Aktif kalori → hidrasyon önerisi |

**Yazma:**
- ml → L dönüşümü yapılır (`HealthDataUnit.LITER`)
- `writeHealthData(type: WATER, startTime: now, endTime: now)`
- Hesap silinirken `deleteAllWrittenWaterIntakes()` ile 2020-01-01'den bugüne tüm bu uygulamanın yazdığı kayıtlar temizlenir

**Adım sayısı — çok kaynaklı akıllı birleştirme:**

Apple Health, adım verisini birden fazla kaynaktan (iPhone, Apple Watch, üçüncü taraf) gönderir. Çift sayımı önlemek için:

```
"Apple Health" kaynağı varsa → tüm time slice'larının toplamını al (merge edilmiş)
Yoksa → her kaynak kendi toplamı; en yüksek kaynağı seç
```

Aynı mantık `ACTIVE_ENERGY_BURNED` için de uygulanır.

**Dış kaynak okuma:**
- `getExternalWaterIntakesToday()` — bugün başka uygulamaların HealthKit'e yazdığı su kayıtlarını bundle ID'ye göre filtreler

---

#### Android — Google Fit (`GoogleFitService`)

**OAuth Scope'ları:**

| Scope | Veri |
|-------|------|
| `fitness.activity.read/write` | Adım, kalori |
| `fitness.body.read/write` | Vücut metrikleri |
| `fitness.nutrition.read/write` | Su tüketimi |
| `fitness.heart_rate.read` | Kalp atışı |
| `fitness.sleep.read` | Uyku verisi |

**İzin akışı:**
1. `signInSilently()` — mevcut Google oturumu kontrol
2. Oturum yoksa bildirim, yoksa `health` paketi ile izin doğrulama
3. Bağlı değilse servis devre dışı kalır

---

#### Gelişmiş Senkronizasyon (`EnhancedHealthSyncService`)

| Özellik | Detay |
|---------|-------|
| **Otomatik periyodik sync** | Her 15 dakikada bir `syncAllHealthData()` |
| **Retry mekanizması** | Max 3 deneme, 5 sn bekleme aralığı |
| **Stream tabanlı sonuç** | `syncResultStream` ile anlık sync durumu dinleme |
| **Veri doğrulama cache** | Son geçerli veri önbellekte tutulur |
| **Ardışık hata sayacı** | `consecutiveFailures` ile bozuk sync tespit |

---

#### Giyilebilir Cihazlar (`WearableService`)

Desteklenen cihaz tipleri: `AppleWatch`, `WearOS`, `Fitbit`, `MiBand`, `Garmin`, `Samsung`

Her cihazdan okunabilen veriler: `steps`, `heartRate`, `calories`, `distance`, `waterIntake`

---

#### Feature Flag Sistemi (`HealthFeatureFlags`)

Tüm sağlık özellikleri compile-time flag ile açılıp kapatılabilir:

| Flag | Durum |
|------|-------|
| `enableHealthIntegration` (master) | ✅ Açık |
| `enableHealthKit` (iOS) | ✅ Açık |
| `enableGoogleFit` (Android) | ✅ Açık |
| `enableWearableDevices` | ✅ Açık |
| `enableAutoSync` (15 dk periyot) | ✅ Açık |
| `enableWriteWaterIntake` | ✅ Açık |
| `enableReadWaterIntake` | ✅ Açık |
| `enableReadSteps` | ✅ Açık |
| `enableReadActiveEnergy` | ✅ Açık |
| `enableActivityBasedRecommendation` | ✅ Açık |
| `enableHealthDataEncryption` | ✅ Açık |
| `enableReadHeartRate` | ❌ Kapalı |
| `enableReadSleepData` | ❌ Kapalı |
| `enableReadWorkoutData` | ❌ Kapalı |

### ⌚ Apple Watch Uygulaması

- **Standalone Watch App**: SwiftUI ile geliştirilmiş native watchOS uygulaması
- **Bilekten Su Ekleme**: Telefonunuza bakmadan su tüketiminizi kaydedin
- **Gerçek Zamanlı Senkronizasyon**: App Group ile anlık veri paylaşımı
- **Progress Ring**: Apple Watch'un aktivite halkalarına benzer görsel gösterge
- **Quick Actions**: Favori miktarınızı tek dokunuşla ekleyin

### 🔊 Siri & Sesli Komutlar

- **Siri Shortcuts**: Sesli komutlarla su ekleyin
- **Custom Intents**: Kişiselleştirilebilir sesli komutlar
- **Intent Extensions**: Native iOS entegrasyonu
- **Çok Dil Desteği**: Türkçe, İngilizce ve Arapça sesli komutlar

### 🎙️ Uygulama İçi Sesli Komut Sistemi

- **Özel Tetikleyici Kelimeler**: Her içeceğe ayrı sesli komut atayın (ör. "kahve" → 200ml kahve ekle)
- **Gerçek Zamanlı Dinleme**: `speech_to_text` ile mikrofon tabanlı komut algılama
- **Kişiselleştirilmiş Loglama**: Kullanıcı sesli komut alışkanlıkları takibi ve analizi
- **Siri'den Bağımsız**: iOS ve Android'de çalışan native uygulama içi çözüm

### 📱 iOS Widget & Home Screen

- **WidgetKit Integration**: iOS 14+ Home Screen widget'ları
- **3 Widget Boyutu**: Small, Medium ve Large widget seçenekleri
- **Canlı Güncellemeler**: Gerçek zamanlı su tüketimi gösterimi
- **Quick Actions**: Widget'tan direkt su ekleme
- **Live Activities**: iOS 16.2+ kilit ekranı ve Dynamic Island canlı takibi

### 🎮 Gamification & Rozetler

- **Rozet Sistemi**: Kazanılabilir rozetler
- **Günlük Streaks**: Ardışık günlük hedef başarıları
- **Başarı Sistemi**: Milestone'lara ulaşınca özel ödüller
- **Ses Efektleri**: Hedef tamamlandığında özel ses (`winner.wav`)
- **Meydan Okuma (Challenge)**: 7 ve 30 günlük hidrasyon meydan okumaları, günlük mini görevler
- **Liga Sistemi**: Kullanıcılar arasında lig bazlı sıralama, lig oluşturma ve davet

### 👥 Sosyal Özellikler

- **Arkadaş Sistemi**: Benzersiz arkadaşlık kodu ile bağlantı kurma, arkadaşlık istekleri
- **Dürtme (Poke)**: Arkadaşını su içmeye teşvik eden anlık bildirim
- **Arkadaş Profili**: Arkadaşın günlük hedef yüzdesi, streak ve haftalık ortalamasını görme (ücretsiz) + ek detaylar (premium)
- **Sosyal Medya Paylaşımı**: Rozet ve başarıların paylaşım kartı olarak oluşturulup paylaşılması (`SocialShareService`)

### 🎁 Viral Büyüme & Referral Sistemi

- **Benzersiz Referral Kodu**: Her kullanıcıya özel davet kodu
- **QR Kod Daveti**: `qr_flutter` ile anlık QR kod oluşturma
- **Deep Link Desteği**: `app_links` ile uygulama içi yönlendirme
- **Ödül Sistemi**: Başarılı davet → davet eden 7 gün, davet edilen 3 gün ücretsiz premium; 5 başarılı davet → 30 gün bonus
- **Viral İstatistikler**: Firestore'da referral ve davet performans takibi

### 🌤️ Hava Durumu Entegrasyonu

- **OpenWeatherMap API**: Gerçek zamanlı hava durumu verisi
- **GPS veya Şehir Seçimi**: Konuma göre otomatik veya manuel şehir seçimi
- **Hidrasyon Önerileri**: Sıcak ve nemli havalarda günlük su ihtiyacı ayarlaması

### 👤 Misafir Modu

- **Kayıtsız Kullanım**: Firebase hesabı olmadan tüm premium özelliklere erişim
- **Demo Verisi**: Uygulama deneyimi için rastgele dolu veri seti
- **Kalıcısız Oturum**: Su eklemeleri yalnızca session süresince saklanır, Firebase'e yazılmaz
- **App Store İncelemesi**: Apple/Google review süreçleri için ideal izole ortam

### 📊 İstatistik & Raporlama Sistemi

#### Veri Modelleri

| Model | İçeriği |
|-------|---------|
| `DailyStat` | `totalMl`, `goalMl`, `completionRate`, `drinkCount`, `avgDrinkMl`, `firstDrinkAt`, `lastDrinkAt`, tüm `DrinkEvent` listesi |
| `WeeklyStat` | `avgDailyMl`, `avgCompletionRate`, `daysGoalMet`, `longestStreak` |
| `MonthlyStat` | `totalMl`, `avgDailyMl`, `completion`, `streak`, `prevComparePercent`, kazanılan/yakın rozetler |
| `TimeBucket` | Zaman dilimine göre tüketim: 06-10 / 10-14 / 14-18 / 18-22 / 22-02 |
| `HydrationReport` | Yukarıdakilerin tamamı + `ScoreCard` + `persona` + `tips` + `drinkTypeBreakdown` |

#### Hidrasyon Skoru (`ScoreCard`) — 0-100 arası

Dört alt skor ağırlıklı ortalama ile birleşir:

```
total = completion × 0.50
      + regularity × 0.20
      + timing     × 0.20
      + overIntake × 0.10
```

| Alt Skor | Hesaplama |
|----------|-----------|
| **completion** | Günlük tamamlanma oranlarının ortalaması |
| **regularity** | `100 − (günlük ml std sapması × 0.6)` — tutarlı içmeyi ödüllendirir |
| **timing** | Kaç farklı saatte içildiği: `50 + (benzersiz_saat / 10 × 50)` — gün boyuna yayılmayı ödüllendirir |
| **overIntake** | `100 − (fazla_ml / (hedef × gün_sayısı) × 50)` — aşırı içmeyi cezalandırır |

**Skor etiketleri:**

| Skor | Etiket |
|------|--------|
| 85-100 | Mükemmel |
| 70-84 | İyi |
| 40-69 | Gelişiyor |
| 0-39 | Zayıf |

#### Persona Etiketi

`HydrationReportService` içecek geçmişine bakarak kullanıcıya bir davranış tipi atar:

| Persona | Koşul |
|---------|-------|
| `sabah açılışçı` | Sabah (06-10) içimi akşama (18+) göre 1.5× fazla |
| `akşam odaklı` | Akşam içimi sabaha göre 1.5× fazla |
| `sık yudumlayan` | Toplam 6+ içecek kaydı |
| `dengeli içici` | Diğer tüm durumlar |

#### Otomatik Koçluk İpuçları (`_buildTips`)

Skor ve zaman dilimi verilerine göre en fazla 3 kişiselleştirilmiş ipucu üretilir:
- `completion < 85` → sabah içimini artır önerisi
- 14-18 dilimindeki hacim 10-14 diliminin %60'ından azsa → öğleden sonra dengelensin
- Haftada 2+ gün `completionRate < 70` → widget hatırlatıcısı güçlendir

#### Rapor Altyapısı (`lib/features/reporting/`)

```
reporting/
├── data/hydration_analytics_repository.dart  # Firestore: DrinkEvents + DailyStats
├── domain/hydration_report_service.dart       # Tüm hesaplamalar
├── models/report_models.dart                  # DailyStat, WeeklyStat, ScoreCard…
└── presentation/
    ├── report_cubit.dart                      # State yönetimi
    ├── pdf_report_builder.dart                # PDF oluşturma
    └── csv_exporter.dart                      # CSV dışa aktarma
```

- **PDF Raporu**: Skor barı, persona etiketi, özet istatistikler, içecek dağılımı (Premium)
- **CSV Dışa Aktarma**: Ham günlük veri (Premium)
- **Grafik Görünümleri**: Bar veya çizgi grafik, 7 / 30 / 365 gün periyotları

### 🤖 Chatbot Asistanı

Uygulama içi yardım ve koçluk sistemi. Hazır sorular + dinamik bağlam enjeksiyonu ile çalışır; gerçek AI/LLM bağlantısı yoktur.

#### 6 Soru Kategorisi

| Kategori | Sorular | Özellik |
|----------|---------|---------|
| 🧠 Akıllı Görüşler | Bugün ne kadar içtim?, Ne kadar kaldı?, Beni motive et | Dinamik — anlık tüketim verisi |
| ⭐ Premium Özellikler | Siri kurulumu, Widget kurulumu, Apple Watch, Premium | iOS/Android'e göre değişir |
| 💧 Su & Sağlık | Sabah içimi, egzersiz hidrasyon, hava durumu etkisi, faydalar | Statik bilgi |
| ☕ İçecekler | Kahve, çay, meyve suyu, spor içeceği | Statik bilgi |
| 📊 Uygulama Özellikleri | İstatistikler, rozetler, bildirimler, arkadaş daveti | Sayfa yönlendirme |
| 🏆 Kişisel Koç | Haftalık durum, zayıf nokta, streak ipucu, en iyi gün, zamanlama, skor anlamı | **Yalnızca Premium** |

#### Dinamik Bağlam Enjeksiyonu

`smart_insights` kategorisindeki sorular kullanıcının anlık verisiyle cevap üretir:

```dart
ctx = {
  'todayIntake':     double,   // ml
  'dailyGoal':       double,
  'remaining':       double,
  'progress':        double,   // 0.0–1.0+
  'goalReached':     bool,
  'challengeActive': bool,
  'challengeDay':    int,
  'hour':            int,
}
```

Motivasyon mesajı `progress` ve `hour` değerine göre farklı bir yanıt üretir (sıfır sabah / düşük / orta / yüksek / tamamlandı / meydan okuma aktif).

#### Aksiyon Sistemi

Cevaplara `ChatAction` eklenerek uygulama içi yönlendirme veya tutorial başlatma yapılır:

| Aksiyon tipi | Kullanım |
|-------------|---------|
| `navigate` | `/statistics`, `/profile`, `/premium`, `/home` |
| `showTutorial` | `siri_shortcut_tutorial`, `ios_widget_tutorial`, `android_widget_tutorial` |
| `addWater` | Chatbot üzerinden direkt su ekleme |
| `showTip` | Anlık ipucu gösterimi |

---

### 🏅 Hidrasyon Koç Kartı (`HydrationCoachCard`)

Ana ekranda sabit olarak bulunan, uygulamanın retention kalbini oluşturan akıllı kart.

#### Çalışma Prensibi

```
İçecek eklendi?
    ↓ evet
Anlık Tepki Modu (6 sn)
  → İçeceğin kategorisine göre tepki mesajı
  → AnimatedSwitcher fade+slide geçişi
    ↓ 6 sn sonra otomatik
Normal Mod
  → progress % + saat segmentine göre bağlamsal mesaj
  → premium: insight bar + günlük ipucu
  → free: rotating upsell (döngüsel premium tanıtım)
```

#### Saat Segmentine Göre Mesaj Tonu

| Saat | Ton |
|------|-----|
| 06-10 | Sabah enerjisi |
| 10-14 | Öğle hatırlatma |
| 14-18 | Öğleden sonra baskısı |
| 18-22 | Akşam tamamlama |
| 22-00 | Gece özeti |

#### Premium Özellikleri

- **Insight Bar**: Streak, haftalık ortalama, en uzun streak gibi metrikler
- **Günlük İpucu** (`_DailyTip`): Günün saatine göre dönen hidrasyon ipucu
- **Kişisel Koç Mesajı**: Kullanıcı adıyla kişiselleştirilmiş motivasyon

#### Free Kullanıcı

- Rotating upsell: Her birkaç açılışta farklı premium özellik tanıtımı
- Anlık tepki ve saat bazlı mesajlar ücretsiz olarak çalışır

### 🔄 Offline Mode & Arka Plan Senkronizasyonu

- **Offline Destek**: İnternet yokken eklenen su kayıtları yerel olarak saklanır (`WaterSyncManager`)
- **iOS Background Fetch**: iOS 13+ Background App Refresh ile günde 2-4 kez otomatik Firebase senkronizasyonu (`BackgroundSyncService`)
- **App Group Senkronizasyonu**: Widget ve Watch App ile gerçek zamanlı veri paylaşımı (`AppGroupSyncService`)

### 💳 Premium Özellikler

- **Onboarding Paywall**: Kullanıcı yolculuğunun sonunda premium teklifi
- **In-App Purchase**: Güvenli abonelik yönetimi
- **RevenueCat Entegrasyonu**: Abonelik yaşam döngüsü yönetimi
- **Aylık & Yıllık Planlar**: Esnek abonelik seçenekleri
- **Reklamsız Deneyim**: Kesintisiz kullanım

### 🌍 Çok Dil & Erişilebilirlik

- **3 Dil Desteği**: Türkçe, İngilizce, Arapça
- **RTL Desteği**: Arapça için sağdan sola yazım

### ♿ Erişilebilirlik Sistemi (VoiceOver / TalkBack)

Görme engelli kullanıcılar için kapsamlı ekran okuyucu desteği uygulanmıştır:

- **Bağlamsal Semantics etiketleri**: Ana su takip kartı "1.2 litre içildi, hedefin %85'i, 300 ml kaldı" şeklinde tek bir anlamlı cümle olarak okunur; istatistik sekmeleri "Haftalık, seçili" / "Aylık, seçmek için dokunun" / "Aylık, premium gerektirir" bilgisini verir
- **Canlı duyurular**: Su eklendiğinde `SemanticsService.announce()` ile ekran okuyucu anında bilgilendirilir ("200 mililitre su eklendi, saat 14:30")
- **Grafik metin alternatifi**: Görsel grafikler `ExcludeSemantics` ile ekran okuyucudan gizlenir; `_buildChartSemanticSummary` ile ekranda yer kaplamayan görünmez bir `Semantics` bloğu tüm grafik verisini ("Pazartesi: 1.2 litre, Salı: 0.8 litre… 7 günden 5 gün hedef tamamlandı") sesli okur
- **Doğru semantik roller**: Etkileşimli elementlerde `button: true`, `selected: isSelected` ile platform sıralaması ve durum bildirimi sağlanır
- **Platform uyumlu kontroller**: `Switch.adaptive` ile iOS/Android kendi erişilebilirlik kurallarını uygular
- **Erişilebilirlik Ayarları Ekranı**: Hacim birimi (ml/fl oz), bilgi paneli, animasyon tercihleri ve kilitlenme raporu gibi ayarları gruplandıran ayrı bir ekran (`AccessibilitySettingsScreen`)

---

## 🛠️ Teknoloji Stack

### Frontend (Flutter)

| Kategori | Teknoloji | Versiyon |
|----------|-----------|----------|
| **Framework** | Flutter | 3.27+ |
| **Dil** | Dart | 3.8+ |
| **State Management** | Provider | 6.1.2 |
| **Dependency Injection** | GetIt + Injectable | 8.2.0 / 2.5.2 |
| **Routing** | App Links (Deep Linking) | 6.3.2 |
| **Local Storage** | SharedPreferences, Secure Storage | 2.3.2 / 9.2.2 |
| **Charts** | FL Chart | 1.1.1 |
| **Animations** | Flutter Animate, Lottie | 4.5.0 / 3.1.2 |
| **Audio** | AudioPlayers | 6.1.0 |
| **Video** | Video Player | 2.9.2 |
| **Speech Recognition** | speech_to_text | 7.3.0 |

### Backend & Cloud

| Servis | Açıklama |
|--------|----------|
| **Firebase Authentication** | Email, Google, Apple Sign-In |
| **Cloud Firestore** | NoSQL veritabanı |
| **Firebase Cloud Messaging** | Push notifications |
| **Firebase Storage** | Profil fotoğrafları |
| **Firebase Analytics** | Kullanıcı davranış analizi |
| **Firebase Crashlytics** | Crash reporting |
| **Firebase Remote Config** | Feature flags, A/B testing |
| **Cloud Functions** | Makbuz doğrulama, webhook'lar |
| **Firebase App Check** | Bot koruması |

### Native iOS

| Teknoloji | Kullanım |
|-----------|----------|
| **Swift 5** | Native iOS kodu |
| **SwiftUI** | Apple Watch uygulaması |
| **WidgetKit** | Home Screen widgets |
| **Siri Intents** | Sesli komutlar |
| **HealthKit** | Sağlık verileri entegrasyonu |
| **App Groups** | Widget/Watch veri paylaşımı |
| **CocoaPods** | Native bağımlılık yöneticisi |

### Native Android

| Teknoloji | Kullanım |
|-----------|----------|
| **Kotlin** | Native Android kodu |
| **Android Jetpack** | Widget implementation |
| **Google Play Services** | Location, Auth |

### Third-Party Services

| Servis | Amaç |
|--------|------|
| **RevenueCat** | Abonelik yönetimi |
| **OpenWeatherMap** | Hava durumu API'si |
| **Google Sign-In** | OAuth authentication |
| **Apple Sign-In** | Native Apple auth |

---

## 📦 Kurulum

### Gereksinimler

- **Flutter SDK**: 3.27.0 veya üzeri
- **Dart SDK**: 3.8.1 veya üzeri
- **Xcode**: 15.0+ (iOS development için)
- **Android Studio**: 2023.1+ (Android development için)
- **CocoaPods**: 1.12+ (iOS bağımlılıkları için)
- **Git**: 2.30+

### 1. Repository'yi Klonlayın

```bash
git clone https://github.com/yafurkan/SuuApp.git
cd SuuApp
```

### 2. Environment Variables Ayarlayın

```bash
# .env.example dosyasını kopyalayın
cp .env.example .env

# .env dosyasını düzenleyin ve gerçek API anahtarlarınızı ekleyin
nano .env
```

**Gerekli API Anahtarları:**

- Firebase (Mobile & Web API keys)
- RevenueCat (Android & iOS API keys)
- Google OAuth Client IDs
- OpenWeatherMap API key
- Encryption key (oluşturmak için: `openssl rand -base64 32`)

### 3. Firebase Konfigürasyonu

**Android:**

```bash
# Firebase Console'dan google-services.json indirin
# Dosyayı şuraya yerleştirin:
android/app/google-services.json
```

**iOS:**

```bash
# Firebase Console'dan GoogleService-Info.plist indirin
# Dosyayı şuraya yerleştirin:
ios/Runner/GoogleService-Info.plist
```

### 4. Flutter Bağımlılıklarını Yükleyin

```bash
flutter pub get
```

### 5. iOS Setup (sadece macOS)

```bash
cd ios
pod install
cd ..
```

### 6. Code Generation

```bash
# Dependency injection ve model generator
flutter pub run build_runner build --delete-conflicting-outputs
```

### 7. Uygulamayı Çalıştırın

```bash
# Development mode
flutter run

# iOS simulator
flutter run -d "iPhone 15 Pro"

# Android emulator
flutter run -d emulator-5554

# Belirli bir .env dosyasıyla
flutter run --dart-define-from-file=.env
```

---

## 🏗️ Mimari

SuuApp, **Clean Architecture** prensiplerini takip eder ve **Domain-Driven Design (DDD)** yaklaşımını benimser.

### Katmanlar

```
┌─────────────────────────────────────────┐
│         PRESENTATION LAYER              │
│  (UI, Widgets, Providers, Screens)      │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│          DOMAIN LAYER                   │
│  (UseCases, Entities, Repositories)     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│           DATA LAYER                    │
│  (Models, Services, Data Sources)       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      INFRASTRUCTURE LAYER               │
│  (Firebase, APIs, Platform Channels)    │
└─────────────────────────────────────────┘
```

### Design Patterns

- **Repository Pattern**: Veri kaynaklarını soyutlar
- **Provider Pattern**: State management (20 provider)
- **Dependency Injection**: GetIt + Injectable
- **Factory Pattern**: Notification content creation
- **Strategy Pattern**: Conflict resolution
- **Singleton Pattern**: Service instances

---

## 📁 Proje Yapısı

```
SuuApp/
├── lib/
│   ├── main.dart                    # Entry point
│   ├── firebase_options.dart        # Firebase config
│   │
│   ├── core/                        # Core utilities
│   │   ├── config/                  # App configuration
│   │   │   └── secure_config.dart   # Secure API key management
│   │   ├── constants/               # App constants
│   │   ├── di/                      # Dependency Injection
│   │   │   └── injection_container.dart
│   │   ├── services/                # Core services
│   │   │   ├── water_data_manager.dart
│   │   │   ├── water_sound_service.dart
│   │   │   └── ...
│   │   ├── theme/                   # App theme
│   │   └── utils/                   # Helper utilities
│   │
│   ├── data/                        # Data layer
│   │   ├── auth/                    # Auth repository
│   │   │   ├── firebase_auth_repository.dart
│   │   │   └── stub_auth_repository.dart
│   │   ├── bundles/                 # İçecek tanımları
│   │   │   └── beverage_definitions.dart
│   │   ├── models/                  # Data models
│   │   │   ├── beverage_model.dart
│   │   │   ├── beverage_size_option.dart
│   │   │   ├── water_intake_model.dart
│   │   │   └── ...
│   │   └── services/                # Data services
│   │       ├── auth_service.dart
│   │       ├── badge_service.dart
│   │       ├── health_kit_service.dart
│   │       ├── enhanced_health_sync_service.dart
│   │       ├── notification_service.dart
│   │       ├── water_service.dart
│   │       ├── widget_service.dart
│   │       ├── watch_water_sync_service.dart
│   │       ├── social_service.dart
│   │       ├── viral_growth_service.dart
│   │       ├── retention_service.dart
│   │       ├── weather_service.dart
│   │       └── ...
│   │
│   ├── features/                    # Bağımsız özellik modülleri
│   │   └── reporting/               # PDF/CSV raporlama (Clean Architecture)
│   │       ├── data/
│   │       ├── domain/
│   │       ├── models/
│   │       └── presentation/
│   │
│   ├── domain/                      # Business logic
│   │   ├── models/                  # Domain models
│   │   ├── enums/                   # Enums
│   │   ├── interfaces/              # Interface definitions
│   │   ├── repositories/            # Repository interfaces
│   │   ├── services/                # Service interfaces
│   │   └── usecases/                # Business use cases
│   │
│   ├── presentation/                # UI layer
│   │   ├── onboarding/              # Onboarding akışı
│   │   │   └── screens/
│   │   │       ├── ob_name_screen.dart
│   │   │       ├── ob_gender_screen.dart
│   │   │       ├── ob_age_screen.dart
│   │   │       ├── ob_height_screen.dart
│   │   │       ├── ob_weight_screen.dart
│   │   │       ├── ob_activity_screen.dart
│   │   │       ├── ob_goals_screen.dart
│   │   │       ├── ob_goal_calculation_screen.dart
│   │   │       ├── ob_health_permission_screen.dart
│   │   │       ├── ob_location_permission_screen.dart
│   │   │       ├── ob_notification_permission_screen.dart
│   │   │       ├── ob_micro_consent_screen.dart
│   │   │       ├── ob_analyzing_screen.dart
│   │   │       ├── ob_paywall_screen.dart
│   │   │       ├── ob_pregnancy_screen.dart
│   │   │       ├── ob_sugary_screen.dart
│   │   │       ├── ob_summary_screen.dart
│   │   │       ├── ob_value_prop_screen.dart
│   │   │       ├── ob_veggies_screen.dart
│   │   │       └── animated_onboarding_screen.dart
│   │   ├── screens/                 # App screens
│   │   │   ├── auth/
│   │   │   ├── challenge/
│   │   │   ├── friends/
│   │   │   ├── guest/
│   │   │   ├── help/
│   │   │   ├── league/
│   │   │   ├── privacy/
│   │   │   ├── profile/
│   │   │   ├── profile_setup/
│   │   │   ├── retention/
│   │   │   ├── settings/
│   │   │   │   ├── accessibility_settings_screen.dart  # Erişilebilirlik ayarları
│   │   │   │   ├── voice_assistant_settings_screen.dart
│   │   │   │   └── siri_shortcuts_settings_screen.dart
│   │   │   ├── splash/
│   │   │   ├── subscription/
│   │   │   ├── viral/
│   │   │   └── voice/
│   │   ├── providers/               # State providers (20 provider)
│   │   │   ├── water_provider.dart
│   │   │   ├── notification_provider.dart
│   │   │   ├── badge_provider.dart
│   │   │   ├── health_integration_provider.dart
│   │   │   ├── home_layout_provider.dart
│   │   │   └── ...
│   │   └── widgets/                 # Reusable widgets
│   │       ├── beverage_selector_dialog.dart
│   │       ├── daily_health_summary_card.dart
│   │       ├── hydration_coach_card.dart
│   │       └── ...
│   │
│   ├── screens/
│   │   ├── home_screen.dart         # Ana ekran
│   │   ├── badges_screen.dart
│   │   ├── statistics_screen.dart
│   │   ├── video_splash_screen.dart
│   │   └── email_verification_success_screen.dart
│   ├── voice/                       # Uygulama içi sesli komut sistemi
│   │   ├── voice_command_service.dart   # speech_to_text dinleme & eşleştirme
│   │   └── voice_command_model.dart     # Sesli komut modelleri
│   ├── l10n/                        # Localization (TR/EN/AR)
│   └── generated/                   # Auto-generated files
│
├── ios/                             # iOS native code
│   ├── Runner/
│   │   ├── AppDelegate.swift
│   │   ├── VoiceAssistantHandler.swift
│   │   ├── Info.plist
│   │   ├── GoogleService-Info.plist # ⚠️ GİTİGNORE
│   │   └── WaterWidgetExtension/
│   │       ├── WaterIntakeWidget.swift
│   │       ├── WaterWidgetBundle.swift
│   │       └── SuuLiveActivity.swift  # iOS Live Activities
│   │
│   ├── WaterWatchApp Watch App/     # Apple Watch app
│   ├── SuuVoiceIntentExtension/     # Siri intents
│   └── WaterIntentExtension/        # Ek Siri intent uzantısı
│
├── android/                         # Android native code
│
├── assets/
│   ├── images/
│   │   ├── logos/                   # Marka logoları (Starbucks, Greenwich, Nevada...)
│   │   ├── beverages/               # İçecek görselleri
│   │   ├── tutorial/                # Tutorial görselleri
│   │   └── tutorial_mascot/         # Tutorial maskot görselleri
│   ├── icons/                       # Uygulama ikonları
│   ├── sounds/                      # Ses efektleri (drinks.wav, winner.wav, homeclick.wav)
│   ├── animations/                  # Lottie animations
│   ├── badges/                      # Rozet görselleri
│   ├── branding/                    # Marka varlıkları (splash logo vb.)
│   ├── fonts/                       # Custom fonts
│   └── videos/                      # Splash screen video
│
├── firebase/                        # Firebase config
│   ├── functions/
│   │   ├── index.js
│   │   ├── receipt-validation.js
│   │   └── revenuecat_webhook.js
│   ├── firestore.rules
│   └── storage.rules
│
├── .env                             # ⚠️ GİTİGNORE - Environment variables
├── .env.example                     # ✅ Template
├── pubspec.yaml                     # Flutter dependencies
└── README.md                        # Bu dosya
```

### ⚠️ Güvenlik Notları

Aşağıdaki dosyalar `.gitignore` ile korunur ve **ASLA** git'e commit edilmemelidir:

```
.env                                          # API anahtarları
android/app/google-services.json             # Firebase config
android/key.properties                        # Keystore credentials
android/app/*.jks                             # Android keystore
ios/Runner/GoogleService-Info.plist          # Firebase config
ios/**/*.mobileprovision                      # Provisioning profiles
ios/**/*.p12                                  # iOS certificates
```

---

## 💻 Geliştirme

### Kod Standartları

- **Dart Style Guide**: Resmi Dart stil kılavuzuna uyun
- **Effective Dart**: Best practices uygulayın
- **Linting**: `flutter analyze` ile düzenli kontrol
- **Formatting**: `flutter format .` ile otomatik formatla

### Git Workflow

```bash
# Yeni özellik branch'i oluştur
git checkout -b feature/new-feature

# Değişiklikleri commit et
git add .
git commit -m "feat: add new feature"

# Push
git push origin feature/new-feature
```

**Commit Mesaj Formatı:**

```
<type>(<scope>): <subject>
```

**Types:** feat, fix, docs, style, refactor, test, chore

### Debug Modu

```bash
# Debug build
flutter run --debug

# Profile (performance analizi)
flutter run --profile

# Firebase Emulator ile test
firebase emulators:start
```

---

## 🧪 Test

```bash
# Tüm testleri çalıştır
flutter test

# Coverage raporu
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
open coverage/html/index.html
```

---

## 🚢 Deployment

### iOS Deployment

```bash
flutter build ios --release \
  --dart-define-from-file=.env \
  --obfuscate \
  --split-debug-info=build/ios/debug-info
```

### Android Deployment

```bash
# App Bundle (Google Play)
flutter build appbundle --release \
  --dart-define-from-file=.env \
  --obfuscate \
  --split-debug-info=build/android/debug-info
```

### Firebase Deploy

```bash
firebase deploy --only firestore:rules
firebase deploy --only functions
```

---

## 📄 Lisans

Bu proje **proprietary** lisans altındadır. Tüm hakları saklıdır.

**© 2025 SuuApp. All rights reserved.**

---

<div align="center">

**Sağlıklı yaşam için su için! 💧**

[⬆ Başa Dön](#-suuapp---akıllı-su-takip-uygulaması)

</div>
