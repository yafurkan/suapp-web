/**
 * Suu — Dil seçici   [ÜRETİLMİŞ DOSYA — elle düzenlemeyin]
 *
 * Kaynak : content/lang-switcher.template.js + content/page-registry.json
 * Üretim : python3 scripts/build-i18n-map.py --apply
 *
 * Harita dosyaya gömülüdür — ek ağ isteği yoktur, tüm sitede tek önbellek.
 *
 * NOT: Otomatik yönlendirme BİLEREK yoktur. Googlebot'un tarayıcı dili EN
 * olduğu için RU/AR sayfalarına geldiğinde EN'e yönlendiriliyordu ve Search
 * Console "Yönlendirmeli sayfa" hatası veriyordu. Manuel seçim yeterli.
 */
(function () {
    'use strict';

    var I18N = __I18N_MAP__;

    var LABELS = {
        tr: { code: 'TR', name: 'Türkçe' },
        en: { code: 'EN', name: 'English' },
        ar: { code: 'AR', name: 'العربية' },
        ru: { code: 'RU', name: 'Русский' },
        de: { code: 'DE', name: 'Deutsch' },
        it: { code: 'IT', name: 'Italiano' },
        hi: { code: 'HI', name: 'हिन्दी' }
    };

    // ── Geçerli sayfa ───────────────────────────────────────
    function currentFile() {
        var parts = window.location.pathname.split('/');
        return parts[parts.length - 1] || 'index.html';
    }

    function currentLang() {
        var attr = (document.documentElement.lang || '').slice(0, 2).toLowerCase();
        return LABELS[attr] ? attr : I18N._default;
    }

    function saveLang(lang) {
        try { localStorage.setItem('suu-lang', lang); } catch (e) {}
    }

    // ── Stiller — tasarım sistemi token'ları varsa onları kullanır ──
    function injectStyles() {
        if (document.getElementById('suu-lang-style')) return;
        var s = document.createElement('style');
        s.id = 'suu-lang-style';
        s.textContent = [
            '#suu-lang{position:relative;direction:ltr;font-family:inherit}',
            '#suu-lang>summary{display:inline-flex;align-items:center;gap:6px;min-height:34px;',
            '  padding:0 10px;border:1px solid var(--border,#D6DDE4);border-radius:999px;',
            '  background:var(--surface,#fff);color:var(--text,#232A33);cursor:pointer;',
            '  font-size:12px;font-weight:700;letter-spacing:.4px;list-style:none;white-space:nowrap}',
            '#suu-lang>summary::-webkit-details-marker{display:none}',
            '#suu-lang>summary::after{content:"";width:0;height:0;margin-inline-start:2px;',
            '  border-inline:4px solid transparent;border-top:5px solid currentColor;opacity:.6}',
            '#suu-lang[open]>summary::after{transform:rotate(180deg)}',
            '#suu-lang>summary:hover{border-color:var(--border-strong,#B4BFCA)}',
            '#suu-lang-list{position:absolute;inset-inline-end:0;top:calc(100% + 6px);z-index:200;',
            '  min-width:150px;padding:6px;margin:0;list-style:none;',
            '  background:var(--surface,#fff);border:1px solid var(--border,#D6DDE4);',
            '  border-radius:10px;box-shadow:0 8px 24px rgba(11,14,19,.14)}',
            '#suu-lang-list li{margin:0}',
            '#suu-lang-list a{display:flex;align-items:center;justify-content:space-between;gap:10px;',
            '  padding:8px 10px;border-radius:6px;color:var(--text,#232A33);text-decoration:none;',
            '  font-size:13px;font-weight:500;white-space:nowrap}',
            '#suu-lang-list a:hover{background:var(--bg-subtle,#F4F6F8)}',
            '#suu-lang-list a[aria-current="true"]{color:var(--text-brand,#1565C0);font-weight:700}',
            '#suu-lang-list .c{font-size:11px;font-weight:700;opacity:.55;letter-spacing:.4px}',
            '@media (max-width:480px){#suu-lang>summary{padding:0 8px;font-size:11px}}'
        ].join('');
        document.head.appendChild(s);
    }

    // ── Bileşen ─────────────────────────────────────────────
    function build(variants, active) {
        var root = document.createElement('details');
        root.id = 'suu-lang';

        var summary = document.createElement('summary');
        summary.setAttribute('aria-label', 'Dil / Language');
        summary.appendChild(document.createTextNode(LABELS[active] ? LABELS[active].code : active.toUpperCase()));
        root.appendChild(summary);

        var list = document.createElement('ul');
        list.id = 'suu-lang-list';

        I18N._langs.forEach(function (lang) {
            var href = variants[lang];
            if (!href || !LABELS[lang]) return;

            var li = document.createElement('li');
            var a = document.createElement('a');
            a.href = href;
            a.hreflang = lang;
            a.lang = lang;
            if (lang === active) a.setAttribute('aria-current', 'true');

            var name = document.createElement('span');
            name.textContent = LABELS[lang].name;
            var code = document.createElement('span');
            code.className = 'c';
            code.textContent = LABELS[lang].code;

            a.appendChild(name);
            a.appendChild(code);
            a.addEventListener('click', function () { saveLang(lang); });

            li.appendChild(a);
            list.appendChild(li);
        });

        root.appendChild(list);

        // Dışarı tıklayınca kapat
        document.addEventListener('click', function (e) {
            if (root.open && !root.contains(e.target)) root.open = false;
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && root.open) { root.open = false; summary.focus(); }
        });

        return root;
    }

    // ── Yerleştirme — yeni tasarım sistemi önce, eski yapılar sonra ──
    function mount(node) {
        var slot = document.querySelector('[data-lang-slot]');
        if (slot) { slot.appendChild(node); return true; }

        var actions = document.querySelector('.nav__actions');
        if (actions) { actions.insertBefore(node, actions.firstChild); return true; }

        var hamburger = document.querySelector('.hamburger');
        if (hamburger && hamburger.parentNode) {
            hamburger.parentNode.insertBefore(node, hamburger);
            return true;
        }

        var navContent = document.querySelector('.nav-content');
        if (navContent) {
            var back = navContent.querySelector('.back-btn');
            if (back) navContent.insertBefore(node, back);
            else navContent.appendChild(node);
            return true;
        }

        var nav = document.querySelector('nav') || document.querySelector('.nav');
        if (nav) {
            node.style.marginInlineStart = 'auto';
            nav.appendChild(node);
            return true;
        }
        return false;
    }

    function init() {
        if (document.getElementById('suu-lang')) return;

        var file = currentFile();

        // Tek URL üzerinde sekmeli çok dil sunan sayfalarda seçici gösterilmez
        if (I18N._shared.indexOf(file) !== -1) return;

        var variants = I18N.pages[file];
        if (!variants) return;                 // haritada yoksa bozuk buton gösterme

        var available = I18N._langs.filter(function (l) { return variants[l]; });
        if (available.length < 2) return;      // tek dilli sayfada seçici anlamsız

        injectStyles();
        mount(build(variants, currentLang()));
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
