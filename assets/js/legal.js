/**
 * Suu — Yasal sayfalar (gizlilik politikası, kullanım şartları)
 *
 * Yedi dil tek URL'de durur; her dil bir .legal-doc bloğu:
 *   <div class="legal-doc" data-lang="en" data-title="…" data-updated="…">
 * Bu dosya seçili dili gösterir, içindekiler listesini o dilin
 * başlıklarından kurar ve sayfa kabuğundaki metinleri (menü düğmesi,
 * alt bilgi bağlantıları) aynı dile çevirir. Hukuki metne dokunmaz —
 * yalnızca başlıklardaki "1." numarasını rozete sarar.
 *
 * Dil sırası: ?lang= → #xx (ya da bölüm bağlantısı #xx-N) → sitede seçilmiş
 * dil (suu-lang) → tarayıcı dili → tr.
 * Sitedeki bağlantılar dil belirtmeden geliyor; Almanca/İtalyanca/Ukraynaca
 * okur Türkçe sekmeye düşmesin diye.
 */
(function () {
    'use strict';

    var SUPPORTED = ['tr', 'en', 'ar', 'ru', 'de', 'it', 'uk'];

    var UI = {
        tr: { toc: 'İçindekiler', top: 'Başa dön', cta: 'Ücretsiz İndir', skip: 'İçeriğe geç', langs: 'Dil seçimi', docs: 'Yasal belgeler' },
        en: { toc: 'Contents', top: 'Back to top', cta: 'Download Free', skip: 'Skip to content', langs: 'Language', docs: 'Legal documents' },
        ar: { toc: 'المحتويات', top: 'العودة إلى الأعلى', cta: 'تنزيل مجاني', skip: 'تخطَّ إلى المحتوى', langs: 'اللغة', docs: 'المستندات القانونية' },
        ru: { toc: 'Содержание', top: 'Наверх', cta: 'Скачать бесплатно', skip: 'Перейти к содержимому', langs: 'Язык', docs: 'Юридические документы' },
        de: { toc: 'Inhalt', top: 'Nach oben', cta: 'Gratis laden', skip: 'Zum Inhalt springen', langs: 'Sprache', docs: 'Rechtliche Dokumente' },
        it: { toc: 'Indice', top: 'Torna su', cta: 'Scarica gratis', skip: 'Vai al contenuto', langs: 'Lingua', docs: 'Documenti legali' },
        uk: { toc: 'Зміст', top: 'Нагору', cta: 'Завантажити безкоштовно', skip: 'Перейти до вмісту', langs: 'Мова', docs: 'Юридичні документи' }
    };

    // Alt bilgideki belge bağlantıları — adlar her sayfanın kendi başlığından
    var DOCS = {
        privacy: {
            href: '/gizlilik-politikasi.html',
            name: { tr: 'Gizlilik Politikası', en: 'Privacy Policy', ar: 'سياسة الخصوصية', ru: 'Политика конфиденциальности', de: 'Datenschutzerklärung', it: 'Informativa sulla privacy', uk: 'Політика конфіденційності' }
        },
        terms: {
            href: '/kullanim-sartlari.html',
            name: { tr: 'Kullanım Şartları', en: 'Terms of Use', ar: 'شروط الاستخدام', ru: 'Условия использования', de: 'Nutzungsbedingungen', it: 'Termini di utilizzo', uk: 'Умови використання' }
        },
        deletion: {
            href: '/delete-account.html',
            name: { tr: 'Hesap Silme', en: 'Delete Account', ar: 'حذف الحساب', ru: 'Удаление аккаунта', de: 'Konto löschen', it: "Eliminazione dell'account", uk: 'Видалення облікового запису' }
        }
    };

    var HOME = {
        tr: '/', en: '/hosgeldiniz-en.html', ar: '/hosgeldiniz-ar.html', ru: '/hosgeldiniz-ru.html',
        de: '/hosgeldiniz-de.html', it: '/hosgeldiniz-it.html', uk: '/hosgeldiniz-uk.html'
    };

    var NUM_RE = /^\s*(\d+)\.\s+/;        // "1. Veri Sorumlusu"
    var SUBNUM_RE = /^\s*(\d+\.\d+)\.?\s+/; // "2.1 Kişisel Bilgiler"

    var docs = document.querySelectorAll('.legal-doc');
    if (!docs.length) return;

    var buttons = document.querySelectorAll('.legal-langs button');
    var footerTexts = document.querySelectorAll('.footer-text');
    var titleEl = document.getElementById('docTitle');
    var updatedEl = document.getElementById('docUpdated');
    var toc = document.getElementById('legalToc');
    var tocList = document.getElementById('legalTocList');
    var tocCount = document.getElementById('legalTocCount');
    var topBtn = document.getElementById('legalTop');
    var desktop = window.matchMedia ? window.matchMedia('(min-width: 1024px)') : null;

    function sections(doc) {
        return doc.querySelectorAll('h2, .contact-box > h3');
    }

    // "1. Başlık" → <span class="legal-num">1</span>Başlık — yalnızca ilk metin düğümü
    function decorate(doc) {
        var lang = doc.getAttribute('data-lang');
        Array.prototype.forEach.call(sections(doc), function (h, i) {
            var node = h.firstChild;
            var m = node && node.nodeType === 3 ? NUM_RE.exec(node.nodeValue) : null;
            var num = m ? m[1] : String(i + 1);
            if (m) {
                node.nodeValue = node.nodeValue.slice(m[0].length);
                var badge = document.createElement('span');
                badge.className = 'legal-num';
                badge.textContent = num;
                h.insertBefore(badge, node);
            }
            if (!h.id) h.id = lang + '-' + num;
            h.setAttribute('data-num', num);
        });
        Array.prototype.forEach.call(doc.querySelectorAll('h3'), function (h) {
            if (h.parentNode.classList.contains('contact-box')) return;
            var node = h.firstChild;
            var m = node && node.nodeType === 3 ? SUBNUM_RE.exec(node.nodeValue) : null;
            if (!m) return;
            node.nodeValue = node.nodeValue.slice(m[0].length);
            var span = document.createElement('span');
            span.className = 'legal-subnum';
            span.textContent = m[1];
            h.insertBefore(span, node);
        });
    }

    function headingText(h) {
        var copy = h.cloneNode(true);
        var badge = copy.querySelector('.legal-num');
        if (badge) badge.remove();
        return copy.textContent.trim();
    }

    function buildToc(doc) {
        if (!toc || !tocList) return;
        var heads = sections(doc);
        tocList.innerHTML = '';
        Array.prototype.forEach.call(heads, function (h) {
            var li = document.createElement('li');
            var a = document.createElement('a');
            var n = document.createElement('span');
            var t = document.createElement('span');
            a.href = '#' + h.id;
            a.setAttribute('data-target', h.id);
            n.className = 'legal-toc__num';
            n.textContent = h.getAttribute('data-num');
            t.textContent = headingText(h);
            a.appendChild(n);
            a.appendChild(t);
            li.appendChild(a);
            tocList.appendChild(li);
        });
        if (tocCount) tocCount.textContent = heads.length;
        toc.hidden = heads.length === 0;
        spy(heads);
    }

    // Okunan bölümü içindekilerde işaretle: ekranın üstünü geçmiş son başlık.
    // (Kesişim gözlemcisi yalnızca başlık bandı geçerken tetikleniyordu —
    // bir bölümün ortasına atlayınca hiçbir satır işaretli kalmıyordu.)
    var spyHeads = [];
    var spyQueued = false;

    function spy(heads) {
        spyHeads = Array.prototype.slice.call(heads);
        updateSpy();
    }

    function updateSpy() {
        spyQueued = false;
        if (!tocList) return;
        var line = 96;                  // yapışkan menünün hemen altı
        var current = null;
        for (var i = 0; i < spyHeads.length; i++) {
            if (spyHeads[i].getBoundingClientRect().top - line <= 0) current = spyHeads[i].id;
            else break;
        }
        // Son bölüm kısaysa başlığı çizgiye hiç ulaşamaz — sayfa sonunda onu işaretle
        var doc = document.documentElement;
        if (spyHeads.length && current && window.innerHeight + window.scrollY >= doc.scrollHeight - 4) {
            current = spyHeads[spyHeads.length - 1].id;
        }
        Array.prototype.forEach.call(tocList.querySelectorAll('a'), function (a) {
            if (a.getAttribute('data-target') === current) a.setAttribute('aria-current', 'true');
            else a.removeAttribute('aria-current');
        });
    }

    window.addEventListener('scroll', function () {
        if (spyQueued) return;
        spyQueued = true;
        window.requestAnimationFrame(updateSpy);
    }, { passive: true });

    function setText(selector, value) {
        Array.prototype.forEach.call(document.querySelectorAll(selector), function (el) { el.textContent = value; });
    }

    function setLanguage(lang, updateUrl) {
        var root = document.documentElement;
        var ui = UI[lang];
        var active = null;

        root.lang = lang;
        root.dir = lang === 'ar' ? 'rtl' : 'ltr';

        Array.prototype.forEach.call(docs, function (doc) {
            var on = doc.getAttribute('data-lang') === lang;
            doc.classList.toggle('active', on);
            if (on) active = doc;
        });
        Array.prototype.forEach.call(footerTexts, function (p) {
            p.classList.toggle('active', p.getAttribute('data-lang') === lang);
        });
        Array.prototype.forEach.call(buttons, function (b) {
            var on = b.getAttribute('data-lang') === lang;
            b.classList.toggle('active', on);
            b.setAttribute('aria-pressed', on ? 'true' : 'false');
        });

        if (active) {
            var title = active.getAttribute('data-title') || '';
            document.title = title;
            // Başlıkta marka tekrarı yok: "Suu - Gizlilik Politikası" → "Gizlilik Politikası"
            if (titleEl) titleEl.textContent = title.replace(/^Suu\s*[-–—]\s*/, '');
            if (updatedEl) updatedEl.textContent = active.getAttribute('data-updated') || '';
            buildToc(active);
        }

        // Sayfa kabuğu
        setText('[data-ui="toc"]', ui.toc);
        setText('[data-ui="cta"]', ui.cta);
        setText('[data-ui="skip"]', ui.skip);
        Array.prototype.forEach.call(document.querySelectorAll('[data-ui-label]'), function (el) {
            el.setAttribute('aria-label', ui[el.getAttribute('data-ui-label')]);
        });
        if (topBtn) { topBtn.setAttribute('aria-label', ui.top); topBtn.title = ui.top; }
        Array.prototype.forEach.call(document.querySelectorAll('[data-home]'), function (a) { a.href = HOME[lang]; });
        Array.prototype.forEach.call(document.querySelectorAll('[data-doc]'), function (a) {
            var d = DOCS[a.getAttribute('data-doc')];
            a.textContent = d.name[lang];
            a.href = lang === 'tr' ? d.href : d.href + '?lang=' + lang;
        });

        if (updateUrl) {
            try {
                var url = new URL(window.location.href);
                if (lang === 'tr') url.searchParams.delete('lang');
                else url.searchParams.set('lang', lang);
                url.hash = '';
                history.replaceState(null, '', url);
            } catch (e) {}
        }
    }

    function pick(value) {
        var code = (value || '').toLowerCase().slice(0, 2);
        return SUPPORTED.indexOf(code) !== -1 ? code : null;
    }

    function initialLanguage() {
        var lang = null;
        try { lang = pick(new URLSearchParams(window.location.search).get('lang')); } catch (e) {}
        if (lang) return lang;
        if (window.location.hash.length === 3) {
            lang = pick(window.location.hash.slice(1));
            if (lang) return lang;
        }
        var section = /^#(\w\w)-\d+$/.exec(window.location.hash);   // bölüm bağlantısı: #de-3
        if (section && (lang = pick(section[1]))) return lang;
        try { lang = pick(localStorage.getItem('suu-lang')); } catch (e) {}
        if (lang) return lang;
        var prefs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language];
        for (var i = 0; i < prefs.length; i++) {
            lang = pick(prefs[i]);
            if (lang) return lang;
        }
        return 'tr';
    }

    Array.prototype.forEach.call(docs, decorate);

    Array.prototype.forEach.call(buttons, function (b) {
        b.addEventListener('click', function () {
            if (b.classList.contains('active')) return;
            setLanguage(b.getAttribute('data-lang'), true);
            centerPill(b);
        });
    });

    // İçindekiler: masaüstünde hep açık; mobilde bir bölüme gidince kapanır
    if (toc) {
        var syncToc = function () { if (desktop && desktop.matches) toc.open = true; };
        syncToc();
        if (desktop) {
            if (desktop.addEventListener) desktop.addEventListener('change', syncToc);
            else if (desktop.addListener) desktop.addListener(syncToc);
        }
        toc.addEventListener('click', function (e) {
            if (e.target.closest('summary') && desktop && desktop.matches) e.preventDefault();
            if (e.target.closest('a') && !(desktop && desktop.matches)) toc.open = false;
        });
    }

    if (topBtn) {
        var onScroll = function () { topBtn.classList.toggle('is-visible', window.scrollY > 900); };
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
        topBtn.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });
    }

    // Seçili dil hapını görünür yap — yalnızca yatayda; scrollIntoView sayfayı da kaydırırdı.
    // Görsel fark üzerinden hesaplandığı için RTL'de de doğru yöne gider.
    function centerPill(btn) {
        var bar = btn && btn.parentNode;
        if (!bar || bar.scrollWidth <= bar.clientWidth) return;
        var b = btn.getBoundingClientRect(), r = bar.getBoundingClientRect();
        bar.scrollLeft += (b.left + b.width / 2) - (r.left + r.width / 2);
    }

    // Türkçe de olsa her zaman çalışır: içindekiler ve kabuk metinleri buradan kurulur
    setLanguage(initialLanguage(), false);
    centerPill(document.querySelector('.legal-langs button.active'));

    // Paylaşılan bölüm bağlantısı (#en-7): kimlikler JS'le verildiği için
    // tarayıcının kendi kaydırması onları bulamaz — burada yapılır.
    if (window.location.hash.length > 3) {
        var target = document.getElementById(decodeURIComponent(window.location.hash.slice(1)));
        if (target && target.offsetParent) target.scrollIntoView();
    }
})();
