/**
 * Suu — Header logo badge
 * Turns the round glowing brand badge in the header into the donation-tracker
 * trigger. The link keeps its href (home) so middle-click, ⌘-click and the
 * no-JS case still work; a plain click opens the donation panel instead.
 * Pages that don't ship donation-widget.js get it loaded on first click.
 * Footer logos are left alone — they stay plain home links.
 */
(function () {
    'use strict';

    var LABELS = {
        tr: 'Bağış takibini aç',
        en: 'Open donation tracker',
        de: 'Spenden-Tracker öffnen',
        it: 'Apri il tracker delle donazioni',
        ru: 'Открыть отчёт о пожертвованиях',
        ar: 'افتح متتبع التبرعات',
        hi: 'दान ट्रैकर खोलें',
        uk: 'Відкрити звіт про пожертви'
    };

    function label() {
        var code = (document.documentElement.getAttribute('lang') || 'tr').toLowerCase().slice(0, 2);
        return LABELS[code] || LABELS.tr;
    }

    // ---------- Styles (progressive: the badge already looks right without them) ----------
    var CSS = [
        '.suu-logo-badge{transition:transform .3s cubic-bezier(.2,.8,.2,1),box-shadow .3s ease}',
        '.suu-logo-badge-wrap{position:relative;display:inline-flex;line-height:0;vertical-align:-0.4em;flex:none}',
        '[data-suu-donate] .suu-logo-badge{animation:suu-badge-breathe 4.5s ease-in-out infinite}',
        '[data-suu-donate]:hover .suu-logo-badge,[data-suu-donate]:focus-visible .suu-logo-badge{transform:scale(1.07)}',
        '[data-suu-donate]:active .suu-logo-badge{transform:scale(.96)}',
        '.suu-logo-badge-heart{position:absolute;inset-inline-end:-1px;inset-block-end:-1px;width:.44em;height:.44em;',
        'border-radius:50%;background:#e8536f;display:flex;align-items:center;justify-content:center;',
        'box-shadow:0 0 0 1.5px rgba(8,12,18,.92),0 1px 4px rgba(0,0,0,.45);pointer-events:none}',
        '.suu-logo-badge-heart svg{width:62%;height:62%;fill:#fff;display:block}',
        '@keyframes suu-badge-breathe{0%,100%{box-shadow:0 0 0 1px rgba(255,255,255,.12),0 0 14px rgba(94,170,255,.42)}',
        '50%{box-shadow:0 0 0 1px rgba(255,255,255,.2),0 0 22px rgba(94,170,255,.72)}}',
        '@media (prefers-reduced-motion:reduce){',
        '.suu-logo-badge{transition:none}[data-suu-donate] .suu-logo-badge{animation:none}',
        '[data-suu-donate]:hover .suu-logo-badge,[data-suu-donate]:focus-visible .suu-logo-badge{transform:none}}'
    ].join('');

    var HEART = '<span class="suu-logo-badge-heart" aria-hidden="true">' +
        '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
        '<path d="M12 21s-7.5-4.7-9.3-9.2C1.4 8.4 3.2 5 6.6 5c2 0 3.4 1.1 4.2 2.3l1.2 1.7 1.2-1.7C14 5.1 15.4 4 17.4 4c3.4 0 5.2 3.4 3.9 6.8C19.5 15.3 12 21 12 21z"/>' +
        '</svg></span>';

    function injectStyles() {
        if (document.getElementById('suu-badge-style')) return;
        var s = document.createElement('style');
        s.id = 'suu-badge-style';
        s.textContent = CSS;
        document.head.appendChild(s);
    }

    // ---------- Opening the donation panel ----------
    var loading = false;

    function loadWidget() {
        if (loading) return;
        loading = true;
        if (!document.querySelector('link[href*="donation-widget.css"]')) {
            var link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = '/donation-widget.css?v=6';
            document.head.appendChild(link);
        }
        if (!document.querySelector('script[src*="donation-widget.js"]')) {
            var s = document.createElement('script');
            s.src = '/donation-widget.js?v=6';
            s.defer = true;
            document.body.appendChild(s);
        }
    }

    function openDonation() {
        var panel = document.getElementById('suu-donation-panel');
        if (panel && panel.classList.contains('suu-dw-open')) {
            window.SuuDonation.close(); // second click on the logo closes it again
            return;
        }
        if (window.SuuDonation && window.SuuDonation.open) {
            window.SuuDonation.open();
            return;
        }
        loadWidget();
        // The widget defines its API synchronously and queues the request until
        // donations.json lands, so we only need to wait for the script itself.
        var tries = 0;
        var timer = setInterval(function () {
            if (window.SuuDonation && window.SuuDonation.open) {
                clearInterval(timer);
                window.SuuDonation.open();
            } else if (++tries > 100) { // ~6s
                clearInterval(timer);
            }
        }, 60);
    }

    // ---------- Wire up header logos ----------
    function upgrade(img) {
        var link = img.closest ? img.closest('a') : null;
        if (!link || link.hasAttribute('data-suu-donate')) return;
        if (img.closest('footer')) return; // footer logo stays a plain home link

        if (!img.parentNode.classList.contains('suu-logo-badge-wrap')) {
            var wrap = document.createElement('span');
            wrap.className = 'suu-logo-badge-wrap';
            img.parentNode.insertBefore(wrap, img);
            wrap.appendChild(img);
            wrap.insertAdjacentHTML('beforeend', HEART);
        }

        var text = label();
        link.setAttribute('data-suu-donate', '');
        link.setAttribute('aria-label', 'Suu — ' + text);
        link.setAttribute('title', text);
        link.addEventListener('click', function (e) {
            if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
            e.preventDefault();
            e.stopPropagation(); // the widget closes the panel on outside clicks
            openDonation();
        });
    }

    function init() {
        var badges = document.querySelectorAll('img.suu-logo-badge');
        if (!badges.length) return;
        injectStyles();
        for (var i = 0; i < badges.length; i++) upgrade(badges[i]);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
