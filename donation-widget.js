/**
 * Suu — Donation Tracker Widget
 * Floating FAB + glassmorphism panel showing live donation progress.
 * Reads data from /donations.json — percentages only, no money figures:
 * amounts live in the local ledger (donations.private.json) and are turned
 * into percentages by scripts/build-donations.py.
 * Multilingual (TR/EN/AR/DE/IT/RU/HI) — syncs with lang-switcher.js via localStorage.
 */
(function () {
    'use strict';

    var DATA_URL = '/donations.json';
    var STORAGE_KEY = 'suu-lang';

    // ---------- Language detection (mirrors lang-switcher.js) ----------
    function detectLang() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved && ['tr', 'en', 'ar', 'ru', 'de', 'it', 'hi'].indexOf(saved) !== -1) return saved;
        } catch (e) {}
        // Fallback: <html lang="..."> attribute
        var htmlLang = (document.documentElement.getAttribute('lang') || '').toLowerCase().slice(0, 2);
        if (['tr', 'en', 'ar', 'ru', 'de', 'it', 'hi'].indexOf(htmlLang) !== -1) return htmlLang;
        // Final fallback: browser
        var navs = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || 'tr'];
        for (var i = 0; i < navs.length; i++) {
            var code = navs[i].toLowerCase().slice(0, 2);
            if (['tr', 'en', 'ar', 'ru', 'de', 'it', 'hi'].indexOf(code) !== -1) return code;
        }
        return 'tr';
    }

    function isRTL(lang) { return lang === 'ar'; }

    // ---------- Percent formatting ----------
    // No money anywhere: donations.json ships percentages only.
    var LOCALES = {
        tr: 'tr-TR', en: 'en-US', ru: 'ru-RU',
        ar: 'ar-SA', de: 'de-DE', it: 'it-IT', hi: 'hi-IN'
    };

    function formatPercent(value, lang, decimals) {
        var p = Number(value) || 0;
        var locale = LOCALES[lang] || 'tr-TR';
        try {
            return new Intl.NumberFormat(locale, {
                style: 'percent',
                maximumFractionDigits: decimals || 0
            }).format(p / 100);
        } catch (e) {
            return p + '%';
        }
    }

    // Under 1% a whole number would read as "0%" — show one decimal instead.
    function percentDecimals(pct) { return (pct > 0 && pct < 1) ? 1 : 0; }

    function prefersReducedMotion() {
        try {
            return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
        } catch (e) { return false; }
    }

    function formatDate(isoDate, lang) {
        if (!isoDate) return '';
        var parts = isoDate.split('-');
        if (parts.length < 2) return isoDate;
        var year = parts[0];
        var month = parseInt(parts[1], 10) - 1;
        var months = {
            tr: ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'],
            en: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
            ru: ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек'],
            ar: ['ينا', 'فبر', 'مار', 'أبر', 'ماي', 'يون', 'يول', 'أغس', 'سبت', 'أكت', 'نوف', 'ديس']
        }[lang] || ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        if (month < 0 || month > 11) return isoDate;
        return months[month] + ' ' + year;
    }

    // ---------- DOM building ----------
    function buildFab(t, pctStr) {
        var btn = document.createElement('button');
        var teaser = t.fabLabel + (pctStr ? ' · ' + pctStr : '');
        btn.id = 'suu-donation-fab';
        btn.setAttribute('aria-label', teaser);
        btn.setAttribute('title', teaser);
        btn.innerHTML = (
            '<span class="suu-dw-fab-icon">' +
              '<svg class="suu-dw-fab-drop" viewBox="0 0 28 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
                '<defs>' +
                  '<linearGradient id="suu-fab-grad" x1="0" y1="0" x2="0" y2="1">' +
                    '<stop offset="0%" stop-color="#6FB3FF"/>' +
                    '<stop offset="100%" stop-color="#2E6FB8"/>' +
                  '</linearGradient>' +
                '</defs>' +
                '<path d="M14 1 C14 1 2 14 2 22 a12 12 0 0 0 24 0 C26 14 14 1 14 1 Z" fill="url(#suu-fab-grad)"/>' +
                '<ellipse cx="10" cy="18" rx="2.4" ry="3.4" fill="rgba(255,255,255,0.45)"/>' +
              '</svg>' +
              // Heart badge: says "this is charity", without saying "money".
              '<span class="suu-dw-fab-badge" aria-hidden="true">' +
                '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">' +
                  '<path d="M12 21s-7.5-4.7-9.3-9.2C1.4 8.4 3.2 5 6.6 5c2 0 3.4 1.1 4.2 2.3l1.2 1.7 1.2-1.7C14 5.1 15.4 4 17.4 4c3.4 0 5.2 3.4 3.9 6.8C19.5 15.3 12 21 12 21z" fill="#e8536f"/>' +
                '</svg>' +
              '</span>' +
            '</span>' +
            '<span class="suu-dw-fab-text">' + escapeHtml(teaser) + '</span>'
        );
        return btn;
    }

    function buildPanel(t, data, lang) {
        var panel = document.createElement('div');
        panel.id = 'suu-donation-panel';
        panel.setAttribute('role', 'dialog');
        panel.setAttribute('aria-labelledby', 'suu-dw-title');
        panel.setAttribute('aria-hidden', 'true');
        if (isRTL(lang)) panel.setAttribute('dir', 'rtl');

        var pct = Math.max(0, Math.min(100, Number(data.progressPercent) || 0));
        var pctStr = formatPercent(pct, lang, percentDecimals(pct));

        panel.innerHTML = (
            '<div class="suu-dw-header">' +
              '<div class="suu-dw-header-text">' +
                '<h3 class="suu-dw-title" id="suu-dw-title">' + escapeHtml(t.title) + '</h3>' +
                '<p class="suu-dw-subtitle">' + escapeHtml(t.subtitle) + '</p>' +
              '</div>' +
              '<button class="suu-dw-close" aria-label="' + escapeAttr(t.close) + '" type="button">×</button>' +
            '</div>' +

            '<div class="suu-dw-main">' +
              // Liquid-glass capsule: the fill slides in on open, the number
              // counts up with it. Pure CSS/DOM — no SVG, no library.
              '<div class="suu-dw-progress-wrap">' +
                '<div class="suu-dw-percent">' + pctStr + '</div>' +
                '<div class="suu-dw-capsule" role="img" aria-label="' +
                    escapeAttr(t.progressLabel + ': ' + pctStr) + '">' +
                  '<div class="suu-dw-liquid">' +
                    '<span class="suu-dw-liquid-flow" aria-hidden="true"></span>' +
                    '<span class="suu-dw-meniscus" aria-hidden="true"></span>' +
                  '</div>' +
                  '<span class="suu-dw-sheen" aria-hidden="true"></span>' +
                '</div>' +
                '<div class="suu-dw-progress-row">' +
                  '<strong>' + escapeHtml(t.progressLabel) + '</strong>' +
                  (t.goalNote ? '<span>' + escapeHtml(t.goalNote) + '</span>' : '') +
                '</div>' +
              '</div>' +

              '<div class="suu-dw-actions">' +
                '<button class="suu-dw-btn suu-dw-btn-secondary suu-dw-receipts-toggle" type="button">' +
                  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
                    '<path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>' +
                    '<path d="M14 2v6h6M8 13h8M8 17h5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>' +
                  '</svg>' +
                  escapeHtml(t.receiptsBtn) +
                  ' (' + (data.receipts ? data.receipts.length : 0) + ')' +
                '</button>' +
              '</div>' +

              '<div class="suu-dw-footer">' +
                escapeHtml(t.transparencyNote) +
                // The separator travels with the date, so a narrow screen never
                // strands a lone "·" at the end of a line.
                (data.lastUpdated
                  ? ' <span class="suu-dw-nowrap">· ' + escapeHtml(t.lastUpdated) + ': ' +
                    escapeHtml(data.lastUpdated) + '</span>'
                  : '') +
              '</div>' +
            '</div>' +

            '<div class="suu-dw-receipts">' +
              '<div class="suu-dw-receipts-header">' +
                '<button class="suu-dw-back-btn" aria-label="' + escapeAttr(t.close) + '" type="button">←</button>' +
                '<span class="suu-dw-receipts-title">' + escapeHtml(t.receiptsTitle) + '</span>' +
              '</div>' +
              renderReceiptList(data.receipts, t, lang) +
            '</div>'
        );

        return panel;
    }

    function renderReceiptList(receipts, t, lang) {
        if (!receipts || !receipts.length) {
            return '<div class="suu-dw-no-receipts">' + escapeHtml(t.noReceipts) + '</div>';
        }
        // Sort newest first
        var sorted = receipts.slice().sort(function (a, b) {
            return (b.date || '').localeCompare(a.date || '');
        });
        var html = '<ul class="suu-dw-receipt-list">';
        for (var i = 0; i < sorted.length; i++) {
            var r = sorted[i];
            var charity = escapeHtml(r.charity || '');
            var date = escapeHtml(formatDate(r.date, lang));
            var share = (r.sharePercent != null) ? '+' + formatPercent(r.sharePercent, lang, 1) : '';
            var url = r.url ? escapeAttr(r.url) : '';
            html += '<li class="suu-dw-receipt-item">' +
                      '<div class="suu-dw-receipt-meta">' +
                        '<span class="suu-dw-receipt-charity">' + charity + '</span>' +
                        '<span class="suu-dw-receipt-date">' + date + '</span>' +
                      '</div>' +
                      (share ? '<span class="suu-dw-receipt-share" title="' + escapeAttr(t.shareLabel || '') + '">' + share + '</span>' : '') +
                      (url ? '<a class="suu-dw-receipt-link" href="' + url + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(t.view) + '</a>' : '') +
                    '</li>';
        }
        html += '</ul>';
        return html;
    }

    // ---------- Utilities ----------
    function escapeHtml(s) {
        if (s == null) return '';
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function escapeAttr(s) { return escapeHtml(s); }

    // ---------- Progress animation ----------
    // Runs every time the panel opens: the liquid slides in from empty and the
    // number counts up on the same easing curve, so they land together.
    var FILL_DURATION = 1400;

    function playProgress(panel, pct, lang) {
        var liquid = panel.querySelector('.suu-dw-liquid');
        var label = panel.querySelector('.suu-dw-percent');
        var decimals = percentDecimals(pct);
        var target = formatPercent(pct, lang, decimals);

        if (prefersReducedMotion() || !window.requestAnimationFrame) {
            if (liquid) liquid.style.width = pct + '%';
            if (label) label.textContent = target;
            return;
        }

        if (liquid) {
            liquid.style.width = '0%';
            // Reading a layout property flushes the reset, so the transition
            // restarts on every open instead of being collapsed into one frame.
            void liquid.offsetWidth;
            liquid.style.width = pct + '%';
        }

        if (!label) return;
        label.textContent = formatPercent(0, lang, decimals);
        var started = null;
        function step(now) {
            if (started === null) started = now;
            var p = Math.min(1, (now - started) / FILL_DURATION);
            // easeOutCubic — the CSS cubic-bezier(0.22, 1, 0.36, 1) twin.
            var eased = 1 - Math.pow(1 - p, 3);
            label.textContent = formatPercent(pct * eased, lang, decimals);
            if (p < 1) window.requestAnimationFrame(step);
            else label.textContent = target;
        }
        window.requestAnimationFrame(step);
    }

    // ---------- FAB teaser ----------
    // The drop alone doesn't say what it opens. Once per session the button
    // widens into a pill ("Bağış Takibi · %9") and settles back, so the offer
    // is legible without shouting money at anyone.
    var TEASER_KEY = 'suu-dw-teased';
    var TEASER_DELAY = 900;
    var TEASER_HOLD = 4200;

    function playFabTeaser(fab) {
        if (prefersReducedMotion() || !window.setTimeout) return;
        try {
            if (sessionStorage.getItem(TEASER_KEY)) return;
            sessionStorage.setItem(TEASER_KEY, '1');
        } catch (e) {
            // Private mode / blocked storage: tease on this page anyway.
        }
        window.setTimeout(function () {
            fab.classList.add('suu-dw-fab-wide');
            window.setTimeout(function () {
                fab.classList.remove('suu-dw-fab-wide');
            }, TEASER_HOLD);
        }, TEASER_DELAY);
    }

    // ---------- Wire up interactions ----------
    function attachHandlers(fab, panel, pct, lang) {
        var mainView = panel.querySelector('.suu-dw-main');
        var receiptsView = panel.querySelector('.suu-dw-receipts');
        var receiptsToggle = panel.querySelector('.suu-dw-receipts-toggle');
        var backBtn = panel.querySelector('.suu-dw-back-btn');
        var closeBtn = panel.querySelector('.suu-dw-close');

        function showReceipts(show) {
            if (show) {
                mainView.style.display = 'none';
                receiptsView.classList.add('suu-dw-show');
            } else {
                mainView.style.display = '';
                receiptsView.classList.remove('suu-dw-show');
            }
        }

        function openPanel() {
            panel.classList.add('suu-dw-open');
            panel.setAttribute('aria-hidden', 'false');
            fab.setAttribute('aria-expanded', 'true');
            fab.classList.remove('suu-dw-fab-wide');
            showReceipts(false);
            playProgress(panel, pct, lang);
        }
        function closePanel() {
            panel.classList.remove('suu-dw-open');
            panel.setAttribute('aria-hidden', 'true');
            fab.setAttribute('aria-expanded', 'false');
        }

        fab.addEventListener('click', function () {
            if (panel.classList.contains('suu-dw-open')) closePanel();
            else openPanel();
        });

        if (closeBtn) closeBtn.addEventListener('click', closePanel);
        if (receiptsToggle) receiptsToggle.addEventListener('click', function () { showReceipts(true); });
        if (backBtn) backBtn.addEventListener('click', function () { showReceipts(false); });

        // Close on outside click
        document.addEventListener('click', function (e) {
            if (!panel.classList.contains('suu-dw-open')) return;
            if (panel.contains(e.target) || fab.contains(e.target)) return;
            closePanel();
        });

        // Close on Escape
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && panel.classList.contains('suu-dw-open')) closePanel();
        });
    }

    // ---------- Init ----------
    function init() {
        // Don't double-inject
        if (document.getElementById('suu-donation-fab')) return;

        var lang = detectLang();

        fetch(DATA_URL, { cache: 'no-cache' })
            .then(function (r) {
                if (!r.ok) throw new Error('donations.json fetch failed: ' + r.status);
                return r.json();
            })
            .then(function (data) {
                var t = (data.translations && data.translations[lang]) || (data.translations && data.translations.tr) || {};
                var pct = Math.max(0, Math.min(100, Number(data.progressPercent) || 0));
                var fab = buildFab(t, formatPercent(pct, lang, percentDecimals(pct)));
                var panel = buildPanel(t, data, lang);
                document.body.appendChild(fab);
                document.body.appendChild(panel);
                attachHandlers(fab, panel, pct, lang);
                playFabTeaser(fab);
            })
            .catch(function (err) {
                // Silent failure — widget is non-essential, don't break the page
                if (window.console) console.warn('[Suu Donation Widget]', err);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
