/**
 * Suu — Özel Gün Kutlamaları
 *
 * Belirli tarihlerde, belirli dillerde tam ekran bir kutlama animasyonu ve
 * gün boyu duran bir köşe rozeti gösterir. Yılın geri kalanında hiçbir şey
 * yapmaz: CSS dosyası bile ancak aktif bir gün varsa istenir.
 *
 * ── AÇMA / KAPAMA ────────────────────────────────────────────────────────
 *   • Tek bir günü kapatmak     : aşağıdaki OZEL_GUNLER içinde acik: false
 *   • Tüm sistemi kapatmak      : SISTEM_ACIK = false
 *   • Yeni bir gün eklemek      : diziye yeni bir nesne yaz — başka dosya yok
 *   • Tarayıcıda denemek        : ?ozelgun=zafer-bayrami  (tarihi yok sayar)
 *   • Tarayıcıda susturmak      : ?ozelgun=kapali
 *
 * ── TARİH ─────────────────────────────────────────────────────────────────
 * Tarih HER ZAMAN Europe/Istanbul'a göre değerlendirilir; yurt dışındaki bir
 * ziyaretçi de bayramı Türkiye takvimiyle görür. "AA-GG" yazılan tarih her yıl
 * tekrar eder, "YYYY-AA-GG" yazılan yalnızca o yıl çalışır.
 *
 * ── GÖRSEL ────────────────────────────────────────────────────────────────
 * Bayrak koda gömülü SVG'dir (Türk Bayrağı Kanunu ölçüleri). Anma fotoğrafı
 * isteğe bağlıdır: gorsel alanındaki dosya varsa fotoğraf hero olur ve bayrak
 * onun alt kenarına binen bir mühre dönüşür; dosya yoksa bayrak tek başına
 * hero kalır — hiçbir zaman kırık görsel çıkmaz.
 */
