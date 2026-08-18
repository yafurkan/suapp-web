/**
 * Suu — hediye kod dağıtıcı API'si (Cloudflare Worker + D1)
 *
 * Neden Worker: suuapp.com GitHub Pages'te statik duruyor. ~965 kodu statik bir
 * dosyaya koymak = ilk botta havuzun bitmesi. Kod havuzu sunucuda kalır,
 * istemciye tek seferde tek kod döner.
 *
 * Uç noktalar:
 *   GET  /stats             → platform kırılımlı kalan/dağıtılan sayısı (herkese açık)
 *   POST /claim             → { ok, code, redeemUrl, remaining, emailSent }
 *   GET  /admin/stats       → detaylı panel verisi (ADMIN_TOKEN)
 *   GET  /admin/claims      → kim hangi kodu aldı, CSV (ADMIN_TOKEN)
 *   GET  /admin/subscribers → SADECE reklam izni verenler, CSV (ADMIN_TOKEN)
 *
 * Kötüye kullanım savunması (katman katman):
 *   1. Origin kontrolü      — istek suuapp.com'dan mı geliyor
 *   2. Turnstile            — bot doğrulaması (Cloudflare, ücretsiz)
 *   3. Bal küpü + süre      — formu 2 sn'de dolduran insan değildir
 *   4. Throttle             — IP başına saatte N deneme (başarısızlar dahil)
 *   5. E-posta normalize    — a.b+1@gmail.com ile a.b@gmail.com aynı kişidir
 *   6. Tek kullanımlık mail — bilinen geçici posta alan adları reddedilir
 *   7. UNIQUE indeks        — DB katmanında tek IP / tek e-posta = tek kod
 *
 * Platform kuralı: kullanıcı iOS veya Android seçer, ama kişi başına toplam
 * TEK kod düşer. İkisini birden alıp 2 ay yapmak mümkün değil.
 */

const ALLOWED_ORIGINS = new Set([
  "https://suuapp.com",
  "https://www.suuapp.com",
]);

const PLATFORMS = new Set(["ios", "android"]);
const LANGS = new Set(["tr", "en", "ru", "ar"]);

// Kayıt olmadan kod üreten yaygın geçici posta servisleri.
const DISPOSABLE_DOMAINS = new Set([
  "0-mail.com", "10minutemail.com", "20minutemail.com", "33mail.com",
  "anonbox.net", "burnermail.io", "dispostable.com", "dropmail.me",
  "emailondeck.com", "fakeinbox.com", "getairmail.com", "getnada.com",
  "guerrillamail.com", "guerrillamail.info", "harakirimail.com",
  "inboxbear.com", "inboxkitten.com", "mail-temp.com", "mail7.io",
  "mailcatch.com", "maildrop.cc", "mailinator.com", "mailnesia.com",
  "mailsac.com", "mintemail.com", "moakt.com", "mohmal.com", "mytemp.email",
  "nada.email", "sharklasers.com", "spam4.me", "spamgourmet.com",
  "temp-mail.io", "temp-mail.org", "tempail.com", "tempinbox.com",
  "tempm.com", "tempmail.dev", "tempmail.plus", "tempmailo.com",
  "throwawaymail.com", "trashmail.com", "trashmail.de", "tmpmail.org",
  "yopmail.com", "yopmail.fr", "yopmail.net", "zetmail.com",
]);

const THROTTLE_LIMIT = 8;        // IP başına deneme
const THROTTLE_WINDOW = 3600;    // saniye (1 saat)
const MAX_RESEND = 3;            // kaybolan kodun tekrar gönderim hakkı

// Panel şifresi kısa tutulduğu için kaba kuvvet kilidi ZORUNLU: IP başına
// saatte 6 hatalı deneme, sonrası 429. Bu kilit olmadan kısa parola denenebilir.
const ADMIN_FAIL_LIMIT = 6;
const ADMIN_FAIL_WINDOW = 3600;

/* ────────────────────────── yardımcılar ────────────────────────── */

