/**
 * Suu — Profil paneli (suuapp.com/<slug>/admin/)
 *
 * Site statik (GitHub Pages); sunucu yok. Panel değişiklikleri doğrudan
 * GitHub deposuna commit'ler, yayın akışı (deploy.yml) 1–2 dakikada canlıya alır.
 *
 *   giriş     → ince ayarlı GitHub anahtarı (yalnızca bu depo, Contents: Read and write)
 *   yükleme   → <slug>/index.html içindeki #profile-data okunur
 *   düzenleme → profile-render.js ile canlı önizleme; taslak tarayıcıda saklanır
 *   yayın     → sayfa + yeni fotoğraflar TEK commit; kullanılmayan eski fotoğraflar silinir
 *
 * Anahtar yalnızca bu tarayıcıda (localStorage / sessionStorage) durur ve
 * yalnızca api.github.com'a gider — sayfanın CSP'si başka bir yere izin vermez.
 */
(function () {
    'use strict';

    var R = window.SuuProfile;
    var CFG = { owner: 'yafurkan', repo: 'suapp-web', branch: 'main', site: 'https://suuapp.com' };
    var API = 'https://api.github.com';
    var SLUG = location.pathname.split('/').filter(Boolean)[0] || 'furkan';
    var PAGE_PATH = SLUG + '/index.html';
    var MEDIA = SLUG + '/media/';
    var KEY_TOKEN = 'suu-profile-token';
    var KEY_DRAFT = 'suu-profile-draft:' + SLUG;
    var TOKEN_URL = 'https://github.com/settings/personal-access-tokens/new?name=' +
        encodeURIComponent('Suu profil paneli') + '&description=' + encodeURIComponent('suuapp.com/' + SLUG + ' sayfasını düzenler') +
        '&target_name=' + CFG.owner + '&contents=write';

    // Görsel boyutları — tarayıcıda küçültülür, depoya hafif dosya gider
    var IMG = {
        // JPEG: profil fotoğrafı aynı zamanda paylaşım önizlemesi (og:image) —
        // LinkedIn gibi bazı platformlar önizlemede WebP göstermiyor
        avatar:  { max: 640, square: true, jpeg: true },
        photo:   { max: 1600 },
        project: { max: 320, square: true }
    };

    var S = {
        token: '', html: '', sha: '',
        original: null, data: null,
        pending: {},      // yeni yüklenen görseller: yol → { dataUrl }
        shown: {},        // yayından sonra Pages güncellenene kadar gösterilecek kopyalar
        busy: false
    };

    var app = document.getElementById('app');

    // ── yardımcılar ──────────────────────────────────────────
    function h(tag, props, kids) {
        var el = document.createElement(tag);
        if (props) Object.keys(props).forEach(function (k) {
            var v = props[k];
            if (v == null || v === false) return;
            if (k === 'className') el.className = v;
            else if (k === 'text') el.textContent = v;
            else if (k === 'html') el.innerHTML = v;
            else if (k.slice(0, 2) === 'on') el.addEventListener(k.slice(2), v);
            else if (k in el && k !== 'list' && k !== 'type') el[k] = v;
            else el.setAttribute(k, v === true ? '' : v);
        });
        [].concat(kids || []).forEach(function (c) {
            if (c == null || c === false) return;
            el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
        });
        return el;
    }
    function $(sel) { return app.querySelector(sel); }
    function clone(o) { return JSON.parse(JSON.stringify(o)); }
    function same(a, b) { return JSON.stringify(a) === JSON.stringify(b); }
    function today() { return new Date().toLocaleDateString('sv-SE'); }
    function icon(name) {
        var s = h('span', { className: 'ad-ic' });
        s.innerHTML = R.icon(name);
        return s;
    }

    function getPath(obj, path) {
        return path.split('.').reduce(function (o, k) { return o == null ? undefined : o[k]; }, obj);
    }
    function setPath(obj, path, value) {
        var keys = path.split('.');
        var last = keys.pop();
        var o = keys.reduce(function (o, k, i) {
            if (o[k] == null) o[k] = /^\d+$/.test(keys[i + 1] || last) ? [] : {};
            return o[k];
        }, obj);
        o[last] = value;
    }

    function b64ToText(b64) {
        var bin = atob(String(b64).replace(/\s/g, ''));
        var bytes = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
        return new TextDecoder().decode(bytes);
    }

    function debounce(fn, ms) {
        var t = 0;
        return function () { clearTimeout(t); t = setTimeout(fn, ms); };
    }

    var toastTimer = 0;
    function toast(msg, kind) {
        var t = document.getElementById('adToast');
        if (!t) { t = h('div', { id: 'adToast', className: 'ad-toast', role: 'status' }); document.body.appendChild(t); }
        t.textContent = msg;
        t.className = 'ad-toast is-on' + (kind ? ' ad-toast--' + kind : '');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { t.classList.remove('is-on'); }, 3200);
    }

    // ── anahtar ──────────────────────────────────────────────
    function readToken() {
        try { return localStorage.getItem(KEY_TOKEN) || sessionStorage.getItem(KEY_TOKEN) || ''; } catch (e) { return ''; }
    }
    function saveToken(t, remember) {
        try {
            localStorage.removeItem(KEY_TOKEN);
            sessionStorage.removeItem(KEY_TOKEN);
            (remember ? localStorage : sessionStorage).setItem(KEY_TOKEN, t);
        } catch (e) {}
    }
    function dropToken() {
        try { localStorage.removeItem(KEY_TOKEN); sessionStorage.removeItem(KEY_TOKEN); } catch (e) {}
    }

    // ── GitHub ───────────────────────────────────────────────
    function repo(p) { return '/repos/' + CFG.owner + '/' + CFG.repo + p; }

    function gh(method, path, body) {
        var headers = {
            Authorization: 'Bearer ' + S.token,
            Accept: 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        };
        if (body) headers['Content-Type'] = 'application/json';
        return fetch(API + path, { method: method, headers: headers, body: body ? JSON.stringify(body) : undefined, cache: 'no-store' })
            .then(function (r) {
                return r.text().then(function (txt) {
                    var j = null;
                    try { j = txt ? JSON.parse(txt) : null; } catch (e) {}
                    if (!r.ok) {
                        var err = new Error((j && j.message) || ('HTTP ' + r.status));
                        err.status = r.status;
                        throw err;
                    }
                    return j;
                });
            });
    }

    function explain(e) {
        var m = String((e && e.message) || '');
        if (e && e.code === 'conflict') return 'Sayfa bu sırada başka bir yerden güncellenmiş. Değişikliklerin taslakta duruyor: paneli yenile, taslağı geri yükle ve tekrar yayınla.';
        if (e && e.code === 'nopush') return 'Bu anahtarla depoya yazılamıyor. Anahtarın ayarlarında Contents → Read and write seçili olmalı.';
        if (e && e.status === 401) return 'GitHub anahtarı geçersiz ya da süresi dolmuş. Yeni bir anahtarla giriş yap.';
        if (e && e.status === 403 && /rate limit/i.test(m)) return 'GitHub istek sınırına ulaşıldı. Birkaç dakika sonra tekrar dene.';
        if (e && e.status === 403) return 'Anahtarın bu depoya yazma izni yok. GitHub\'da anahtarı düzenleyip Contents → Read and write seç.';
        if (e && e.status === 404) return 'Depo ya da sayfa bulunamadı. Anahtar ' + CFG.owner + '/' + CFG.repo + ' deposuna erişebiliyor mu? (Repository access)';
        if (e && (e.status === 409 || e.status === 422)) return 'GitHub değişikliği kabul etmedi: ' + m;
        if (e instanceof TypeError) return 'GitHub\'a bağlanılamadı. İnternet bağlantını kontrol et.';
        return m || 'Beklenmeyen bir hata oluştu.';
    }

    // ── açılış ───────────────────────────────────────────────
    function boot() {
        S.token = readToken();
        if (!S.token) return showLogin();
        load().catch(function (e) {
            if (e && (e.status === 401 || e.status === 404 || e.code === 'nopush')) dropToken();
            showLogin(explain(e));
        });
    }

    function load() {
        app.innerHTML = '<p class="ad-loading">Sayfa GitHub\'dan okunuyor…</p>';
        return gh('GET', repo('')).then(function (r) {
            if (r && r.permissions && r.permissions.push === false) {
                var e = new Error('nopush'); e.code = 'nopush'; throw e;
            }
            return gh('GET', repo('/contents/' + PAGE_PATH + '?ref=' + CFG.branch));
        }).then(function (file) {
            S.html = b64ToText(file.content);
            S.sha = file.sha;
            S.original = normalize(R.readData(S.html));
            S.data = clone(S.original);
            S.pending = {};
            showEditor();
            offerDraft();
        });
    }

    // ── giriş ekranı ─────────────────────────────────────────
    function showLogin(error) {
        app.innerHTML = '';
        var input = h('input', { type: 'password', id: 'adToken', autocomplete: 'off', spellcheck: false, placeholder: 'github_pat_…' });
        var remember = h('input', { type: 'checkbox', checked: true });
        var go = h('button', { type: 'submit', className: 'ad-btn ad-btn--primary', text: 'Giriş yap' });
        var err = h('p', { className: 'ad-error', role: 'alert', text: error || '' });
        var form = h('form', { className: 'ad-login', onsubmit: function (e) {
            e.preventDefault();
            var t = input.value.trim();
            if (!t) { err.textContent = 'Anahtarı yapıştır.'; return; }
            S.token = t;
            go.disabled = true;
            go.textContent = 'Kontrol ediliyor…';
            load().then(function () { saveToken(t, remember.checked); }).catch(function (e) {
                S.token = '';
                showLogin(explain(e));
            });
        } }, [
            h('div', { className: 'ad-login__brand' }, [h('img', { src: '/assets/brand/suu-badge-128.png', alt: '', width: 44, height: 44 }), h('div', null, [h('b', { text: 'Profil paneli' }), h('span', { text: 'suuapp.com/' + SLUG })])]),
            h('p', { className: 'ad-login__lead', text: 'Değişiklikler GitHub\'daki site deposuna kaydedilir ve 1–2 dakika içinde sayfada görünür. Giriş için bir kez GitHub erişim anahtarı oluşturman yeterli.' }),
            h('ol', { className: 'ad-steps' }, [
                h('li', null, [h('a', { href: TOKEN_URL, target: '_blank', rel: 'noopener', text: 'GitHub\'da yeni anahtar oluştur ↗' })]),
                h('li', null, ['Repository access: ', h('b', { text: 'Only select repositories → ' + CFG.owner + '/' + CFG.repo })]),
                h('li', null, ['Permissions → Repository permissions → ', h('b', { text: 'Contents: Read and write' })]),
                h('li', { text: 'Oluşan anahtarı (github_pat_ ile başlar) aşağıya yapıştır.' })
            ]),
            h('label', { className: 'ad-field' }, [h('span', { className: 'ad-label', text: 'GitHub anahtarı' }), input]),
            h('label', { className: 'ad-check' }, [remember, ' Bu cihazda hatırla']),
            err,
            go,
            h('p', { className: 'ad-note', text: 'Anahtar yalnızca bu tarayıcıda saklanır ve yalnızca GitHub\'a gönderilir. Ortak bir bilgisayardaysan "hatırla"yı kapat.' })
        ]);
        app.appendChild(h('div', { className: 'ad-login-wrap' }, [form]));
        input.focus();
    }

    // ── düzenleyici ──────────────────────────────────────────
    var TYPE_OPTS = Object.keys(R.TYPES).map(function (k) { return [k, R.TYPES[k].label]; });

    var LISTS = {
        links: {
            add: 'Bağlantı ekle',
            blank: function () { return { type: 'instagram', url: '', label: '' }; },
            fields: function (i, it) {
                var t = R.TYPES[it.type] || R.TYPES.other;
                return [
                    field('links.' + i + '.type', { label: 'Tür', type: 'select', options: TYPE_OPTS, onChange: function () { redrawList('links'); } }),
                    field('links.' + i + '.url', { label: it.type === 'email' ? 'E-posta adresi' : (it.type === 'phone' || it.type === 'whatsapp') ? 'Numara' : 'Adres', ph: t.ph, wide: true }),
                    field('links.' + i + '.label', { label: 'Görünen ad (isteğe bağlı)', ph: t.label })
                ];
            }
        },
        stats: {
            add: 'Rakam ekle', max: 4,
            blank: function () { return { value: '', label: '' }; },
            fields: function (i) {
                return [
                    field('stats.' + i + '.value', { label: 'Değer', ph: '4.9★' }),
                    field('stats.' + i + '.label', { label: 'Açıklama', ph: 'Google Play' })
                ];
            }
        },
        photos: {
            add: 'Fotoğraf ekle', multi: 'photo',
            blank: function () { return { src: '', alt: '' }; },
            fields: function (i) {
                return [
                    imageField('photos.' + i + '.src', 'photo', 'Fotoğraf'),
                    field('photos.' + i + '.alt', { label: 'Açıklama (ekran okuyucu ve büyük görünüm için)', ph: 'örn. Suu lansmanında' })
                ];
            }
        },
        projects: {
            add: 'İş ekle',
            blank: function () { return { title: '', role: '', period: '', description: '', url: '', image: '' }; },
            fields: function (i) {
                var p = 'projects.' + i + '.';
                return [
                    imageField(p + 'image', 'project', 'Logo / görsel'),
                    field(p + 'title', { label: 'Başlık', ph: 'Suu' }),
                    field(p + 'role', { label: 'Rolün', ph: 'Kurucu & geliştirici' }),
                    field(p + 'period', { label: 'Dönem', ph: '2024 – bugün' }),
                    field(p + 'url', { label: 'Bağlantı (isteğe bağlı)', ph: 'https://…', wide: true }),
                    field(p + 'description', { label: 'Kısa açıklama', type: 'textarea', rows: 3, wide: true })
                ];
            }
        },
        accounts: {
            add: 'Hesap ekle',
            blank: function () { return { platform: 'instagram', name: '', handle: '', url: '' }; },
            fields: function (i) {
                var p = 'accounts.' + i + '.';
                return [
                    field(p + 'platform', { label: 'Platform', type: 'select', options: TYPE_OPTS }),
                    field(p + 'name', { label: 'Hesap adı', ph: 'Suu' }),
                    field(p + 'handle', { label: 'Kullanıcı adı / alt yazı', ph: '@suu.turkey' }),
                    field(p + 'url', { label: 'Adres', ph: 'https://…', wide: true })
                ];
            }
        },
        press: {
            add: 'Haber ekle',
            blank: function () { return { outlet: '', title: '', url: '', date: '' }; },
            fields: function (i) {
                var p = 'press.' + i + '.';
                return [
                    field(p + 'outlet', { label: 'Yayın', ph: 'örn. Webrazzi' }),
                    field(p + 'date', { label: 'Tarih', ph: 'Ekim 2026' }),
                    field(p + 'title', { label: 'Başlık', ph: 'Haberin başlığı', wide: true }),
                    field(p + 'url', { label: 'Bağlantı', ph: 'https://…', wide: true })
                ];
            }
        }
    };

    function field(path, o) {
        var val = getPath(S.data, path);
        var input;
        if (o.type === 'textarea') input = h('textarea', { rows: o.rows || 4 });
        else if (o.type === 'select') {
            input = h('select');
            o.options.forEach(function (op) { input.appendChild(h('option', { value: op[0], text: op[1] })); });
        } else input = h('input', { type: 'text' });
        input.value = val == null ? '' : val;
        if (o.ph) input.placeholder = o.ph;
        if (o.max) input.maxLength = o.max;
        input.addEventListener(o.type === 'select' ? 'change' : 'input', function () {
            setPath(S.data, path, input.value);
            changed();
            if (o.onChange) o.onChange(input.value);
        });
        return h('label', { className: 'ad-field' + (o.wide ? ' ad-field--wide' : '') }, [
            h('span', { className: 'ad-label', text: o.label }),
            input,
            o.hint ? h('small', { className: 'ad-hint', text: o.hint }) : null
        ]);
    }

    function shownSrc(src) {
        if (!src) return '';
        if (S.pending[src]) return S.pending[src].dataUrl;
        if (S.shown[src]) return S.shown[src];
        return src;
    }

    function imageField(path, kind, label) {
        var box = h('div', { className: 'ad-image ad-image--' + kind });
        function draw() {
            box.innerHTML = '';
            var src = getPath(S.data, path);
            var file = h('input', { type: 'file', accept: 'image/*', className: 'ad-file' });
            file.addEventListener('change', function () {
                if (!file.files[0]) return;
                addImage(file.files[0], kind).then(function (p) {
                    setPath(S.data, path, p);
                    draw();
                    changed();
                }, function (e) { toast(e.message, 'error'); });
            });
            box.appendChild(src ? h('img', { src: shownSrc(src), alt: '' }) : h('span', { className: 'ad-image__empty', text: 'Görsel yok' }));
            box.appendChild(h('div', { className: 'ad-image__btns' }, [
                h('button', { type: 'button', className: 'ad-btn ad-btn--sm', text: src ? 'Değiştir' : 'Görsel seç', onclick: function () { file.click(); } }),
                src && kind !== 'avatar' ? h('button', { type: 'button', className: 'ad-btn ad-btn--sm ad-btn--ghost', text: 'Kaldır', onclick: function () { setPath(S.data, path, ''); draw(); changed(); } }) : null,
                file
            ]));
        }
        draw();
        return h('div', { className: 'ad-field' + (kind === 'photo' ? ' ad-field--photo' : '') }, [h('span', { className: 'ad-label', text: label }), box]);
    }

    // Dosyayı tarayıcıda küçült, depoya gidecek yolu ver
    function addImage(file, kind) {
        return new Promise(function (resolve, reject) {
            if (file.size > 30 * 1024 * 1024) return reject(new Error('Dosya çok büyük (en fazla 30 MB).'));
            var url = URL.createObjectURL(file);
            var img = new Image();
            img.onload = function () {
                URL.revokeObjectURL(url);
                try {
                    var spec = IMG[kind];
                    var w = img.naturalWidth, ht = img.naturalHeight;
                    var sx = 0, sy = 0, sw = w, sh = ht;
                    if (spec.square) { var s = Math.min(w, ht); sx = (w - s) / 2; sy = (ht - s) / 2; sw = sh = s; }
                    var k = Math.min(1, spec.max / Math.max(sw, sh));
                    var c = document.createElement('canvas');
                    c.width = Math.max(1, Math.round(sw * k));
                    c.height = Math.max(1, Math.round(sh * k));
                    var ctx = c.getContext('2d');
                    ctx.imageSmoothingQuality = 'high';
                    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, c.width, c.height);
                    // WebP'yi kodlayamayan tarayıcıda (eski Safari) JPEG
                    var webp = spec.jpeg ? '' : c.toDataURL('image/webp', 0.84);
                    var dataUrl = /^data:image\/webp/.test(webp) ? webp : c.toDataURL('image/jpeg', 0.86);
                    var ext = /^data:image\/webp/.test(dataUrl) ? 'webp' : 'jpg';
                    var path = '/' + MEDIA + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 6) + '.' + ext;
                    S.pending[path] = { dataUrl: dataUrl };
                    resolve(path);
                } catch (e) { reject(new Error('Görsel işlenemedi.')); }
            };
            img.onerror = function () {
                URL.revokeObjectURL(url);
                reject(new Error('Bu dosya açılamadı. HEIC fotoğrafsa JPG olarak kaydedip tekrar dene.'));
            };
            img.src = url;
        });
    }

    function listCard(key, title, hint) {
        var body = h('div', { className: 'ad-list', id: 'list-' + key });
        var card = h('section', { className: 'ad-card' }, [
            h('header', { className: 'ad-card__head' }, [h('h2', { text: title }), hint ? h('p', { text: hint }) : null]),
            body
        ]);
        drawList(key, body);
        return card;
    }

    function redrawList(key) {
        var body = document.getElementById('list-' + key);
        if (body) drawList(key, body);
    }

    function drawList(key, body) {
        var def = LISTS[key];
        if (!Array.isArray(S.data[key])) S.data[key] = [];
        var items = S.data[key];
        body.innerHTML = '';
        items.forEach(function (it, i) {
            var move = function (d) {
                return function () {
                    var j = i + d;
                    if (j < 0 || j >= items.length) return;
                    var tmp = items[i]; items[i] = items[j]; items[j] = tmp;
                    redrawList(key); changed();
                };
            };
            body.appendChild(h('div', { className: 'ad-item' }, [
                h('div', { className: 'ad-item__fields' }, def.fields(i, it)),
                h('div', { className: 'ad-item__tools' }, [
                    h('button', { type: 'button', className: 'ad-tool', title: 'Yukarı', 'aria-label': 'Yukarı taşı', disabled: i === 0, text: '↑', onclick: move(-1) }),
                    h('button', { type: 'button', className: 'ad-tool', title: 'Aşağı', 'aria-label': 'Aşağı taşı', disabled: i === items.length - 1, text: '↓', onclick: move(1) }),
                    h('button', { type: 'button', className: 'ad-tool ad-tool--del', title: 'Sil', 'aria-label': 'Sil', text: '×', onclick: function () {
                        items.splice(i, 1); redrawList(key); changed();
                    } })
                ])
            ]));
        });
        var tools = [];
        if (!def.max || items.length < def.max) {
            tools.push(h('button', { type: 'button', className: 'ad-btn ad-btn--add', text: '+ ' + def.add, onclick: function () {
                if (def.multi) return pickMany(key, def.multi);
                items.push(def.blank()); redrawList(key); changed();
                var last = body.querySelector('.ad-item:last-of-type input, .ad-item:last-of-type select');
                if (last) last.focus();
            } }));
        }
        body.appendChild(h('div', { className: 'ad-list__foot' }, tools));
    }

    // Fotoğraflar: birden çok dosya tek seferde
    function pickMany(key, kind) {
        var file = h('input', { type: 'file', accept: 'image/*', multiple: true, className: 'ad-file' });
        file.addEventListener('change', function () {
            var files = Array.prototype.slice.call(file.files);
            if (!files.length) return;
            toast(files.length + ' fotoğraf hazırlanıyor…');
            files.reduce(function (p, f) {
                return p.then(function () {
                    return addImage(f, kind).then(function (path) {
                        S.data[key].push({ src: path, alt: '' });
                    }, function (e) { toast(f.name + ': ' + e.message, 'error'); });
                });
            }, Promise.resolve()).then(function () { redrawList(key); changed(); });
            file.remove();
        });
        document.body.appendChild(file);
        file.click();
    }

    function card(title, hint, kids) {
        return h('section', { className: 'ad-card' }, [
            h('header', { className: 'ad-card__head' }, [h('h2', { text: title }), hint ? h('p', { text: hint }) : null]),
            h('div', { className: 'ad-grid' }, kids)
        ]);
    }

    // Eksik alanları hem yayındaki kopyaya hem çalışma kopyasına aynı biçimde ekle —
    // yalnızca birine eklenseydi panel hiçbir şey değişmeden "değişiklik var" derdi.
    function normalize(d) {
        d = d || {};
        ['links', 'stats', 'photos', 'projects', 'accounts', 'press'].forEach(function (k) {
            if (!Array.isArray(d[k])) d[k] = [];
        });
        if (!d.sections || typeof d.sections !== 'object') d.sections = {};
        if (!d.cta || typeof d.cta !== 'object') d.cta = { label: '', url: '' };
        if (!d.slug) d.slug = SLUG;
        return d;
    }

    function showEditor() {
        app.innerHTML = '';

        var form = h('div', { className: 'ad-form', id: 'adForm' }, [
            h('div', { id: 'adBanner' }),
            card('Profil', 'Sayfanın en üstü: fotoğraf, isim ve kısa tanım.', [
                imageField('avatar', 'avatar', 'Profil fotoğrafı'),
                field('name', { label: 'Ad soyad', ph: 'Furkan Mert Fındıklı' }),
                field('headline', { label: 'Kısa tanım', ph: 'Suu\'nun kurucusu · Mobil uygulama geliştirici', wide: true }),
                field('location', { label: 'Konum', ph: 'İstanbul' }),
                field('status', { label: 'Durum rozeti (isteğe bağlı)', ph: 'örn. Yeni iş birliklerine açığım', hint: 'Boş bırakırsan görünmez.' }),
                field('cta.label', { label: 'Ana düğme yazısı', ph: 'Suu\'yu ücretsiz indir' }),
                field('cta.url', { label: 'Ana düğme bağlantısı', ph: '/app?src=' + SLUG })
            ]),
            listCard('links', 'Bağlantılar', 'Instagram, LinkedIn, e-posta… Adresi boş bırakılan satır sayfada görünmez.'),
            card('Hakkımda', 'Paragrafları boş bir satırla ayır.', [
                field('bio', { label: 'Tanıtım yazısı', type: 'textarea', rows: 7, wide: true })
            ]),
            listCard('stats', 'Öne çıkan rakamlar', 'Hakkımda kartının altında görünür; en fazla 4.'),
            listCard('photos', 'Fotoğraflar', '3 ve üzeri fotoğraf kayan şerit olur. Fotoğraflar yüklenirken otomatik küçültülür.'),
            listCard('projects', 'Yaptığım işler', null),
            listCard('accounts', 'İş hesapları', 'Şirket ya da marka hesapları.'),
            listCard('press', 'Basında', 'Haber yoksa bu bölüm sayfada görünmez.'),
            card('Bölüm başlıkları', 'Sayfadaki küçük başlıkları değiştirmek istersen.', Object.keys(R.SECTIONS).map(function (k) {
                return field('sections.' + k, { label: R.SECTIONS[k], ph: R.SECTIONS[k] });
            }))
        ]);

        var frame = h('iframe', { id: 'adPreview', title: 'Önizleme', sandbox: 'allow-same-origin', loading: 'eager' });
        var preview = h('aside', { className: 'ad-preview' }, [
            h('div', { className: 'ad-phone' }, [frame]),
            h('a', { className: 'ad-preview__open', href: '/' + SLUG + '/', target: '_blank', rel: 'noopener', text: 'Yayındaki sayfayı aç ↗' })
        ]);

        var tabs = h('div', { className: 'ad-tabs', role: 'tablist' }, [
            h('button', { type: 'button', className: 'is-on', 'data-tab': 'form', text: 'Düzenle', onclick: tab }),
            h('button', { type: 'button', 'data-tab': 'preview', text: 'Önizle', onclick: tab })
        ]);

        app.appendChild(h('header', { className: 'ad-top' }, [
            h('a', { className: 'ad-top__brand', href: '/' + SLUG + '/', target: '_blank', rel: 'noopener' }, [
                h('img', { src: '/assets/brand/suu-badge-128.png', alt: '', width: 32, height: 32 }),
                h('span', null, [h('b', { text: 'Profil paneli' }), h('small', { text: 'suuapp.com/' + SLUG })])
            ]),
            h('button', { type: 'button', className: 'ad-btn ad-btn--sm ad-btn--ghost', text: 'Çıkış', onclick: function () {
                if (dirty() && !confirm('Yayınlanmamış değişiklikler taslak olarak bu tarayıcıda kalacak. Çıkılsın mı?')) return;
                dropToken();
                location.reload();
            } })
        ]));
        app.appendChild(tabs);
        app.appendChild(h('div', { className: 'ad-main', 'data-view': 'form' }, [form, preview]));
        app.appendChild(h('footer', { className: 'ad-bar' }, [
            h('span', { className: 'ad-bar__status', id: 'adStatus' }),
            h('button', { type: 'button', className: 'ad-btn ad-btn--ghost', id: 'adRevert', text: 'Geri al', onclick: revert }),
            h('button', { type: 'button', className: 'ad-btn ad-btn--primary', id: 'adPublish', text: 'Yayınla', onclick: publish })
        ]));

        renderPreview(true);
        updateStatus();
    }

    function tab(e) {
        var which = e.currentTarget.getAttribute('data-tab');
        Array.prototype.forEach.call(app.querySelectorAll('.ad-tabs button'), function (b) {
            b.classList.toggle('is-on', b.getAttribute('data-tab') === which);
        });
        $('.ad-main').setAttribute('data-view', which);
        if (which === 'preview') renderPreview(false);
        window.scrollTo(0, 0);
    }

    // ── önizleme ─────────────────────────────────────────────
    function renderPreview(full) {
        var frame = document.getElementById('adPreview');
        if (!frame) return;
        var opts = { asset: shownSrc };
        var doc = frame.contentDocument;
        var main = !full && doc && doc.getElementById('profile');
        if (main) {
            main.innerHTML = R.body(S.data, opts);
            return;
        }
        var html = R.apply(S.html, S.data, opts)
            .replace(/<script\b[^>]*\bsrc="[^"]*"[^>]*><\/script>\s*/g, '')
            .replace('</head>', '<style>.pf-in{animation:none!important}</style></head>');
        frame.srcdoc = html;
    }

    var previewSoon = debounce(function () { renderPreview(false); }, 250);

    // ── değişiklik, taslak ───────────────────────────────────
    function dirty() {
        return !same(S.data, S.original);
    }

    function updateStatus() {
        var st = document.getElementById('adStatus');
        if (!st || S.busy) return;
        var d = dirty();
        st.textContent = d ? 'Yayınlanmamış değişiklik var' : 'Yayındaki sürümle aynı';
        st.className = 'ad-bar__status' + (d ? ' is-dirty' : '');
        document.getElementById('adPublish').disabled = !d;
        document.getElementById('adRevert').disabled = !d;
    }

    var saveDraft = debounce(function () {
        if (!S.data) return;
        try {
            if (!dirty()) { localStorage.removeItem(KEY_DRAFT); return; }
            var used = images(S.data);
            var pending = {};
            Object.keys(S.pending).forEach(function (p) { if (used[p]) pending[p] = S.pending[p]; });
            try {
                localStorage.setItem(KEY_DRAFT, JSON.stringify({ base: S.sha, at: Date.now(), data: S.data, pending: pending }));
            } catch (e) {
                // Kota dolduysa fotoğraflarsız sakla — en azından yazılar kaybolmasın
                localStorage.setItem(KEY_DRAFT, JSON.stringify({ base: S.sha, at: Date.now(), data: S.data, pending: {} }));
            }
        } catch (e) {}
    }, 600);

    function changed() {
        updateStatus();
        previewSoon();
        saveDraft();
    }

    function offerDraft() {
        var draft = null;
        try { draft = JSON.parse(localStorage.getItem(KEY_DRAFT) || 'null'); } catch (e) {}
        if (!draft || !draft.data || same(draft.data, S.original)) return;
        var banner = document.getElementById('adBanner');
        var when = new Date(draft.at || Date.now()).toLocaleString('tr-TR', { dateStyle: 'medium', timeStyle: 'short' });
        banner.appendChild(h('div', { className: 'ad-banner' }, [
            h('p', null, [h('b', { text: 'Yayınlanmamış bir taslağın var' }), ' (' + when + ').' +
                (draft.base !== S.sha ? ' Sayfa o zamandan beri güncellenmiş; geri yüklersen o değişikliklerin üzerine yazarsın.' : '')]),
            h('div', null, [
                h('button', { type: 'button', className: 'ad-btn ad-btn--sm ad-btn--primary', text: 'Taslağı geri yükle', onclick: function () {
                    S.data = normalize(draft.data);
                    S.pending = draft.pending || {};
                    // Kota yüzünden fotoğrafsız saklanmış taslak: dosyası olmayan yeni yolları at,
                    // yoksa sayfaya kırık görsel yayınlanır
                    var known = images(S.original);
                    var ok = function (p) { return !p || known[p] || S.pending[p] || p.indexOf('/' + MEDIA) !== 0; };
                    var lost = 0;
                    if (!ok(S.data.avatar)) { S.data.avatar = S.original.avatar; lost++; }
                    S.data.photos = S.data.photos.filter(function (p) { if (ok(p.src)) return true; lost++; return false; });
                    S.data.projects.forEach(function (p) { if (!ok(p.image)) { p.image = ''; lost++; } });
                    if (lost) setTimeout(function () { toast(lost + ' fotoğraf taslakta saklanamamıştı; yeniden eklemen gerekiyor.', 'error'); }, 400);
                    showEditor();
                    changed();
                    toast('Taslak geri yüklendi.');
                } }),
                h('button', { type: 'button', className: 'ad-btn ad-btn--sm ad-btn--ghost', text: 'Sil', onclick: function () {
                    try { localStorage.removeItem(KEY_DRAFT); } catch (e) {}
                    banner.innerHTML = '';
                } })
            ])
        ]));
    }

    function revert() {
        if (!confirm('Yayınlanmamış tüm değişiklikler silinsin mi?')) return;
        S.data = clone(S.original);
        S.pending = {};
        try { localStorage.removeItem(KEY_DRAFT); } catch (e) {}
        showEditor();
        toast('Yayındaki sürüme dönüldü.');
    }

    // Verideki tüm görsel yolları
    function images(d) {
        var out = {};
        var add = function (s) { if (s) out[s] = true; };
        add(d.avatar);
        (d.photos || []).forEach(function (p) { add(p && p.src); });
        (d.projects || []).forEach(function (p) { add(p && p.image); });
        return out;
    }

    // ── yayın: tek commit ────────────────────────────────────
    function setBusy(on, msg) {
        S.busy = on;
        var st = document.getElementById('adStatus');
        if (st && msg) { st.textContent = msg; st.className = 'ad-bar__status is-busy'; }
        ['adPublish', 'adRevert'].forEach(function (id) {
            var b = document.getElementById(id);
            if (b) b.disabled = on;
        });
        if (!on) updateStatus();
    }

    function publish() {
        if (S.busy || !dirty()) return;
        if (!String(S.data.name || '').trim()) { toast('Ad soyad boş olamaz.', 'error'); return; }

        var data = clone(S.data);
        data.updated = today();
        var html = R.apply(S.html, data);
        var used = images(data);
        var uploads = Object.keys(S.pending).filter(function (p) { return used[p]; });
        var orphans = Object.keys(images(S.original)).filter(function (p) {
            return p.indexOf('/' + MEDIA) === 0 && !used[p];
        });
        var shas = {};
        var commit = null;

        setBusy(true, 'Yayınlanıyor…');

        // Silinecekler yalnızca depoda gerçekten var olanlar (yoksa GitHub tüm commit'i reddeder)
        var mediaList = orphans.length
            ? gh('GET', repo('/contents/' + MEDIA.replace(/\/$/, '') + '?ref=' + CFG.branch))
                .catch(function (e) { if (e.status === 404) return []; throw e; })
            : Promise.resolve([]);

        mediaList.then(function (list) {
            var have = {};
            (list || []).forEach(function (f) { have['/' + f.path] = true; });
            orphans = orphans.filter(function (p) { return have[p]; });

            return uploads.reduce(function (p, path, i) {
                return p.then(function () {
                    setBusy(true, 'Fotoğraflar yükleniyor (' + (i + 1) + '/' + uploads.length + ')…');
                    return gh('POST', repo('/git/blobs'), { content: S.pending[path].dataUrl.split(',')[1], encoding: 'base64' })
                        .then(function (b) { shas[path] = b.sha; });
                });
            }, Promise.resolve());
        }).then(function () {
            setBusy(true, 'Kaydediliyor…');
            return attempt(0);
        }).then(function () {
            // Pages yayını bitene kadar yeni fotoğrafları yerel kopyadan göster
            uploads.forEach(function (p) { S.shown[p] = S.pending[p].dataUrl; });
            S.html = html;
            S.original = data;
            S.data = clone(data);
            S.pending = {};
            try { localStorage.removeItem(KEY_DRAFT); } catch (e) {}
            return gh('GET', repo('/contents/' + PAGE_PATH + '?ref=' + commit.sha)).then(function (f) { S.sha = f.sha; });
        }).then(function () {
            setBusy(false);
            showEditor();
            published(commit);
        }).catch(function (e) {
            setBusy(false);
            var st = document.getElementById('adStatus');
            if (st) { st.textContent = explain(e); st.className = 'ad-bar__status is-error'; }
            toast(explain(e), 'error');
        });

        function attempt(n) {
            var head;
            return gh('GET', repo('/git/ref/heads/' + CFG.branch)).then(function (ref) {
                head = ref.object.sha;
                // Bu sırada sayfa başka yerden değiştiyse üzerine yazma
                return gh('GET', repo('/contents/' + PAGE_PATH + '?ref=' + head));
            }).then(function (cur) {
                if (cur.sha !== S.sha) { var e = new Error('conflict'); e.code = 'conflict'; throw e; }
                return gh('GET', repo('/git/commits/' + head));
            }).then(function (base) {
                var entries = [{ path: PAGE_PATH, mode: '100644', type: 'blob', content: html }]
                    .concat(uploads.map(function (p) { return { path: p.slice(1), mode: '100644', type: 'blob', sha: shas[p] }; }))
                    .concat(orphans.map(function (p) { return { path: p.slice(1), mode: '100644', type: 'blob', sha: null }; }));
                return gh('POST', repo('/git/trees'), { base_tree: base.tree.sha, tree: entries });
            }).then(function (tree) {
                var parts = [];
                if (uploads.length) parts.push(uploads.length + ' yeni görsel');
                if (orphans.length) parts.push(orphans.length + ' görsel kaldırıldı');
                return gh('POST', repo('/git/commits'), {
                    message: 'profil(' + SLUG + '): panelden güncellendi' + (parts.length ? '\n\n' + parts.join(', ') : ''),
                    tree: tree.sha,
                    parents: [head]
                });
            }).then(function (c) {
                commit = c;
                return gh('PATCH', repo('/git/refs/heads/' + CFG.branch), { sha: c.sha, force: false });
            }).catch(function (e) {
                // Ana dal tam bu sırada ilerlediyse (başka bir commit) baştan dene
                if (e.status === 422 && n < 2) return attempt(n + 1);
                throw e;
            });
        }
    }

    function published(c) {
        var banner = document.getElementById('adBanner');
        if (!banner) return;
        banner.innerHTML = '';
        banner.appendChild(h('div', { className: 'ad-banner ad-banner--ok' }, [
            h('p', null, [h('b', { text: 'Yayınlandı.' }), ' Sayfa 1–2 dakika içinde güncellenir (tarayıcın eski sürümü gösterirse sayfayı yenile).']),
            h('div', null, [
                h('a', { className: 'ad-btn ad-btn--sm ad-btn--primary', href: '/' + SLUG + '/', target: '_blank', rel: 'noopener', text: 'Sayfayı aç ↗' }),
                c && c.html_url ? h('a', { className: 'ad-btn ad-btn--sm ad-btn--ghost', href: c.html_url, target: '_blank', rel: 'noopener', text: 'Değişikliği GitHub\'da gör' }) : null
            ])
        ]));
        window.scrollTo({ top: 0, behavior: 'smooth' });
        toast('Yayınlandı.', 'ok');
    }

    window.addEventListener('beforeunload', function (e) {
        if (S.data && dirty() && !S.busy) { e.preventDefault(); e.returnValue = ''; }
    });

    boot();
})();
