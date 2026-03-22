/**
 * Suu - Language Switcher
 * Detects browser language, redirects to appropriate page,
 * and injects TR/EN/AR switcher buttons into the navbar.
 */
(function () {
    'use strict';

    // Page map: current filename → language variants
    var PAGE_MAP = {
        'hosgeldiniz.html': { tr: 'hosgeldiniz.html', en: 'hosgeldiniz-en.html', ar: 'hosgeldiniz-ar.html' },
        'ozellikler.html':  { tr: 'ozellikler.html',  en: 'hosgeldiniz-en.html', ar: 'hosgeldiniz-ar.html' },
        'faq.html':         { tr: 'faq.html',          en: 'hosgeldiniz-en.html', ar: 'hosgeldiniz-ar.html' },
        'blog.html':        { tr: 'blog.html',          en: 'blog-en.html',        ar: 'blog-ar.html' },
        'hosgeldiniz-en.html': { tr: 'hosgeldiniz.html', en: 'hosgeldiniz-en.html', ar: 'hosgeldiniz-ar.html' },
        'hosgeldiniz-ar.html': { tr: 'hosgeldiniz.html', en: 'hosgeldiniz-en.html', ar: 'hosgeldiniz-ar.html' },
        'blog-en.html':     { tr: 'blog.html',          en: 'blog-en.html',        ar: 'blog-ar.html' },
        'blog-ar.html':     { tr: 'blog.html',          en: 'blog-en.html',        ar: 'blog-ar.html' },
        'hakkimizda.html':  { tr: 'hakkimizda.html',    en: 'about.html',          ar: 'hakkimizda-ar.html' },
        'about.html':       { tr: 'hakkimizda.html',    en: 'about.html',          ar: 'hakkimizda-ar.html' },
        'hakkimizda-ar.html': { tr: 'hakkimizda.html',  en: 'about.html',          ar: 'hakkimizda-ar.html' },
        // Blog post cross-language mappings (TR ↔ EN ↔ AR) — absolute paths from root
        'su-icmenin-faydalari.html':              { tr: '/blog/su-icmenin-faydalari.html',              en: '/blog/en/benefits-of-drinking-water.html',  ar: '/blog/ar/fawaid-shurb-almae.html' },
        'benefits-of-drinking-water.html':        { tr: '/blog/su-icmenin-faydalari.html',              en: '/blog/en/benefits-of-drinking-water.html',  ar: '/blog/ar/fawaid-shurb-almae.html' },
        'fawaid-shurb-almae.html':                { tr: '/blog/su-icmenin-faydalari.html',              en: '/blog/en/benefits-of-drinking-water.html',  ar: '/blog/ar/fawaid-shurb-almae.html' },
        'gunluk-ne-kadar-su-icmeli.html':         { tr: '/blog/gunluk-ne-kadar-su-icmeli.html',        en: '/blog/en/how-much-water-should-i-drink.html', ar: '/blog/ar/kam-litr-mae-yawmiyan.html' },
        'how-much-water-should-i-drink.html':     { tr: '/blog/gunluk-ne-kadar-su-icmeli.html',        en: '/blog/en/how-much-water-should-i-drink.html', ar: '/blog/ar/kam-litr-mae-yawmiyan.html' },
        'kam-litr-mae-yawmiyan.html':             { tr: '/blog/gunluk-ne-kadar-su-icmeli.html',        en: '/blog/en/how-much-water-should-i-drink.html', ar: '/blog/ar/kam-litr-mae-yawmiyan.html' },
        'su-takip-uygulamasi-neden-kullanmaliyim.html': { tr: '/blog/su-takip-uygulamasi-neden-kullanmaliyim.html', en: '/blog/en/best-water-tracking-app.html', ar: '/blog/ar/afdal-tatbiq-mae.html' },
        'best-water-tracking-app.html':           { tr: '/blog/su-takip-uygulamasi-neden-kullanmaliyim.html', en: '/blog/en/best-water-tracking-app.html', ar: '/blog/ar/afdal-tatbiq-mae.html' },
        'afdal-tatbiq-mae.html':                  { tr: '/blog/su-takip-uygulamasi-neden-kullanmaliyim.html', en: '/blog/en/best-water-tracking-app.html', ar: '/blog/ar/afdal-tatbiq-mae.html' },
        'su-icme-aliskanlik.html':                { tr: '/blog/su-icme-aliskanlik.html',                en: '/blog/en/water-drinking-habits.html',       ar: '/blog/ar/adat-shurb-almae.html' },
        'water-drinking-habits.html':             { tr: '/blog/su-icme-aliskanlik.html',                en: '/blog/en/water-drinking-habits.html',       ar: '/blog/ar/adat-shurb-almae.html' },
        'adat-shurb-almae.html':                  { tr: '/blog/su-icme-aliskanlik.html',                en: '/blog/en/water-drinking-habits.html',       ar: '/blog/ar/adat-shurb-almae.html' },
        'spor-ve-hidrasyon.html':                 { tr: '/blog/spor-ve-hidrasyon.html',                 en: '/blog/en/hydration-and-exercise.html',      ar: '/blog/ar/arriyada-waltartib.html' },
        'hydration-and-exercise.html':            { tr: '/blog/spor-ve-hidrasyon.html',                 en: '/blog/en/hydration-and-exercise.html',      ar: '/blog/ar/arriyada-waltartib.html' },
        'arriyada-waltartib.html':                { tr: '/blog/spor-ve-hidrasyon.html',                 en: '/blog/en/hydration-and-exercise.html',      ar: '/blog/ar/arriyada-waltartib.html' },
        'kahve-cay-su-sayar-mi.html':             { tr: '/blog/kahve-cay-su-sayar-mi.html',             en: '/blog/en/coffee-tea-hydration.html',        ar: '/blog/ar/alqahwa-walshay-walmae.html' },
        'coffee-tea-hydration.html':              { tr: '/blog/kahve-cay-su-sayar-mi.html',             en: '/blog/en/coffee-tea-hydration.html',        ar: '/blog/ar/alqahwa-walshay-walmae.html' },
        'alqahwa-walshay-walmae.html':            { tr: '/blog/kahve-cay-su-sayar-mi.html',             en: '/blog/en/coffee-tea-hydration.html',        ar: '/blog/ar/alqahwa-walshay-walmae.html' },
        'susuzluk-belirtileri.html':              { tr: '/blog/susuzluk-belirtileri.html',              en: '/blog/en/signs-of-dehydration.html',        ar: '/blog/ar/alamat-aljafaf.html' },
        'signs-of-dehydration.html':              { tr: '/blog/susuzluk-belirtileri.html',              en: '/blog/en/signs-of-dehydration.html',        ar: '/blog/ar/alamat-aljafaf.html' },
        'alamat-aljafaf.html':                    { tr: '/blog/susuzluk-belirtileri.html',              en: '/blog/en/signs-of-dehydration.html',        ar: '/blog/ar/alamat-aljafaf.html' },
        'sabah-su-icmenin-faydalari.html':        { tr: '/blog/sabah-su-icmenin-faydalari.html',        en: '/blog/en/morning-water-benefits.html',      ar: '/blog/ar/fawaid-shurb-almae-sabahan.html' },
        'morning-water-benefits.html':            { tr: '/blog/sabah-su-icmenin-faydalari.html',        en: '/blog/en/morning-water-benefits.html',      ar: '/blog/ar/fawaid-shurb-almae-sabahan.html' },
        'fawaid-shurb-almae-sabahan.html':        { tr: '/blog/sabah-su-icmenin-faydalari.html',        en: '/blog/en/morning-water-benefits.html',      ar: '/blog/ar/fawaid-shurb-almae-sabahan.html' },
        'kilo-ve-su.html':                        { tr: '/blog/kilo-ve-su.html',                        en: '/blog/en/water-and-weight-loss.html',        ar: '/blog/ar/almae-walidara-alwazn.html' },
        'water-and-weight-loss.html':             { tr: '/blog/kilo-ve-su.html',                        en: '/blog/en/water-and-weight-loss.html',        ar: '/blog/ar/almae-walidara-alwazn.html' },
        'almae-walidara-alwazn.html':             { tr: '/blog/kilo-ve-su.html',                        en: '/blog/en/water-and-weight-loss.html',        ar: '/blog/ar/almae-walidara-alwazn.html' },
        'su-ve-cilt-sagligi.html':                { tr: '/blog/su-ve-cilt-sagligi.html',                en: '/blog/en/water-and-skin-health.html',       ar: '/blog/ar/almae-walsihha-aljildiyya.html' },
        'water-and-skin-health.html':             { tr: '/blog/su-ve-cilt-sagligi.html',                en: '/blog/en/water-and-skin-health.html',       ar: '/blog/ar/almae-walsihha-aljildiyya.html' },
        'almae-walsihha-aljildiyya.html':         { tr: '/blog/su-ve-cilt-sagligi.html',                en: '/blog/en/water-and-skin-health.html',       ar: '/blog/ar/almae-walsihha-aljildiyya.html' },
        'su-ve-uyku-kalitesi.html':               { tr: '/blog/su-ve-uyku-kalitesi.html',               en: '/blog/en/water-and-sleep.html',              ar: '/blog/ar/almae-wannawm.html' },
        'water-and-sleep.html':                   { tr: '/blog/su-ve-uyku-kalitesi.html',               en: '/blog/en/water-and-sleep.html',              ar: '/blog/ar/almae-wannawm.html' },
        'almae-wannawm.html':                     { tr: '/blog/su-ve-uyku-kalitesi.html',               en: '/blog/en/water-and-sleep.html',              ar: '/blog/ar/almae-wannawm.html' },
        'su-ve-bobrek-sagligi.html':              { tr: '/blog/su-ve-bobrek-sagligi.html',              en: '/blog/en/water-and-kidney-health.html',     ar: '/blog/ar/almae-wasihhat-alkulaa.html' },
        'water-and-kidney-health.html':           { tr: '/blog/su-ve-bobrek-sagligi.html',              en: '/blog/en/water-and-kidney-health.html',     ar: '/blog/ar/almae-wasihhat-alkulaa.html' },
        'almae-wasihhat-alkulaa.html':            { tr: '/blog/su-ve-bobrek-sagligi.html',              en: '/blog/en/water-and-kidney-health.html',     ar: '/blog/ar/almae-wasihhat-alkulaa.html' },
    };

    function getCurrentPage() {
        var path = window.location.pathname;
        var parts = path.split('/');
        return parts[parts.length - 1] || 'index.html';
    }

    function getSavedLang() {
        try { return localStorage.getItem('suu-lang'); } catch (e) { return null; }
    }

    function saveLang(lang) {
        try { localStorage.setItem('suu-lang', lang); } catch (e) {}
    }

    function detectBrowserLang() {
        var langs = (navigator.languages && navigator.languages.length)
            ? navigator.languages
            : [navigator.language || 'tr'];
        for (var i = 0; i < langs.length; i++) {
            var code = langs[i].toLowerCase().slice(0, 2);
            if (code === 'ar') return 'ar';
            if (code === 'en') return 'en';
            if (code === 'tr') return 'tr';
        }
        return 'tr';
    }

    function getCurrentLang() {
        var saved = getSavedLang();
        return saved || detectBrowserLang();
    }

    function getTargetUrl(lang) {
        var page = getCurrentPage();
        var map = PAGE_MAP[page];
        if (!map) return null;
        return map[lang] || null;
    }

    function isCurrentUrl(url) {
        if (!url) return false;
        var page = getCurrentPage();
        // Check if the URL ends with the current filename
        return url === page || url.split('/').pop() === page;
    }

    function setLang(lang) {
        saveLang(lang);
        var url = getTargetUrl(lang);
        if (url && !isCurrentUrl(url)) {
            window.location.href = url;
        } else if (url) {
            // Already on the right page, just update the switcher UI
            updateSwitcherUI(lang);
        }
    }

    // Expose setLang globally for onclick handlers
    window.suuSetLang = setLang;

    function updateSwitcherUI(lang) {
        var btns = document.querySelectorAll('.suu-lang-btn');
        for (var i = 0; i < btns.length; i++) {
            var btn = btns[i];
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    }

    function injectStyles() {
        if (document.getElementById('suu-lang-style')) return;
        var style = document.createElement('style');
        style.id = 'suu-lang-style';
        style.textContent = [
            '#suu-lang-switcher {',
            '  display: flex;',
            '  align-items: center;',
            '  gap: 4px;',
            '  direction: ltr;',
            '  margin-left: 12px;',
            '}',
            '.suu-lang-btn {',
            '  background: transparent;',
            '  border: 1px solid rgba(74,144,217,0.5);',
            '  color: #4A90D9;',
            '  border-radius: 5px;',
            '  padding: 4px 9px;',
            '  font-size: 11px;',
            '  font-weight: 700;',
            '  cursor: pointer;',
            '  transition: all 0.2s;',
            '  letter-spacing: 0.5px;',
            '  font-family: inherit;',
            '  line-height: 1.4;',
            '}',
            '.suu-lang-btn:hover,',
            '.suu-lang-btn.active {',
            '  background: #4A90D9;',
            '  border-color: #4A90D9;',
            '  color: white;',
            '}',
            /* Dark navbar support */
            '.navbar .suu-lang-btn {',
            '  border-color: rgba(255,255,255,0.4);',
            '  color: rgba(255,255,255,0.85);',
            '}',
            '.navbar .suu-lang-btn:hover,',
            '.navbar .suu-lang-btn.active {',
            '  background: rgba(255,255,255,0.25);',
            '  border-color: white;',
            '  color: white;',
            '}',
            '@media (max-width: 768px) {',
            '  #suu-lang-switcher { margin-left: 8px; }',
            '  .suu-lang-btn { padding: 3px 7px; font-size: 10px; }',
            '}',
        ].join('\n');
        document.head.appendChild(style);
    }

    function createSwitcher(currentLang) {
        var div = document.createElement('div');
        div.id = 'suu-lang-switcher';
        var langs = [
            { code: 'tr', label: 'TR' },
            { code: 'en', label: 'EN' },
            { code: 'ar', label: 'AR' },
        ];
        langs.forEach(function (l) {
            var btn = document.createElement('button');
            btn.className = 'suu-lang-btn' + (l.code === currentLang ? ' active' : '');
            btn.setAttribute('data-lang', l.code);
            btn.textContent = l.label;
            btn.setAttribute('aria-label', l.label);
            btn.onclick = function () { setLang(l.code); };
            div.appendChild(btn);
        });
        return div;
    }

    function injectSwitcher(currentLang) {
        if (document.getElementById('suu-lang-switcher')) return;

        // Try main site navbar first (hosgeldiniz, ozellikler, faq)
        var hamburger = document.querySelector('.hamburger');
        if (hamburger && hamburger.parentNode) {
            hamburger.parentNode.insertBefore(createSwitcher(currentLang), hamburger);
            return;
        }

        // Try blog.html nav
        var navContent = document.querySelector('.nav-content');
        if (navContent) {
            var backBtn = navContent.querySelector('.back-btn');
            if (backBtn) {
                navContent.insertBefore(createSwitcher(currentLang), backBtn);
            } else {
                navContent.appendChild(createSwitcher(currentLang));
            }
            return;
        }

        // Fallback: any nav container
        var nav = document.querySelector('nav') || document.querySelector('.nav');
        if (nav) {
            nav.appendChild(createSwitcher(currentLang));
        }
    }

    function autoRedirect(currentLang) {
        // Only redirect once per session to avoid loops
        if (sessionStorage.getItem('suu-redirected')) return;
        if (getSavedLang()) return; // User already chose manually — respect their choice

        var page = getCurrentPage();
        var map = PAGE_MAP[page];
        if (!map) return;

        var target = map[currentLang];
        if (target && target !== page) {
            sessionStorage.setItem('suu-redirected', '1');
            window.location.replace(target);
        }
    }

    function init() {
        var currentLang = getCurrentLang();
        // Mark session so we don't loop
        autoRedirect(currentLang);
        injectStyles();
        injectSwitcher(currentLang);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
