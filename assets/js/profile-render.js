/**
 * Suu — Kişisel profil sayfası çizicisi (suuapp.com/<slug>/)
 *
 * Tek kaynak: sayfanın içindeki <script id="profile-data"> JSON'u.
 * Bu dosya o veriden sayfanın <head> etiketlerini ve gövdesini üretir.
 * Üç yerde aynı kod çalışır, böylece önizleme ile yayın hiç ayrışmaz:
 *   - panel (/<slug>/admin/)          canlı önizleme + yayınlarken
 *   - scripts/build-profile.mjs       elle düzenlenen veriyi sayfaya basmak için
 *   - (sayfanın kendisi bunu yüklemez — HTML zaten basılı gelir)
 *
 * Kullanıcı verisinin tamamı kaçışlanır; bağlantılar yalnızca http(s),
 * mailto, tel ya da site içi yol olabilir.
 */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.SuuProfile = factory();
})(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    var SITE = 'https://suuapp.com';

    // Lucide çizgi ikonları (ISC) — X logosu dolgu
    var I = {
        instagram: '<rect x="2" y="2" width="20" height="20" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><path d="M17.5 6.5h.01"/>',
        linkedin: '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
        x: '<path fill="currentColor" stroke="none" d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>',
        youtube: '<path d="M2.5 17a24.12 24.12 0 0 1 0-10 2 2 0 0 1 1.4-1.4 49.56 49.56 0 0 1 16.2 0A2 2 0 0 1 21.5 7a24.12 24.12 0 0 1 0 10 2 2 0 0 1-1.4 1.4 49.55 49.55 0 0 1-16.2 0A2 2 0 0 1 2.5 17"/><path d="m10 15 5-3-5-3z"/>',
        tiktok: '<path d="M9 12a4 4 0 1 0 4 4V2a5 5 0 0 0 5 5"/>',
        github: '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
        email: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
        phone: '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
        whatsapp: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
        website: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
        link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
        arrow: '<path d="M7 17 17 7"/><path d="M7 7h10v10"/>',
        pin: '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
        share: '<path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="m16 6-4-4-4 4"/><path d="M12 2v13"/>',
        contact: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6"/><path d="M22 11h-6"/>',
        download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
        news: '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/>'
    };

    // Bağlantı türleri — panelin açılır listesi de buradan okunur
    var TYPES = {
        instagram: { label: 'Instagram', icon: 'instagram', ph: 'https://instagram.com/kullaniciadi' },
        linkedin:  { label: 'LinkedIn',  icon: 'linkedin',  ph: 'https://linkedin.com/in/kullaniciadi' },
        x:         { label: 'X',         icon: 'x',         ph: 'https://x.com/kullaniciadi' },
        youtube:   { label: 'YouTube',   icon: 'youtube',   ph: 'https://youtube.com/@kanal' },
        tiktok:    { label: 'TikTok',    icon: 'tiktok',    ph: 'https://tiktok.com/@kullaniciadi' },
        github:    { label: 'GitHub',    icon: 'github',    ph: 'https://github.com/kullaniciadi' },
        email:     { label: 'E-posta',   icon: 'email',     ph: 'ad@ornek.com' },
        phone:     { label: 'Telefon',   icon: 'phone',     ph: '+90 5xx xxx xx xx' },
        whatsapp:  { label: 'WhatsApp',  icon: 'whatsapp',  ph: '+90 5xx xxx xx xx' },
        website:   { label: 'Web sitesi', icon: 'website',  ph: 'https://ornek.com' },
        other:     { label: 'Bağlantı',  icon: 'link',      ph: 'https://…' }
    };

    var SECTIONS = { links: 'Bağlantılar', about: 'Hakkımda', photos: 'Fotoğraflar', projects: 'Yaptığım işler', accounts: 'İş hesapları', press: 'Basında' };

    var UI = { save: 'Kişiyi kaydet', share: 'Paylaş', updated: 'Son güncelleme' };
    var MONTHS = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];

    // "2026-10-17" → "17 Ekim 2026"; başka biçim olduğu gibi kalır
    function formatDate(s) {
        var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || ''));
        return m ? (+m[3]) + ' ' + MONTHS[+m[2] - 1] + ' ' + m[1] : String(s || '');
    }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function icon(name, cls) {
        return '<svg class="' + (cls || 'pf-ic') + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + (I[name] || I.link) + '</svg>';
    }

    // Yalnızca güvenli şemalar; diğer her şey "#" olur
    function safeUrl(u) {
        u = String(u || '').trim();
        if (/^(https?:|mailto:|tel:)/i.test(u)) return u;
        // "/\evil.com" tarayıcıda "//evil.com" olur — site içi yol sayılmaz
        if (/^\/(?![\/\\])/.test(u)) return u;
        return '#';
    }

    function safeImg(u) {
        u = String(u || '').trim();
        if (/^\/(?![\/\\])/.test(u) || /^https:\/\//i.test(u) || /^(data|blob):image\//i.test(u) || /^blob:/i.test(u)) return u;
        return '';
    }

    function absolute(u) {
        return /^\//.test(u) ? SITE + u : u;
    }

    // Kullanıcının yazdığı değerden gerçek bağlantı
    function linkHref(l) {
        var v = String(l.url || '').trim();
        if (!v) return '';
        if (l.type === 'email') return /^mailto:/i.test(v) ? v : 'mailto:' + v;
        if (l.type === 'phone') return /^tel:/i.test(v) ? v : 'tel:' + v.replace(/[^\d+]/g, '');
        if (l.type === 'whatsapp' && !/^https?:/i.test(v)) return 'https://wa.me/' + v.replace(/\D/g, '');
        if (!/^(https?:|mailto:|tel:|\/)/i.test(v)) return 'https://' + v;
        return v;
    }

    // Satırdaki ikinci satır: kullanıcı adı ya da sade adres
    function linkHint(l) {
        var v = String(l.url || '').trim();
        if (l.type === 'email') return v.replace(/^mailto:/i, '');
        if (l.type === 'phone' || l.type === 'whatsapp') return v.replace(/^(tel:|https?:\/\/wa\.me\/)/i, '');
        var m = /^(?:https?:\/\/)?(?:www\.)?([^?#]+?)\/*(?:[?#].*)?$/i.exec(v);
        if (!m) return v;
        var path = m[1];
        var handle = /(?:instagram|x|twitter|tiktok|github|youtube)\.com\/(@?[^/]+)/i.exec(path);
        if (handle) return handle[1].charAt(0) === '@' ? handle[1] : '@' + handle[1];
        var li = /linkedin\.com\/(?:in|company)\/([^/]+)/i.exec(path);
        if (li) return li[1];
        return path;
    }

    function paragraphs(text) {
        return String(text || '').split(/\n\s*\n/).map(function (p) { return p.trim(); }).filter(Boolean)
            .map(function (p) { return '<p>' + esc(p).replace(/\n/g, '<br>') + '</p>'; }).join('');
    }

    function list(a) { return Array.isArray(a) ? a : []; }

    function filled(a, key) {
        return list(a).filter(function (x) { return x && String(x[key] || '').trim(); });
    }

    function pageUrl(d) { return SITE + '/' + d.slug + '/'; }

    function describe(d) {
        var text = String(d.bio || d.headline || '').replace(/\s+/g, ' ').trim();
        return text.length > 158 ? text.slice(0, 155).replace(/\s+\S*$/, '') + '…' : text;
    }

    function title(d) {
        return d.headline ? d.name + ' — ' + d.headline : d.name;
    }

    // ── <head> ───────────────────────────────────────────────
    function head(d) {
        var url = pageUrl(d);
        var img = safeImg(d.avatar) ? absolute(d.avatar) : SITE + '/assets/og-image.png';
        var links = filled(d.links, 'url').map(linkHref).filter(function (u) { return /^https:/i.test(u); });
        var ld = {
            '@context': 'https://schema.org',
            '@type': 'ProfilePage',
            '@id': url + '#page',
            url: url,
            name: title(d),
            inLanguage: d.lang || 'tr',
            dateModified: d.updated || undefined,
            mainEntity: {
                '@type': 'Person',
                '@id': d.personId || SITE + '/#' + d.slug,
                name: d.name,
                jobTitle: d.headline || undefined,
                description: describe(d) || undefined,
                image: img,
                url: url,
                homeLocation: d.location ? { '@type': 'Place', name: d.location } : undefined,
                worksFor: d.orgId ? { '@id': d.orgId } : undefined,
                sameAs: links.length ? links : undefined
            }
        };
        var json = JSON.stringify(ld, null, 2).replace(/</g, '\\u003c');
        return [
            '<title>' + esc(title(d)) + '</title>',
            '<meta name="description" content="' + esc(describe(d)) + '">',
            '<link rel="canonical" href="' + esc(url) + '">',
            '<meta property="og:type" content="profile">',
            '<meta property="og:site_name" content="Suu">',
            '<meta property="og:locale" content="tr_TR">',
            '<meta property="og:title" content="' + esc(title(d)) + '">',
            '<meta property="og:description" content="' + esc(describe(d)) + '">',
            '<meta property="og:url" content="' + esc(url) + '">',
            '<meta property="og:image" content="' + esc(img) + '">',
            '<meta name="twitter:card" content="summary">',
            '<meta name="twitter:title" content="' + esc(title(d)) + '">',
            '<meta name="twitter:description" content="' + esc(describe(d)) + '">',
            '<meta name="twitter:image" content="' + esc(img) + '">',
            '<script type="application/ld+json">\n' + json + '\n</script>'
        ].join('\n');
    }

    // ── gövde ────────────────────────────────────────────────
    function body(d, opts) {
        opts = opts || {};
        var asset = opts.asset || function (s) { return s; };
        // Boş bırakılan bölüm başlığı varsayılana döner — başlıksız bölüm kalmasın
        var sec = {};
        Object.keys(SECTIONS).forEach(function (k) {
            sec[k] = (d.sections && String(d.sections[k] || '').trim()) || SECTIONS[k];
        });
        var n = 0;                                   // giriş animasyonu sırası
        function step() { return ' style="--i:' + (n++) + '"'; }
        function ext(href) { return /^https?:/i.test(href) ? ' target="_blank" rel="noopener me"' : ''; }
        var out = [];

        out.push('<div class="pf-bg" aria-hidden="true"><span></span><span></span><span></span></div>');

        // Hero
        var avatar = safeImg(asset(d.avatar));
        out.push('<header class="pf-hero">');
        if (avatar) {
            out.push('<div class="pf-avatar pf-in"' + step() + '><span class="pf-avatar__ring"></span>' +
                '<img src="' + esc(avatar) + '" alt="' + esc(d.name) + '" width="320" height="320" fetchpriority="high"></div>');
        }
        out.push('<h1 class="pf-name pf-in"' + step() + '>' + esc(d.name) + '</h1>');
        if (d.headline) out.push('<p class="pf-headline pf-in"' + step() + '>' + esc(d.headline) + '</p>');
        if (d.location || d.status) {
            out.push('<div class="pf-chips pf-in"' + step() + '>');
            if (d.location) out.push('<span class="pf-chip">' + icon('pin') + esc(d.location) + '</span>');
            if (d.status) out.push('<span class="pf-chip pf-chip--status"><i></i>' + esc(d.status) + '</span>');
            out.push('</div>');
        }
        var cta = d.cta && d.cta.label && d.cta.url ? d.cta : null;
        out.push('<div class="pf-actions pf-in"' + step() + '>');
        if (cta) {
            var ch = safeUrl(cta.url);
            out.push('<a class="pf-btn pf-btn--primary" href="' + esc(ch) + '"' + ext(ch) + '>' + icon('download') + esc(cta.label) + '</a>');
        }
        out.push('<button type="button" class="pf-btn" data-action="vcard">' + icon('contact') + esc(UI.save) + '</button>');
        out.push('<button type="button" class="pf-btn pf-btn--icon" data-action="share" aria-label="' + esc(UI.share) + '" title="' + esc(UI.share) + '">' + icon('share') + '</button>');
        out.push('</div>');
        out.push('</header>');

        // Bağlantılar — sayfanın asıl işi; ilk ekranda görünsün diye tanıtım yazısından önce
        var links = filled(d.links, 'url');
        if (links.length) {
            out.push('<section class="pf-section" aria-label="' + esc(sec.links) + '"><ul class="pf-links">');
            links.forEach(function (l) {
                var t = TYPES[l.type] || TYPES.other;
                var href = safeUrl(linkHref(l));
                out.push('<li class="pf-in"' + step() + '><a class="pf-link pf-link--' + esc(l.type in TYPES ? l.type : 'other') + '" href="' + esc(href) + '"' + ext(href) + '>' +
                    '<span class="pf-link__icon">' + icon(t.icon) + '</span>' +
                    '<span class="pf-link__text"><b>' + esc(l.label || t.label) + '</b><small>' + esc(linkHint(l)) + '</small></span>' +
                    icon('arrow', 'pf-ic pf-link__go') + '</a></li>');
            });
            out.push('</ul></section>');
        }

        // Hakkımda + öne çıkan rakamlar
        var stats = filled(d.stats, 'value');
        if (d.bio || stats.length) {
            out.push('<section class="pf-section"><h2 class="pf-h2">' + esc(sec.about) + '</h2><div class="pf-about">');
            if (d.bio) out.push('<div class="pf-bio">' + paragraphs(d.bio) + '</div>');
            if (stats.length) {
                out.push('<ul class="pf-stats">');
                stats.forEach(function (s) {
                    out.push('<li><b>' + esc(s.value) + '</b><span>' + esc(s.label) + '</span></li>');
                });
                out.push('</ul>');
            }
            out.push('</div></section>');
        }

        // Fotoğraflar — 3 ve üstünde kayan şerit (kopya şerit ekran okuyucudan gizli)
        var photos = filled(d.photos, 'src').filter(function (p) { return safeImg(asset(p.src)); });
        if (photos.length) {
            var marquee = photos.length >= 3;
            var fig = function (p, i, dup) {
                return '<figure class="pf-photo"' + (dup ? '' : ' data-index="' + i + '"') + '>' +
                    '<img src="' + esc(safeImg(asset(p.src))) + '" alt="' + (dup ? '' : esc(p.alt || '')) + '" loading="lazy" decoding="async"></figure>';
            };
            out.push('<section class="pf-section pf-photos"><h2 class="pf-h2">' + esc(sec.photos) + '</h2>');
            out.push('<div class="pf-gallery' + (marquee ? ' pf-gallery--marquee' : '') + '" style="--n:' + photos.length + '">');
            out.push('<div class="pf-gallery__track">' + photos.map(function (p, i) { return fig(p, i, false); }).join(''));
            if (marquee) out.push('</div><div class="pf-gallery__track" aria-hidden="true">' + photos.map(function (p, i) { return fig(p, i, true); }).join(''));
            out.push('</div></div></section>');
        }

        // Yaptığım işler
        var projects = filled(d.projects, 'title');
        if (projects.length) {
            out.push('<section class="pf-section"><h2 class="pf-h2">' + esc(sec.projects) + '</h2><div class="pf-projects">');
            projects.forEach(function (p) {
                var href = p.url ? safeUrl(p.url) : '';
                var img = safeImg(asset(p.image));
                var tag = href ? 'a' : 'div';
                out.push('<' + tag + ' class="pf-project"' + (href ? ' href="' + esc(href) + '"' + ext(href) : '') + '>' +
                    (img ? '<img class="pf-project__img" src="' + esc(img) + '" alt="" loading="lazy" decoding="async">' : '<span class="pf-project__img pf-project__img--empty">' + esc(String(p.title).charAt(0)) + '</span>') +
                    '<span class="pf-project__body"><b class="pf-project__title">' + esc(p.title) + '</b>' +
                    ((p.role || p.period) ? '<small class="pf-project__meta">' + esc(p.role || '') + (p.role && p.period ? ' · ' : '') +
                        (p.period ? '<span class="pf-nowrap">' + esc(p.period) + '</span>' : '') + '</small>' : '') +
                    (p.description ? '<span class="pf-project__desc">' + esc(p.description) + '</span>' : '') +
                    '</span>' + (href ? icon('arrow', 'pf-ic pf-project__go') : '') + '</' + tag + '>');
            });
            out.push('</div></section>');
        }

        // İş hesapları
        var accounts = filled(d.accounts, 'url');
        if (accounts.length) {
            out.push('<section class="pf-section"><h2 class="pf-h2">' + esc(sec.accounts) + '</h2><ul class="pf-accounts">');
            accounts.forEach(function (a) {
                var t = TYPES[a.platform] || TYPES.website;
                var href = safeUrl(linkHref({ type: a.platform, url: a.url }));
                out.push('<li><a class="pf-account" href="' + esc(href) + '"' + ext(href) + '>' +
                    '<span class="pf-account__icon">' + icon(t.icon) + '</span>' +
                    '<span class="pf-account__text"><b>' + esc(a.name || t.label) + '</b><small>' + esc(a.handle || linkHint({ type: a.platform, url: a.url })) + '</small></span>' +
                    icon('arrow', 'pf-ic pf-account__go') + '</a></li>');
            });
            out.push('</ul></section>');
        }

        // Basında
        var press = filled(d.press, 'title');
        if (press.length) {
            out.push('<section class="pf-section"><h2 class="pf-h2">' + esc(sec.press) + '</h2><ul class="pf-press">');
            press.forEach(function (p) {
                var href = p.url ? safeUrl(p.url) : '';
                var tag = href ? 'a' : 'div';
                out.push('<li><' + tag + ' class="pf-press__item"' + (href ? ' href="' + esc(href) + '"' + ext(href) : '') + '>' +
                    '<span class="pf-press__icon">' + icon('news') + '</span>' +
                    '<span class="pf-press__text">' + (p.outlet ? '<small>' + esc(p.outlet) + (p.date ? ' · ' + esc(p.date) : '') + '</small>' : '') +
                    '<b>' + esc(p.title) + '</b></span>' + (href ? icon('arrow', 'pf-ic pf-press__go') : '') + '</' + tag + '></li>');
            });
            out.push('</ul></section>');
        }

        out.push('<footer class="pf-footer"><a href="/" class="pf-footer__brand"><img src="/assets/brand/suu-badge-128.png" alt="" width="28" height="28">suuapp.com</a>' +
            (d.updated ? '<span>' + esc(UI.updated) + ': ' + esc(formatDate(d.updated)) + '</span>' : '') + '</footer>');

        return out.join('\n');
    }

    // Sayfadaki işaretler arasını yeniden basar. İşaret yoksa hata — sayfa bozulmasın.
    var MARKS = {
        head: [/<!--profile:head-->[\s\S]*?<!--\/profile:head-->/, '<!--profile:head-->\n', '\n<!--/profile:head-->'],
        body: [/<!--profile:body-->[\s\S]*?<!--\/profile:body-->/, '<!--profile:body-->\n', '\n<!--/profile:body-->'],
        data: [/<script type="application\/json" id="profile-data">[\s\S]*?<\/script>/, '<script type="application/json" id="profile-data">\n', '\n</script>']
    };

    function readData(html) {
        var m = /<script type="application\/json" id="profile-data">([\s\S]*?)<\/script>/.exec(html);
        if (!m) throw new Error('Sayfada profil verisi bulunamadı (#profile-data).');
        return JSON.parse(m[1]);
    }

    function apply(html, d, opts) {
        var parts = {
            head: head(d),
            body: body(d, opts),
            data: JSON.stringify(d, null, 2).replace(/</g, '\\u003c')
        };
        Object.keys(MARKS).forEach(function (k) {
            var mk = MARKS[k];
            if (!mk[0].test(html)) throw new Error('Sayfa şablonunda işaret eksik: ' + k);
            html = html.replace(mk[0], function () { return mk[1] + parts[k] + mk[2]; });
        });
        return html;
    }

    return {
        TYPES: TYPES, SECTIONS: SECTIONS, ICONS: I,
        esc: esc, icon: icon, safeUrl: safeUrl, safeImg: safeImg, linkHref: linkHref, linkHint: linkHint,
        head: head, body: body, apply: apply, readData: readData, pageUrl: pageUrl
    };
});
