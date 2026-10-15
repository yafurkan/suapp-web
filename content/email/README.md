# E-posta imza kartı

- Kaynak: `imza-furkan.html` (1200×340, logo gömülü, QR → https://suuapp.com/app)
- Yayındaki görsel: `assets/brand/email/imza-furkan.jpg` → https://suuapp.com/assets/brand/email/imza-furkan.jpg
- Gmail: furkanmertfurkan@gmail.com → Ayarlar → İmza → "Suu imza kartı"; info@suuapp.com için yeni e-postalarda ve yanıtlarda varsayılan.

Yeniden üretmek (unvan/adres değişirse):

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
  --force-device-scale-factor=1 --default-background-color=00000000 --window-size=1200,340 \
  --screenshot=/tmp/imza.png content/email/imza-furkan.html
```

Sonra PNG'yi beyaz zemine JPEG (kalite 90) olarak `assets/brand/email/imza-furkan.jpg` üzerine yaz ve yayınla. Gmail imzası aynı adresi kullandığı için kendiliğinden güncellenir (Gmail görseli önbelleğe alabilir; gerekirse dosya adını değiştirip imzayı yeniden kur).
