# Hediye kod dağıtıcı — kurulum

Statik siteye (GitHub Pages) sıra takip eden, kötüye kullanıma kapalı bir kod
dağıtıcı eklemek için gereken tek şey bu Worker. Tamamı Cloudflare'in ücretsiz
katmanında çalışır: Workers 100.000 istek/gün, D1 5 milyon okuma/gün.

Havuz: **iOS 465 kod** (elle dağıtılan ilk 35 atlandı) + **Android 500 kod**.

---

## 1. Cloudflare hesabı ve giriş

```bash
cd worker
npm install
npx wrangler login          # tarayıcı açılır, hesabı yetkilendir
```

## 2. Veritabanını oluştur

```bash
npx wrangler d1 create suu-gift-codes
```

Çıktıdaki `database_id` değerini `wrangler.toml` içindeki
`BURAYA_D1_DATABASE_ID` yerine yapıştır. Sonra tabloları kur:

```bash
npx wrangler d1 execute suu-gift-codes --remote --file=./schema.sql
```

## 3. Gizli değerleri gir

```bash
npx wrangler secret put HASH_SALT        # uzun rastgele dize (aşağıda üretici var)
npx wrangler secret put ADMIN_TOKEN      # panel parolası (x9f4c2e7b.html girişi)
npx wrangler secret put TURNSTILE_SECRET # 4. adımda alınacak
npx wrangler secret put RESEND_API_KEY   # 5. adımda alınacak
```

Salt üretmek için: `openssl rand -hex 32`

> `HASH_SALT` **sonradan değiştirilemez**: IP ve e-posta özetleri onunla
> üretiliyor. Değiştirirsen mevcut kayıtlar eşleşmez ve daha önce kod almış
> herkes ikinci kez kod alabilir.

## 4. Turnstile (bot koruması, ücretsiz)

Cloudflare paneli → **Turnstile** → *Add site*
- Domain: `suuapp.com`
- Widget türü: **Managed**

İki anahtar çıkar:
- **Site key** → `content/gift/config.json` içindeki `turnstileSiteKey`
- **Secret key** → `npx wrangler secret put TURNSTILE_SECRET`

> Turnstile secret'ı tanımlanmazsa Worker doğrulamayı **atlar**. Diğer katmanlar
> (IP, e-posta, bal küpü, hız sınırı) çalışmaya devam eder ama gerçek bot
> koruması olmaz. Kampanyayı paylaşmadan önce mutlaka tanımla.

## 5. E-posta (Resend, ücretsiz 3.000/ay)

1. [resend.com](https://resend.com) hesabı aç → **Domains** → `suuapp.com` ekle
2. Resend'in verdiği **SPF ve DKIM** kayıtlarını **inetmar** DNS paneline gir
   (suuapp.com'un nameserver'ları `ns3/ns4.inetmar.net`)
3. Doğrulama yeşile döndükten sonra: **API Keys** → yeni anahtar →
   `npx wrangler secret put RESEND_API_KEY`

> Resend anahtarı olmadan da sistem çalışır: kod ekranda görünür, kullanıcıya
> "e-posta gönderilemedi, kodu şimdi kopyala" uyarısı çıkar. Alan adı doğrulaması
> bitene kadar bu halde yayına alınabilir.

## 6. Kodları yükle

```bash
cd ..
python3 scripts/gift-codes-import.py --apply
cd worker
npx wrangler d1 execute suu-gift-codes --remote --file=./seed-codes.sql
```

`seed-codes.sql` `.gitignore`'da — kodlar repoya **girmez**. Kaynak dosyalar
`~/Downloads` altında kalır.

Doğrula:

```bash
npx wrangler d1 execute suu-gift-codes --remote \
  --command "SELECT platform, status, COUNT(*) FROM codes GROUP BY platform, status"
```

Beklenen: `ios/free 465`, `android/free 500`.

## 7. Worker'ı yayına al

```bash
npx wrangler deploy
```

Çıkan adresi (`https://suu-gift-codes.<subdomain>.workers.dev`) iki yere yaz —
ikisi de tek dosyadan beslenir:

```bash
cd ..
# content/gift/config.json → "apiBase" alanını güncelle
python3 scripts/build-gift-pages.py --apply    # 7 sayfa + paneli yeniden üretir
```

## 8. Yayınla

```bash
git add -A && git commit -m "feat: hediye kod dağıtımı" && git push
```

GitHub Actions siteyi otomatik deploy eder.

---

## Sonraki partiler

Yeni kod dosyası geldiğinde:

```bash
python3 scripts/gift-codes-import.py --ios ~/Downloads/yeni.xlsx --ios-skip 0 --apply
cd worker && npx wrangler d1 execute suu-gift-codes --remote --file=./seed-codes.sql
```

`INSERT OR IGNORE` sayesinde aynı kod iki kez havuza girmez; script'i yanlışlıkla
iki kez çalıştırmak zarar vermez.

## Bakım komutları

```bash
# Kalan / dağıtılan
npx wrangler d1 execute suu-gift-codes --remote \
  --command "SELECT platform, status, COUNT(*) n FROM codes GROUP BY platform, status"

# Yanlışlıkla dağıtılan bir kodu havuza geri koy
npx wrangler d1 execute suu-gift-codes --remote \
  --command "UPDATE codes SET status='free', claimed_at=NULL, claim_id=NULL WHERE code='XXX'"

# Bir kişinin talebini sil (tekrar kod alabilsin)
npx wrangler d1 execute suu-gift-codes --remote \
  --command "DELETE FROM claims WHERE email='kisi@ornek.com'"

# Canlı log
npx wrangler tail
```

## Yerel test

```bash
npx wrangler d1 execute suu-gift-dev --local -c wrangler.dev.toml --file=./schema.sql
npx wrangler dev -c wrangler.dev.toml --port 8788 --local
```

`wrangler.dev.toml` ve `.dev.vars` git dışıdır.
