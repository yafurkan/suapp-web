# Su Takip Website

Modern ve responsive su takip uygulaması web sitesi.

## 🚀 Canlı Demo
[Web sitesini görüntüle](https://suuapp.com)

## 📋 Özellikler
- Responsive tasarım
- Modern kullanıcı arayüzü  
- Animasyonlar ve geçişler
- Mobil uyumlu
- Gerçek uygulama ekran görüntüleri

## 🛠️ Teknolojiler
- HTML5
- CSS3
- JavaScript (Vanilla)

## 📦 Kurulum
1. Projeyi klonlayın
2. Ekran görüntülerini `assets/screenshots/` klasörüne ekleyin
3. `index.html` dosyasını tarayıcıda açın

## 📱 Ekran Görüntüleri Ekleme
Aşağıdaki ekran görüntülerini `assets/screenshots/` klasörüne ekleyin:

- `ana-ekran.png` - Uygulamanın ana ekranı
- `istatistikler.png` - İstatistikler sayfası
- `profil.png` - Profil ayarları sayfası
- `hatirlatmalar.png` - Hatırlatmalar sayfası
- `hedefler.png` - Hedefler sayfası

### Önerilen Ekran Görüntüsü Özellikleri:
- Format: PNG (şeffaf arka plan)
- Boyut: 1080x1920 (mobil ekran oranı)
- Kalite: Yüksek çözünürlük
- İçerik: Gerçek uygulama verileri ile

## 📝 Deployment
Bu proje GitHub Pages ile otomatik olarak deploy edilmektedir.
# Update

## 🔄 GitHub Pages'i Kodla Yeniden Etkinleştirme
GitHub Pages ayarını GitHub arayüzünden kaldırdıysanız `scripts/enable-pages.sh` betiğiyle aynı işlemi programatik olarak yapabilirsiniz.

1. Repo ve Pages izinleri olan bir GitHub Personal Access Token oluşturup terminalde `export GITHUB_TOKEN=ghp_...` şeklinde tanımlayın. (Gerekirse `REPO_OWNER`, `REPO_NAME`, `CUSTOM_DOMAIN` değişkenleriyle kendi değerlerinizi geçebilirsiniz.)
2. Proje klasöründe `./scripts/enable-pages.sh` komutunu çalıştırın.
3. Betik Pages'i `workflow` modunda yeniden açar ve `suuapp.com` domainini HTTPS zorlamasıyla ayarlar. Ardından küçük bir değişiklik push ederek `.github/workflows/deploy.yml` aksiyonunun yeni deploy üretmesini sağlayın.
