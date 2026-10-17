/**
 * Suu — Kişisel profil sayfası davranışı (suuapp.com/<slug>/)
 *
 * İçerik HTML'de basılı gelir; bu dosya yalnızca etkileşim ekler:
 *   - fotoğrafa dokununca büyük görünüm (ok tuşları, kaydırma, Esc)
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
    var UI = { copied: 'Bağlantı kopyalandı', saved: 'Kişi kartı indirildi', close: 'Kapat', prev: 'Önceki', next: 'Sonraki' };

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

    // ── büyük fotoğraf ──
    var photos = (data.photos || []).filter(function (p) { return p && p.src; });
    var lb = null, lbIndex = 0, lastFocus = null;

    function buildLightbox() {
        lb = document.createElement('div');
        lb.className = 'pf-lightbox';
        lb.setAttribute('role', 'dialog');
        lb.setAttribute('aria-modal', 'true');
        var btn = function (kind, label, path) {
            return '<button type="button" data-lb="' + kind + '" aria-label="' + label + '"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + path + '</svg></button>';
        };
        lb.innerHTML = '<figure><img alt=""><figcaption></figcaption></figure>' +
            btn('close', UI.close, '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>') +
            (photos.length > 1 ? btn('prev', UI.prev, '<path d="m15 18-6-6 6-6"/>') + btn('next', UI.next, '<path d="m9 18 6-6-6-6"/>') : '');
        document.body.appendChild(lb);
        lb.addEventListener('click', function (e) {
            var b = e.target.closest('[data-lb]');
            if (b) {
                var k = b.getAttribute('data-lb');
                if (k === 'close') closeLb();
                else showLb(lbIndex + (k === 'next' ? 1 : -1));
            } else if (e.target === lb) closeLb();
        });
        // kaydırarak geçiş
        var x0 = null;
        lb.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, { passive: true });
        lb.addEventListener('touchend', function (e) {
            if (x0 === null) return;
            var dx = e.changedTouches[0].clientX - x0;
            if (Math.abs(dx) > 50 && photos.length > 1) showLb(lbIndex + (dx < 0 ? 1 : -1));
            x0 = null;
        });
    }

    function showLb(i) {
        if (!photos.length) return;
        lbIndex = (i + photos.length) % photos.length;
        var p = photos[lbIndex];
        var img = lb.querySelector('img');
        img.src = p.src;
        img.alt = p.alt || '';
        lb.querySelector('figcaption').textContent = p.alt || '';
    }

    function openLb(i) {
        if (!lb) buildLightbox();
        lastFocus = document.activeElement;
        showLb(i);
        lb.classList.add('is-open');
        document.documentElement.style.overflow = 'hidden';
        lb.querySelector('[data-lb="close"]').focus();
    }

    function closeLb() {
        lb.classList.remove('is-open');
        document.documentElement.style.overflow = '';
        if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    document.addEventListener('keydown', function (e) {
        if (!lb || !lb.classList.contains('is-open')) return;
        if (e.key === 'Escape') closeLb();
        else if (e.key === 'ArrowRight') showLb(lbIndex + 1);
        else if (e.key === 'ArrowLeft') showLb(lbIndex - 1);
    });

    // Fotoğraflar klavyeyle de açılsın
    Array.prototype.forEach.call(root.querySelectorAll('.pf-photo[data-index]'), function (f) {
        f.setAttribute('tabindex', '0');
        f.setAttribute('role', 'button');
    });

    root.addEventListener('click', function (e) {
        var act = e.target.closest('[data-action]');
        if (act) {
            var a = act.getAttribute('data-action');
            if (a === 'share') share();
            else if (a === 'vcard') vcard();
            return;
        }
        var ph = e.target.closest('.pf-photo');
        if (ph) {
            // kopya şeritteki fotoğraf: sıra numarası görünür kopyasından
            var idx = ph.hasAttribute('data-index') ? +ph.getAttribute('data-index')
                : Array.prototype.indexOf.call(ph.parentNode.children, ph);
            openLb(idx);
        }
    });
    root.addEventListener('keydown', function (e) {
        if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('.pf-photo[data-index]')) {
            e.preventDefault();
            openLb(+e.target.getAttribute('data-index'));
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