function corsHeaders(origin, env) {
  const allowLocal = env.ALLOW_LOCALHOST === "1" &&
    /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin || "");
  const allowed = ALLOWED_ORIGINS.has(origin) || allowLocal;
  return {
    "Access-Control-Allow-Origin": allowed ? origin : "https://suuapp.com",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

function json(data, status, origin, env) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
      ...corsHeaders(origin, env),
    },
  });
}

async function hmac(secret, message) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Sabit süreli karşılaştırma — admin jetonunu zamanlama saldırısına açmamak için. */
function safeEqual(a, b) {
  if (typeof a !== "string" || typeof b !== "string" || a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

/**
 * E-postayı kimlik olarak normalize eder.
 * furkan+suu@gmail.com, f.u.r.k.a.n@gmail.com ve furkan@googlemail.com
 * hepsi aynı kutuya düşer; üçü de tek kod almalı.
 */
function normalizeEmail(raw) {
  const email = String(raw || "").trim().toLowerCase();
  if (email.length < 6 || email.length > 254) return null;
  if (!/^[^\s@,;:<>"'\\]+@[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/.test(email)) return null;

  const at = email.lastIndexOf("@");
  let local = email.slice(0, at);
  let domain = email.slice(at + 1);

  local = local.split("+")[0];
  if (domain === "googlemail.com") domain = "gmail.com";
  if (domain === "gmail.com") local = local.replace(/\./g, "");
  if (!local) return null;

  return { email, normalized: `${local}@${domain}`, domain };
}

/** Kayan pencere sayacı. true = izin var. */
async function allowAttempt(db, key, limit, windowSec) {
  const now = Math.floor(Date.now() / 1000);
  const row = await db.prepare("SELECT count, window_start FROM throttle WHERE key = ?")
    .bind(key).first();

  if (!row || now - row.window_start >= windowSec) {
    await db.prepare(
      `INSERT INTO throttle (key, count, window_start) VALUES (?, 1, ?)
       ON CONFLICT(key) DO UPDATE SET count = 1, window_start = excluded.window_start`,
    ).bind(key, now).run();
    return true;
  }
  if (row.count >= limit) return false;
  await db.prepare("UPDATE throttle SET count = count + 1 WHERE key = ?").bind(key).run();
  return true;
}

/** Pencere içindeki hatalı deneme sayısı. */
async function failCount(db, key, windowSec) {
  const now = Math.floor(Date.now() / 1000);
  const row = await db.prepare("SELECT count, window_start FROM throttle WHERE key = ?")
    .bind(key).first();
  if (!row || now - row.window_start >= windowSec) return 0;
  return row.count;
}

/** Hatalı denemeyi sayar (başarılı giriş sayacı artırmaz). */
async function noteFailure(db, key, windowSec) {
  const now = Math.floor(Date.now() / 1000);
  const row = await db.prepare("SELECT count, window_start FROM throttle WHERE key = ?")
    .bind(key).first();
  if (!row || now - row.window_start >= windowSec) {
    await db.prepare(
      `INSERT INTO throttle (key, count, window_start) VALUES (?, 1, ?)
       ON CONFLICT(key) DO UPDATE SET count = 1, window_start = excluded.window_start`,
    ).bind(key, now).run();
  } else {
    await db.prepare("UPDATE throttle SET count = count + 1 WHERE key = ?").bind(key).run();
  }
}

async function verifyTurnstile(token, ip, env) {
  if (!env.TURNSTILE_SECRET) return true;   // anahtar tanımlı değilse doğrulama atlanır
  if (!token) return false;
  const body = new FormData();
  body.append("secret", env.TURNSTILE_SECRET);
  body.append("response", token);
  if (ip) body.append("remoteip", ip);
  try {
    const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify",
      { method: "POST", body });
    const out = await res.json();
    return out.success === true;
  } catch {
    return false;   // doğrulayamıyorsak kod dağıtmayız
  }
}

/**
 * Seçilen platformdaki sıradaki boş kodu atomik olarak kilitler.
 * SELECT+UPDATE arasında başkası kapabilir; koşullu UPDATE'in etkilediği satır
 * sayısı 0 ise sıra bize gelmemiş demektir, bir sonrakini deneriz.
 */
async function takeNextCode(db, claimId, platform) {
  for (let attempt = 0; attempt < 6; attempt++) {
    const next = await db.prepare(
      "SELECT id, code FROM codes WHERE platform = ? AND status = 'free' ORDER BY id LIMIT 1",
    ).bind(platform).first();
    if (!next) return null;   // bu platformun havuzu bitti

    const res = await db.prepare(
      `UPDATE codes SET status = 'claimed', claimed_at = ?, claim_id = ?
       WHERE id = ? AND status = 'free'`,
    ).bind(new Date().toISOString(), claimId, next.id).run();

    if (res.meta && res.meta.changes === 1) return next;
  }
  return null;
}

function redeemUrl(code, platform, env) {
  if (platform === "android") {
    return `https://play.google.com/redeem?code=${encodeURIComponent(code)}`;
  }
  const appId = env.APP_STORE_ID || "6757619920";
  return `https://apps.apple.com/redeem?ctx=offercodes&id=${appId}&code=${encodeURIComponent(code)}`;
}

const STORE_NAME = { ios: "App Store", android: "Google Play" };

/* ────────────────────────── e-posta ────────────────────────── */

const MAIL_COPY = {
  tr: {
    subject: "Suu Premium hediye kodun 🎁",
    heading: "Hediye kodun hazır",
    intro: "1 ay Suu Premium senin. Kodu {store} üzerinde kullanman yeterli:",
    cta: "Kodu {store}'da kullan",
    steps: [
      "Aşağıdaki butona telefonundan dokun (veya kodu kopyala).",
      "{store} açılır, kod otomatik gelir; hesabınla onayla.",
      "Suu'yu aç — Premium aktif olur.",
    ],
    note: "Kod tek kullanımlıktır ve yalnızca {store} içindir. Sorun yaşarsan bu e-postayı yanıtlaman yeterli.",
    footer: "Bu e-postayı suuapp.com'daki hediye kod formunu doldurduğun için aldın.",
  },
  en: {
    subject: "Your Suu Premium gift code 🎁",
    heading: "Your gift code is ready",
    intro: "One month of Suu Premium is yours. Just redeem it on {store}:",
    cta: "Redeem on {store}",
    steps: [
      "Tap the button below on your phone (or copy the code).",
      "{store} opens with the code filled in; confirm with your account.",
      "Open Suu — Premium is active.",
    ],
    note: "The code is single-use and works on {store} only. Just reply to this email if anything goes wrong.",
    footer: "You received this because you requested a gift code on suuapp.com.",
  },
  ru: {
    subject: "Ваш подарочный код Suu Premium 🎁",
    heading: "Код готов",
    intro: "Месяц Suu Premium — ваш. Активируйте код в {store}:",
    cta: "Активировать в {store}",
    steps: [
      "Нажмите кнопку ниже на телефоне (или скопируйте код).",
      "Откроется {store} с подставленным кодом; подтвердите аккаунтом.",
      "Откройте Suu — Premium активен.",
    ],
    note: "Код одноразовый и работает только в {store}. Если что-то не так — просто ответьте на это письмо.",
    footer: "Вы получили это письмо, потому что запросили код на suuapp.com.",
  },
  ar: {
    subject: "رمز هدية Suu Premium 🎁",
    heading: "رمز الهدية جاهز",
    intro: "شهر من Suu Premium لك. استخدم الرمز في {store}:",
    cta: "استخدام الرمز في {store}",
    steps: [
      "اضغط الزر أدناه من هاتفك (أو انسخ الرمز).",
      "سيفتح {store} والرمز مُدخل؛ أكّد بحسابك.",
      "افتح Suu — تم تفعيل Premium.",
    ],
    note: "الرمز للاستخدام مرة واحدة ويعمل في {store} فقط. إن واجهت مشكلة، رُدّ على هذه الرسالة.",
    footer: "وصلتك هذه الرسالة لأنك طلبت رمز هدية على suuapp.com.",
  },
};

function mailHtml(code, platform, lang, env) {
  const t = MAIL_COPY[lang] || MAIL_COPY.en;
  const store = STORE_NAME[platform] || STORE_NAME.ios;
  const fill = (s) => s.replaceAll("{store}", store);
  const dir = lang === "ar" ? "rtl" : "ltr";
  const url = redeemUrl(code, platform, env);
  const steps = t.steps.map((s, i) =>
    `<tr><td style="padding:4px 0;color:#4a5568;font-size:15px;line-height:1.6">
       <b style="color:#2196f3">${i + 1}.</b> ${fill(s)}</td></tr>`).join("");

  return `<!doctype html><html dir="${dir}"><body style="margin:0;padding:24px;background:#f4f7fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center">
<table role="presentation" width="100%" style="max-width:520px;background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(33,150,243,.12)">
  <tr><td style="background:linear-gradient(135deg,#2196f3,#0d47a1);padding:28px 32px;color:#fff">
    <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;opacity:.85">Suu</div>
    <div style="font-size:22px;font-weight:700;margin-top:6px">${t.heading}</div>
  </td></tr>
  <tr><td style="padding:28px 32px">
    <p style="margin:0 0 18px;color:#2d3748;font-size:16px;line-height:1.6">${fill(t.intro)}</p>
    <div style="border:2px dashed #2196f3;border-radius:12px;padding:18px;text-align:center;background:#f5fbff">
      <div style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:24px;font-weight:700;letter-spacing:.1em;color:#0d47a1;word-break:break-all">${code}</div>
    </div>
    <div style="text-align:center;margin:22px 0">
      <a href="${url}" style="display:inline-block;background:#2196f3;color:#fff;text-decoration:none;font-weight:600;font-size:16px;padding:14px 28px;border-radius:12px">${fill(t.cta)}</a>
    </div>
    <table role="presentation" width="100%">${steps}</table>
    <p style="margin:20px 0 0;color:#718096;font-size:13px;line-height:1.6">${fill(t.note)}</p>
  </td></tr>
  <tr><td style="padding:16px 32px 24px;border-top:1px solid #edf2f7;color:#a0aec0;font-size:12px;line-height:1.6">
    ${t.footer}<br><a href="https://suuapp.com" style="color:#2196f3;text-decoration:none">suuapp.com</a>
  </td></tr>
</table></td></tr></table></body></html>`;
}

async function sendCodeEmail(to, code, platform, lang, env) {
  if (!env.RESEND_API_KEY) return false;
  const t = MAIL_COPY[lang] || MAIL_COPY.en;
  const store = STORE_NAME[platform] || STORE_NAME.ios;
  try {
    const res = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        from: env.MAIL_FROM || "Suu <hediye@suuapp.com>",
        to: [to],
        subject: t.subject,
        html: mailHtml(code, platform, lang, env),
        text: `${t.heading}\n\n${code}\n\n${redeemUrl(code, platform, env)}\n\n${t.note.replaceAll("{store}", store)}`,
      }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

/* ────────────────────────── uç noktalar ────────────────────────── */

async function platformCounts(db) {
  const { results } = await db.prepare(
    `SELECT platform,
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'free' THEN 1 ELSE 0 END) AS remaining
     FROM codes GROUP BY platform`,
  ).all();

  const out = { ios: { total: 0, remaining: 0, claimed: 0 }, android: { total: 0, remaining: 0, claimed: 0 } };
  for (const r of results) {
    if (!out[r.platform]) continue;
    out[r.platform] = {
      total: r.total,
      remaining: r.remaining,
      claimed: r.total - r.remaining,
    };
  }
  return out;
}

async function handleStats(db, origin, env) {
  const p = await platformCounts(db);
  const total = p.ios.total + p.android.total;
  const remaining = p.ios.remaining + p.android.remaining;
  return json({
    ok: true, total, remaining, claimed: total - remaining, platforms: p,
  }, 200, origin, env);
}

async function handleClaim(request, db, origin, env) {
  const ip = request.headers.get("CF-Connecting-IP") || "";
  const country = request.cf?.country || request.headers.get("CF-IPCountry") || "";
  const ua = request.headers.get("User-Agent") || "";

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: "bad_request" }, 400, origin, env);
  }

  const lang = LANGS.has(body.lang) ? body.lang : "en";
  const platform = PLATFORMS.has(body.platform) ? body.platform : null;
  if (!platform) return json({ ok: false, error: "platform_required" }, 400, origin, env);

  // Bal küpü: gerçek kullanıcı görmediği alanı dolduramaz.
  if (body.website) return json({ ok: false, error: "captcha_failed" }, 403, origin, env);
  // İnsan formu 2 saniyeden hızlı dolduramaz.
  if (typeof body.elapsed === "number" && body.elapsed < 2000) {
    return json({ ok: false, error: "captcha_failed" }, 403, origin, env);
  }

  const salt = env.HASH_SALT || "suu-gift-fallback-salt";
  const ipHash = await hmac(salt, `ip:${ip}`);

  if (!await allowAttempt(db, `ip:${ipHash}`, THROTTLE_LIMIT, THROTTLE_WINDOW)) {
    return json({ ok: false, error: "rate_limited" }, 429, origin, env);
  }

  if (!await verifyTurnstile(body.turnstileToken, ip, env)) {
    return json({ ok: false, error: "captcha_failed" }, 403, origin, env);
  }

  const parsed = normalizeEmail(body.email);
  if (!parsed) return json({ ok: false, error: "invalid_email" }, 400, origin, env);
  if (DISPOSABLE_DOMAINS.has(parsed.domain)) {
    return json({ ok: false, error: "disposable_email" }, 400, origin, env);
  }

  const emailHash = await hmac(salt, `email:${parsed.normalized}`);

  // Bu e-posta daha önce kod aldıysa: kodu ekranda TEKRAR GÖSTERMEYİZ
  // (rastgele adres deneyip başkasının kodunu okumayı engeller), sadece
  // sahibinin kutusuna yeniden yollarız.
  const prior = await db.prepare(
    `SELECT c.id, c.resend_count, c.email, c.platform, k.code
     FROM claims c LEFT JOIN codes k ON k.id = c.code_id
     WHERE c.email_hash = ?`,
  ).bind(emailHash).first();

  if (prior) {
    let resent = false;
    if (prior.code && prior.resend_count < MAX_RESEND) {
      resent = await sendCodeEmail(prior.email, prior.code, prior.platform, lang, env);
      if (resent) {
        await db.prepare("UPDATE claims SET resend_count = resend_count + 1 WHERE id = ?")
          .bind(prior.id).run();
      }
    }
    return json({ ok: false, error: "already_claimed_email", resent }, 409, origin, env);
  }

  const ipPrior = await db.prepare("SELECT id FROM claims WHERE ip_hash = ?")
    .bind(ipHash).first();
  if (ipPrior) return json({ ok: false, error: "already_claimed_ip" }, 409, origin, env);

  // Kod bitmişse boşuna talep yazmayalım — erken çıkış.
  const free = await db.prepare(
    "SELECT COUNT(*) AS n FROM codes WHERE platform = ? AND status = 'free'",
  ).bind(platform).first();
  if (!free || free.n === 0) {
    return json({ ok: false, error: "exhausted", platform }, 410, origin, env);
  }

  const claimId = crypto.randomUUID();
  const uaHash = ua ? await hmac(salt, `ua:${ua}`) : null;
  const consent = body.marketingConsent === true ? 1 : 0;
  const nowIso = new Date().toISOString();

  // Talebi ÖNCE yazarız: iki UNIQUE indeks burada kilit görevi görür, eşzamanlı
  // ikinci istek INSERT'te patlar ve koda hiç ulaşamaz.
  try {
    await db.prepare(
      `INSERT INTO claims
         (id, code_id, platform, email, email_hash, ip_hash, ua_hash, country, lang,
          created_at, marketing_consent, consent_at, consent_text)
       VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
    ).bind(
      claimId, platform, parsed.email, emailHash, ipHash, uaHash, country, lang,
      nowIso, consent, consent ? nowIso : null,
      consent ? String(body.consentText || "").slice(0, 500) : null,
    ).run();
  } catch (err) {
    const msg = String(err?.message || err);
    if (/ux_claims_ip/.test(msg)) return json({ ok: false, error: "already_claimed_ip" }, 409, origin, env);
    if (/ux_claims_email/.test(msg)) return json({ ok: false, error: "already_claimed_email" }, 409, origin, env);
    if (/UNIQUE/i.test(msg)) return json({ ok: false, error: "already_claimed_email" }, 409, origin, env);
    return json({ ok: false, error: "server_error" }, 500, origin, env);
  }

  const taken = await takeNextCode(db, claimId, platform);
  if (!taken) {
    // Havuz bu arada bitti — talebi geri alırız ki stok yenilenince tekrar denenebilsin.
    await db.prepare("DELETE FROM claims WHERE id = ?").bind(claimId).run();
    return json({ ok: false, error: "exhausted", platform }, 410, origin, env);
  }

  await db.prepare("UPDATE claims SET code_id = ? WHERE id = ?").bind(taken.id, claimId).run();

  const emailSent = await sendCodeEmail(parsed.email, taken.code, platform, lang, env);
  if (emailSent) {
    await db.prepare("UPDATE claims SET email_sent = 1 WHERE id = ?").bind(claimId).run();
  }

  const left = await db.prepare(
    "SELECT COUNT(*) AS n FROM codes WHERE platform = ? AND status = 'free'",
  ).bind(platform).first();

  return json({
    ok: true,
    code: taken.code,
    platform,
    store: STORE_NAME[platform],
    redeemUrl: redeemUrl(taken.code, platform, env),
    remaining: left?.n ?? 0,
    emailSent,
  }, 200, origin, env);
}

/* ─────────────────────────── admin ─────────────────────────── */

function adminOk(url, request, env) {
  const token = url.searchParams.get("key") ||
    (request.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  return Boolean(env.ADMIN_TOKEN) && safeEqual(token, env.ADMIN_TOKEN);
}

/** Panelin okuduğu özet: kalan/dağıtılan, günlük eğri, izin oranı, dil/ülke. */
async function handleAdminStats(db, origin, env) {
  const platforms = await platformCounts(db);

  const totals = await db.prepare(
    `SELECT COUNT(*) AS claims,
            SUM(marketing_consent) AS consented,
            SUM(email_sent) AS mailed
     FROM claims`,
  ).first();

  const daily = await db.prepare(
    `SELECT substr(created_at, 1, 10) AS gun,
            COUNT(*) AS adet,
            SUM(CASE WHEN platform = 'ios' THEN 1 ELSE 0 END) AS ios,
            SUM(CASE WHEN platform = 'android' THEN 1 ELSE 0 END) AS android
     FROM claims GROUP BY gun ORDER BY gun DESC LIMIT 30`,
  ).all();

  const byLang = await db.prepare(
    "SELECT lang, COUNT(*) AS adet FROM claims GROUP BY lang ORDER BY adet DESC",
  ).all();

  const byCountry = await db.prepare(
    "SELECT country, COUNT(*) AS adet FROM claims GROUP BY country ORDER BY adet DESC LIMIT 15",
  ).all();

  const last = await db.prepare(
    `SELECT c.created_at, c.email, c.platform, c.lang, c.country,
            c.marketing_consent, c.email_sent, k.code, k.seq
     FROM claims c LEFT JOIN codes k ON k.id = c.code_id
     ORDER BY c.created_at DESC LIMIT 25`,
  ).all();

  return json({
    ok: true,
    platforms,
    claims: totals?.claims ?? 0,
    consented: totals?.consented ?? 0,
    mailed: totals?.mailed ?? 0,
    daily: daily.results,
    byLang: byLang.results,
    byCountry: byCountry.results,
    recent: last.results,
    generatedAt: new Date().toISOString(),
  }, 200, origin, env);
}

function csv(rows, filename) {
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const body = rows.map((r) => r.map(esc).join(",")).join("\n");
  return new Response("\uFEFF" + body, {   // BOM: Excel'de Türkçe karakterler bozulmasın
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="${filename}"`,
      "Cache-Control": "no-store",
    },
  });
}

