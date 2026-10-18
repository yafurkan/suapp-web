/* Suu Android tour — coded in-app walkthrough for an Android phone screen (360×820 design space).
   Needs suu-phone-tour.js loaded first (shared street map).
   SuuAndroidTour.mount(screenEl, { assets: '/assets/android/' }) → { destroy } */
(function () {
  var F = 'Roboto,"Google Sans",system-ui,-apple-system,sans-serif';
  var OUT = 'cubic-bezier(.22,1,.36,1)', IO = 'cubic-bezier(.65,0,.35,1)', SPRING = 'cubic-bezier(.34,1.56,.64,1)';
  var C = { bg: '#101318', track: '#212429', card: '#1c1f24', blue: '#1e88f0', green: '#19b37a', orange: '#f5a524', pink: '#ec407a', gold: '#f5c45a', panel: '#1e293b', btn: '#2563eb', btnTx: '#0b2a6b' };
  var I = {
    drop: '<path d="M12 2.5C12 2.5 5 10.5 5 15a7 7 0 0 0 14 0c0-4.5-7-12.5-7-12.5z"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    fork: '<path d="M7 3v8a2 2 0 0 0 2 2v8M5 3v5a2 2 0 0 0 4 0V3M17 21V3c-2 1.5-3 4-3 7v3h3"/>',
    run: '<circle cx="14" cy="4.5" r="1.8"/><path d="M10 21l2.2-6 3 2.8V21M8 11.5l3-3.2 3.2 1.6 2 3H19M11 8.5l-1.6 5.5"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    paw: '<circle cx="6.5" cy="10" r="2"/><circle cx="10" cy="6" r="2"/><circle cx="14" cy="6" r="2"/><circle cx="17.5" cy="10" r="2"/><path d="M7.5 17c0-3 2.2-5 4.5-5s4.5 2 4.5 5c0 1.6-1.6 2.5-4.5 2.5S7.5 18.6 7.5 17z"/>',
    share: '<path d="M12 3v10M8 7l4-4 4 4"/><path d="M6 11h-.5A1.5 1.5 0 0 0 4 12.5v7A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5v-7a1.5 1.5 0 0 0-1.5-1.5H18"/>',
    scan: '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><circle cx="12" cy="12" r="2.6" fill="currentColor"/>',
    barcode: '<path d="M3 7V5h4M17 5h4v2M3 17v2h4M17 19h4v-2M7 8v8M10 8v8M13 8v8M16 8v8"/>',
    mic: '<path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    flashOff: '<path d="M13 2L5 13h6l-1 9 8-11h-6zM3 3l18 18"/>',
    gallery: '<rect x="3" y="5" width="13" height="13" rx="2"/><path d="M8 21h11a2 2 0 0 0 2-2V8M3 14l3.5-3.5 4 4 2-2L16 16"/>',
    sparkle: '<path d="M10 3l1.8 5.2L17 10l-5.2 1.8L10 17l-1.8-5.2L3 10l5.2-1.8zM18 14l.9 2.1L21 17l-2.1.9L18 20l-.9-2.1L15 17l2.1-.9z"/>',
    pause: '<path d="M9 5v14M15 5v14"/>',
    stop: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/>',
    gps: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5" fill="currentColor"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    chev: '<path d="M6 9l6 6 6-6"/>'
  };
  function icon(n, s, c, sw, fill) { return '<svg width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="' + (fill ? c : 'none') + '" stroke="' + (fill ? 'none' : c) + '" stroke-width="' + (sw || 2) + '" stroke-linecap="round" stroke-linejoin="round" style="display:block;color:' + c + '">' + I[n] + '</svg>'; }
  function el(p, css, html) { var e = document.createElement('div'); if (css) e.style.cssText = css; if (html != null) e.innerHTML = html; if (p) p.appendChild(e); return e; }
  function abs(x, y, w, h) { return 'position:absolute;left:' + x + 'px;top:' + y + 'px;' + (w != null ? 'width:' + w + 'px;' : '') + (h != null ? 'height:' + h + 'px;' : ''); }
  function circ(cx, cy, r) { return abs(cx - r, cy - r, r * 2, r * 2) + 'border-radius:50%;'; }
  function eo(p) { return 1 - Math.pow(1 - p, 3); }
  function mmss(s) { s = Math.round(s); return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
  function pace(s) { s = Math.round(s); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }
  function fmt(n) { return Math.round(n).toLocaleString('tr-TR'); }

  function mount(container, o) {
    o = o || {};
    var A = o.assets || 'assets/android/';
    var IMG = { home: A + 'home.jpg', levels: A + 'levels.jpg', map: A + 'map.jpg', food: A + 'food.jpg', petCard: A + 'pet-card.png', petLvl: A + 'pet-lvl.png', mbtn: A + 'mascot-btn.png' };
    Object.keys(IMG).forEach(function (k) { var i = new Image(); i.src = IMG[k]; });
    if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
    container.style.overflow = 'hidden';
    var root = el(container, 'position:absolute;left:0;top:0;width:360px;height:820px;transform-origin:0 0;overflow:hidden;background:' + C.bg + ';font-family:' + F + ';color:#fff;-webkit-font-smoothing:antialiased;user-select:none;');
    function fit() { root.style.transform = 'scale(' + (container.clientWidth / 360) + ')'; }
    fit();
    var ro = window.ResizeObserver ? new ResizeObserver(fit) : null; ro && ro.observe(container);
    var dead = false, paused = false;
    var io = window.IntersectionObserver ? new IntersectionObserver(function (e) {
      paused = !e[0].isIntersecting;
      root.getAnimations({ subtree: true }).forEach(function (a) { if (paused && a.playState === 'running') a.pause(); else if (!paused && a.playState === 'paused') a.play(); });
    }) : null;
    io && io.observe(container);
    function wait(ms) { return new Promise(function (res) { var left = ms, last = performance.now(); (function f(now) { if (dead) return; now = now || performance.now(); if (!paused) left -= now - last; last = now; if (left <= 0) res(); else requestAnimationFrame(f); })(); }); }
    function tween(ms, fn) { return new Promise(function (res) { var t = 0, last = performance.now(); (function f(now) { if (dead) return; now = now || performance.now(); if (!paused) t += now - last; last = now; var p = Math.min(1, t / ms); fn(p); if (p >= 1) res(); else requestAnimationFrame(f); })(); }); }
    function ani(n, fr, op) { var opt = { fill: 'forwards', easing: OUT, duration: 400 }; for (var k in op) opt[k] = op[k]; return n.animate(fr, opt); }
    function fadeIn(n, ms, d) { return ani(n, [{ opacity: 0 }, { opacity: 1 }], { duration: ms || 300, delay: d || 0 }); }
    function fadeOut(n, ms, d) { return ani(n, [{ opacity: 1 }, { opacity: 0 }], { duration: ms || 300, delay: d || 0 }); }
    function pop(n, d) { return ani(n, [{ opacity: 0, transform: 'scale(.6)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 480, delay: d || 0, easing: SPRING }); }
    function press(n) { n.animate([{ transform: 'scale(1)' }, { transform: 'scale(.92)', offset: .4 }, { transform: 'scale(1)' }], { duration: 340, easing: OUT }); }
    var cover = el(root, 'position:absolute;inset:0;background:#000;z-index:100;pointer-events:none;opacity:1;');
    var stage, u;

    if (!o.force && window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) {
      stage = el(root, 'position:absolute;inset:0;'); el(stage, 'position:absolute;inset:0;background:url(' + IMG.home + ') 0 0/360px 820px;');
      cover.style.opacity = 0;
      return { destroy: destroy };
    }

    function layer(z, bg) { var l = el(stage, 'position:absolute;inset:0;overflow:hidden;z-index:' + z + ';' + (bg ? 'background:url(' + bg + ') 0 0/360px 820px no-repeat;' : '')); return l; }
    function txt(p, x, y, w, css, t) { return el(p, abs(x, y, w) + 'text-align:center;white-space:nowrap;' + css, t); }
    function floatText(x, y, t, col) {
      var f = el(stage, abs(x - 80, y, 160) + 'text-align:center;font-weight:800;font-size:17px;color:' + col + ';text-shadow:0 2px 12px rgba(0,0,0,.6);z-index:40;', t);
      ani(f, [{ opacity: 0, transform: 'translateY(10px) scale(.8)' }, { opacity: 1, transform: 'translateY(-8px) scale(1)', offset: .25 }, { opacity: 1, transform: 'translateY(-24px)', offset: .75 }, { opacity: 0, transform: 'translateY(-36px)' }], { duration: 1400, easing: 'ease-out' });
    }

    function build() {
      if (stage) stage.remove();
      stage = el(root, 'position:absolute;inset:0;');
      u = {};
      /* ---------- HOME ---------- */
      var H = u.home = layer(1, IMG.home);
      var R = [[57, 11, C.blue, .26], [43, 10, C.green, .24], [29, 9, C.orange, 0]];
      var sv = '<svg width="160" height="160" viewBox="0 0 160 160" style="position:absolute;left:100px;top:155px;overflow:visible">';
      sv += '<circle cx="80" cy="80" r="44" fill="none" stroke="' + C.bg + '" stroke-width="46"/>';
      R.forEach(function (r, i) {
        sv += '<circle cx="80" cy="80" r="' + r[0] + '" fill="none" stroke="' + C.track + '" stroke-width="' + r[1] + '"/>';
        sv += '<circle data-a="' + i + '" cx="80" cy="80" r="' + r[0] + '" fill="none" stroke="' + r[2] + '" stroke-width="' + r[1] + '" stroke-linecap="round" pathLength="100" stroke-dasharray="' + (r[3] * 100) + ' 100" transform="rotate(-90 80 80)" style="filter:drop-shadow(0 0 4px ' + r[2] + '66)"/>';
      });
      el(H, 'position:absolute;inset:0;', sv + '</svg>');
      u.arc = [0, 1, 2].map(function (i) { return H.querySelector('[data-a="' + i + '"]'); });
      u.arcV = R.map(function (r) { return r[3]; });
      el(H, abs(14, 339, 332, 23) + 'background:' + C.bg + ';');
      u.vWater = txt(H, 26, 341, 110, 'font-weight:700;font-size:12.5px;', '500 / 1900 ml');
      u.vFood = txt(H, 125, 341, 110, 'font-weight:700;font-size:12.5px;', '495 / 2058 kcal');
      u.vEx = txt(H, 224, 341, 110, 'font-weight:700;font-size:12.5px;color:' + C.orange + ';', '0 dk');
      u.mac = [[72.5, '495', '/2058'], [144, '39', '/257g'], [215.5, '29', '/103g']].map(function (m) {
        var w = el(H, circ(m[0], 671, 21) + 'background:' + C.card + ';display:flex;flex-direction:column;align-items:center;justify-content:center;');
        var n = el(w, 'font-weight:700;font-size:11.5px;line-height:1.1;', m[1]);
        el(w, 'font-size:8px;color:#8c8e93;', m[2]);
        return n;
      });
      u.water = el(H, circ(180, 455, 66) + 'background:radial-gradient(circle at 40% 30%,#2ad6f7,#2a7ef2 60%,#2a5fe8);box-shadow:0 0 40px rgba(40,140,250,.55);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;',
        icon('drop', 22, '#fff', 0, true) + '<div style="font-weight:700;font-size:17px">250 ml</div>');
      u.badge = el(H, circ(165.5, 63.5, 21) + 'background:radial-gradient(circle at 40% 30%,#f1f3f6,#a7adb6 70%,#7d838c);box-shadow:0 0 0 3px #3a2c17, 0 0 0 4px #6b5326;display:grid;place-items:center;font-weight:800;font-size:20px;color:#1d2128;opacity:0;', '6');
      u.badgeHit = el(H, circ(165.5, 63.5, 21));
      u.dim = el(H, 'position:absolute;inset:0;background:rgba(10,12,16,.55);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);opacity:0;z-index:5;');
      u.menu = [['fork', '#66bb6a', 'Besin Ekle'], ['run', '#ff9800', 'Egzersiz Ekle'], ['target', '#7e57c2', 'Hedefe Yaklaştır'], ['paw', '#ec407a', 'Pet Dostum'], ['share', '#8b5cf6', 'Story Paylaş']].map(function (m, i) {
        var y = 336.5 + i * 58.2;
        var pill = el(H, 'position:absolute;right:72px;top:' + (y - 18) + 'px;height:36px;padding:0 13px;border-radius:10px;background:#1f2737;display:flex;align-items:center;font-size:14px;font-weight:700;white-space:nowrap;opacity:0;z-index:6;', m[2]);
        var dot = el(H, circ(321, y, 22.5) + 'background:' + m[1] + ';box-shadow:0 4px 16px ' + m[1] + '77;display:grid;place-items:center;opacity:0;z-index:6;', icon(m[0], 22, '#fff', 2.4, m[0] === 'paw'));
        return { pill: pill, dot: dot, dy: 644 - y, y: y };
      });
      u.fab = el(H, circ(316, 644, 27.5) + 'background:#f2423a;box-shadow:0 6px 20px rgba(242,66,58,.45);display:grid;place-items:center;z-index:7;', icon('plus', 26, '#fff', 3));
      u.fabI = u.fab.firstChild;
      el(H, circ(316, 715, 27) + 'background:url(' + IMG.mbtn + ') center/112% no-repeat;z-index:7;');
      /* ---------- CAMERA ---------- */
      var K = u.cam = layer(3, IMG.food); K.style.opacity = 0;
      el(K, abs(0, 0, 360, 150) + 'background:linear-gradient(rgba(0,0,0,.45),rgba(0,0,0,0));');
      el(K, abs(0, 560, 360, 220) + 'background:linear-gradient(rgba(0,0,0,0),rgba(0,0,0,.55));');
      txt(K, 16, 9, 40, 'font-size:13px;font-weight:600;text-align:left;', '07:49');
      el(K, abs(102, 48, 157, 37) + 'border-radius:19px;background:#fff;color:#111;display:flex;align-items:center;justify-content:center;gap:7px;font-weight:700;font-size:14px;', icon('fork', 14, '#777', 2) + 'Son öğünler' + icon('chev', 13, '#111', 2.6));
      el(K, circ(326, 66, 22) + 'background:rgba(60,60,60,.72);display:grid;place-items:center;', icon('x', 20, '#fff', 2.4));
      el(K, abs(100, 96, 160, 31) + 'border-radius:16px;background:rgba(60,60,60,.72);display:flex;align-items:center;justify-content:center;gap:6px;font-weight:600;font-size:12px;', icon('sparkle', 13, '#fff', 0, true) + 'Son ücretsiz analizin');
      el(K, 'position:absolute;inset:0;', '<svg width="360" height="820" style="position:absolute;inset:0"><g fill="none" stroke="#fff" stroke-width="3.5" stroke-linecap="round"><path d="M50 330V292q0-12 12-12h38"/><path d="M260 280h38q12 0 12 12v38"/><path d="M50 492v37q0 12 12 12h38"/><path d="M260 541h38q12 0 12-12v-37"/></g></svg>');
      u.scanL = el(K, abs(56, 286, 248, 3) + 'background:#ef4444;box-shadow:0 0 14px 3px rgba(239,68,68,.7);opacity:0;');
      u.camBtns = [[55, 'scan', 'Tara', true], [138, 'barcode', 'Barkod'], [221, 'mic', 'Tanımla'], [304, 'search', 'Arama']].map(function (b) {
        var c = el(K, circ(b[0], 612, 25.5) + 'background:' + (b[3] ? '#fff' : 'rgba(70,64,60,.72)') + ';box-shadow:inset 0 0 0 1px rgba(255,255,255,.18);display:grid;place-items:center;', icon(b[1], 22, b[3] ? '#ef4444' : '#fff', 2.2));
        txt(K, b[0] - 40, 643, 80, 'font-weight:700;font-size:12px;text-shadow:0 1px 4px rgba(0,0,0,.5);', b[2]);
        return c;
      });
      el(K, circ(58, 711, 22) + 'background:rgba(40,40,40,.7);display:grid;place-items:center;', icon('flashOff', 20, '#fff', 2.2));
      el(K, circ(302, 711, 22) + 'background:rgba(40,40,40,.7);display:grid;place-items:center;', icon('gallery', 20, '#fff', 2));
      u.shutter = el(K, circ(180, 711, 37) + 'box-shadow:inset 0 0 0 4px #fff;display:grid;place-items:center;', '<div style="width:56px;height:56px;border-radius:50%;background:#fff"></div>');
      txt(K, 140, 757, 80, 'font-size:12px;color:rgba(255,255,255,.7);', 'Galeri');
      u.flash = el(K, 'position:absolute;inset:0;background:radial-gradient(circle at 50% 50%,#fff 0,rgba(255,255,255,.92) 30%,rgba(255,255,255,0) 72%);opacity:0;z-index:4;');
      u.tags = [[22, 238, 'Kola', '#e11d48'], [150, 560, 'Pepperoni pizza', '#f59e0b']].map(function (t) {
        return el(K, abs(t[0], t[1]) + 'height:28px;padding:0 11px 0 9px;border-radius:14px;background:rgba(17,20,27,.86);display:flex;align-items:center;gap:7px;font-size:12.5px;font-weight:700;white-space:nowrap;opacity:0;z-index:3;', '<i style="width:8px;height:8px;border-radius:50%;background:' + t[3] + '"></i>' + t[2]);
      });
      u.anl = el(K, abs(110, 504, 140, 28) + 'border-radius:14px;background:rgba(17,20,27,.86);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;letter-spacing:.06em;opacity:0;z-index:3;', 'ANALİZ EDİLİYOR');
      var S = u.sheet = el(K, abs(0, 820, 360, 400) + 'border-radius:26px 26px 0 0;background:' + C.panel + ';box-shadow:0 -10px 40px rgba(0,0,0,.5);z-index:6;');
      el(S, abs(160, 9, 40, 4) + 'border-radius:2px;background:#475569;');
      el(S, abs(22, 28) + 'font-size:11px;font-weight:700;letter-spacing:.16em;color:#94a3b8;', 'ÖĞÜN ANALİZİ');
      el(S, abs(22, 48) + 'font-size:19px;font-weight:800;', 'Pepperoni pizza + Kola');
      u.kc = el(S, abs(22, 82) + 'font-size:40px;font-weight:800;letter-spacing:-.02em;', '0<span style="font-size:16px;color:#94a3b8;font-weight:700"> kcal</span>');
      u.bars = [['Karb', 82, 257, C.orange], ['Protein', 26, 103, C.pink], ['Yağ', 27, 69, '#a855f7']].map(function (m, i) {
        var y = 150 + i * 44;
        el(S, abs(22, y) + 'font-size:13.5px;font-weight:600;color:#cbd5e1;', m[0]);
        var v = el(S, 'position:absolute;right:22px;top:' + y + 'px;font-size:13.5px;font-weight:800;', '0 g');
        el(S, abs(22, y + 22, 316, 7) + 'border-radius:4px;background:#334155;');
        var f = el(S, abs(22, y + 22, 0, 7) + 'border-radius:4px;background:' + m[3] + ';');
        return { v: v, f: f, g: m[1], w: 316 * Math.min(1, m[1] / m[2] * 2.2) };
      });
      u.add = el(S, abs(22, 300, 316, 50) + 'border-radius:25px;background:' + C.btn + ';display:grid;place-items:center;font-weight:800;font-size:16px;color:' + C.btnTx + ';', 'Öğüne ekle');
      /* ---------- LEVELS ---------- */
      var L = u.lv = layer(3, IMG.levels); L.style.opacity = 0;
      el(L, abs(35, 291, 291, 14) + 'border-radius:7px;background:#363f50;');
      u.lvBar = el(L, abs(35, 291, 0, 14) + 'border-radius:7px;background:linear-gradient(90deg,#e7a40f,#fbd96b);box-shadow:0 0 12px rgba(245,196,90,.4);');
      u.git = el(L, abs(252, 717, 64, 30));
      /* ---------- MAP ---------- */
      var M = u.map = layer(3); M.style.opacity = 0;
      u.mapImg = el(M, 'position:absolute;inset:0;background:url(' + IMG.map + ') 0 0/360px 820px no-repeat;transform-origin:188px 411px;z-index:2;');
      u.st = window.SuuPhoneTour.streetMap(M, window.SuuPhoneTour.TXT.tr);
      u.st.layer.style.zIndex = 1;
      u.live = el(M, 'position:absolute;inset:0;z-index:3;opacity:0;');
      el(u.live, abs(0, 0, 360, 90) + 'background:linear-gradient(rgba(16,19,24,.7),rgba(16,19,24,0));');
      txt(u.live, 16, 9, 40, 'font-size:13px;font-weight:600;text-align:left;', '07:50');
      el(u.live, abs(0, 640, 360, 180) + 'background:linear-gradient(rgba(16,19,24,0),' + C.bg + ' 45%);');
      var pn = el(u.live, abs(16, 525, 328, 114) + 'border-radius:26px;background:rgba(34,39,43,.96);box-shadow:0 8px 30px rgba(0,0,0,.45);');
      el(pn, abs(0, 15, 328) + 'display:flex;justify-content:center;align-items:center;gap:8px;font-weight:700;font-size:14px;color:#22c55e;', icon('gps', 17, '#22c55e', 2) + 'GPS Alındı');
      u.stat = [[63, 'Süre', '00:00'], [164, 'Ort. tempo', '-:--'], [265, 'Mesafe', '0,00 km']].map(function (m) {
        var v = txt(pn, m[0] - 60, 50, 120, 'font-weight:800;font-size:22px;letter-spacing:-.01em;font-variant-numeric:tabular-nums;', m[2]);
        txt(pn, m[0] - 60, 82, 120, 'font-size:11px;color:#9aa0a6;', m[1]);
        return v;
      });
      el(pn, abs(113, 54, 1, 44) + 'background:#3a3f44;'); el(pn, abs(214, 54, 1, 44) + 'background:#3a3f44;');
      u.pauseB = el(u.live, circ(77, 708, 28) + 'background:#2a2f35;display:grid;place-items:center;', icon('pause', 22, '#fff', 2.6));
      txt(u.live, 37, 746, 80, 'font-weight:700;font-size:13px;', 'Duraklat');
      u.stopB = el(u.live, circ(180, 699, 40) + 'background:#ef4444;box-shadow:0 0 30px rgba(239,68,68,.5);display:grid;place-items:center;', icon('stop', 30, '#fff', 0, true));
      txt(u.live, 140, 746, 80, 'font-weight:700;font-size:14px;color:#f87171;', 'Bitir');
      u.startHit = el(M, circ(180, 699, 40) + 'z-index:4;');
      /* ---------- QUEST DONE ---------- */
      var Q = u.qd = layer(4); Q.style.opacity = 0;
      el(Q, 'position:absolute;inset:0;background:rgba(5,7,10,.62);');
      var cd = u.qCard = el(Q, abs(22, 74, 316, 674) + 'border-radius:30px;background:' + C.panel + ';box-shadow:0 20px 60px rgba(0,0,0,.5);');
      el(cd, 'position:absolute;right:20px;top:18px;height:36px;padding:0 15px;border-radius:18px;background:#3d3a33;display:flex;align-items:center;color:#f5d27a;font-weight:700;font-size:13.5px;', 'Harikasın, furkan!');
      u.qPet = el(cd, abs(83, 64, 150, 150) + 'background:url(' + IMG.petCard + ') center/contain no-repeat;');
      txt(cd, 0, 228, 316, 'font-weight:800;font-size:23px;', 'Görev tamam!');
      el(cd, abs(30, 268, 14, 14), icon('run', 14, C.pink, 2.4));
      el(cd, abs(48, 262, 240) + 'text-align:center;font-size:14px;line-height:1.45;color:#cbd5e1;', '30 dakikalık hareket hedefini tamamla');
      u.rows = [['sparkle', C.gold, '#3a3a2e', 'Günlük görev', 30], ['run', C.pink, '#3b2a35', 'Egzersiz', 20], ['run', C.pink, '#3b2a35', 'Hareket hedefi', 25]].map(function (r, i) {
        var w = el(cd, abs(20, 318 + i * 40, 276, 34) + 'display:flex;align-items:center;gap:14px;opacity:0;');
        el(w, 'width:30px;height:30px;border-radius:50%;background:' + r[2] + ';display:grid;place-items:center;flex:0 0 auto;', icon(r[0], 15, r[1], 2.4, r[0] === 'sparkle'));
        el(w, 'flex:1;font-size:15px;', r[3]);
        el(w, 'font-weight:800;font-size:14.5px;color:' + C.gold + ';', '+' + r[4] + ' XP');
        return w;
      });
      el(cd, abs(20, 446, 276, 1) + 'background:#334155;');
      el(cd, abs(20, 466) + 'font-weight:700;font-size:16px;', 'Toplam');
      u.total = el(cd, 'position:absolute;right:20px;top:458px;font-weight:800;font-size:25px;color:' + C.gold + ';font-variant-numeric:tabular-nums;', '+0 XP');
      u.qBadge = el(cd, circ(31, 524, 11) + 'background:radial-gradient(circle at 40% 30%,#f1f3f6,#a7adb6 70%,#7d838c);box-shadow:0 0 0 2px #5b6470;display:grid;place-items:center;font-weight:800;font-size:11px;color:#1d2128;', '5');
      u.qLv = el(cd, abs(52, 514) + 'font-weight:700;font-size:14.5px;', 'Seviye 5 · Demir');
      u.qXp = el(cd, 'position:absolute;right:20px;top:514px;font-weight:700;font-size:14px;font-variant-numeric:tabular-nums;', '245 / 250 XP');
      el(cd, abs(20, 546, 276, 11) + 'border-radius:6px;background:#45505f;');
      u.qBar = el(cd, abs(20, 546, 270, 11) + 'border-radius:6px;background:linear-gradient(90deg,#e7a40f,#fbd96b);');
      u.qNext = el(cd, abs(20, 566) + 'font-weight:600;font-size:13px;color:' + C.gold + ';', 'Sonraki seviyeye 5 XP');
      u.qBtn = el(cd, abs(20, 600, 276, 50) + 'border-radius:25px;background:' + C.btn + ';display:grid;place-items:center;font-weight:800;font-size:17px;color:' + C.btnTx + ';', 'Devam');
      /* ---------- LEVEL UP ---------- */
      var V = u.lu = layer(5); V.style.opacity = 0;
      V.style.background = 'radial-gradient(40% 25% at 8% 58%,rgba(40,90,140,.35),transparent),radial-gradient(35% 22% at 88% 76%,rgba(150,40,30,.35),transparent),radial-gradient(45% 30% at 50% 45%,rgba(60,70,90,.35),transparent),#0b0e12';
      txt(V, 16, 9, 40, 'font-size:13px;font-weight:600;text-align:left;', '07:51');
      el(V, 'position:absolute;inset:0;', '<svg width="360" height="820" style="position:absolute;inset:0"><circle cx="180" cy="203" r="70" fill="none" stroke="#262b31" stroke-width="11"/><circle data-lr cx="180" cy="203" r="70" fill="none" stroke="#6b7a8c" stroke-width="11" stroke-linecap="round" pathLength="100" stroke-dasharray="0 100" transform="rotate(-90 180 203)"/></svg>');
      u.luArc = V.querySelector('[data-lr]');
      u.luGlow = el(V, circ(180, 203, 90) + 'background:radial-gradient(closest-side,rgba(255,236,170,.55),rgba(255,236,170,0));opacity:0;');
      u.luBadge = el(V, circ(180, 203, 56) + 'background:radial-gradient(circle at 42% 28%,#f4f6f8,#b9bfc7 55%,#7f8690);box-shadow:inset 0 -6px 14px rgba(0,0,0,.25),0 8px 24px rgba(0,0,0,.5);overflow:hidden;');
      el(u.luBadge, abs(18, 12, 60, 26) + 'border-radius:50%;background:rgba(255,255,255,.55);');
      u.luNum = el(u.luBadge, 'position:absolute;inset:0;display:grid;place-items:center;font-weight:900;font-size:66px;color:#1f242c;', '5');
      el(u.luBadge, abs(41, 94, 30, 6), '<i style="position:absolute;left:0;width:6px;height:6px;border-radius:50%;background:#5b616b"></i><i style="position:absolute;right:0;width:6px;height:6px;border-radius:50%;background:#5b616b"></i>');
      u.luTitle = txt(V, 0, 294, 360, 'font-weight:800;font-size:33px;opacity:0;', 'Seviye 6!');
      el(V, circ(180, 478, 85) + 'background:radial-gradient(closest-side,rgba(255,150,120,.28),rgba(255,150,120,0));');
      u.luPet = el(V, abs(105, 400, 150, 150) + 'background:url(' + IMG.petLvl + ') center/contain no-repeat;opacity:0;');
      u.luPill = el(V, abs(106, 553, 148, 34) + 'border-radius:17px;background:#2a2d33;display:grid;place-items:center;color:#f2d78a;font-weight:700;font-size:14px;opacity:0;', 'Açıldı: Sosyal');
      u.luNext = txt(V, 0, 596, 360, 'font-weight:600;font-size:13px;color:#cbd5e1;opacity:0;', 'Sonraki seviyeye 230 XP');
      u.luBtn = el(V, abs(24, 706, 312, 50) + 'border-radius:25px;background:' + C.btn + ';display:grid;place-items:center;font-weight:800;font-size:17px;color:' + C.btnTx + ';opacity:0;', 'Devam');
      /* ---------- finger ---------- */
      u.fg = el(stage, abs(0, 0, 44, 44) + 'margin:-22px 0 0 -22px;z-index:50;pointer-events:none;opacity:0;');
      u.fdot = el(u.fg, 'position:absolute;inset:7px;border-radius:50%;background:rgba(255,255,255,.82);box-shadow:0 3px 12px rgba(0,0,0,.45);');
      u.fx = 230; u.fy = 560;
      u.fg.style.transform = 'translate(230px,560px)';
    }

    function fingerTo(x, y, ms) { ani(u.fg, [{ transform: 'translate(' + u.fx + 'px,' + u.fy + 'px)' }, { transform: 'translate(' + x + 'px,' + y + 'px)' }], { duration: ms, easing: IO }); u.fx = x; u.fy = y; return wait(ms); }
    function showF(v) { ani(u.fg, [{ opacity: v ? 0 : 1 }, { opacity: v ? 1 : 0 }], { duration: 220 }); }
    function tap(t) {
      u.fdot.animate([{ transform: 'scale(1)' }, { transform: 'scale(.72)', offset: .4 }, { transform: 'scale(1)' }], { duration: 320, easing: OUT });
      var rp = el(stage, circ(u.fx, u.fy, 22) + 'border:2px solid rgba(255,255,255,.85);box-sizing:border-box;z-index:49;pointer-events:none;');
      rp.animate([{ transform: 'scale(.5)', opacity: 1 }, { transform: 'scale(1.7)', opacity: 0 }], { duration: 520, easing: OUT }).onfinish = function () { rp.remove(); };
      if (t) press(t);
      return wait(330);
    }
    function setArc(i, v, ms) { var f = u.arcV[i]; u.arcV[i] = v; return tween(ms || 900, function (p) { u.arc[i].setAttribute('stroke-dasharray', ((f + (v - f) * eo(p)) * 100).toFixed(2) + ' 100'); }); }
    function count(n, from, to, ms, fn) { return tween(ms, function (p) { n.innerHTML = fn(from + (to - from) * eo(p)); }); }
    function menu(v) {
      ani(u.dim, [{ opacity: v ? 0 : 1 }, { opacity: v ? 1 : 0 }], { duration: v ? 320 : 260 });
      ani(u.fabI, [{ transform: v ? 'rotate(0)' : 'rotate(45deg)' }, { transform: v ? 'rotate(45deg)' : 'rotate(0)' }], { duration: 380, easing: SPRING });
      var n = u.menu.length;
      u.menu.forEach(function (m, i) {
        var d = v ? (n - 1 - i) * 40 : i * 18;
        ani(m.dot, [{ opacity: v ? 0 : 1, transform: v ? 'translateY(' + m.dy * .45 + 'px) scale(.3)' : 'none' }, { opacity: v ? 1 : 0, transform: v ? 'none' : 'translateY(' + m.dy * .3 + 'px) scale(.4)' }], { duration: v ? 440 : 220, delay: d, easing: v ? SPRING : 'ease-in' });
        ani(m.pill, [{ opacity: v ? 0 : 1, transform: v ? 'translateX(14px)' : 'none' }, { opacity: v ? 1 : 0, transform: v ? 'none' : 'translateX(10px)' }], { duration: v ? 360 : 200, delay: d + (v ? 70 : 0) });
      });
      return wait(v ? (n - 1) * 40 + 440 : 300);
    }
    function push(s) { s.style.opacity = 1; ani(s, [{ transform: 'translateY(100%)' }, { transform: 'none' }], { duration: 520, easing: OUT }); ani(u.home, [{ filter: 'brightness(1)' }, { filter: 'brightness(.55)' }], { duration: 520 }); return wait(560); }
    function pop2(s) { var a = ani(s, [{ transform: 'none', opacity: 1 }, { transform: 'translateY(60px)', opacity: 0 }], { duration: 440, easing: IO }); ani(u.home, [{ filter: 'brightness(.55)' }, { filter: 'brightness(1)' }], { duration: 480 }); return a.finished.then(function () { return wait(120); }); }

    async function run() {
      ani(cover, [{ opacity: 1 }, { opacity: 0 }], { duration: 500 });
      await wait(900);
      /* water */
      showF(true); await fingerTo(196, 470, 600); await tap(u.water);
      u.water.animate([{ boxShadow: '0 0 40px rgba(40,140,250,.55)' }, { boxShadow: '0 0 70px rgba(40,180,255,.95)' }, { boxShadow: '0 0 40px rgba(40,140,250,.55)' }], { duration: 900 });
      floatText(180, 370, '+250 ml', '#7cc4ff');
      setArc(0, .39); count(u.vWater, 500, 750, 900, function (v) { return fmt(v) + ' / 1900 ml'; });
      await wait(1300);
      /* + → Besin Ekle */
      await fingerTo(318, 648, 600); await tap(u.fab);
      await menu(true); await wait(250);
      await fingerTo(322, 340, 520); await tap(u.menu[0].dot);
      menu(false);
      u.cam.style.opacity = 1; ani(u.cam, [{ transform: 'scale(1.06)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 500 });
      await wait(900);
      /* shutter */
      await fingerTo(184, 716, 600); await tap(u.shutter);
      ani(u.flash, [{ opacity: 0, transform: 'scale(.4)' }, { opacity: 1, transform: 'scale(1)', offset: .15 }, { opacity: 0, transform: 'scale(1.5)' }], { duration: 650, easing: 'ease-out' });
      showF(false); await wait(450);
      fadeIn(u.anl, 250); fadeIn(u.scanL, 200);
      ani(u.scanL, [{ transform: 'translateY(0)' }, { transform: 'translateY(250px)' }], { duration: 900, iterations: 2, direction: 'alternate', easing: 'ease-in-out', fill: 'none' });
      pop(u.tags[0], 500); pop(u.tags[1], 850);
      await wait(1900);
      fadeOut(u.anl, 200); fadeOut(u.scanL, 200);
      ani(u.sheet, [{ transform: 'none' }, { transform: 'translateY(-390px)' }], { duration: 560, easing: OUT });
      await wait(350);
      count(u.kc, 0, 680, 1000, function (v) { return fmt(v) + '<span style="font-size:16px;color:#94a3b8;font-weight:700"> kcal</span>'; });
      u.bars.forEach(function (b, i) { ani(b.f, [{ width: '0px' }, { width: b.w + 'px' }], { duration: 900, delay: 150 + i * 120 }); count(b.v, 0, b.g, 1000, function (v) { return Math.round(v) + ' g'; }); });
      await wait(1500);
      showF(true); await fingerTo(186, 720, 600); await tap(u.add);
      fadeOut(u.tags[0], 200); fadeOut(u.tags[1], 200);
      await (ani(u.cam, [{ transform: 'none', opacity: 1 }, { transform: 'translateY(60px)', opacity: 0 }], { duration: 460, easing: IO }).finished);
      floatText(180, 290, '+680 kcal', '#5fe0a8');
      setArc(1, .57);
      count(u.vFood, 495, 1175, 900, function (v) { return fmt(v) + ' / 2058 kcal'; });
      count(u.mac[0], 495, 1175, 900, function (v) { return fmt(v); });
      count(u.mac[1], 39, 121, 900, function (v) { return Math.round(v); });
      count(u.mac[2], 29, 55, 900, function (v) { return Math.round(v); });
      await wait(1400);
      /* level badge → quests */
      await fingerTo(168, 68, 700); await tap(null);
      await push(u.lv);
      ani(u.lvBar, [{ width: '0px' }, { width: '285px' }], { duration: 1000, easing: OUT });
      await wait(1300);
      await fingerTo(286, 734, 650); await tap(u.git);
      /* map */
      u.map.style.opacity = 1; ani(u.map, [{ opacity: 0, transform: 'translateX(40px)' }, { opacity: 1, transform: 'none' }], { duration: 480 });
      await wait(1000);
      await fingerTo(184, 703, 600); await tap(u.startHit);
      showF(false);
      var St = u.st, P = St.route, Ln = P.getTotalLength(), p0 = P.getPointAtLength(0);
      var cam = { x: p0.x, y: p0.y, z: .45, cy: 300 };
      function applyCam() { St.world.style.transform = 'translate(' + (180 - cam.x * cam.z).toFixed(1) + 'px,' + (cam.cy - cam.y * cam.z).toFixed(1) + 'px) scale(' + cam.z.toFixed(3) + ')'; }
      applyCam(); St.setHead(p0, 0); St.animate();
      ani(u.mapImg, [{ transform: 'scale(1)', opacity: 1 }, { transform: 'scale(5)', opacity: 0 }], { duration: 1100, easing: 'cubic-bezier(.55,0,.75,.4)' });
      ani(St.layer, [{ opacity: 0 }, { opacity: 1 }], { duration: 700, delay: 350 });
      fadeIn(u.live, 400, 700);
      await tween(1200, function (p) { cam.z = .45 + (1.1 - .45) * eo(p); applyCam(); });
      [P, St.glow, St.casing].forEach(function (q) { q.style.strokeDasharray = Ln; q.style.strokeDashoffset = Ln; q.setAttribute('opacity', 1); });
      var SPL = [[1, "5'48\""], [2, "5'31\""], [3, "5'19\""], [4, "5'05\""]], shown = 0;
      await tween(7600, function (p) {
        var e = Math.min(1, (p < .06 ? p * p / .12 : p - .03) / .97);
        [P, St.glow, St.casing].forEach(function (q) { q.style.strokeDashoffset = Ln * (1 - e); });
        var pt = P.getPointAtLength(Ln * e), nx = P.getPointAtLength(Math.min(Ln, Ln * e + 8));
        St.setHead(pt, (nx.x === pt.x && nx.y === pt.y) ? 0 : Math.atan2(nx.y - pt.y, nx.x - pt.x) * 180 / Math.PI + 90);
        cam.x += (pt.x - cam.x) * .1; cam.y += (pt.y - cam.y) * .1; cam.z += (1 - cam.z) * .03; applyCam();
        u.stat[0].textContent = mmss(1634 * e);
        u.stat[1].textContent = e > .03 ? pace(348 - 43 * e) : '-:--';
        u.stat[2].textContent = (4.82 * e).toFixed(2).replace('.', ',') + ' km';
        while (shown < SPL.length && e >= SPL[shown][0] / 4.82) { var q = P.getPointAtLength(Ln * SPL[shown][0] / 4.82); St.addMark(q, SPL[shown][0], SPL[shown][1], q.x > 560); shown++; }
      });
      showF(true); await fingerTo(184, 703, 600); await tap(u.stopB);
      showF(false);
      var c0 = { x: cam.x, y: cam.y, z: cam.z, cy: cam.cy };
      await tween(1100, function (p) { var k = 1 - Math.pow(1 - p, 4); cam.x = c0.x + (520 - c0.x) * k; cam.y = c0.y + (790 - c0.y) * k; cam.z = c0.z + (.42 - c0.z) * k; cam.cy = c0.cy + (270 - c0.cy) * k; applyCam(); });
      await wait(500);
      /* quest done */
      u.home.getAnimations().forEach(function (a) { a.cancel(); });
      u.lv.style.opacity = 0;
      u.vEx.textContent = '27 dk'; u.arc[2].setAttribute('stroke-dasharray', '90 100'); u.arcV[2] = .9;
      fadeOut(u.map, 450);
      u.qd.style.opacity = 1; fadeIn(u.qd, 300);
      ani(u.qCard, [{ opacity: 0, transform: 'translateY(30px) scale(.94)' }, { opacity: 1, transform: 'none' }], { duration: 520, easing: SPRING });
      ani(u.qPet, [{ transform: 'translateY(16px) scale(.8)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 650, delay: 180, easing: SPRING });
      u.qPet.animate([{ transform: 'translateY(0)' }, { transform: 'translateY(-6px)' }], { duration: 1100, delay: 900, iterations: Infinity, direction: 'alternate', easing: 'ease-in-out' });
      u.rows.forEach(function (r, i) { ani(r, [{ opacity: 0, transform: 'translateX(-14px)' }, { opacity: 1, transform: 'none' }], { duration: 420, delay: 600 + i * 260 }); });
      await wait(1100);
      await count(u.total, 0, 75, 900, function (v) { return '+' + Math.round(v) + ' XP'; });
      u.total.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.18)' }, { transform: 'scale(1)' }], { duration: 380, easing: SPRING });
      ani(u.qBar, [{ width: '270px' }, { width: '276px' }], { duration: 600 });
      u.qBar.animate([{ boxShadow: '0 0 0 rgba(245,196,90,0)' }, { boxShadow: '0 0 18px rgba(245,196,90,.9)' }, { boxShadow: '0 0 0 rgba(245,196,90,0)' }], { duration: 900, delay: 400 });
      await count(u.qXp, 245, 250, 600, function (v) { return Math.round(v) + ' / 250 XP'; });
      u.qNext.textContent = 'Sonraki seviyeye 0 XP';
      u.qBadge.textContent = '6'; pop(u.qBadge); u.qLv.textContent = 'Seviye 6 · Demir';
      await wait(900);
      showF(true); await fingerTo(186, 700, 650); await tap(u.qBtn);
      showF(false);
      /* level up */
      u.lu.style.opacity = 1; fadeIn(u.lu, 350);
      fadeOut(u.qd, 300, 200);
      u.luArc.setAttribute('stroke-dasharray', '92 100');
      await wait(450);
      await tween(650, function (p) { u.luArc.setAttribute('stroke-dasharray', (92 + 8 * eo(p)).toFixed(1) + ' 100'); });
      ani(u.luGlow, [{ opacity: 0, transform: 'scale(.7)' }, { opacity: 1, transform: 'scale(1.15)', offset: .35 }, { opacity: 0, transform: 'scale(1.5)' }], { duration: 900, easing: 'ease-out' });
      u.luBadge.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.14)', offset: .3 }, { transform: 'scale(.96)', offset: .6 }, { transform: 'scale(1)' }], { duration: 700, easing: 'ease-out' });
      ani(u.luNum, [{ transform: 'translateY(0)', opacity: 1 }, { transform: 'translateY(-40px)', opacity: 0 }], { duration: 220, easing: 'ease-in' }).finished.then(function () {
        u.luNum.textContent = '6';
        ani(u.luNum, [{ transform: 'translateY(40px)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 420, easing: SPRING });
      });
      for (var i = 0; i < 26; i++) {
        var ang = Math.random() * Math.PI * 2, dist = 90 + Math.random() * 110, cols = [C.gold, '#7cc4ff', '#f472b6', '#fff', '#5fe0a8'];
        var cf = el(u.lu, abs(177, 200, 6, 10) + 'border-radius:2px;background:' + cols[i % 5] + ';z-index:3;');
        cf.animate([{ transform: 'translate(0,0) rotate(0)', opacity: 1 }, { transform: 'translate(' + Math.cos(ang) * dist + 'px,' + (Math.sin(ang) * dist + 60) + 'px) rotate(' + (Math.random() * 540) + 'deg)', opacity: 0 }], { duration: 1200 + Math.random() * 500, easing: 'cubic-bezier(.15,.7,.3,1)', fill: 'forwards' });
      }
      ani(u.luTitle, [{ opacity: 0, transform: 'scale(.6)' }, { opacity: 1, transform: 'none' }], { duration: 520, delay: 250, easing: SPRING });
      await wait(400);
      await tween(500, function (p) { u.luArc.setAttribute('stroke-dasharray', (100 - 78 * eo(p)).toFixed(1) + ' 100'); });
      ani(u.luPet, [{ opacity: 0, transform: 'translateY(30px) scale(.8)' }, { opacity: 1, transform: 'none' }], { duration: 650, easing: SPRING });
      u.luPet.animate([{ transform: 'translateY(0) rotate(0)' }, { transform: 'translateY(-8px) rotate(-2deg)' }], { duration: 900, delay: 700, iterations: Infinity, direction: 'alternate', easing: 'ease-in-out' });
      pop(u.luPill, 400); fadeIn(u.luNext, 400, 600); fadeIn(u.luBtn, 400, 800);
      await wait(2300);
      showF(true); await fingerTo(186, 732, 650); await tap(u.luBtn);
      showF(false);
      /* back home, badge 6 */
      await (fadeOut(u.lu, 420).finished);
      ani(u.badge, [{ opacity: 0, transform: 'scale(.4)' }, { opacity: 1, transform: 'scale(1)' }], { duration: 520, easing: SPRING });
      u.badge.animate([{ boxShadow: '0 0 0 3px #3a2c17, 0 0 0 4px #6b5326, 0 0 0 rgba(245,196,90,0)' }, { boxShadow: '0 0 0 3px #3a2c17, 0 0 0 4px #6b5326, 0 0 26px rgba(245,196,90,.95)' }, { boxShadow: '0 0 0 3px #3a2c17, 0 0 0 4px #6b5326, 0 0 0 rgba(245,196,90,0)' }], { duration: 1200, delay: 300 });
      floatText(166, 92, '+75 XP', C.gold);
      await wait(2600);
      await (ani(cover, [{ opacity: 0 }, { opacity: 1 }], { duration: 500 }).finished);
    }

    (async function loop() {
      while (!dead) {
        build();
        try { await run(); } catch (e) { if (!dead) console.error(e); return; }
      }
    })();

    function destroy() { dead = true; io && io.disconnect(); ro && ro.disconnect(); root.remove(); }
    return { destroy: destroy };
  }
  window.SuuAndroidTour = { mount: mount };
})();
