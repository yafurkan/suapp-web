/* Suu hero intro v2 — plays over the hero <h1>, then reveals the real headline.
   Usage (after the h1, e.g. end of <body>):
     <script src="/suu-intro.js"></script>
     <script>SuuIntro.play(document.querySelector('.hero h1'), { logo: '/assets/brand/suu-badge-128.png' });</script>
   Options: lang: 'tr' (default) | 'en' · once: 'session' (default) | 'visitor' | false · logo · colors {egz,kal,su} · force */
(function () {
  var ICON = {
    egz: '<path d="M36 60 H84"/><rect x="24" y="38" width="12" height="44" rx="3"/><rect x="84" y="38" width="12" height="44" rx="3"/><path d="M14 48 V72 M106 48 V72"/>',
    kal: '<path d="M24 56 C 24 32, 96 32, 96 56 Z"/><path d="M20 68 H100"/><path d="M24 80 Q 42 73 60 80 T 96 80"/><path d="M26 92 H94 V96 C 94 101, 90 104, 85 104 H35 C 30 104, 26 101, 26 96 Z"/>',
    su: '<path d="M60 18 C 60 18, 32 52, 32 73 A 28 28 0 0 0 88 73 C 88 52, 60 18, 60 18 Z"/>'
  };
  var LABELS = { tr: { egz: 'EGZERSİZ', kal: 'KALORİ', su: 'SU', dec: ',' }, en: { egz: 'EXERCISE', kal: 'CALORIES', su: 'WATER', dec: '.' } };
  var EASE = 'cubic-bezier(.22,1,.36,1)', SOFT = 'cubic-bezier(.4,0,.2,1)';
  var active = new WeakMap();
  function el(tag, css, html) { var e = document.createElement(tag); if (css) e.style.cssText = css; if (html != null) e.innerHTML = html; return e; }
  function cl(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function travelEase(t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  var DEC = ',';
  function fmt(v) { return v.toFixed(2).replace('.', DEC) + ' L'; }
  var SVGNS = 'http://www.w3.org/2000/svg';
  function sv(tag, attrs) { var e = document.createElementNS(SVGNS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }

  function play(h1, o) {
    o = o || {};
    if (!h1 || !h1.animate) return;
    var LABEL = LABELS[o.lang === 'en' ? 'en' : 'tr']; DEC = LABEL.dec;
    if (active.get(h1)) active.get(h1).skip(true);
    var key = o.key || 'suu-hero-intro', store = null;
    try { store = o.once === false ? null : (o.once === 'visitor' ? localStorage : sessionStorage); if (store && store.getItem(key)) return; } catch (e) {}
    if (!o.force && window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    var C = o.colors || { egz: '#f5a524', kal: '#34c77b', su: '#3b8cf6' };
    var host = h1.offsetParent || document.body;
    var W = h1.offsetWidth, H = h1.offsetHeight;
    if (!W || !H) return;
    var S = Math.round(Math.max(40, Math.min(H * 0.26, 76)));
    var D = Math.round(S * 1.5);
    var cy = Math.round(H * 0.44), cx = Math.round(W / 2);
    var span = Math.min(W / 2 - S * 0.7, S * 3.3);
    var X = { egz: cx - span, su: cx, kal: cx + span };
    var small = Math.max(10, Math.round(S * 0.15));

    var prevOp = h1.style.opacity;
    h1.style.opacity = '0';
    var ov = el('div', 'position:absolute;left:' + h1.offsetLeft + 'px;top:' + h1.offsetTop + 'px;width:' + W + 'px;height:' + H + 'px;z-index:5;cursor:pointer;color:#fff;font-family:inherit;line-height:1;letter-spacing:0;');
    ov.setAttribute('aria-hidden', 'true');

    // paths
    var svg = sv('svg', { width: W, height: H, style: 'position:absolute;inset:0;overflow:visible' });
    var P = {};
    ['egz', 'kal'].forEach(function (id) {
      var dir = id === 'egz' ? 1 : -1;
      var x1 = X[id] + dir * (S / 2 + 8), x2 = X.su - dir * (D / 2 + 8);
      var a = H * 0.2 * (id === 'egz' ? -1 : 1);
      var d = 'M' + x1 + ' ' + cy + ' C ' + (x1 + (x2 - x1) * .3) + ' ' + (cy + a) + ', ' + (x1 + (x2 - x1) * .7) + ' ' + (cy + a) + ', ' + x2 + ' ' + cy;
      var base = sv('path', { d: d, fill: 'none', stroke: '#fff', 'stroke-opacity': '.16', 'stroke-width': '1.5', 'stroke-linecap': 'round', pathLength: '1', 'stroke-dasharray': '1', 'stroke-dashoffset': '1' });
      var glow = sv('path', { d: d, fill: 'none', stroke: C[id], 'stroke-opacity': '.28', 'stroke-width': '7', 'stroke-linecap': 'round', pathLength: '1', 'stroke-dasharray': '0 2', opacity: '0' });
      var comet = sv('path', { d: d, fill: 'none', stroke: C[id], 'stroke-width': '2.5', 'stroke-linecap': 'round', pathLength: '1', 'stroke-dasharray': '0 2', opacity: '0' });
      svg.appendChild(base); svg.appendChild(glow); svg.appendChild(comet);
      P[id] = { base: base, glow: glow, comet: comet };
    });
    ov.appendChild(svg);

    // side nodes
    var N = {};
    ['egz', 'kal'].forEach(function (id) {
      var w = el('div', 'position:absolute;left:' + (X[id] - S / 2) + 'px;top:' + (cy - S / 2) + 'px;width:' + S + 'px;height:' + S + 'px;opacity:0;');
      var c = el('div', 'position:absolute;inset:0;border-radius:50%;background:rgba(255,255,255,.035);box-shadow:inset 0 0 0 1px rgba(255,255,255,.16);display:grid;place-items:center;',
        '<svg width="' + S * .46 + '" height="' + S * .46 + '" viewBox="0 0 120 120" fill="none" stroke="' + C[id] + '" stroke-width="7" stroke-linejoin="round" stroke-linecap="round">' + ICON[id] + '</svg>');
      var hi = el('div', 'position:absolute;inset:0;border-radius:50%;box-shadow:inset 0 0 0 1.5px ' + C[id] + ', 0 0 ' + S * .4 + 'px ' + C[id] + '55;opacity:0;');
      var l = el('div', 'position:absolute;left:-40px;right:-40px;top:' + (S + 12) + 'px;text-align:center;font-weight:700;font-size:' + small + 'px;letter-spacing:.18em;opacity:.45;white-space:nowrap;', LABEL[id]);
      c.appendChild(hi); w.appendChild(c); w.appendChild(l); ov.appendChild(w);
      N[id] = { wrap: w, circ: c, hi: hi, label: l };
    });

    // SU hub with liquid
    var su = el('div', 'position:absolute;left:' + (X.su - D / 2) + 'px;top:' + (cy - D / 2) + 'px;width:' + D + 'px;height:' + D + 'px;opacity:0;');
    var bloom = el('div', 'position:absolute;left:-60%;top:-60%;width:220%;height:220%;border-radius:50%;background:radial-gradient(closest-side,' + C.su + '66,' + C.su + '00);opacity:0;');
    var body = el('div', 'position:absolute;inset:0;border-radius:50%;overflow:hidden;background:rgba(255,255,255,.04);box-shadow:inset 0 0 0 1px rgba(255,255,255,.2);');
    var water = el('div', 'position:absolute;left:0;top:0;width:100%;height:100%;');
    var waveW = D * 2;
    var wave = el('div', 'position:absolute;left:0;top:-8px;width:' + waveW + 'px;height:10px;',
      '<svg width="' + waveW + '" height="10" viewBox="0 0 ' + waveW + ' 10" preserveAspectRatio="none" style="display:block"><path d="M0 5 ' +
      (function () { var s = '', q = D / 4; for (var i = 0; i < 8; i++) s += 'Q ' + (i * q * 2 + q) + ' ' + (i % 2 ? 10 : 0) + ' ' + (i * q * 2 + q * 2) + ' 5 '; return s; })() +
      'V 10 H0 Z" fill="' + C.su + '"/></svg>');
    var fill = el('div', 'position:absolute;left:0;right:0;top:1px;height:' + D + 'px;background:' + C.su + ';');
    water.appendChild(wave); water.appendChild(fill);
    body.appendChild(water);
    var dropIcon = el('div', 'position:absolute;inset:0;display:grid;place-items:center;',
      '<svg width="' + D * .42 + '" height="' + D * .42 + '" viewBox="0 0 120 120" fill="none" stroke="#fff" stroke-width="6" stroke-linejoin="round" stroke-linecap="round">' + ICON.su + '</svg>');
    body.appendChild(dropIcon);
    var ripple = el('div', 'position:absolute;inset:0;border-radius:50%;box-shadow:0 0 0 1.5px ' + C.su + ';opacity:0;');
    var count = el('div', 'position:absolute;left:-60px;right:-60px;top:' + (D + 12) + 'px;text-align:center;font-weight:700;font-size:' + Math.max(12, Math.round(S * .2)) + 'px;letter-spacing:.02em;font-variant-numeric:tabular-nums;opacity:0;', fmt(2.5));
    su.appendChild(bloom); su.appendChild(body); su.appendChild(ripple); su.appendChild(count);
    ov.appendChild(su);

    // travelling light: head + trail, one per path
    var TRAIL = 7;
    ['egz', 'kal'].forEach(function (id) {
      P[id].trail = [];
      for (var i = 0; i < TRAIL; i++) {
        var sz = Math.max(3, S * .16 * (1 - i / TRAIL));
        var t = el('div', 'position:absolute;left:' + (-sz / 2) + 'px;top:' + (-sz / 2) + 'px;width:' + sz + 'px;height:' + sz + 'px;border-radius:50%;opacity:0;will-change:transform,opacity;');
        ov.appendChild(t); P[id].trail.push(t);
      }
    });
    // logo that drops in from above
    var LG = Math.round(D * 1.08);
    var drop = el('div', 'position:absolute;left:' + (X.su - LG / 2) + 'px;top:' + (cy - LG / 2) + 'px;width:' + LG + 'px;height:' + LG + 'px;opacity:0;z-index:2;');
    var dropGlow = el('div', 'position:absolute;left:-70%;top:-70%;width:240%;height:240%;border-radius:50%;background:radial-gradient(closest-side,rgba(255,255,255,.28),rgba(255,255,255,0));opacity:0;');
    var dropImg = el('div', 'position:absolute;inset:0;border-radius:50%;overflow:hidden;box-shadow:0 0 0 1px rgba(255,255,255,.25), 0 0 ' + LG * .35 + 'px rgba(255,255,255,.35);',
      '<img src="' + (o.logo || '/assets/brand/suu-badge-128.png') + '" alt="" style="width:100%;height:100%;object-fit:cover;display:block">');
    drop.appendChild(dropGlow); drop.appendChild(dropImg); ov.appendChild(drop);
    host.appendChild(ov);

    var T0 = performance.now(), anims = [], tasks = [], raf = 0, done = false;
    function A(n, f, d, dur, e, extra) { var opt = { delay: d, duration: dur, easing: e || EASE, fill: 'both' }; if (extra) for (var k in extra) opt[k] = extra[k]; var a = n.animate(f, opt); anims.push(a); return a; }

    // 0 — appear
    A(N.egz.wrap, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], 80, 700);
    A(su, [{ opacity: 0, transform: 'scale(.9)' }, { opacity: 1, transform: 'none' }], 160, 800);
    A(N.kal.wrap, [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }], 240, 700);
    A(count, [{ opacity: 0 }, { opacity: .9 }], 600, 500);
    ['egz', 'kal'].forEach(function (id, i) { A(P[id].base, [{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], 350 + i * 120, 900, SOFT); });
    var level = 0.3;
    function levelY(l) { return 'translateY(' + (D * (1 - l)) + 'px)'; }
    water.style.transform = levelY(level);
    A(wave, [{ transform: 'translateX(0)' }, { transform: 'translateX(' + (-D) + 'px)' }], 0, 1800, 'linear', { iterations: Infinity, fill: 'none' });

    var SPRING = [
      { transform: 'scale(1)', easing: SOFT },
      { transform: 'scale(1.06)', offset: .3, easing: 'cubic-bezier(.5,0,.75,0)' },
      { transform: 'scale(.92)', offset: .48, easing: 'cubic-bezier(.25,1,.5,1)' },
      { transform: 'scale(1.07)', offset: .72, easing: SOFT },
      { transform: 'scale(.99)', offset: .88, easing: SOFT },
      { transform: 'scale(1)' }
    ];
    function travel(id, t0, dur, back) {
      var geo = P[id].base, tr = P[id].trail, col = back ? C.su : C[id];
      tasks.push({
        t0: t0, dur: dur, run: function (p) {
          var e = travelEase(p), L = geo.getTotalLength(), seg = .22;
          var pos = back ? 1 - e : e;
          var off = back ? -pos : seg - pos;
          [P[id].comet, P[id].glow].forEach(function (n) { n.setAttribute('stroke', col); n.setAttribute('stroke-dasharray', seg + ' 2'); n.setAttribute('stroke-dashoffset', off); });
          var fade = cl(p / .08) * cl((1 - p) / .12);
          P[id].comet.setAttribute('opacity', fade); P[id].glow.setAttribute('opacity', fade);
          var shrink = p > .86 ? 1 - (p - .86) / .14 : 1;
          for (var k = 0; k < TRAIL; k++) {
            var ek = back ? Math.min(1, pos + k * .018) : Math.max(0, pos - k * .018);
            var pt = geo.getPointAtLength(ek * L);
            tr[k].style.background = k === 0 ? '#fff' : col;
            tr[k].style.boxShadow = k === 0 ? '0 0 ' + S * .25 + 'px ' + S * .08 + 'px ' + col : 'none';
            tr[k].style.opacity = (fade * (1 - k / TRAIL)).toFixed(3);
            tr[k].style.transform = 'translate(' + pt.x + 'px,' + pt.y + 'px) scale(' + Math.max(.05, shrink) + ')';
          }
        }, end: function () { for (var k = 0; k < TRAIL; k++) tr[k].style.opacity = 0; P[id].comet.setAttribute('opacity', 0); P[id].glow.setAttribute('opacity', 0); }
      });
    }
    function feed(id, t0, dur, toLevel, fromL, toL) {
      travel(id, t0, dur, false);
      A(N[id].circ, [{ transform: 'scale(1)' }, { transform: 'scale(.93)', offset: .35 }, { transform: 'scale(1.03)', offset: .7 }, { transform: 'scale(1)' }], t0 - 140, 520, SOFT);
      A(N[id].hi, [{ opacity: 0 }, { opacity: 1, offset: .2 }, { opacity: 0 }], t0 - 140, dur * .9, SOFT);
      var arrive = t0 + dur;
      A(su, SPRING, arrive - 260, 860, 'linear');
      bloom.style.background = 'radial-gradient(closest-side,' + C[id] + '66,' + C[id] + '00)';
      A(bloom, [{ opacity: 0 }, { opacity: 1, offset: .3 }, { opacity: 0 }], arrive - 40, 900, SOFT);
      A(ripple, [{ opacity: .8, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(1.55)' }], arrive + 40, 800);
      A(water, [{ transform: levelY(level) }, { transform: levelY(toLevel) }], arrive + 20, 900);
      level = toLevel;
      tasks.push({ t0: arrive + 20, dur: 900, run: function (p) { var e = 1 - Math.pow(1 - p, 3); count.textContent = fmt(fromL + (toL - fromL) * e); } });
    }
    function giveBack(t0, dur) {
      A(su, [{ transform: 'scale(1)' }, { transform: 'scale(.94)', offset: .35 }, { transform: 'scale(1.03)', offset: .7 }, { transform: 'scale(1)' }], t0 - 140, 520, SOFT);
      ['egz', 'kal'].forEach(function (id) {
        travel(id, t0, dur, true);
        A(N[id].circ, SPRING, t0 + dur - 240, 820, 'linear');
        A(N[id].hi, [{ opacity: 0 }, { opacity: 1, offset: .3 }, { opacity: .5 }], t0 + dur - 80, 600, SOFT);
      });
    }
    feed('egz', 900, 900, .58, 2.5, 3.0);
    feed('kal', 1750, 900, .82, 3.0, 3.25);
    giveBack(2700, 800);

    // logo drops in from above and pulls everything in
    var LD = 3600, PULL = LD + 650;
    A(drop, [
      { opacity: 0, transform: 'translateY(' + (-(cy + LG)) + 'px) scale(.85)' },
      { opacity: 1, transform: 'translateY(' + (-(cy + LG) * .25) + 'px) scale(.95)', offset: .55 },
      { opacity: 1, transform: 'translateY(4px) scale(1.02)', offset: .85 },
      { opacity: 1, transform: 'none' }
    ], LD, 700, SOFT);
    A(dropGlow, [{ opacity: 0 }, { opacity: 1 }], LD + 300, 600, SOFT);
    A(count, [{ opacity: .9 }, { opacity: 0 }], LD, 350, SOFT);
    A(su, [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(.4)' }], LD + 450, 380, 'cubic-bezier(.55,0,1,.45)');
    ['egz', 'kal'].forEach(function (id) {
      A(N[id].label, [{ opacity: .45 }, { opacity: 0 }], PULL - 150, 250, SOFT);
      A(N[id].wrap, [
        { opacity: 1, transform: 'none' },
        { opacity: 1, transform: 'translateX(' + (X.su - X[id]) * .15 + 'px) scale(1.08,.94)', offset: .3 },
        { opacity: 0, transform: 'translateX(' + (X.su - X[id]) + 'px) scale(.12)' }
      ], PULL, 520, 'cubic-bezier(.6,0,.9,.4)');
      A(P[id].base, [{ strokeDashoffset: 0, opacity: 1 }, { strokeDashoffset: -1, opacity: .6 }], PULL, 480, 'cubic-bezier(.6,0,.9,.4)');
    });
    A(dropImg, SPRING, PULL + 380, 860, 'linear');
    A(dropGlow, [{ opacity: 1, transform: 'scale(1)' }, { opacity: 1, transform: 'scale(1.35)', offset: .35 }, { opacity: .8, transform: 'scale(1.1)' }], PULL + 440, 700, SOFT);
    var CV = PULL + 1100;

    function tick(now) {
      if (done) return;
      var t = now - T0;
      tasks.forEach(function (k) {
        if (k.fin || t < k.t0) return;
        var p = cl((t - k.t0) / k.dur);
        k.run(p);
        if (p >= 1) { k.fin = true; k.end && k.end(); }
      });
      raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);

    var endTimer = setTimeout(function () { finish(false); }, CV);
    function finish(fast) {
      if (done) return; done = true;
      clearTimeout(endTimer); cancelAnimationFrame(raf);
      var dur = fast ? 220 : 520;
      var out = ov.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(-6px)' }], { duration: dur, easing: SOFT, fill: 'forwards' });
      h1.style.opacity = prevOp;
      h1.animate([
        { opacity: 0, transform: 'translateY(10px)', clipPath: 'inset(0 0 100% 0)' },
        { opacity: 1, transform: 'none', clipPath: 'inset(0 0 0% 0)' }
      ], { duration: fast ? 400 : 1000, delay: fast ? 0 : 120, easing: EASE, fill: 'backwards' });
      out.onfinish = function () {
        anims.forEach(function (a) { a.cancel(); });
        ov.remove();
        try { store && store.setItem(key, '1'); } catch (e) {}
        active.delete(h1);
        o.onDone && o.onDone();
      };
    }
    ov.addEventListener('click', function () { finish(true); });
    var handle = { skip: function (fast) { finish(fast); } };
    active.set(h1, handle);
    return handle;
  }

  window.SuuIntro = { play: play };
})();
