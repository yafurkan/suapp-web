-- Suu hediye kod dağıtıcı — D1 şeması
-- Kurulum: npx wrangler d1 execute suu-gift-codes --remote --file=./schema.sql
--
-- Tasarım notu: "aynı IP/e-posta ikinci kez kod alamaz" kuralı uygulama
-- katmanında DEĞİL, veritabanı katmanında UNIQUE indeksle zorlanır. Uygulama
-- kontrolü eşzamanlı iki isteği kaçırabilir (TOCTOU); UNIQUE indeks kaçırmaz.

-- Kod havuzu. platform içinde id = dağıtım sırası (ORDER BY id ile sırayla verilir).
--   ios     → App Store offer kodu (18 hane), kaynak Suu_Kurumsal_Mesajli_Kodlar.xlsx
--   android → Google Play promo kodu (23 hane), kaynak promotion_codes.csv
CREATE TABLE IF NOT EXISTS codes (
  id         INTEGER PRIMARY KEY,
  code       TEXT    NOT NULL UNIQUE,
  platform   TEXT    NOT NULL DEFAULT 'ios',    -- ios | android
  seq        INTEGER,                            -- kaynak dosyadaki sıra no
  batch      TEXT    NOT NULL DEFAULT 'default',
  status     TEXT    NOT NULL DEFAULT 'free',    -- free | claimed | disabled
  claimed_at TEXT,
  claim_id   TEXT
);

-- "Şu platformdaki sıradaki boş kod" sorgusunun indeksi.
CREATE INDEX IF NOT EXISTS ix_codes_free ON codes(platform, status, id);

-- Talepler. E-posta düz metin saklanır (kodu göndermek ve duyuru listesi için
-- gerekli); IP ASLA düz metin saklanmaz — sadece HMAC özeti (KVKK/GDPR).
CREATE TABLE IF NOT EXISTS claims (
  id          TEXT    PRIMARY KEY,
  code_id     INTEGER,
  platform    TEXT    NOT NULL DEFAULT 'ios',
  email       TEXT    NOT NULL,
  email_hash  TEXT    NOT NULL,          -- normalize edilmiş e-postanın HMAC'i
  ip_hash     TEXT    NOT NULL,
  ua_hash     TEXT,
  country     TEXT,
  lang        TEXT,
  created_at  TEXT    NOT NULL,
  -- Hangi sponsorluk sayfasından geldi (dahacommunity gibi). NULL = genel sayfa.
  -- Kampanya başına performans ölçmenin tek yolu; sonradan eklenemez çünkü
  -- geçmiş talepler hangi sayfadan geldiğini artık bilmez.
  partner     TEXT,
  email_sent  INTEGER NOT NULL DEFAULT 0,
  resend_count INTEGER NOT NULL DEFAULT 0,
  -- Ticari elektronik ileti açık rızası (KVKK/İYS + GDPR).
  -- 0 = izin YOK; sadece kod maili gider, duyuru listesine eklenmez.
  marketing_consent INTEGER NOT NULL DEFAULT 0,
  consent_at        TEXT,
  consent_text      TEXT,                -- rıza anındaki metnin sürümü (ispat)
  FOREIGN KEY (code_id) REFERENCES codes(id)
);

-- Kötüye kullanımı engelleyen iki kural. Platformdan BAĞIMSIZ: bir kişi
-- toplamda tek kod alır, iOS'tan bir Android'den bir alıp 2 ay yapamaz.
CREATE UNIQUE INDEX IF NOT EXISTS ux_claims_email ON claims(email_hash);
CREATE UNIQUE INDEX IF NOT EXISTS ux_claims_ip    ON claims(ip_hash);

-- Duyuru listesi sorgusu: WHERE marketing_consent = 1
CREATE INDEX IF NOT EXISTS ix_claims_consent ON claims(marketing_consent);

-- Sponsorluk kırılımı
CREATE INDEX IF NOT EXISTS ix_claims_partner ON claims(partner);

-- Kaba kuvvet / e-posta taraması için sayaç (kayan pencere).
CREATE TABLE IF NOT EXISTS throttle (
  key          TEXT    PRIMARY KEY,
  count        INTEGER NOT NULL DEFAULT 0,
  window_start INTEGER NOT NULL
);
