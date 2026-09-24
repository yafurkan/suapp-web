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
 * Hero maketi küçük telefonlarda küçültüldüğü için (bkz. suu.css, 700px altı)
 * sahne bir butonun içine alınır: dokunulduğunda ekran görüntüsü tam boy
 * bir katmanda büyüyerek açılır.
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

    // Büyütme katmanının metinleri — sayfa dili <html lang> ile gelir.
    var STR = {
        tr: { zoom: 'Büyüt',      aria: 'Ekran görüntüsünü büyüt',   close: 'Kapat' },
        en: { zoom: 'Enlarge',    aria: 'Enlarge the screenshot',    close: 'Close' },
        de: { zoom: 'Vergrößern', aria: 'Screenshot vergrößern',     close: 'Schließen' },
        it: { zoom: 'Ingrandisci',aria: 'Ingrandisci lo screenshot', close: 'Chiudi' },
        ru: { zoom: 'Увеличить',  aria: 'Увеличить скриншот',        close: 'Закрыть' },
        uk: { zoom: 'Збільшити',  aria: 'Збільшити знімок екрана',   close: 'Закрити' },
        ar: { zoom: 'تكبير',      aria: 'تكبير لقطة الشاشة',          close: 'إغلاق' },
        hi: { zoom: 'बड़ा करें',    aria: 'स्क्रीनशॉट बड़ा करें',          close: 'बंद करें' }
    };

    function strings() {
        var lang = (document.documentElement.lang || 'tr').slice(0, 2).toLowerCase();
        return STR[lang] || STR.en;
    }

    function reducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

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

    // ── Hero telefonundaki kodlu uygulama turu ──────────────
    // iOS ekranının üstüne suu-phone-tour.js ile döngüsel bir gezinti
    // oynatılır. Statik ekran görüntüsü altta kalır: yer tutar (CLS yok),
    // botlar görür, tur yüklenemezse görünen odur.
    var TOUR = {
        camera: '/assets/tour/camera.jpg',
        map:    '/assets/tour/map.jpg',
        mascot: '/assets/tour/mascot.png'
    };

    function mountTour(host) {
        return window.SuuPhoneTour ? window.SuuPhoneTour.mount(host, TOUR) : null;
    }

    function initTour(root) {
        var host = root.querySelector('[data-tour]');
        if (!host || !mountTour(host)) return;
        var timer = null;

        // Android seçilince tur gizlenir; display:none olunca turun kendi
        // IntersectionObserver'ı onu duraklatır. Çevirmenin ortasında (ön yüz
        // arkaya geçtiğinde) gizlenir ki dönüş sırasında ekran boş kalmasın.
        if (root.dataset.face === 'android') host.style.display = 'none';
        painters.push(function (platform) {
            clearTimeout(timer);
            if (platform === 'ios') { host.style.display = ''; return; }
            if (reducedMotion()) { host.style.display = 'none'; return; }
            timer = setTimeout(function () { host.style.display = 'none'; }, 480);
        });
    }

    // ── Maketi büyütme ──────────────────────────────────────
    // Küçük telefonlarda hero maketi ekranı kaplamasın diye küçültüldü;
    // detayı görmek isteyen üstüne dokununca maket büyüyerek açılır.
    function openZoom(root, trigger, t) {
        var platform = root.dataset.face === 'android' ? 'android' : 'ios';
        var source = root.querySelector('img[data-platform="' + platform + '"]');
        var origin = source && source.closest('.phone');
        if (!origin) return;

        var reduced = reducedMotion();
        var lb = document.createElement('div');
        lb.className = 'lbox';
        lb.setAttribute('role', 'dialog');
        lb.setAttribute('aria-modal', 'true');
        lb.setAttribute('aria-label', source.alt || t.aria);

        var close = document.createElement('button');
        close.type = 'button';
        close.className = 'lbox__close';
        close.setAttribute('aria-label', t.close);
        close.innerHTML = '&times;';

        var frame = document.createElement('div');
        frame.className = 'phone lbox__phone' + (platform === 'android' ? ' phone--punch' : '');
        var img = document.createElement('img');
        img.src = source.currentSrc || source.src;
        img.alt = source.alt;
        frame.appendChild(img);

        // Hero'da tur oynuyorsa büyütülmüş maket de turu gösterir.
        var tour = null;
        if (platform === 'ios' && root.querySelector('[data-tour]')) {
            var host = document.createElement('div');
            host.className = 'phone__tour';
            host.setAttribute('aria-hidden', 'true');
            frame.appendChild(host);
            tour = mountTour(host);
        }

        lb.appendChild(close);
        lb.appendChild(frame);
        document.body.appendChild(lb);
        document.body.classList.add('lbox-open');
        close.focus();

        // Küçük maketten büyüğe doğru açılış (FLIP)
        function shift(from, to) {
            return 'translate(' +
                ((from.left + from.width / 2) - (to.left + to.width / 2)) + 'px,' +
                ((from.top + from.height / 2) - (to.top + to.height / 2)) + 'px) scale(' +
                (from.width / to.width) + ')';
        }

        var animated = !reduced && typeof frame.animate === 'function';
        if (animated) {
            frame.animate(
                [{ transform: shift(origin.getBoundingClientRect(), frame.getBoundingClientRect()) },
                 { transform: 'none' }],
                { duration: 360, easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)' }
            );
            lb.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, easing: 'ease-out' });
        }

        function dismiss() {
            document.removeEventListener('keydown', onKey, true);
            document.body.classList.remove('lbox-open');
            if (trigger) trigger.focus();

            function remove() { if (tour) tour.destroy(); lb.remove(); }
            var back = origin.getBoundingClientRect();
            if (!animated || !back.width) { remove(); return; }
            var out = frame.animate(
                [{ transform: 'none' }, { transform: shift(back, frame.getBoundingClientRect()) }],
                { duration: 260, easing: 'cubic-bezier(0.4, 0, 0.6, 1)', fill: 'forwards' }
            );
            lb.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 260, fill: 'forwards' });
            out.onfinish = remove;
        }

        function onKey(e) {
            if (e.key === 'Escape') { e.preventDefault(); dismiss(); return; }
            // Tek denetimli katman: odak dışarı kaçmasın.
            if (e.key === 'Tab') { e.preventDefault(); close.focus(); }
        }

        lb.addEventListener('click', dismiss);
        document.addEventListener('keydown', onKey, true);
    }

    function initZoom(root) {
        var stage = root.querySelector('.devsw__stage');
        if (!stage || root.querySelector('.devsw__zoom')) return;
        var t = strings();

        // Sahne butonun içine alınır: maketin tamamı tek bir dokunma hedefi olur.
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'devsw__zoom';
        btn.setAttribute('aria-label', t.aria);
        btn.title = t.zoom;
        stage.parentNode.insertBefore(btn, stage);
        btn.appendChild(stage);

        var hint = document.createElement('span');
        hint.className = 'devsw__zoom__hint';
        hint.setAttribute('aria-hidden', 'true');
        hint.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" ' +
            'stroke="currentColor" stroke-width="2.2" stroke-linecap="round">' +
            '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.8-3.8M11 8v6M8 11h6"/></svg>';
        btn.appendChild(hint);

        btn.addEventListener('click', function () { openZoom(root, btn, t); });
    }

    function init() {
        document.querySelectorAll('img[data-screen]').forEach(attachFallback);
        document.querySelectorAll('[data-device]').forEach(initDevice);
        document.querySelectorAll('[data-device]').forEach(initZoom);
        document.querySelectorAll('[data-shots]').forEach(initGallery);
        // Kayıtlı tercih → cihaz tahmini → iOS (HTML'in başlangıç durumu)
        apply(preferred() || 'ios');
        // suu-phone-tour.js sayfanın sonunda defer ile gelir; bu dosya ondan
        // önce çalıştığı için tur, DOMContentLoaded'da (tüm defer'lar bitince)
        // kurulur.
        whenTourLoaded(function () {
            document.querySelectorAll('[data-device]').forEach(initTour);
        });
    }

    function whenTourLoaded(fn) {
        if (window.SuuPhoneTour || document.readyState === 'complete') fn();
        else document.addEventListener('DOMContentLoaded', fn, { once: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