/** Kimin hangi kodu aldığı — CSV. */
async function handleAdminClaims(db) {
  const { results } = await db.prepare(
    `SELECT c.created_at, c.email, c.platform, c.lang, c.country,
            c.marketing_consent, c.email_sent, k.seq, k.code
     FROM claims c LEFT JOIN codes k ON k.id = c.code_id
     ORDER BY c.created_at`,
  ).all();

  const rows = [["tarih", "eposta", "platform", "dil", "ulke", "reklam_izni", "mail_gitti", "kaynak_sira", "kod"]];
  for (const r of results) {
    rows.push([r.created_at, r.email, r.platform, r.lang, r.country,
      r.marketing_consent, r.email_sent, r.seq, r.code]);
  }
  return csv(rows, "suu-hediye-kod-talepleri.csv");
}

/** Duyuru listesi — SADECE açık rıza verenler. */
async function handleAdminSubscribers(db) {
  const { results } = await db.prepare(
    `SELECT email, lang, country, platform, consent_at
     FROM claims WHERE marketing_consent = 1 ORDER BY consent_at`,
  ).all();

  const rows = [["eposta", "dil", "ulke", "platform", "izin_tarihi"]];
  for (const r of results) {
    rows.push([r.email, r.lang, r.country, r.platform, r.consent_at]);
  }
  return csv(rows, "suu-duyuru-listesi.csv");
}

