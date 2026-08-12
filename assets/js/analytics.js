/**
 * Suu — Birleşik ölçüm katmanı
 *
 * Tek dosya, tüm sayfalar. Şunları yapar:
 *   1. Microsoft Clarity'yi yükler (ısı haritası + oturum kaydı)
 *   2. GA4'ü yükler — SADECE geçerli bir ölçüm ID'si tanımlıysa
 *   3. Tüm indirme/CTA tıklamalarını otomatik olay olarak gönderir
 *   4. /app bağlantılarına eksikse ?src= yerleşim parametresini ekler
 *
 * KURULUM: Aşağıdaki GA4_ID'ye gerçek ölçüm kimliğini yazın (G-XXXXXXXXXX).
 * Boş bırakıldığı sürece GA4 hiç yüklenmez — ölü placeholder isteği atılmaz.
 */
(function () {
    'use strict';

    // ── Yapılandırma ────────────────────────────────────────
    var GA4_ID = '';                 // ← GA4 ölçüm ID'si buraya (G-XXXXXXXXXX)
    var CLARITY_ID = 'tabxahhw7s';   // Microsoft Clarity proje kimliği

    var STORE_HOSTS = {
        'apps.apple.com': 'app_store',
        'itunes.apple.com': 'app_store',
        'play.google.com': 'google_play'
    };

    // ── Clarity ─────────────────────────────────────────────
    function loadClarity(id) {
        if (!id || window.clarity) return;
        (function (c, l, a, r, i, t, y) {
            c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
            t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i;
            y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
        })(window, document, 'clarity', 'script', id);
    }

    // ── GA4 ─────────────────────────────────────────────────
    function loadGa4(id) {
        if (!/^G-[A-Z0-9]{6,}$/.test(id)) return false;   // placeholder'ı yükleme
        var s = document.createElement('script');
        s.async = true;
        s.src = 'https://www.googletagmanager.com/gtag/js?id=' + id;
        document.head.appendChild(s);

        window.dataLayer = window.dataLayer || [];
        window.gtag = function () { window.dataLayer.push(arguments); };
        window.gtag('js', new Date());
        window.gtag('config', id);
        return true;
    }

    // ── Olay gönderimi ──────────────────────────────────────
    function track(name, params) {
        if (typeof window.gtag === 'function') window.gtag('event', name, params);
        if (typeof window.clarity === 'function') {
            window.clarity('event', name);
            // Clarity'de filtrelenebilmesi için en ayırt edici alanı etiketle
            if (params && params.placement) window.clarity('set', name, params.placement);
        }
    }

    // ── Yardımcılar ─────────────────────────────────────────
    function pageLang() {
        return (document.documentElement.lang || 'tr').slice(0, 2).toLowerCase();
    }

    function storeOf(href) {
        try {
            var host = new URL(href, window.location.href).hostname.replace(/^www\./, '');
            return STORE_HOSTS[host] || null;
        } catch (e) {
            return null;
        }
    }

    function isDownloadRedirect(href) {
        try {
            var u = new URL(href, window.location.href);
            return u.hostname === window.location.hostname &&
                   /^\/app\/?(index\.html)?$/.test(u.pathname);
        } catch (e) {
            return false;
        }
    }

    /**
     * Yerleşimi belirler. Öncelik sırası:
     *   1. data-cta="hero" gibi açık işaret
     *   2. En yakın id'li <section>
     *   3. 'unknown'
     */
    function placementOf(el) {
        var explicit = el.closest('[data-cta]');
        if (explicit) return explicit.getAttribute('data-cta');

        var section = el.closest('section[id], [data-section]');
        if (section) return section.getAttribute('data-section') || section.id;

        return 'unknown';
    }

    // ── CTA tıklama dinleyicisi ─────────────────────────────
    function onClick(event) {
        var link = event.target.closest('a[href]');
        if (!link) return;

        var href = link.getAttribute('href');
        if (!href) return;

        var store = storeOf(href);
        var redirect = isDownloadRedirect(href);
        if (!store && !redirect) return;

        var placement = placementOf(link);

        // /app bağlantısına yerleşim parametresini ekle (yoksa)
        if (redirect && placement !== 'unknown' && href.indexOf('src=') === -1) {
            link.setAttribute('href', href + (href.indexOf('?') === -1 ? '?' : '&') + 'src=' + encodeURIComponent(placement));
        }

        track('cta_click', {
            placement: placement,
            store: store || 'redirect',
            lang: pageLang(),
            page: window.location.pathname
        });
    }

    // ── Başlat ──────────────────────────────────────────────
    loadClarity(CLARITY_ID);
    var gaReady = loadGa4(GA4_ID);

    document.addEventListener('click', onClick, { passive: true });

    // Kurulum eksikse konsolda tek satır hatırlatma (kullanıcıyı rahatsız etmez)
    if (!gaReady && GA4_ID) {
        console.warn('[Suu] GA4 ölçüm ID geçersiz, yüklenmedi:', GA4_ID);
    }

    // Hata ayıklama için dışa aç
    window.suuTrack = track;
})();
