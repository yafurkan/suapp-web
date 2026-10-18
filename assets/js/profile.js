/**
 * Suu — Kişisel profil sayfası davranışı (suuapp.com/<slug>/)
 *
 * İçerik HTML'de basılı gelir; bu dosya yalnızca etkileşim ekler:
 *   - profil fotoğrafına ya da bir fotoğrafa dokununca Instagram tarzı hikâye
 *   - kayan şerit dokunurken durur
 *   - "Kişiyi kaydet" → rehbere eklenebilen .vcf (fotoğraf gömülü)
 *   - "Paylaş" → sistem paylaşımı, yoksa bağlantıyı kopyalar
 * Veri: sayfadaki <script id="profile-data">.
 */
(function () {
    'use strict';

    var root = document.getElementById('profile');
    if (!root) return;

    var data = {};
    try { data = JSON.parse(document.getElementById('profile-data').textContent); } catch (e) {}

    var PAGE = 'https://suuapp.com/' + (data.slug || '') + '/';
    var UI = {
        copied: 'Bağlantı kopyalandı', saved: 'Kişi kartı indirildi',
        story: 'Fotoğraflar', watch: 'Fotoğrafları hikâye olarak izle', photo: 'Fotoğraf',
        close: 'Kapat', prev: 'Önceki', next: 'Sonraki', pause: 'Duraklat', play: 'Devam ettir', like: 'Beğen'
    };

    // ── küçük bildirim ──
    var toastEl = null, toastTimer = 0;
    function toast(msg) {
        if (!toastEl) {
            toastEl = document.createElement('div');
            toastEl.className = 'pf-toast';
            toastEl.setAttribute('role', 'status');
            document.body.appendChild(toastEl);
        }
        toastEl.textContent = msg;
        toastEl.classList.add('is-on');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { toastEl.classList.remove('is-on'); }, 2200);
    }

    function copy(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text);
        var t = document.createElement('textarea');
        t.value = text;
        t.setAttribute('readonly', '');
        t.style.position = 'fixed';
        t.style.opacity = '0';
        document.body.appendChild(t);
        t.select();
        try { document.execCommand('copy'); } catch (e) {}
        t.remove();
        return Promise.resolve();
    }

    function share() {
        var payload = { title: document.title, text: data.headline || data.name || '', url: PAGE };
        if (navigator.share) {
            navigator.share(payload).catch(function () {});
            return;
        }
        copy(PAGE).then(function () { toast(UI.copied); });
    }

    // ── vCard ──
    function v(s) {
        return String(s == null ? '' : s).replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/([,;])/g, '\\$1');
    }

    function firstLink(type) {
        var l = (data.links || []).filter(function (x) { return x.type === type && x.url; })[0];
        return l ? String(l.url).trim() : '';
    }

    // Profil fotoğrafını kartın içine göm — rehber uzak adresi indirmiyor
    function avatarBase64() {
        return new Promise(function (resolve) {
            if (!data.avatar || !/^\/(?!\/)/.test(data.avatar)) return resolve('');
            var img = new Image();
            img.onload = function () {
                try {
                    var c = document.createElement('canvas');
                    c.width = c.height = 256;
                    var s = Math.min(img.naturalWidth, img.naturalHeight);
                    c.getContext('2d').drawImage(img, (img.naturalWidth - s) / 2, (img.naturalHeight - s) / 2, s, s, 0, 0, 256, 256);
                    resolve(c.toDataURL('image/jpeg', 0.85).split(',')[1] || '');
                } catch (e) { resolve(''); }
            };
            img.onerror = function () { resolve(''); };
            img.src = data.avatar;
        });
    }

    function vcard() {
        avatarBase64().then(function (photo) {
            var name = String(data.name || '').trim();
            var parts = name.split(/\s+/);
            var family = parts.length > 1 ? parts.pop() : '';
            var lines = [
                'BEGIN:VCARD',
                'VERSION:3.0',
                'N:' + v(family) + ';' + v(parts.join(' ')) + ';;;',
                'FN:' + v(name)
            ];
            if (data.headline) lines.push('TITLE:' + v(data.headline));
            var email = firstLink('email').replace(/^mailto:/i, '');
            if (email) lines.push('EMAIL;TYPE=INTERNET:' + v(email));
            var phone = firstLink('phone').replace(/^tel:/i, '') || firstLink('whatsapp').replace(/^https?:\/\/wa\.me\//i, '');
            if (phone) lines.push('TEL;TYPE=CELL:' + v(phone));
            if (data.location) lines.push('ADR;TYPE=WORK:;;;' + v(data.location) + ';;;');
            lines.push('URL:' + PAGE);
            (data.links || []).forEach(function (l) {
                if (!l.url || /^(email|phone|whatsapp)$/.test(l.type)) return;
                var u = String(l.url).trim();
                if (!/^https?:/i.test(u)) u = 'https://' + u;
                lines.push('X-SOCIALPROFILE;TYPE=' + (l.type || 'other') + ':' + u);
            });
            if (data.headline || data.bio) lines.push('NOTE:' + v(data.headline || ''));
            if (photo) lines.push('PHOTO;ENCODING=b;TYPE=JPEG:' + photo);
            lines.push('END:VCARD');

            var blob = new Blob([lines.join('\r\n') + '\r\n'], { type: 'text/vcard;charset=utf-8' });
            var a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = (data.slug || 'kisi') + '.vcf';
            document.body.appendChild(a);
            a.click();
            a.remove();
            setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
            toast(UI.saved);
        });
    }

    // ── hikâye: profil fotoğrafına ya da bir fotoğrafa dokununca ──
    // Instagram hikâyesi gibi: üstte dolan çubuklar, 10 sn sonra sıradaki;
    // sağa dokun ileri, sola dokun geri, basılı tut dur, aşağı çek kapat.
    // Sağ altta beğeni: canlı yayındaki gibi alttan kalpler yükselir.
    // Fotoğraf listesi sayfadaki şeritten okunur — çizicinin süzdüğü adresler
    // ve data-index sırası birebir aynı kalır.
    var STORY_MS = 10000;
    var stories = Array.prototype.map.call(root.querySelectorAll('.pf-photo[data-index] img'), function (img) {
        return { src: img.getAttribute('src'), alt: img.getAttribute('alt') || '' };
    });
    var calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var st = null, frame, img, bg, bars, live, caption, pauseBtn, likeBtn, heartsEl;
    var stIndex = 0, stElapsed = 0, stLast = 0, stRaf = 0, stReady = false, stBursts = [], liked = {};
    var stPaused = false, stHolding = false, stPushed = false, lastFocus = null;

    var ICON = {
        close: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
        pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
        play: '<polygon points="6 3 20 12 6 21 6 3"/>',
        prev: '<path d="m15 18-6-6 6-6"/>',
        next: '<path d="m9 18 6-6-6-6"/>',
        heart: '<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>'
    };
    var HEART_COLORS = ['#FF3040', '#FF5C7A', '#FF8FA3', '#E1306C', '#FF7A45'];
    function svg(path) {
        return '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + path + '</svg>';
    }

    function isOpen() { return !!st && st.classList.contains('is-open'); }

    function buildStory() {
        st = document.createElement('div');
        st.className = 'pf-story';
        st.setAttribute('role', 'dialog');
        st.setAttribute('aria-modal', 'true');
        st.setAttribute('aria-label', UI.story);
        st.tabIndex = -1;
        st.innerHTML = '<div class="pf-story__frame">' +
            '<img class="pf-story__bg" alt="" aria-hidden="true">' +
            '<img class="pf-story__img" alt="" draggable="false">' +
            '<span class="pf-story__spin" aria-hidden="true"></span>' +
            '<div class="pf-story__top">' +
                '<div class="pf-story__bars">' + stories.map(function () { return '<span><i></i></span>'; }).join('') + '</div>' +
                '<div class="pf-story__head"><img class="pf-story__avatar" alt=""><span class="pf-story__who"><b></b><small></small></span>' +
                    '<button type="button" data-st="pause">' + svg(ICON.pause) + '</button>' +
                    '<button type="button" data-st="close" aria-label="' + UI.close + '">' + svg(ICON.close) + '</button></div>' +
            '</div>' +
            '<button type="button" class="pf-story__zone pf-story__zone--prev" data-st="prev" aria-label="' + UI.prev + '">' + svg(ICON.prev) + '</button>' +
            '<button type="button" class="pf-story__zone pf-story__zone--next" data-st="next" aria-label="' + UI.next + '">' + svg(ICON.next) + '</button>' +
            '<div class="pf-story__foot"><p class="pf-story__caption"></p>' +
                '<span class="pf-story__likewrap"><span class="pf-story__hearts" aria-hidden="true"></span>' +
                '<button type="button" class="pf-story__like" data-st="like" aria-pressed="false" aria-label="' + UI.like + '">' + svg(ICON.heart) + '</button></span></div>' +
            '<p class="pf-story__live" aria-live="polite"></p>' +
            '</div>';
        document.body.appendChild(st);

        frame = st.querySelector('.pf-story__frame');
        img = st.querySelector('.pf-story__img');
        bg = st.querySelector('.pf-story__bg');
        bars = st.querySelectorAll('.pf-story__bars i');
        live = st.querySelector('.pf-story__live');
        caption = st.querySelector('.pf-story__caption');
        pauseBtn = st.querySelector('[data-st="pause"]');
        likeBtn = st.querySelector('[data-st="like"]');
        heartsEl = st.querySelector('.pf-story__hearts');
        likeBtn.addEventListener('animationend', function () { likeBtn.classList.remove('is-pop'); });
        var av = root.querySelector('.pf-avatar img');
        if (av) st.querySelector('.pf-story__avatar').src = av.getAttribute('src');
        else st.querySelector('.pf-story__avatar').remove();
        st.querySelector('.pf-story__who b').textContent = data.name || '';
        st.querySelector('.pf-story__who small').textContent = data.headline || '';
        setPaused(false);

        img.onload = img.onerror = loaded;
        window.addEventListener('resize', function () { if (isOpen()) fit(); });

        // Dokunma: kısa dokunuş bölgeye göre ileri/geri (click), basılı tutmak
        // durdurur, yana kaydırmak geçer, aşağı çekmek kapatır.
        var down = null, holdTimer = 0, suppress = false;
        frame.addEventListener('pointerdown', function (e) {
            if (e.button > 0 || e.target.closest('.pf-story__head button, .pf-story__like')) return;
            suppress = false;
            down = { x: e.clientX, y: e.clientY, t: Date.now() };
            stHolding = true;
            holdTimer = setTimeout(function () { st.classList.add('is-holding'); }, 200);
        });
        st.addEventListener('pointermove', function (e) {
            if (!down) return;
            var dx = e.clientX - down.x, dy = e.clientY - down.y;
            if (dy > 0 && dy > Math.abs(dx)) {
                frame.style.transition = 'none';
                frame.style.transform = 'translateY(' + dy + 'px) scale(' + Math.max(0.85, 1 - dy / 1500) + ')';
            }
        });
        function up(e) {
            if (!down) return;
            var dx = e.clientX - down.x, dy = e.clientY - down.y;
            clearTimeout(holdTimer);
            suppress = Date.now() - down.t > 250 || Math.abs(dx) > 10 || Math.abs(dy) > 10;
            down = null;
            stHolding = false;
            st.classList.remove('is-holding');
            frame.style.transition = '';
            if (e.type === 'pointerup' && dy > 90 && dy > Math.abs(dx)) {
                frame.style.transform = 'translateY(' + (dy + 140) + 'px) scale(0.8)';
                closeStory();
                return;
            }
            frame.style.transform = '';
            if (e.type === 'pointerup' && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(stIndex + (dx < 0 ? 1 : -1));
        }
        st.addEventListener('pointerup', up);
        st.addEventListener('pointercancel', up);
        st.addEventListener('pointerleave', up);
        // Uzun basışta görsel menüsü / seçim açılmasın
        st.addEventListener('contextmenu', function (e) { e.preventDefault(); });
        // Fareyle tıklanan bölge odağı almasın — yoksa Boşluk duraklatmak yerine onu tetikler
        frame.addEventListener('mousedown', function (e) {
            if (e.target.closest('.pf-story__zone')) e.preventDefault();
        });

        st.addEventListener('click', function (e) {
            var b = e.target.closest('[data-st]');
            if (!b) {
                if (e.target === st) closeStory();          // masaüstünde çerçevenin dışı
                return;
            }
            var k = b.getAttribute('data-st');
            if (k === 'close') closeStory();
            else if (k === 'pause') setPaused(!stPaused);
            else if (k === 'like') toggleLike();
            // basılı tutma / kaydırma sonrası gelen click geçiş sayılmaz; klavye (detail 0) her zaman geçer
            else if (!(suppress && e.detail)) go(stIndex + (k === 'next' ? 1 : -1));
        });
    }

    function setPaused(p) {
        stPaused = p;
        st.classList.toggle('is-paused', p);
        pauseBtn.setAttribute('aria-label', p ? UI.play : UI.pause);
        pauseBtn.innerHTML = svg(p ? ICON.play : ICON.pause);
    }

    // Alttan yükselen kalpler — her biri farklı boy, renk, salınım ve hızda
    function hearts(n) {
        if (calm) return;
        for (var i = 0; i < n; i++) {
            var h = document.createElement('span');
            h.className = 'pf-heart';
            h.style.setProperty('--dx', Math.round(Math.random() * 56 - 36) + 'px');   // sağ kenara taşmasın diye sola yatkın
            h.style.setProperty('--rise', Math.round(frame.clientHeight * (0.3 + Math.random() * 0.22)) + 'px');
            h.style.setProperty('--s', (0.7 + Math.random() * 0.6).toFixed(2));
            h.style.setProperty('--rot', Math.round(Math.random() * 30 - 15) + 'deg');
            h.style.color = HEART_COLORS[Math.floor(Math.random() * HEART_COLORS.length)];
            h.style.animationDuration = (1.7 + Math.random() * 0.9).toFixed(2) + 's';
            h.style.animationDelay = (i * 0.16 + Math.random() * 0.08).toFixed(2) + 's';
            h.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>';
            h.addEventListener('animationend', function () { this.remove(); });
            heartsEl.appendChild(h);
        }
    }

    function showLike() {
        var on = !!liked[stIndex];
        likeBtn.classList.toggle('is-liked', on);
        likeBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }

    // Yalnızca görsel — hiçbir yere gönderilmez, sayılmaz
    function toggleLike() {
        liked[stIndex] = !liked[stIndex];
        showLike();
        if (!liked[stIndex]) return;
        likeBtn.classList.remove('is-pop');
        void likeBtn.offsetWidth;
        likeBtn.classList.add('is-pop');
        hearts(8);
    }

    // Dikey fotoğraf ekranı doldurur; yatay/kare fotoğrafta ya da yatay
    // ekranda kırpmak yerine sığdırılır, boşluğu aynı fotoğrafın bulanığı doldurur
    function fit() {
        var wide = img.naturalWidth / (img.naturalHeight || 1) > 0.9 || frame.clientWidth > frame.clientHeight;
        st.classList.toggle('is-fit', wide);
    }

    function loaded() {
        stReady = true;
        st.classList.remove('is-loading');
        fit();
    }

    function go(i) {
        if (i >= stories.length) return closeStory();
        stIndex = Math.max(0, i);                         // ilk hikâyede geri = baştan
        stElapsed = 0;
        Array.prototype.forEach.call(bars, function (b, k) { b.style.transform = 'scaleX(' + (k < stIndex ? 1 : 0) + ')'; });
        var p = stories[stIndex];
        img.alt = p.alt;
        caption.textContent = p.alt && p.alt !== data.name ? p.alt : '';
        live.textContent = UI.photo + ' ' + (stIndex + 1) + ' / ' + stories.length;
        showLike();
        // "beğeni geliyor": her hikâyede bir, çoğunda iki kalp dalgası
        stBursts = [1200 + Math.random() * 2300];
        if (Math.random() < 0.6) stBursts.push(5500 + Math.random() * 2500);
        img.style.transform = '';
        if (img.getAttribute('src') === p.src && img.complete) {
            loaded();
        } else {
            stReady = false;
            st.classList.add('is-loading');
            img.src = p.src;
            bg.src = p.src;
        }
        if (stories[stIndex + 1]) new Image().src = stories[stIndex + 1].src;
    }

    function tick(t) {
        var dt = stLast ? Math.min(t - stLast, 100) : 0;   // sekme arkadayken süre birikmesin
        stLast = t;
        if (stReady && !stPaused && !stHolding) stElapsed += dt;
        var k = Math.min(stElapsed / STORY_MS, 1);
        bars[stIndex].style.transform = 'scaleX(' + k + ')';
        if (!calm) img.style.transform = 'scale(' + (1 + 0.05 * k) + ')';
        if (stBursts.length && stElapsed >= stBursts[0]) { stBursts.shift(); hearts(4 + Math.floor(Math.random() * 4)); }
        if (stElapsed >= STORY_MS) go(stIndex + 1);
        if (isOpen()) stRaf = requestAnimationFrame(tick);
    }

    function openStory(i, from) {
        if (!stories.length || isOpen()) return;
        if (!st) buildStory();
        lastFocus = document.activeElement;
        // Dokunulan yerden büyüyerek açılsın (kapanırken oraya küçülür)
        frame.style.transition = 'none';
        frame.style.transform = '';
        var r = from && from.getBoundingClientRect(), f = frame.getBoundingClientRect();
        frame.style.transformOrigin = r ? (r.left + r.width / 2 - f.left) + 'px ' + (r.top + r.height / 2 - f.top) + 'px' : '';
        void frame.offsetWidth;
        frame.style.transition = '';
        setPaused(false);
        go(i);
        st.classList.add('is-open');
        document.documentElement.style.overflow = 'hidden';
        // Telefonda geri tuşu/hareketi sayfadan çıkmasın, hikâyeyi kapatsın
        history.pushState({ pfStory: 1 }, '');
        stPushed = true;
        st.focus({ preventScroll: true });
        cancelAnimationFrame(stRaf);
        stLast = 0;
        stRaf = requestAnimationFrame(tick);
    }

    function closeStory() {
        if (!isOpen()) return;
        st.classList.remove('is-open', 'is-holding');
        cancelAnimationFrame(stRaf);
        heartsEl.textContent = '';
        document.documentElement.style.overflow = '';
        if (stPushed) { stPushed = false; history.back(); }
        if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
    }

    window.addEventListener('popstate', function () {
        if (!isOpen()) return;
        stPushed = false;
        closeStory();
    });
    // Hikâye açıkken sayfa yenilendiyse kalan geçmiş kaydı temizlensin
    if (history.state && history.state.pfStory) history.replaceState(null, '');

    document.addEventListener('keydown', function (e) {
        if (!isOpen()) return;
        if (e.key === 'Escape') closeStory();
        else if (e.key === 'ArrowRight') go(stIndex + 1);
        else if (e.key === 'ArrowLeft') go(stIndex - 1);
        else if (e.key === ' ' && !e.target.closest('button')) { e.preventDefault(); setPaused(!stPaused); }
        else if (e.key === 'Tab') {
            // odak hikâyenin içinde kalsın
            var f = st.querySelectorAll('button'), first = f[0], last = f[f.length - 1];
            if (e.shiftKey ? (document.activeElement === first || document.activeElement === st) : document.activeElement === last) {
                e.preventDefault();
                (e.shiftKey ? last : first).focus();
            }
        }
    });

    // Profil fotoğrafı hikâyeyi açar; şeritteki fotoğraflar klavyeyle de açılsın
    var avatarEl = root.querySelector('.pf-avatar');
    if (avatarEl && stories.length) {
        avatarEl.classList.add('pf-avatar--story');
        avatarEl.setAttribute('role', 'button');
        avatarEl.setAttribute('tabindex', '0');
        avatarEl.setAttribute('aria-label', UI.watch);
    }
    Array.prototype.forEach.call(root.querySelectorAll('.pf-photo[data-index]'), function (f) {
        f.setAttribute('tabindex', '0');
        f.setAttribute('role', 'button');
    });

    // Instagram'daki gibi: profil fotoğrafına dokununca halka kesik kesik döner,
    // ilk fotoğraf hazır olunca hikâye açılır. Kısa bir an hep döner ki dokunuşun
    // karşılığı görünsün; yavaş bağlantıda da en geç 4 sn'de açılır.
    function openFromAvatar(av) {
        if (isOpen() || av.classList.contains('is-loading')) return;
        if (calm) return openStory(0, av);
        av.classList.add('is-loading');
        var first = new Image();
        first.src = stories[0].src;
        var ready = first.decode ? first.decode().catch(function () {}) : Promise.resolve();
        var at = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
        Promise.race([Promise.all([ready, at(450)]), at(4000)]).then(function () {
            av.classList.remove('is-loading');
            openStory(0, av);
        });
    }

    function photoIndex(ph) {
        // kopya şeritteki fotoğraf: sıra numarası görünür kopyasından
        return ph.hasAttribute('data-index') ? +ph.getAttribute('data-index')
            : Array.prototype.indexOf.call(ph.parentNode.children, ph);
    }

    root.addEventListener('click', function (e) {
        var act = e.target.closest('[data-action]');
        if (act) {
            var a = act.getAttribute('data-action');
            if (a === 'share') share();
            else if (a === 'vcard') vcard();
            return;
        }
        var av = e.target.closest('.pf-avatar--story');
        if (av) return openFromAvatar(av);
        var ph = e.target.closest('.pf-photo');
        if (ph) openStory(photoIndex(ph), ph);
    });
    root.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter' && e.key !== ' ') return;
        var t = e.target;
        if (t.matches && t.matches('.pf-avatar--story, .pf-photo[data-index]')) {
            e.preventDefault();
            if (t.classList.contains('pf-avatar--story')) openFromAvatar(t);
            else openStory(photoIndex(t), t);
        }
    });

    // Dokunmatikte :hover yok — parmak şeritteyken dursun
    var gallery = root.querySelector('.pf-gallery--marquee');
    if (gallery) {
        var resume = 0;
        gallery.addEventListener('touchstart', function () { clearTimeout(resume); gallery.classList.add('is-paused'); }, { passive: true });
        gallery.addEventListener('touchend', function () { resume = setTimeout(function () { gallery.classList.remove('is-paused'); }, 1200); });
    }
})();