/* ────────────────────────── yönlendirme ────────────────────────── */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    const db = env.DB;

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, env) });
    }

    if (url.pathname.startsWith("/admin/")) {
      const salt = env.HASH_SALT || "suu-gift-fallback-salt";
      const adminKey = "adm:" + await hmac(salt, request.headers.get("CF-Connecting-IP") || "");

      if (await failCount(db, adminKey, ADMIN_FAIL_WINDOW) >= ADMIN_FAIL_LIMIT) {
        return json({ ok: false, error: "locked" }, 429, origin, env);
      }
      if (!adminOk(url, request, env)) {
        await noteFailure(db, adminKey, ADMIN_FAIL_WINDOW);
        return json({ ok: false, error: "forbidden" }, 403, origin, env);
      }
      try {
        if (url.pathname === "/admin/stats") return await handleAdminStats(db, origin, env);
        if (url.pathname === "/admin/claims") return await handleAdminClaims(db);
        if (url.pathname === "/admin/subscribers") return await handleAdminSubscribers(db);
      } catch (err) {
        console.error("admin failed", err);
        return json({ ok: false, error: "server_error" }, 500, origin, env);
      }
      return json({ ok: false, error: "not_found" }, 404, origin, env);
    }

    if (url.pathname === "/stats" && request.method === "GET") {
      try {
        return await handleStats(db, origin, env);
      } catch (err) {
        console.error("stats failed", err);
        return json({ ok: false, error: "server_error" }, 500, origin, env);
      }
    }

    if (url.pathname === "/claim" && request.method === "POST") {
      const allowLocal = env.ALLOW_LOCALHOST === "1" &&
        /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/.test(origin);
      if (!ALLOWED_ORIGINS.has(origin) && !allowLocal) {
        return json({ ok: false, error: "bad_origin" }, 403, origin, env);
      }
      try {
        return await handleClaim(request, db, origin, env);
      } catch (err) {
        console.error("claim failed", err);
        return json({ ok: false, error: "server_error" }, 500, origin, env);
      }
    }

    return json({ ok: false, error: "not_found" }, 404, origin, env);
  },
};
