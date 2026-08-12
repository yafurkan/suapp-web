/**
 * Suu — iOS / Android ekran görüntüsü galerisi
 *
 * İki platformun görselleri de DOM'da kalır; JS yalnızca görünürlük
 * değiştirir. Böylece arama motorları ve AI botları her iki seti de
 * görür — SEO/AEO açısından içerik kaybı olmaz.
 *
 * Yükleme sırası (görsel bulunamazsa):
 *     <platform>/<sayfa dili>  →  <platform>/tr  →  _placeholder.svg
 *
 * Beklenen HTML:
 *   <div class="shots" data-shots>
 *     <div class="shots__tabs" role="tablist">
 *       <button class="shots__tab" role="tab" aria-selected="true"
 *               aria-controls="shots-ios" id="tab-ios">iOS</button>
 *       <button class="shots__tab" role="tab" aria-selected="false"
 *               aria-controls="shots-android" id="tab-android">Android</button>
 *     </div>
 *     <div class="shots__panel" id="shots-ios"     role="tabpanel" aria-labelledby="tab-ios">…</div>
 *     <div class="shots__panel" id="shots-android" role="tabpanel" aria-labelledby="tab-android" hidden>…</div>
 *   </div>
 */
(function () {
    'use strict';

    var BASE = '/assets/screenshots/';
    var PLACEHOLDER = BASE + '_placeholder.svg';

    // ── Görsel fallback zinciri ─────────────────────────────
    function attachFallback(img) {
        if (img.dataset.fallbackBound) return;
        img.dataset.fallbackBound = '1';

        function step() {
            var platform = img.dataset.platform;
            var screen = img.dataset.screen;
            var stage = img.dataset.fallbackStage || 'lang';

            if (stage === 'lang' && platform && screen) {
                img.dataset.fallbackStage = 'tr';
                img.src = BASE + platform + '/tr/' + screen + '.webp';
                return;
            }
            if (img.src.indexOf('_placeholder.svg') === -1) {
                img.dataset.fallbackStage = 'placeholder';
                img.src = PLACEHOLDER;
                return;
            }
            img.removeEventListener('error', step);   // sonsuz döngüyü kes
        }

        img.addEventListener('error', step);

        // Bu script defer ile yüklendiği için görsel, dinleyici bağlanmadan
        // önce çoktan hata vermiş olabilir — o durumu ayrıca yakala.
        if (img.complete && img.naturalWidth === 0) step();
    }

    // ── Sekme davranışı ─────────────────────────────────────
    function initGallery(root) {
        var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
        if (!tabs.length) return;

        function select(tab) {
            tabs.forEach(function (t) {
                var panel = document.getElementById(t.getAttribute('aria-controls'));
                var active = t === tab;
                t.setAttribute('aria-selected', active ? 'true' : 'false');
                t.setAttribute('tabindex', active ? '0' : '-1');
                if (panel) panel.hidden = !active;
            });
            try { localStorage.setItem('suu-platform', tab.dataset.platform || ''); } catch (e) {}
        }

        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () { select(tab); });
            tab.addEventListener('keydown', function (e) {
                var i = tabs.indexOf(tab);
                var next = null;
                if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
                if (e.key === 'ArrowLeft')  next = tabs[(i - 1 + tabs.length) % tabs.length];
                if (next) { e.preventDefault(); next.focus(); select(next); }
            });
        });

        // Başlangıç sekmesi: kayıtlı tercih → cihaz tahmini → ilk sekme
        var preferred = null;
        try { preferred = localStorage.getItem('suu-platform'); } catch (e) {}
        if (!preferred) {
            preferred = /iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent) ? 'ios'
                      : /Android/.test(navigator.userAgent) ? 'android'
                      : null;
        }
        var start = preferred && tabs.filter(function (t) { return t.dataset.platform === preferred; })[0];
        select(start || tabs[0]);
    }

    function init() {
        document.querySelectorAll('img[data-screen]').forEach(attachFallback);
        document.querySelectorAll('[data-shots]').forEach(initGallery);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
