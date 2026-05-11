/**
 * Suu — Donation Tracker Widget
 * Floating FAB + glassmorphism panel showing live donation progress.
 * Reads data from /donations.json. Manual monthly update by editing JSON.
 * Multilingual (TR/EN/RU/AR) — syncs with lang-switcher.js via localStorage.
 */
(function () {
    'use strict';

    var DATA_URL = '/donations.json';
    var STORAGE_KEY = 'suu-lang';

    // ---------- Language detection (mirrors lang-switcher.js) ----------
    function detectLang() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved && ['tr', 'en', 'ar', 'ru'].indexOf(saved) !== -1) return saved;
        } catch (e) {}
        // Fallback: <html lang="..."> attribute
        var htmlLang = (document.documentElement.getAttribute('lang') || '').toLowerCase().slice(0, 2);
        if (['tr', 'en', 'ar', 'ru'].indexOf(htmlLang) !== -1) return htmlLang;
        // Final fallback: browser
        var navs = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || 'tr'];
        for (var i = 0; i < navs.length; i++) {
            var code = navs[i].toLowerCase().slice(0, 2);
            if (['tr', 'en', 'ar', 'ru'].indexOf(code) !== -1) return code;
        }
        return 'tr';
    }

    function isRTL(lang) { return lang === 'ar'; }

    // ---------- Currency conversion + formatting ----------
    // Amounts in donations.json are stored in baseCurrency (TRY).
    // We convert to the user's language currency via `rates`,
    // then format with Intl.NumberFormat for proper locale-specific output.
    function convertAmount(baseAmount, lang, data) {
        var cfg = (data.currencyByLang && data.currencyByLang[lang]) || (data.currencyByLang && data.currencyByLang.tr) || { code: 'TRY', locale: 'tr-TR' };
        var rate = (data.rates && data.rates[cfg.code]) || 1;
        return { value: baseAmount * rate, code: cfg.code, locale: cfg.locale };
    }

    function formatAmount(baseAmount, lang, data) {
        var c = convertAmount(baseAmount, lang, data);
        try {
            return new Intl.NumberFormat(c.locale, {
                style: 'currency',
                currency: c.code,
                maximumFractionDigits: 0,
                minimumFractionDigits: 0
            }).format(Math.round(c.value));
        } catch (e) {
            return Math.round(c.value) + ' ' + c.code;
        }
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
    function buildFab(t) {
        var btn = document.createElement('button');
        btn.id = 'suu-donation-fab';
        btn.setAttribute('aria-label', t.fabLabel);
        btn.setAttribute('title', t.fabLabel);
        btn.innerHTML = (
            '<svg class="suu-dw-fab-drop" viewBox="0 0 28 32" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
            '<defs>' +
            '<linearGradient id="suu-fab-grad" x1="0" y1="0" x2="0" y2="1">' +
            '<stop offset="0%" stop-color="#6FB3FF"/>' +
            '<stop offset="100%" stop-color="#2E6FB8"/>' +
            '</linearGradient>' +
            '</defs>' +
            '<path d="M14 1 C14 1 2 14 2 22 a12 12 0 0 0 24 0 C26 14 14 1 14 1 Z" fill="url(#suu-fab-grad)"/>' +
            '<ellipse cx="10" cy="18" rx="2.4" ry="3.4" fill="rgba(255,255,255,0.45)"/>' +
            '</svg>'
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

        var pct = data.goalAmount > 0 ? Math.min(100, (data.totalAmount / data.goalAmount) * 100) : 0;
        var raisedStr = formatAmount(data.totalAmount, lang, data);
        var goalStr = formatAmount(data.goalAmount, lang, data);

        // Bucket SVG: a wooden bucket outline with masked water fill.
        // Water rect uses CSS transform scaleY based on percent.
        var waterScale = (pct / 100).toFixed(3);

        panel.innerHTML = (
            '<div class="suu-dw-header">' +
              '<div class="suu-dw-header-text">' +
                '<h3 class="suu-dw-title" id="suu-dw-title">' + escapeHtml(t.title) + '</h3>' +
                '<p class="suu-dw-subtitle">' + escapeHtml(t.subtitle) + '</p>' +
              '</div>' +
              '<button class="suu-dw-close" aria-label="' + escapeAttr(t.close) + '" type="button">×</button>' +
            '</div>' +

            '<div class="suu-dw-main">' +
              '<div class="suu-dw-bucket-wrap">' +
                '<div class="suu-dw-bucket">' +
                  '<svg viewBox="0 0 130 130" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
                    '<defs>' +
                      '<linearGradient id="suu-dw-water-gradient" x1="0" y1="0" x2="0" y2="1">' +
                        '<stop offset="0%" stop-color="#6FB3FF" stop-opacity="0.95"/>' +
                        '<stop offset="100%" stop-color="#2E6FB8" stop-opacity="0.98"/>' +
                      '</linearGradient>' +
                      '<linearGradient id="suu-dw-bucket-grad" x1="0" y1="0" x2="0" y2="1">' +
                        '<stop offset="0%" stop-color="#c89968"/>' +
                        '<stop offset="100%" stop-color="#8b6638"/>' +
                      '</linearGradient>' +
                      // Clip path: defines the inner shape of the bucket (where water lives)
                      '<clipPath id="suu-dw-bucket-clip">' +
                        '<path d="M28 38 L102 38 L94 110 Q94 116 88 116 L42 116 Q36 116 36 110 Z"/>' +
                      '</clipPath>' +
                    '</defs>' +

                    // Bucket handle (behind body)
                    '<path d="M38 38 Q38 18 65 18 Q92 18 92 38" stroke="#5a3a1c" stroke-width="2.5" fill="none" stroke-linecap="round"/>' +

                    // Bucket body outline (wood-look)
                    '<path d="M28 38 L102 38 L94 110 Q94 116 88 116 L42 116 Q36 116 36 110 Z" fill="url(#suu-dw-bucket-grad)" stroke="#5a3a1c" stroke-width="1.5"/>' +

                    // Wood plank lines
                    '<line x1="48" y1="40" x2="46" y2="114" stroke="#6b4626" stroke-width="0.8" opacity="0.5"/>' +
                    '<line x1="65" y1="40" x2="65" y2="115" stroke="#6b4626" stroke-width="0.8" opacity="0.5"/>' +
                    '<line x1="82" y1="40" x2="84" y2="114" stroke="#6b4626" stroke-width="0.8" opacity="0.5"/>' +

                    // Water (clipped to bucket interior, scaleY animated)
                    '<g clip-path="url(#suu-dw-bucket-clip)">' +
                      '<rect class="suu-dw-water" x="28" y="38" width="74" height="78" style="transform: scaleY(' + waterScale + '); transform-origin: center bottom; transform-box: fill-box;"/>' +
                      '<ellipse class="suu-dw-wave" cx="65" cy="40" rx="42" ry="3" style="transform: translateY(' + (78 - 78 * pct / 100).toFixed(1) + 'px); transition: transform 1.2s cubic-bezier(0.22, 1, 0.36, 1);"/>' +
                    '</g>' +

                    // Top metal rim (in front of water for clean edge)
                    '<rect x="26" y="36" width="78" height="5" rx="2" fill="#5a3a1c"/>' +
                    '<rect x="26" y="36" width="78" height="1.5" fill="#8b6638"/>' +
                  '</svg>' +
                '</div>' +
                '<div class="suu-dw-percent">' + Math.round(pct) + '%</div>' +
                '<div class="suu-dw-amount-row">' +
                  '<strong>' + raisedStr + '</strong>' +
                  '<span>/ ' + goalStr + '</span>' +
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
                (data.lastUpdated ? ' · ' + escapeHtml(t.lastUpdated) + ': ' + escapeHtml(data.lastUpdated) : '') +
              '</div>' +
            '</div>' +

            '<div class="suu-dw-receipts">' +
              '<div class="suu-dw-receipts-header">' +
                '<button class="suu-dw-back-btn" aria-label="' + escapeAttr(t.close) + '" type="button">←</button>' +
                '<span class="suu-dw-receipts-title">' + escapeHtml(t.receiptsTitle) + '</span>' +
              '</div>' +
              renderReceiptList(data.receipts, t, lang, data) +
            '</div>'
        );

        return panel;
    }

    function renderReceiptList(receipts, t, lang, data) {
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
            var amount = (r.amount != null) ? formatAmount(r.amount, lang, data) : '';
            var url = r.url ? escapeAttr(r.url) : '';
            html += '<li class="suu-dw-receipt-item">' +
                      '<div class="suu-dw-receipt-meta">' +
                        '<span class="suu-dw-receipt-charity">' + charity + '</span>' +
                        '<span class="suu-dw-receipt-date">' + date + '</span>' +
                      '</div>' +
                      (amount ? '<span class="suu-dw-receipt-amount">' + amount + '</span>' : '') +
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

    // ---------- Wire up interactions ----------
    function attachHandlers(fab, panel) {
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
            showReceipts(false);
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
                var fab = buildFab(t);
                var panel = buildPanel(t, data, lang);
                document.body.appendChild(fab);
                document.body.appendChild(panel);
                attachHandlers(fab, panel);
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
