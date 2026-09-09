/**
 * Suu — iOS / Android platform durumu
 *
 * Sayfada platformu gösteren birden fazla yer var: hero'daki 3B çevrilen
 * telefon ve ekran görüntüsü galerisi. Hepsi TEK bir duruma bakar —
 * kullanıcı nerede seçerse seçsin diğerleri de döner, tercih saklanır.
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
 *
 *   <div class="devsw" data-device data-face="ios">
 *     <div class="devsw__stage">
 *       <div class="devsw__face">…</div>
 *       <div class="devsw__face devsw__face--back">…</div>
 *     </div>
 *     <div class="devsw__tabs"><button data-platform="ios">…</button>…</div>
 *   </div>
 */
(function () {
    'use strict';

    var BASE = '/assets/screenshots/';
    var PLACEHOLDER = BASE + '_placeholder.svg';
    var PLATFORMS = ['ios', 'android'];

    // ── Ortak platform durumu ───────────────────────────────
    var painters = [];        // her arayüz kendini boyayan bir fonksiyon bırakır
    var current = null;

    function apply(platform) {
        if (PLATFORMS.indexOf(platform) === -1 || platform === current) return;
        current = platform;
        painters.forEach(function (paint) { paint(platform); });
        try { localStorage.setItem('suu-platform', platform); } catch (e) {}
    }

    function preferred() {
        var saved = null;
        try { saved = localStorage.getItem('suu-platform'); } catch (e) {}
        if (PLATFORMS.indexOf(saved) !== -1) return saved;
        if (/iPhone|iPad|iPod|Macintosh/.test(navigator.userAgent)) return 'ios';
        if (/Android/.test(navigator.userAgent)) return 'android';
        return null;
    }

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

    // ── Ekran görüntüsü galerisi ────────────────────────────
    function initGallery(root) {
        var tabs = Array.prototype.slice.call(root.querySelectorAll('[role="tab"]'));
        if (!tabs.length) return;

        tabs.forEach(function (tab) {
            tab.addEventListener('click', function () { apply(tab.dataset.platform); });
            tab.addEventListener('keydown', function (e) {
                var i = tabs.indexOf(tab);
                var next = null;
                if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
                if (e.key === 'ArrowLeft')  next = tabs[(i - 1 + tabs.length) % tabs.length];
                if (next) { e.preventDefault(); next.focus(); apply(next.dataset.platform); }
            });
        });

        painters.push(function (platform) {
            tabs.forEach(function (t) {
                var panel = document.getElementById(t.getAttribute('aria-controls'));
                var active = t.dataset.platform === platform;
                t.setAttribute('aria-selected', active ? 'true' : 'false');
                t.setAttribute('tabindex', active ? '0' : '-1');
                if (panel) panel.hidden = !active;
            });
        });
    }

    // ── Hero'daki çevrilen telefon ──────────────────────────
    function initDevice(root) {
        var btns = Array.prototype.slice.call(root.querySelectorAll('.devsw__tab'));
        var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var timer = null, first = true;

        btns.forEach(function (b) {
            b.addEventListener('click', function () { apply(b.dataset.platform); });
        });

        painters.push(function (platform) {
            root.dataset.face = platform;
            btns.forEach(function (b) {
                var on = b.dataset.platform === platform;
                b.classList.toggle('is-on', on);
                b.setAttribute('aria-pressed', on ? 'true' : 'false');
            });
            // Açılışta dönme yok: ziyaretçi kendi telefonunu dönmeden, hazır bulsun.
            if (first) { first = false; return; }
            if (reduced) return;
            clearTimeout(timer);
            root.classList.remove('is-flipping');
            void root.offsetWidth;                  // animasyonu yeniden tetikler
            root.classList.add('is-flipping');
            timer = setTimeout(function () { root.classList.remove('is-flipping'); }, 1000);
        });
    }

    function init() {
        document.querySelectorAll('img[data-screen]').forEach(attachFallback);
        document.querySelectorAll('[data-device]').forEach(initDevice);
        document.querySelectorAll('[data-shots]').forEach(initGallery);
        // Kayıtlı tercih → cihaz tahmini → iOS (HTML'in başlangıç durumu)
        apply(preferred() || 'ios');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
