/* Suu — açık / koyu tema düğmesi
 *
 * suu.css koyu temayı token'larla zaten taşıyor: sistem tercihi koyuysa
 * otomatik açılır, <html data-theme="light|dark"> ise sistem tercihini ezer.
 * Bu dosya yalnızca o özniteliği değiştiren düğmeyi ekler ve seçimi
 * localStorage'da ('suu-theme') saklar.
 *
 * İlk boyamadan önce temayı uygulayan tek satırlık satır içi script her
 * sayfanın <head>'inde ayrıca durur (scripts/inject-theme-toggle.py) —
 * bu dosya defer yüklendiği için tek başına açık → koyu bir yanıp sönmeye
 * yol açardı.
 *
 * Düğme dil seçicinin (#suu-lang) hemen yanına, o yoksa .nav__actions'ın
 * başına yerleşir. Sınıfı .btn değildir: mobilde .nav__actions .btn gizlenir.
 */
(function () {
    'use strict';

    var KEY = 'suu-theme';
    var root = document.documentElement;
    var mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    var LABELS = {
        tr: ['Koyu temaya geç', 'Açık temaya geç'],
        en: ['Switch to dark mode', 'Switch to light mode'],
        ar: ['التبديل إلى الوضع الداكن', 'التبديل إلى الوضع الفاتح'],
        ru: ['Включить тёмную тему', 'Включить светлую тему'],
        de: ['Zum dunklen Modus wechseln', 'Zum hellen Modus wechseln'],
        it: ['Passa al tema scuro', 'Passa al tema chiaro'],
        uk: ['Увімкнути темну тему', 'Увімкнути світлу тему'],
        hi: ['डार्क मोड चालू करें', 'लाइट मोड चालू करें']
    };

    var MOON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
    var SUN = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><circle cx="12" cy="12" r="4.5"/><path d="M12 1.5v2.5M12 20v2.5M4.6 4.6l1.8 1.8M17.6 17.6l1.8 1.8M1.5 12H4M20 12h2.5M4.6 19.4l1.8-1.8M17.6 6.4l1.8-1.8"/></svg>';

    function stored() {
        try {
            var v = localStorage.getItem(KEY);
            return v === 'dark' || v === 'light' ? v : null;
        } catch (e) { return null; }
    }

    function current() {
        var a = root.getAttribute('data-theme');
        if (a === 'dark' || a === 'light') return a;
        return mq && mq.matches ? 'dark' : 'light';
    }

    function labels() {
        var lang = (root.getAttribute('lang') || 'en').slice(0, 2).toLowerCase();
        return LABELS[lang] || LABELS.en;
    }

    function injectStyles() {
        if (document.getElementById('suu-theme-style')) return;
        var s = document.createElement('style');
        s.id = 'suu-theme-style';
        // Dil seçicinin hap biçimiyle aynı çizgide; token yoksa açık tema değerleri
        s.textContent = [
            '#suu-theme{display:inline-flex;align-items:center;justify-content:center;flex:none;',
            '  width:34px;height:34px;padding:0;margin:0;border:1px solid var(--border,#D6DDE4);',
            '  border-radius:999px;background:var(--surface,#fff);color:var(--text,#232A33);',
            '  cursor:pointer;line-height:0;-webkit-tap-highlight-color:transparent;',
            '  transition:border-color .15s ease,background-color .15s ease,transform .15s ease}',
            '#suu-theme:hover{border-color:var(--border-strong,#B4BFCA)}',
            '#suu-theme:active{transform:scale(.94)}',
            '#suu-theme:focus-visible{outline:2px solid var(--su-500,#1E88E5);outline-offset:2px}',
            '@media (prefers-reduced-motion:reduce){#suu-theme{transition:none}#suu-theme:active{transform:none}}'
        ].join('');
        document.head.appendChild(s);
    }

    function render(btn) {
        var dark = current() === 'dark';
        var text = labels()[dark ? 1 : 0];
        btn.innerHTML = dark ? SUN : MOON;
        btn.setAttribute('aria-label', text);
        btn.setAttribute('title', text);
        btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
    }

    function apply(theme, btn) {
        root.setAttribute('data-theme', theme);
        try { localStorage.setItem(KEY, theme); } catch (e) {}
        if (btn) render(btn);
    }

    function mount(btn) {
        var lang = document.getElementById('suu-lang');
        if (lang && lang.parentNode) {
            lang.parentNode.insertBefore(btn, lang.nextSibling);
            return true;
        }
        var slot = document.querySelector('[data-lang-slot]');
        if (slot) { slot.appendChild(btn); return true; }
        var actions = document.querySelector('.nav__actions');
        if (actions) { actions.insertBefore(btn, actions.firstChild); return true; }
        return false;
    }

    function init() {
        if (document.getElementById('suu-theme')) return;

        // Satır içi script bir şekilde atlandıysa (eski önbellek vb.) burada uygula
        var saved = stored();
        if (saved && root.getAttribute('data-theme') !== saved) root.setAttribute('data-theme', saved);

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.id = 'suu-theme';
        injectStyles();
        render(btn);
        if (!mount(btn)) return;

        btn.addEventListener('click', function () {
            apply(current() === 'dark' ? 'light' : 'dark', btn);
        });

        // Elle seçim yoksa sistem değişimini izle
        if (mq) {
            var onSystem = function () { if (!stored()) render(btn); };
            if (mq.addEventListener) mq.addEventListener('change', onSystem);
            else if (mq.addListener) mq.addListener(onSystem);
        }

        // Başka sekmede değişirse bu sekme de uysun
        window.addEventListener('storage', function (e) {
            if (e.key !== KEY) return;
            if (e.newValue === 'dark' || e.newValue === 'light') root.setAttribute('data-theme', e.newValue);
            else root.removeAttribute('data-theme');
            render(btn);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
