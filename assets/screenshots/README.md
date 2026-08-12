# Ekran Görüntüsü Şeması

```
assets/screenshots/
├── ios/{tr,en,ar,ru,de,it,hi}/<ekran>.webp
├── android/{tr,en,ar,ru,de,it,hi}/<ekran>.webp
└── _placeholder.svg          # dosya yoksa gösterilen çerçeve
```

**Yükleme sırası (`assets/js/screenshots.js`):**
`<platform>/<sayfa dili>` → `<platform>/tr` → `_placeholder.svg`

Yani bir ekranın yalnızca Türkçesi varsa diğer diller onu gösterir; hiç yoksa placeholder çıkar, sayfa kırılmaz.

## Çekilecek ekranlar

Her ikisi için de aynı slug'lar kullanılır — dosya adı değişmez, sadece klasör değişir.

| Slug | Ekran | Öncelik |
|---|---|---|
| `ana-ekran` | Ana ekran / günlük özet | ★ Zorunlu |
| `kalori-foto-analiz` | Yemek fotoğrafı → analiz sonucu | ★ Zorunlu |
| `makro-detay` | Protein / karbonhidrat / yağ dökümü | ★ Zorunlu |
| `suu-ai-sohbet` | Suu AI sohbet ekranı | ★ Zorunlu |
| `egzersiz-liste` | Aktivite seçim listesi (~50 spor) | ★ Zorunlu |
| `kosu-detay` | Koşu: mesafe, tempo, kalori, su | ★ Zorunlu |
| `bisiklet-detay` | Bisiklet: hız, irtifa, mesafe | ★ Zorunlu |
| `su-ekleme` | Su/içecek ekleme | ★ Zorunlu |
| `sesli-giris` | Sesli öğün girişi | Önerilen |
| `icecek-secimi` | 91 içecek listesi | Önerilen |
| `istatistik` | Günlük/haftalık/aylık grafikler | Önerilen |
| `hikaye-paylasim` | Hikâye şablonu paylaşımı | Önerilen |
| `evcil-hayvan` | Sanal evcil hayvan | Önerilen |
| `hatirlatma` | Akıllı hatırlatıcılar | Önerilen |
| `gun-challenge` | Günlük challenge | Opsiyonel |
| `basarilar` | Rozetler / başarılar | Opsiyonel |
| `profil` | Profil / hedefler | Opsiyonel |

**Yalnızca iOS:** `dynamic-island`, `live-activity`, `widget`, `siri`
**Yalnızca Android:** `widget-android`

## Teknik gereksinimler

- **Format:** WebP (kalite ~82). PNG yükleme, dönüştür: `cwebp -q 82 giris.png -o cikis.webp`
- **En-boy oranı:** 1170×2532 (iPhone) / 1080×2340 (Android) veya benzeri; sayfada `.phone` çerçevesine oturur
- **Dosya boyutu:** ideal <60 KB, üst sınır 120 KB
- **Durum çubuğu:** temiz olsun (tam pil, tam sinyal, sabit saat)
- **İçerik:** gerçekçi ama kişisel veri içermeyen örnek veriler

## Ekleme sonrası

```bash
python3 scripts/check-screenshots.py     # eksik ekranları listeler
```