(function () {
    'use strict';

    // ── Ana şalter ──────────────────────────────────────────
    var SISTEM_ACIK = true;

    // ── Özel günler ─────────────────────────────────────────
    // baslangic/bitis : "AA-GG" (her yıl) veya "YYYY-AA-GG" (tek seferlik)
    // diller          : hangi <html lang> değerlerinde çıkacağı
    // ilkYil          : "{yil}" yer tutucusunu doldurmak için (2026-1922 = 104)
    // siklik          : 'gun' (günde bir) | 'oturum' | 'her' (her sayfada)
    // rozetKisa       : dar ekranda (≤480px) kullanılan tek satırlık sürüm
    var OZEL_GUNLER = [
        {
            id: 'zafer-bayrami',
            acik: true,
            diller: ['tr'],
            baslangic: '08-30',
            bitis: '08-31',
            ilkYil: 1922,
            siklik: 'gun',
            baslik: '30 Ağustos Zafer Bayramı Kutlu Olsun',
            altBaslik: 'Büyük Taarruz\'un {yil}. yılında, kurucu iradeyi saygıyla anıyoruz.',
            soz: 'Ordular! İlk hedefiniz Akdeniz\'dir, ileri!',
            sozSahibi: 'Mustafa Kemal Atatürk',
            rozet: '30 Ağustos Zafer Bayramımız kutlu olsun.',
            rozetKisa: '30 Ağustos kutlu olsun',
            gorsel: '/assets/special/ataturk.jpg',
            gorselAlt: 'Mustafa Kemal Atatürk, sisli bir kamp alanında çadırların ve atların arasında oturmuş çay içerken'
        },

        // ── Hazır bekleyen günler: acik: true yapmak yeterli ──
        {
            id: 'cumhuriyet-bayrami',
            acik: false,
            diller: ['tr'],
            baslangic: '10-29',
            bitis: '10-29',
            ilkYil: 1923,
            siklik: 'gun',
            baslik: '29 Ekim Cumhuriyet Bayramı Kutlu Olsun',
            altBaslik: 'Cumhuriyetimizin {yil}. yılı kutlu olsun.',
            soz: 'Ne mutlu Türküm diyene!',
            sozSahibi: 'Mustafa Kemal Atatürk',
            rozet: '29 Ekim Cumhuriyet Bayramımız kutlu olsun.',
            rozetKisa: '29 Ekim kutlu olsun',
            gorsel: '/assets/special/ataturk.jpg',
            gorselAlt: 'Mustafa Kemal Atatürk'
        },
        {
            id: 'genclik-bayrami',
            acik: false,
            diller: ['tr'],
            baslangic: '05-19',
            bitis: '05-19',
            ilkYil: 1919,
            siklik: 'gun',
            baslik: '19 Mayıs Atatürk\'ü Anma, Gençlik ve Spor Bayramı',
            altBaslik: 'Kurtuluş yolculuğunun başlangıcının {yil}. yılı.',
            soz: 'Ey Türk gençliği! Birinci vazifen, Türk istiklâlini, Türk Cumhuriyetini, ilelebet muhafaza ve müdafaa etmektir.',
            sozSahibi: 'Mustafa Kemal Atatürk',
            rozet: '19 Mayıs Gençlik ve Spor Bayramımız kutlu olsun.',
            rozetKisa: '19 Mayıs kutlu olsun',
            gorsel: '/assets/special/ataturk.jpg',
            gorselAlt: 'Mustafa Kemal Atatürk'
        },
        {
            id: 'ulusal-egemenlik',
            acik: false,
            diller: ['tr'],
            baslangic: '04-23',
            bitis: '04-23',
            ilkYil: 1920,
            siklik: 'gun',
            baslik: '23 Nisan Ulusal Egemenlik ve Çocuk Bayramı',
            altBaslik: 'Egemenliğin millete geçişinin {yil}. yılı.',
            soz: 'Egemenlik kayıtsız şartsız milletindir.',
            sozSahibi: 'Mustafa Kemal Atatürk',
            rozet: '23 Nisan Ulusal Egemenlik ve Çocuk Bayramımız kutlu olsun.',
            rozetKisa: '23 Nisan kutlu olsun',
            gorsel: '/assets/special/ataturk.jpg',
            gorselAlt: 'Mustafa Kemal Atatürk'
        }
    ];

    // ── Sabitler ────────────────────────────────────────────
    var CSS_YOLU = '/assets/css/special-days.css';
    var DEPO_ONEK = 'suu_ozelgun_';
    var KONFETI_ADEDI = 44;
    var OTOMATIK_KAPANMA = 8000;   // ms — perde kendiliğinden kapanır
    var GORSEL_BEKLEME = 1200;     // ms — portre bu sürede gelmezse onsuz kurulur

    var azHareket = false;
    try {
        azHareket = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) { /* eski tarayıcı */ }

    // ── Tarih (Europe/Istanbul) ─────────────────────────────
    function bugun() {
        try {
            // en-CA biçimi: YYYY-MM-DD — dizge karşılaştırması doğrudan çalışır
            return new Intl.DateTimeFormat('en-CA', {
                timeZone: 'Europe/Istanbul',
                year: 'numeric', month: '2-digit', day: '2-digit'
            }).format(new Date());
        } catch (e) {
            return new Date().toISOString().slice(0, 10);
        }
    }

    function tamTarih(parca, yil) {
        return parca.length === 5 ? yil + '-' + parca : parca;
    }

    function tarihUygun(gun, tarih) {
        var yil = tarih.slice(0, 4);
        var bas = tamTarih(gun.baslangic, yil);
        var bit = tamTarih(gun.bitis || gun.baslangic, yil);
        return tarih >= bas && tarih <= bit;
    }

    // ── Dil ─────────────────────────────────────────────────
    function sayfaDili() {
        var kod = (document.documentElement.getAttribute('lang') || '').toLowerCase();
        return kod.split('-')[0];
    }

    // ── Depo (localStorage kapalıysa sessizce çalışmaya devam) ──
    function oku(anahtar) {
        try { return window.localStorage.getItem(DEPO_ONEK + anahtar); } catch (e) { return null; }
    }
    function yaz(anahtar, deger) {
        try { window.localStorage.setItem(DEPO_ONEK + anahtar, deger); } catch (e) { /* yoksay */ }
    }

    // ── Hangi gün aktif? ────────────────────────────────────
    function aktifGun() {
        var param = '';
        try {
            param = new URLSearchParams(window.location.search).get('ozelgun') || '';
        } catch (e) { /* eski tarayıcı */ }

        if (param === 'kapali' || param === 'off') return null;

        // Önizleme: tarihi ve dili yok say, adı geçen günü göster
        if (param) {
            for (var i = 0; i < OZEL_GUNLER.length; i++) {
                if (OZEL_GUNLER[i].id === param) return OZEL_GUNLER[i];
            }
            return null;
        }

        if (!SISTEM_ACIK) return null;

        var dil = sayfaDili();
        var tarih = bugun();
        for (var j = 0; j < OZEL_GUNLER.length; j++) {
            var gun = OZEL_GUNLER[j];
            if (!gun.acik) continue;
            if (gun.diller.indexOf(dil) === -1) continue;
            if (!tarihUygun(gun, tarih)) continue;
            return gun;
        }
        return null;
    }

    // ── Metin yer tutucuları ────────────────────────────────
    function metin(sablon, gun, tarih) {
        if (!sablon) return '';
        var yil = gun.ilkYil ? (parseInt(tarih.slice(0, 4), 10) - gun.ilkYil) : '';
        return String(sablon).replace(/\{yil\}/g, yil);
    }

    // ── Türk bayrağı SVG'si ─────────────────────────────────
    // Ölçüler Türk Bayrağı Kanunu'ndan: en G=800, boy 1.5G=1200,
    // dış çember çapı G/2, iç çember çapı 0.4G, yıldızın çevrel çemberi G/4.
    var AY = 'M400,200 a200,200 0 1,0 0,400 a200,200 0 1,0 0,-400 Z ' +
             'M450,240 a160,160 0 1,0 0,320 a160,160 0 1,0 0,-320 Z';
    var YILDIZ = '552.0,400.0 621.1,377.5 621.1,304.9 663.8,363.7 732.9,341.2 ' +
                 '690.2,400.0 732.9,458.8 663.8,436.3 621.1,495.1 621.1,422.5';

    function bayrakSvg(dalgali, benzersiz, golgeli) {
        var dalgaId = 'sog-dalga-' + benzersiz;
        var golgeId = 'sog-golge-' + benzersiz;

        golgeli = golgeli !== false;

        var tanimlar = '<defs>';
        if (dalgali) {
            tanimlar +=
                '<filter id="' + dalgaId + '" x="-10%" y="-18%" width="120%" height="136%">' +
                  '<feTurbulence type="fractalNoise" baseFrequency="0.0022 0.006" ' +
                    'numOctaves="2" seed="7" result="gurultu">' +
                    '<animate attributeName="baseFrequency" dur="9s" ' +
                      'values="0.0022 0.006;0.0034 0.0082;0.0022 0.006" repeatCount="indefinite"/>' +
                  '</feTurbulence>' +
                  '<feDisplacementMap in="SourceGraphic" in2="gurultu" scale="15" ' +
                    'xChannelSelector="R" yChannelSelector="G"/>' +
                '</filter>';
        }
        if (golgeli) tanimlar +=
            '<linearGradient id="' + golgeId + '" x1="0" y1="0" x2="1" y2="0">' +
              '<stop offset="0" stop-color="#000" stop-opacity="0.16"/>' +
              '<stop offset="0.2" stop-color="#fff" stop-opacity="0.13"/>' +
              '<stop offset="0.42" stop-color="#000" stop-opacity="0.11"/>' +
              '<stop offset="0.64" stop-color="#fff" stop-opacity="0.13"/>' +
              '<stop offset="0.86" stop-color="#000" stop-opacity="0.12"/>' +
              '<stop offset="1" stop-color="#fff" stop-opacity="0.07"/>' +
              (dalgali
                ? '<animateTransform attributeName="gradientTransform" type="translate" ' +
                  'values="-0.22 0;0.22 0;-0.22 0" dur="6.5s" repeatCount="indefinite"/>'
                : '') +
            '</linearGradient>';
        tanimlar += '</defs>';

        return '<svg viewBox="0 0 1200 800" xmlns="http://www.w3.org/2000/svg" ' +
                    'role="img" aria-label="Türk bayrağı">' +
            tanimlar +
            '<g' + (dalgali ? ' filter="url(#' + dalgaId + ')"' : '') + '>' +
              '<rect width="1200" height="800" fill="#E30A17"/>' +
              '<path fill="#FFFFFF" fill-rule="evenodd" d="' + AY + '"/>' +
              '<polygon fill="#FFFFFF" points="' + YILDIZ + '"/>' +
              (golgeli ? '<rect width="1200" height="800" fill="url(#' + golgeId + ')"/>' : '') +
            '</g>' +
        '</svg>';
    }

    // ── CSS'i ihtiyaç anında yükle ──────────────────────────
    function cssYukle(bitince) {
        if (document.querySelector('link[data-sog-css]')) { bitince(); return; }
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = CSS_YOLU;
        link.setAttribute('data-sog-css', '1');
        var cagrildi = false;
        function birKez() { if (!cagrildi) { cagrildi = true; bitince(); } }
        link.onload = birKez;
        link.onerror = birKez;
        document.head.appendChild(link);
        setTimeout(birKez, 1500);   // ağ takılırsa kutlamayı yine de göster
    }

    // ── Portreyi önden dene ─────────────────────────────────
    function gorselDene(yol, bitince) {
        if (!yol) { bitince(null); return; }
        var bitti = false;
        function son(sonuc) { if (!bitti) { bitti = true; bitince(sonuc); } }
        var img = new Image();
        img.onload = function () { son(yol); };
        img.onerror = function () { son(null); };
        img.src = yol;
        setTimeout(function () { son(null); }, GORSEL_BEKLEME);
    }

    // ── İpucu metni: fare mi, parmak mı ─────────────────────
    function ipucuMetni() {
        var fare = false;
        try { fare = window.matchMedia('(hover: hover) and (pointer: fine)').matches; }
        catch (e) { /* eski tarayıcı */ }
        return fare ? 'Kapatmak için tıklayın veya ESC' : 'Kapatmak için ekrana dokun';
    }

    // ── Konfeti ─────────────────────────────────────────────
    function konfeti() {
        var renkler = ['#E30A17', '#FFFFFF', '#FF4D57', '#FFD75E', '#FFFFFF'];
        var kat = document.createElement('div');
        kat.className = 'sog-konfeti';
        kat.setAttribute('aria-hidden', 'true');
        var parcalar = '';
        for (var i = 0; i < KONFETI_ADEDI; i++) {
            var sol = (Math.random() * 100).toFixed(2);
            var sure = (4.5 + Math.random() * 4).toFixed(2);
            var gecikme = (Math.random() * 5).toFixed(2);
            var en = (5 + Math.random() * 7).toFixed(0);
            var boy = (Math.round(en * (1 + Math.random())));
            var renk = renkler[i % renkler.length];
            var yuvarlak = Math.random() < 0.25 ? 'border-radius:50%;' : '';
            parcalar += '<i class="sog-parca" style="left:' + sol + '%;width:' + en +
                'px;height:' + boy + 'px;background:' + renk + ';animation-duration:' +
                sure + 's;animation-delay:' + gecikme + 's;' + yuvarlak + '"></i>';
        }
        kat.innerHTML = parcalar;
        return kat;
    }

    // ── Köşe rozeti ─────────────────────────────────────────
    function rozetGoster(gun, tarih) {
        if (oku(gun.id + '_rozet') === tarih) return;
        if (document.querySelector('.sog-rozet')) return;

        var rozet = document.createElement('aside');
        rozet.className = 'sog-rozet';
        rozet.setAttribute('role', 'note');
        rozet.innerHTML =
            '<span class="sog-rozet-bayrak">' + bayrakSvg(false, 'rozet', false) + '</span>' +
            '<span class="sog-rozet-metin">' +
              '<span class="sog-rozet-uzun"></span>' +
              '<span class="sog-rozet-kisa"></span>' +
            '</span>' +
            '<button type="button" class="sog-rozet-kapat" aria-label="Kutlamayı kapat">&times;</button>';
        rozet.querySelector('.sog-rozet-uzun').textContent = metin(gun.rozet, gun, tarih);
        rozet.querySelector('.sog-rozet-kisa').textContent =
            metin(gun.rozetKisa || gun.rozet, gun, tarih);

        rozet.querySelector('.sog-rozet-kapat').addEventListener('click', function () {
            rozet.classList.add('sog-kapaniyor');
            yaz(gun.id + '_rozet', tarih);
            setTimeout(function () { rozet.remove(); }, 320);
        });

        document.body.appendChild(rozet);
    }

    // ── Tam ekran kutlama ───────────────────────────────────
    function perdeGoster(gun, tarih, gorselYolu, kapaninca) {
        var perde = document.createElement('div');
        perde.className = 'sog-perde';
        perde.setAttribute('role', 'dialog');
        perde.setAttribute('aria-modal', 'true');
        perde.setAttribute('aria-label', metin(gun.baslik, gun, tarih));

        if (!azHareket) perde.appendChild(konfeti());

        var kapat = document.createElement('button');
        kapat.type = 'button';
        kapat.className = 'sog-kapat';
        kapat.setAttribute('aria-label', 'Kutlamayı kapat');
        kapat.innerHTML = '&times;';
        perde.appendChild(kapat);

        var kart = document.createElement('div');
        kart.className = 'sog-kart';

        // İki sütun: görsel + metin. Dikeyde alt alta yığılır, yatık/alçak
        // pencerede yan yana geçer — ayrım CSS'te, yapı burada sabit.
        var bayrakEtiketi = '<div class="sog-bayrak">' + bayrakSvg(!azHareket, 'perde') + '</div>';
        var gorselSutun = '<div class="sog-sutun-gorsel">';

        if (gorselYolu) {
            // Fotoğraf bir sahne, portre değil — daire içine kırpmak kompozisyonu
            // kesiyordu. Kendi en/boy oranında çerçevelenir, bayrak alt kenarına
            // binen bir mühür gibi durur.
            gorselSutun +=
                '<figure class="sog-foto">' +
                  '<span class="sog-foto-cerceve">' +
                    '<img src="' + gorselYolu + '" alt="' +
                      (gun.gorselAlt || '').replace(/"/g, '&quot;') + '" decoding="async">' +
                  '</span>' +
                  '<span class="sog-bayrak-yuva">' + bayrakEtiketi + '</span>' +
                '</figure>';
            kart.className += ' sog-kart--fotolu';
        } else {
            gorselSutun += bayrakEtiketi;
        }
        gorselSutun += '</div>';

        var metinSutun = '<div class="sog-sutun-metin">' +
              '<h2 class="sog-baslik"></h2>' +
              '<div class="sog-cizgi" aria-hidden="true"></div>' +
              '<p class="sog-alt"></p>';
        if (gun.soz) {
            metinSutun += '<blockquote class="sog-soz"><span class="sog-soz-metin"></span>' +
                  '<cite></cite></blockquote>';
        }
        metinSutun += '<p class="sog-ipucu">' + ipucuMetni() + '</p></div>';

        kart.innerHTML = gorselSutun + metinSutun;

        kart.querySelector('.sog-baslik').textContent = metin(gun.baslik, gun, tarih);
        kart.querySelector('.sog-alt').textContent = metin(gun.altBaslik, gun, tarih);
        if (gun.soz) {
            kart.querySelector('.sog-soz-metin').textContent = '“' + gun.soz + '”';
            kart.querySelector('cite').textContent = gun.sozSahibi || '';
        }

        perde.appendChild(kart);
        document.body.appendChild(perde);

        // ── Kapatma ──
        var kapandi = false;
        var zamanlayici = setTimeout(kapatPerde, OTOMATIK_KAPANMA);

        function kapatPerde() {
            if (kapandi) return;
            kapandi = true;
            clearTimeout(zamanlayici);
            document.removeEventListener('keydown', tusla);
            perde.classList.add('sog-kapaniyor');
            setTimeout(function () {
                perde.remove();
                if (kapaninca) kapaninca();
            }, 360);
        }

        function tusla(e) { if (e.key === 'Escape') kapatPerde(); }

        perde.addEventListener('click', kapatPerde);
        kapat.addEventListener('click', function (e) { e.stopPropagation(); kapatPerde(); });
        document.addEventListener('keydown', tusla);

        try { kapat.focus({ preventScroll: true }); } catch (e) { /* yoksay */ }
    }

    // ── Akış ────────────────────────────────────────────────
    function baslat() {
        var gun = aktifGun();
        if (!gun) return;

        var tarih = bugun();
        var onizleme = false;
        try {
            onizleme = !!new URLSearchParams(window.location.search).get('ozelgun');
        } catch (e) { /* yoksay */ }

        // Perde daha önce gösterildi mi?
        var perdeGerek = true;
        if (!onizleme) {
            if (gun.siklik === 'her') {
                perdeGerek = true;
            } else if (gun.siklik === 'oturum') {
                try {
                    perdeGerek = !window.sessionStorage.getItem(DEPO_ONEK + gun.id);
                    if (perdeGerek) window.sessionStorage.setItem(DEPO_ONEK + gun.id, tarih);
                } catch (e) { /* yoksay */ }
            } else {
                perdeGerek = oku(gun.id + '_perde') !== tarih;
                if (perdeGerek) yaz(gun.id + '_perde', tarih);
            }
        }

        cssYukle(function () {
            if (!perdeGerek) { rozetGoster(gun, tarih); return; }
            gorselDene(gun.gorsel, function (yol) {
                perdeGoster(gun, tarih, yol, function () { rozetGoster(gun, tarih); });
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', baslat);
    } else {
        baslat();
    }
})();
