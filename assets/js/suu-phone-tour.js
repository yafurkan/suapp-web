/* Suu phone tour — coded, looping in-app walkthrough for the hero phone mockup.
   Usage:
     <div id="suu-tour" style="width:300px;aspect-ratio:390/844"></div>
     <script src="/assets/js/suu-phone-tour.js"></script>
     <script>SuuPhoneTour.mount(document.getElementById('suu-tour'), { camera:'/assets/tour/camera.jpg', map:'/assets/tour/map.jpg' });</script>
   The element is the phone SCREEN (put it inside your existing frame). Pauses off-screen; static under reduced motion. */
(function () {
  var W = 390, H = 844;
  var F = '-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","Segoe UI",Roboto,sans-serif';
  var C = { blue: '#3b82f6', green: '#22c55e', pink: '#f7727f', cyan: '#00a8e8', red: '#f0443a', gray: '#9aa3b8', yellow: '#f3c343', purple: '#8b5cf6', orange: '#f59e0b' };
  var OUT = 'cubic-bezier(.22,1,.36,1)', IO = 'cubic-bezier(.65,0,.35,1)', SPRING = 'cubic-bezier(.34,1.56,.64,1)';
  var I = {
    drop: '<path d="M12 2.5C12 2.5 5 10.5 5 15a7 7 0 0 0 14 0c0-4.5-7-12.5-7-12.5z"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    home: '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z"/>',
    user: '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="10" r="3.5"/><path d="M6 19c1.5-3 4-4 6-4s4.5 1 6 4"/>',
    camera: '<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="4"/>',
    run: '<circle cx="14.5" cy="4" r="2"/><path d="M7 21l3.5-6 3 2.5V22M5 12l3.5-3.5 4.5 1 2.5 3.5 3 1M10.5 15l2.5-5.5"/>',
    chev: '<path d="M8 9l4-4 4 4M8 15l4 4 4-4"/>',
    chevR: '<path d="M9 6l6 6-6 6"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
    cloud: '<path d="M7 19h10a4 4 0 0 0 .5-7.97A6 6 0 0 0 6.1 10.5 4.3 4.3 0 0 0 7 19z"/>',
    fork: '<path d="M7 3v8a2 2 0 0 0 2 2v8M5 3v5a2 2 0 0 0 4 0V3M17 21V3c-2 1.5-3 4-3 7v3h3"/>',
    cup: '<path d="M4 9h13v4a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M17 10h2a2 2 0 0 1 0 4h-2M3 21h16"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    paw: '<circle cx="6.5" cy="10" r="2"/><circle cx="10" cy="6" r="2"/><circle cx="14" cy="6" r="2"/><circle cx="17.5" cy="10" r="2"/><path d="M7.5 17c0-3 2.2-5 4.5-5s4.5 2 4.5 5c0 1.6-1.6 2.5-4.5 2.5S7.5 18.6 7.5 17z"/>',
    share: '<path d="M12 3v10M8 7l4-4 4 4"/><path d="M6 11h-.5A1.5 1.5 0 0 0 4 12.5v7A1.5 1.5 0 0 0 5.5 21h13a1.5 1.5 0 0 0 1.5-1.5v-7a1.5 1.5 0 0 0-1.5-1.5H18"/>',
    wifi: '<path d="M2 8.5a15 15 0 0 1 20 0M5 12a10 10 0 0 1 14 0M8.5 15.5a5 5 0 0 1 7 0"/>'
  };
  function icon(n, s, c, fill, sw) { return '<svg width="' + s + '" height="' + s + '" viewBox="0 0 24 24" fill="' + (fill ? c : 'none') + '" stroke="' + (fill ? 'none' : c) + '" stroke-width="' + (sw || 2) + '" stroke-linecap="round" stroke-linejoin="round" style="display:block;flex:none">' + I[n] + '</svg>'; }
  function el(p, css, html, tag) { var e = document.createElement(tag || 'div'); if (css) e.style.cssText = css; if (html != null) e.innerHTML = html; if (p) p.appendChild(e); return e; }
  function abs(x, y, w, h) { return 'position:absolute;left:' + x + 'px;top:' + y + 'px;' + (w != null ? 'width:' + w + 'px;' : '') + (h != null ? 'height:' + h + 'px;' : ''); }
  function eo(p) { return 1 - Math.pow(1 - p, 3); }
  function mmss(s) { s = Math.round(s); return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
  function pace(s) { s = Math.round(s); return Math.floor(s / 60) + "'" + String(s % 60).padStart(2, '0') + '"'; }

  function seeded(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  var COAST = [[0, 840], [260, 790], [520, 770], [820, 715], [960, 720], [1250, 810], [1500, 900]];
  function coastX(y) { for (var i = 1; i < COAST.length; i++) if (y <= COAST[i][0]) { var a = COAST[i - 1], b = COAST[i], k = (y - a[0]) / (b[0] - a[0]); return a[1] + (b[1] - a[1]) * k; } return 900; }
  var PARKS = [[185, 300, 515, 615], [555, 880, 705, 1250], [40, 880, 300, 1140], [360, 1130, 520, 1340]];
  function inPark(x, y, pad) { pad = pad || 0; return PARKS.some(function (p) { return x > p[0] - pad && x < p[2] + pad && y > p[1] - pad && y < p[3] + pad; }); }
  var ROUTE = 'M330 780 L330 660 C 330 620, 300 600, 280 570 C 250 520, 260 450, 320 420 C 380 390, 450 400, 480 360 L 540 290 C 580 250, 650 250, 700 300 L 736 400 C 740 520, 690 640, 690 760 C 690 860, 668 930, 680 1000 C 690 1100, 720 1180, 760 1260 L 700 1310 C 650 1330, 600 1300, 590 1250 L 540 1060 C 530 1000, 540 960, 520 900';
  var TXT = {
    tr: { hello: 'Hadi Başlayalım, Furkan! 💪', water: 'Su', nutrition: 'Beslenme', exercise: 'Egzersiz', min: 'dk', tapHint: 'Dokun ekle · Basılı tut daha fazlası', kcalLbl: 'kalori', carbShort: 'Karb', protein: 'Protein', fat: 'Yağ', carbs: 'Karbonhidrat', daily: 'Günlük Özet', cola: 'Kola', home: 'Ana Sayfa', you: 'Sen',
      menu: ['Besin Ekle', 'Egzersiz Ekle', 'Hızlı İçecek', 'Hedefe Yaklaştır', 'Pet Dostum', 'Story Paylaş'], mealAnalysis: 'ÖĞÜN ANALİZİ', mealName: 'Pepperoni pizza + Kola', pizza: 'Pepperoni pizza', addMeal: 'Öğüne ekle', run: 'Koşu', start: 'Başlat', history: 'Geçmiş', gps: 'GPS aktif', stats: ['MESAFE', 'SÜRE', 'TEMPO'], pause: 'Duraklat', finish: 'Bitir', runDone: 'KOŞU TAMAMLANDI', dist: '4,82', time: 'Süre', pace: 'Tempo', goalUp: 'Su hedefin +500 ml arttı', goalFloat: '+500 ml hedef', dec: ',',
      parks: ['Maçka Parkı', 'Yıldız Parkı', 'Abbasağa Parkı', 'Ihlamur Bahçesi'], sea: 'BOĞAZİÇİ', road: 'Dolmabahçe Cd.' },
    en: { hello: "Let's get started, Furkan! 💪", water: 'Water', nutrition: 'Nutrition', exercise: 'Exercise', min: 'min', tapHint: 'Tap to add · Hold for more', kcalLbl: 'kcal', carbShort: 'Carbs', protein: 'Protein', fat: 'Fat', carbs: 'Carbs', daily: 'Daily Summary', cola: 'Cola', home: 'Home', you: 'You',
      menu: ['Add Food', 'Add Exercise', 'Quick Drink', 'Boost Goal', 'Pet Buddy', 'Share Story'], mealAnalysis: 'MEAL ANALYSIS', mealName: 'Pepperoni pizza + Cola', pizza: 'Pepperoni pizza', addMeal: 'Add to meal', run: 'Run', start: 'Start', history: 'History', gps: 'GPS active', stats: ['DISTANCE', 'TIME', 'PACE'], pause: 'Pause', finish: 'Finish', runDone: 'RUN COMPLETE', dist: '4.82', time: 'Time', pace: 'Pace', goalUp: 'Water goal +500 ml', goalFloat: '+500 ml goal', dec: '.',
      parks: ['Maçka Park', 'Yıldız Park', 'Abbasağa Park', 'Ihlamur Garden'], sea: 'BOSPHORUS', road: 'Dolmabahçe Ave.', camFix: true }
  };
  function streetMap(p, T) {
    var layer = el(p, 'position:absolute;inset:0;overflow:hidden;opacity:0;background:#232937;');
    var world = el(layer, 'position:absolute;left:0;top:0;width:1200px;height:1500px;transform-origin:0 0;will-change:transform;');
    var r = seeded(11), x, y, i, s = '<svg width="1200" height="1500" viewBox="0 0 1200 1500" style="display:block;overflow:visible;font-family:' + F + '">';
    s += '<defs><radialGradient id="suuCone" cx="50%" cy="100%" r="100%"><stop offset="0" stop-color="#3aa0ff" stop-opacity=".55"/><stop offset="1" stop-color="#3aa0ff" stop-opacity="0"/></radialGradient></defs>';
    var VX = [], HY = [];
    for (x = 98; x < 1200; x += 116) VX.push(x);
    for (y = 97; y < 1500; y += 104) HY.push(y);
    VX.forEach(function (vx) { s += '<path d="M' + vx + ' 0V1500" stroke="#3a4152" stroke-width="10"/>'; });
    HY.forEach(function (hy) { s += '<path d="M0 ' + hy + 'H1200" stroke="#3a4152" stroke-width="10"/>'; });
    var green = [];
    for (x = -18; x < 1200; x += 116) for (y = -12; y < 1500; y += 104) {
      var bx = x + 6, by = y + 5, bw = 100, bh = 88;
      if (bx + bw > coastX(by + bh / 2) - 58 || inPark(bx + bw / 2, by + bh / 2, 40)) continue;
      var t = r();
      s += '<rect x="' + bx + '" y="' + by + '" width="' + bw + '" height="' + bh + '" rx="8" fill="#2b3140"/>';
      if (t < .3) {
        s += '<rect x="' + (bx + 6) + '" y="' + (by + 6) + '" width="' + (bw - 12) + '" height="' + (bh - 12) + '" rx="10" fill="#22402f"/>';
        s += '<path d="M' + (bx + 14) + ' ' + (by + bh / 2) + ' C ' + (bx + 40) + ' ' + (by + 12) + ', ' + (bx + 60) + ' ' + (by + bh - 12) + ', ' + (bx + bw - 14) + ' ' + (by + bh / 2) + '" fill="none" stroke="#3a6a50" stroke-width="2.5" stroke-dasharray="5 5"/>';
        green.push([bx + 6, by + 6, bx + bw - 6, by + bh - 6, 5]);
      } else if (t < .55) {
        s += '<rect x="' + (bx + 6) + '" y="' + (by + 6) + '" width="' + (bw - 12) + '" height="' + (bh - 12) + '" rx="5" fill="#353c4e"/>';
        s += '<rect x="' + (bx + 24) + '" y="' + (by + 22) + '" width="' + (bw - 48) + '" height="' + (bh - 44) + '" rx="8" fill="#22402f"/>';
        green.push([bx + 24, by + 22, bx + bw - 24, by + bh - 22, 2]);
      } else {
        var cols = 2 + (r() > .5 ? 1 : 0), cw = (bw - 12 - (cols - 1) * 5) / cols;
        for (var c = 0; c < cols; c++) {
          var hh = (bh - 17) / 2;
          for (var rr = 0; rr < 2; rr++) {
            if (r() < .22) { s += '<rect x="' + (bx + 6 + c * (cw + 5)).toFixed(1) + '" y="' + (by + 6 + rr * (hh + 5)).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + hh.toFixed(1) + '" rx="4" fill="#24402f"/>'; green.push([bx + 6 + c * (cw + 5), by + 6 + rr * (hh + 5), bx + 6 + c * (cw + 5) + cw, by + 6 + rr * (hh + 5) + hh, 1]); continue; }
            var sh = r() > .5 ? '#363d50' : '#323849';
            s += '<rect x="' + (bx + 6 + c * (cw + 5)).toFixed(1) + '" y="' + (by + 6 + rr * (hh + 5)).toFixed(1) + '" width="' + cw.toFixed(1) + '" height="' + hh.toFixed(1) + '" rx="3" fill="' + sh + '"/>';
          }
        }
      }
    }
    s += '<path d="M200 330 Q 340 296 500 340 L 512 592 Q 360 624 188 602 Z" fill="#23402f"/>';
    s += '<path d="M560 900 Q 640 878 692 908 L 702 1232 Q 620 1254 558 1222 Z" fill="#23402f"/>';
    s += '<path d="M48 890 Q 170 866 296 896 L 292 1136 Q 160 1150 44 1130 Z" fill="#23402f"/><ellipse cx="170" cy="1010" rx="56" ry="30" fill="#1b2a52"/><ellipse cx="170" cy="1010" rx="56" ry="30" fill="none" stroke="#2a3d6e" stroke-width="3"/>';
    s += '<path d="M366 1138 Q 440 1124 516 1140 L 514 1334 Q 440 1346 362 1330 Z" fill="#23402f"/>';
    s += '<path d="M215 560 C 280 520, 250 440, 330 410 S 470 380, 495 350" fill="none" stroke="#3a6a50" stroke-width="3" stroke-dasharray="6 6"/>';
    s += '<path d="M572 1200 C 610 1120, 600 1000, 660 920" fill="none" stroke="#3a6a50" stroke-width="3" stroke-dasharray="6 6"/>';
    s += '<path d="M790 0 C 750 200, 712 380, 722 520 S 652 820, 672 960 S 752 1250, 852 1500" fill="none" stroke="#4b5468" stroke-width="14"/>';
    s += '<path id="suuCoastRd" d="M790 0 C 750 200, 712 380, 722 520 S 652 820, 672 960 S 752 1250, 852 1500" fill="none" stroke="#5a6377" stroke-width="2" stroke-dasharray="10 12"/>';
    s += '<path d="M840 0 C 800 200, 760 380, 770 520 S 700 820, 720 960 S 800 1250, 900 1500 L1200 1500 L1200 0 Z" fill="#1b2a52"/>';
    s += '<path d="M840 0 C 800 200, 760 380, 770 520 S 700 820, 720 960 S 800 1250, 900 1500" fill="none" stroke="#2a3d6e" stroke-width="4"/>';
    s += '<g data-waves>';
    for (i = 0; i < 22; i++) { y = 40 + i * 66 + r() * 20; x = coastX(y) + 50 + r() * (330 - (coastX(y) - 700)); s += '<path d="M' + x.toFixed(0) + ' ' + y.toFixed(0) + ' q 10 -6 20 0 t 20 0 t 20 0 t 20 0" fill="none" stroke="#6f8fdc" stroke-opacity=".28" stroke-width="2" stroke-linecap="round" stroke-dasharray="26 34"/>'; }
    s += '</g>';
    s += '<g data-trees>';
    function trees(n, box) { for (var k = 0; k < n; k++) { var tx, ty, tries = 0; do { tx = box[0] + 18 + r() * (box[2] - box[0] - 36); ty = box[1] + 22 + r() * (box[3] - box[1] - 44); tries++; } while (tries < 5 && Math.abs(ty - 480) < 12); var tr = 6 + r() * 6; s += '<g transform="translate(' + tx.toFixed(0) + ' ' + ty.toFixed(0) + ')"><g class="suuT" style="transform-box:fill-box;transform-origin:center"><circle r="' + tr.toFixed(1) + '" fill="#2d5a41"/><circle cx="' + (-tr * .3).toFixed(1) + '" cy="' + (-tr * .3).toFixed(1) + '" r="' + (tr * .55).toFixed(1) + '" fill="#3c7556"/></g></g>'; } }
    trees(34, PARKS[0]); trees(20, PARKS[1]); trees(16, PARKS[2]); trees(12, PARKS[3]);
    green.forEach(function (g) { var n = g[4]; for (var k = 0; k < n; k++) { var tx = g[0] + 8 + r() * (g[2] - g[0] - 16), ty = g[1] + 8 + r() * (g[3] - g[1] - 16), tr = 4 + r() * 4; s += '<g transform="translate(' + tx.toFixed(0) + ' ' + ty.toFixed(0) + ')"><g class="suuT" style="transform-box:fill-box;transform-origin:center"><circle r="' + tr.toFixed(1) + '" fill="#2d5a41"/><circle cx="' + (-tr * .3).toFixed(1) + '" cy="' + (-tr * .3).toFixed(1) + '" r="' + (tr * .55).toFixed(1) + '" fill="#3c7556"/></g></g>'; } });
    for (y = 20; y < 1500; y += 34) { x = coastX(y) - 66; s += '<circle cx="' + x.toFixed(0) + '" cy="' + y + '" r="5" fill="#2d5a41"/>'; }
    s += '</g>';
    s += '<g data-ferry style="transform-box:fill-box"><path d="M-8 30 L-4 60 M8 30 L4 60" stroke="#8fb0ff" stroke-opacity=".35" stroke-width="2"/><path d="M-9 -16 L9 -16 L9 22 L0 30 L-9 22 Z" fill="#d9dee8"/><rect x="-5" y="-8" width="10" height="14" rx="2" fill="#9aa6bf"/></g>';
    function lab(x, y, t, c, sz, rot, ls) { return '<text x="' + x + '" y="' + y + '" fill="' + c + '" font-size="' + sz + '" font-weight="700" letter-spacing="' + (ls || 1.5) + '" text-anchor="middle"' + (rot ? ' transform="rotate(' + rot + ' ' + x + ' ' + y + ')"' : '') + '>' + t + '</text>'; }
    s += lab(345, 478, T.parks[0], '#7cc49a', 14, 0, .3) + lab(630, 1070, T.parks[1], '#7cc49a', 13, -84, .3);
    s += lab(1010, 720, T.sea, '#5b7fc7', 18, -78, 8) + lab(130, 210, 'NİŞANTAŞI', '#8a93a8', 12, 0, 2.5) + lab(170, 1070, T.parks[2], '#7cc49a', 13, 0, .3) + lab(440, 1240, T.parks[3], '#7cc49a', 12, 0, .3) + lab(470, 800, 'BEŞİKTAŞ', '#8a93a8', 13, 0, 3) + lab(560, 1400, 'ORTAKÖY', '#8a93a8', 12, 0, 2.5);
    s += '<text fill="#8a93a8" font-size="11" font-weight="700" letter-spacing=".5"><textPath href="#suuCoastRd" startOffset="38%">' + T.road + '</textPath></text>';
    s += '<g data-cars>';
    var CARC = ['#e8ebf1', '#f5c65a', '#ff8f7f', '#9fc3ff', '#e8ebf1'];
    for (i = 0; i < 26; i++) {
      var col = CARC[i % CARC.length];
      s += '<g data-car="' + i + '"><rect x="-7" y="-3.5" width="14" height="7" rx="2.5" fill="' + col + '"/><rect x="2" y="-2.5" width="3" height="5" rx="1" fill="#1b2130" fill-opacity=".55"/><circle cx="7.5" cy="-2" r="1.3" fill="#fff6c2"/><circle cx="7.5" cy="2" r="1.3" fill="#fff6c2"/></g>';
    }
    s += '</g>';
    s += '<path data-casing d="' + ROUTE + '" fill="none" stroke="#0b1a36" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>';
    s += '<path data-glow d="' + ROUTE + '" fill="none" stroke="#1e90ff" stroke-opacity=".35" stroke-width="18" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>';
    s += '<path data-route d="' + ROUTE + '" fill="none" stroke="#3aa0ff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" opacity="0"/>';
    s += '<g data-marks></g>';
    s += '<g data-head><circle data-pulse r="11" fill="#1e90ff" fill-opacity=".35" style="transform-box:fill-box;transform-origin:center"/><path d="M0 0 L-24 -52 A 58 58 0 0 1 24 -52 Z" fill="url(#suuCone)"/><circle r="9" fill="#1e90ff" stroke="#fff" stroke-width="3"/></g>';
    world.innerHTML = s + '</svg>';
    var q = function (a) { return world.querySelector('[' + a + ']'); };
    var m = { layer: layer, world: world, route: q('data-route'), glow: q('data-glow'), casing: q('data-casing'), head: q('data-head'), marks: q('data-marks') };
    m.animate = function () {
      Array.prototype.forEach.call(world.querySelectorAll('[data-waves] path'), function (w, k) { w.animate([{ strokeDashoffset: 0 }, { strokeDashoffset: -60 }], { duration: 2600 + (k % 5) * 400, iterations: Infinity }); w.animate([{ transform: 'translateY(0)' }, { transform: 'translateY(-4px)' }], { duration: 1800 + (k % 3) * 300, iterations: Infinity, direction: 'alternate', easing: 'ease-in-out' }); });
      Array.prototype.forEach.call(world.querySelectorAll('.suuT'), function (t, k) { t.animate([{ transform: 'scale(1) rotate(0deg)' }, { transform: 'scale(1.07) rotate(4deg)' }], { duration: 1400 + (k % 7) * 180, delay: -(k * 137 % 1400), iterations: Infinity, direction: 'alternate', easing: 'ease-in-out' }); });
      q('data-ferry').animate([{ transform: 'translate(930px,1480px) rotate(-8deg)' }, { transform: 'translate(880px,760px) rotate(4deg)' }, { transform: 'translate(900px,40px) rotate(-6deg)' }], { duration: 26000, iterations: Infinity });
      var rr2 = seeded(5);
      Array.prototype.forEach.call(world.querySelectorAll('[data-car]'), function (car, k) {
        var dur = 7000 + rr2() * 7000, dly = -rr2() * dur, fw = k % 2 === 0, f;
        if (k < 8) {
          car.style.offsetPath = "path('" + (fw ? 'M790 0 C 750 200, 712 380, 722 520 S 652 820, 672 960 S 752 1250, 852 1500' : 'M852 1500 C 752 1250, 672 960, 672 960 S 652 820, 722 520 S 750 200, 790 0') + "')";
          car.style.offsetRotate = 'auto';
          car.style.transform = 'translateY(' + (fw ? 3.5 : 3.5) + 'px)';
          car.animate([{ offsetDistance: '0%' }, { offsetDistance: '100%' }], { duration: dur * 1.4, delay: dly, iterations: Infinity });
        } else if (k < 17) {
          var hy = [201, 721, 825, 1449, 201, 721, 825, 1449, 721][k - 8];
          var ly = hy + (fw ? 3 : -3), xe = coastX(hy) - 52;
          var A = 'translate(-40px,' + ly + 'px)', B = 'translate(' + xe + 'px,' + ly + 'px)';
          f = fw ? [{ transform: A, opacity: 0 }, { opacity: 1, offset: .06 }, { opacity: 1, offset: .94 }, { transform: B, opacity: 0 }]
                 : [{ transform: B + ' rotate(180deg)', opacity: 0 }, { opacity: 1, offset: .06 }, { opacity: 1, offset: .94 }, { transform: A + ' rotate(180deg)', opacity: 0 }];
          car.animate(f, { duration: dur, delay: dly, iterations: Infinity });
        } else {
          var seg = [[98, -40, 860], [562, -40, 860], [330, 640, 1540], [446, 640, 1110], [214, 640, 860], [98, -40, 860], [562, -40, 860], [330, 640, 1540], [446, 640, 1110]][k - 17];
          var lx = seg[0] + (fw ? -3 : 3);
          var T0 = 'translate(' + lx + 'px,' + seg[1] + 'px)', T1 = 'translate(' + lx + 'px,' + seg[2] + 'px)';
          f = fw ? [{ transform: T0 + ' rotate(90deg)', opacity: 0 }, { opacity: 1, offset: .08 }, { opacity: 1, offset: .92 }, { transform: T1 + ' rotate(90deg)', opacity: 0 }]
                 : [{ transform: T1 + ' rotate(-90deg)', opacity: 0 }, { opacity: 1, offset: .08 }, { opacity: 1, offset: .92 }, { transform: T0 + ' rotate(-90deg)', opacity: 0 }];
          car.animate(f, { duration: dur * (seg[2] - seg[1]) / 1100, delay: dly, iterations: Infinity });
        }
      });
      q('data-pulse').animate([{ transform: 'scale(1)', opacity: 1 }, { transform: 'scale(2.6)', opacity: 0 }], { duration: 1600, iterations: Infinity });
    };
    m.setHead = function (pt, a) { m.head.setAttribute('transform', 'translate(' + pt.x.toFixed(1) + ' ' + pt.y.toFixed(1) + ') rotate(' + a.toFixed(1) + ')'); };
    m.addMark = function (pt, km, pc, right) {
      var NS = 'http://www.w3.org/2000/svg', g = document.createElementNS(NS, 'g'), inner = document.createElementNS(NS, 'g');
      g.setAttribute('transform', 'translate(' + pt.x + ' ' + pt.y + ')');
      inner.setAttribute('style', 'transform-box:fill-box;transform-origin:center');
      var w = 96, x0 = right ? -w - 14 : 14;
      inner.innerHTML = '<rect x="' + x0 + '" y="-14" width="' + w + '" height="28" rx="14" fill="#0c121c" fill-opacity=".92"/><text x="' + (x0 + 12) + '" y="5" fill="#fff" font-size="12.5" font-weight="800">' + km + ' km <tspan fill="#6aa8ff">' + pc + '</tspan></text><circle r="7" fill="#fff" stroke="#1e90ff" stroke-width="3"/>';
      g.appendChild(inner); m.marks.appendChild(g);
      inner.animate([{ transform: 'scale(.4)', opacity: 0 }, { transform: 'scale(1)', opacity: 1 }], { duration: 420, easing: SPRING });
    };
    return m;
  }

  function mount(container, o) {
    o = o || {};
    var T = TXT[o.lang === 'en' ? 'en' : 'tr'];
    var IMG = { camera: o.camera || 'assets/tour/camera.jpg', map: o.map || 'assets/tour/map.jpg', mascot: o.mascot || 'assets/tour/mascot.png' };
    if (getComputedStyle(container).position === 'static') container.style.position = 'relative';
    container.style.overflow = 'hidden';
    var stage = el(container, 'position:absolute;left:0;top:0;width:' + W + 'px;height:' + H + 'px;transform-origin:0 0;');
    function fit() { stage.style.transform = 'scale(' + (container.clientWidth / W) + ')'; }
    fit();
    var ro = window.ResizeObserver ? new ResizeObserver(fit) : null; ro && ro.observe(container);
    var dead = false, paused = false;
    var io = window.IntersectionObserver ? new IntersectionObserver(function (e) { paused = !e[0].isIntersecting; }) : null; io && io.observe(container);
    [IMG.camera, IMG.map].forEach(function (s) { var i = new Image(); i.src = s; });

    function wait(ms) { return new Promise(function (res) { var left = ms, last = performance.now(); (function f(now) { if (dead) return; now = now || performance.now(); if (!paused) left -= now - last; last = now; if (left <= 0) res(); else requestAnimationFrame(f); })(); }); }
    function tween(ms, fn) { return new Promise(function (res) { var t = 0, last = performance.now(); (function f(now) { if (dead) return; now = now || performance.now(); if (!paused) t += now - last; last = now; var p = Math.min(1, t / ms); fn(p); if (p < 1) requestAnimationFrame(f); else res(); })(); }); }
    function count(node, a, b, ms, fmt) { return tween(ms, function (p) { node.textContent = fmt(a + (b - a) * eo(p)); }); }

    function statusBar(p, t) {
      el(p, abs(36, 14) + 'font-size:16px;font-weight:600;letter-spacing:-.01em;', t);
      el(p, abs(286, 15) + 'display:flex;align-items:center;gap:6px;',
        '<span style="color:#8a92a6;font-size:10px;letter-spacing:1px">••••</span>' + icon('wifi', 16, '#fff', false, 2.4) +
        '<span style="background:#fff;color:#000;border-radius:4px;font-size:9.5px;font-weight:800;padding:1px 4px">100</span>');
    }
    function ringSvg(size, defs, sw) {
      var c = size / 2, s = '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '" style="display:block">';
      defs.forEach(function (d) {
        s += '<circle cx="' + c + '" cy="' + c + '" r="' + d.r + '" fill="none" stroke="' + d.track + '" stroke-width="' + sw + '"/>';
        s += '<circle data-k="' + d.k + '" cx="' + c + '" cy="' + c + '" r="' + d.r + '" fill="none" stroke="' + d.col + '" stroke-width="' + sw + '" stroke-linecap="round" pathLength="1" stroke-dasharray="1 1" stroke-dashoffset="0.999" transform="rotate(-90 ' + c + ' ' + c + ')" style="transition:stroke-dashoffset 1.1s ' + OUT + '"/>';
      });
      return s + '</svg>';
    }
    function setRing(c, f) { c.style.strokeDashoffset = String(1 - Math.max(.001, Math.min(1, f))); }

    function build() {
      var R = el(stage, 'position:absolute;inset:0;overflow:hidden;background:#0e1524;font-family:' + F + ';color:#fff;-webkit-font-smoothing:antialiased;line-height:1.2;');
      var u = { root: R };
      /* HOME */
      var hm = el(R, 'position:absolute;inset:0;background:linear-gradient(180deg,#101a2e 0%,#0d1422 60%);');
      u.home = hm;
      statusBar(hm, '22:36');
      el(hm, abs(18, 58, 44, 44) + 'border-radius:50%;background:linear-gradient(135deg,#40527a,#1a2233);display:grid;place-items:center;font-weight:700;font-size:18px;box-shadow:0 0 0 2px rgba(255,255,255,.08);', 'F');
      el(hm, abs(222, 64, 66, 32) + 'border-radius:16px;background:#13304f;display:flex;align-items:center;justify-content:center;gap:5px;color:#4ea5ff;font-weight:700;font-size:16px;', icon('cloud', 18, '#4ea5ff', true) + '16°');
      el(hm, abs(298, 64, 74, 32) + 'border-radius:16px;background:#2a231d;display:flex;align-items:center;justify-content:center;gap:3px;color:#f5a524;font-weight:700;font-size:16px;', '<span style="font-size:14px">🔥</span>24' + icon('chevR', 12, '#f5a524', false, 3));
      el(hm, abs(18, 114, 360) + 'font-size:25px;font-weight:800;letter-spacing:-.02em;white-space:nowrap;', T.hello);
      var rw = el(hm, abs(120, 158, 150, 150), ringSvg(150, [
        { k: 'su', r: 67, track: '#1b2c50', col: C.blue }, { k: 'kal', r: 54, track: '#12342a', col: C.green }, { k: 'egz', r: 41, track: '#3a2232', col: C.pink }], 11));
      el(rw, 'position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;font-weight:800;font-size:13px;', icon('drop', 22, '#fff', true) + 'Suu');
      u.r = { su: rw.querySelector('[data-k=su]'), kal: rw.querySelector('[data-k=kal]'), egz: rw.querySelector('[data-k=egz]') };
      function leg(x, col, label, val) {
        el(hm, abs(x, 331, 9, 9) + 'border-radius:50%;background:' + col + ';');
        el(hm, abs(x + 15, 318) + 'font-size:12.5px;color:#c6cce0;', label);
        return el(hm, abs(x + 15, 334) + 'font-size:14px;font-weight:800;white-space:nowrap;font-variant-numeric:tabular-nums;', val);
      }
      u.suVal = leg(24, C.blue, T.water, '398 / 3150 ml');
      u.kalVal = leg(142, C.green, T.nutrition, '140 / 2914 kcal');
      u.egzVal = leg(290, C.pink, T.exercise, '20 ' + T.min);
      u.waterBtn = el(hm, abs(135, 370, 120, 120) + 'border-radius:50%;background:radial-gradient(circle at 50% 35%,#3a78f5,#2459e0);box-shadow:0 0 50px rgba(44,104,239,.45);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;font-size:22px;font-weight:800;', icon('drop', 30, '#fff', true) + '200 ml');
      el(hm, abs(0, 499, 390) + 'text-align:center;font-size:12.5px;color:#c9cfdf;', T.tapHint);
      el(hm, abs(0, 521, 390) + 'display:flex;justify-content:center;gap:6px;', '<i style="width:18px;height:6px;border-radius:3px;background:#2c68ef"></i><i style="width:6px;height:6px;border-radius:3px;background:#3a4256"></i><i style="width:6px;height:6px;border-radius:3px;background:#3a4256"></i><i style="width:6px;height:6px;border-radius:3px;background:#3a4256"></i>');
      var mc = el(hm, abs(18, 540, 354, 98) + 'border-radius:22px;background:#151d2f;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06);');
      u.mac = [];
      [[T.kcalLbl, '140', '/2.914', C.green, '#1c3a2c'], [T.carbShort, '35', '/364g', C.yellow, '#3a3420'], [T.protein, '0', '/146g', '#e0566b', '#3a1f28'], [T.fat, '0', '/97g', C.purple, '#2a2240']].forEach(function (m, i) {
        var col = el(mc, abs(12 + i * 78, 8, 64) + 'display:flex;flex-direction:column;align-items:center;');
        var rs = el(col, 'position:relative;width:56px;height:56px;', ringSvg(56, [{ k: 'm', r: 24, track: m[4], col: m[3] }], 5));
        var v = el(rs, 'position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;font-weight:800;font-size:14px;font-variant-numeric:tabular-nums;', '<span>' + m[1] + '</span><span style="font-size:8.5px;font-weight:500;color:#aab2c6">' + m[2] + '</span>');
        el(col, 'margin-top:6px;font-size:12px;font-weight:600;', m[0]);
        u.mac.push({ ring: rs.querySelector('[data-k=m]'), val: v.firstChild });
      });
      el(mc, abs(330, 40), icon('chevR', 16, '#8a92a6', false, 2.5));
      u.fab = el(hm, abs(317, 614, 54, 54) + 'border-radius:50%;background:radial-gradient(circle at 50% 35%,#ff5a4f,#e2382e);box-shadow:0 6px 24px rgba(240,68,58,.5);display:grid;place-items:center;z-index:8;', icon('plus', 26, '#fff', false, 3));
      u.fabIcon = u.fab.firstChild;
      el(hm, abs(317, 683, 54, 54) + 'border-radius:50%;overflow:hidden;box-shadow:0 6px 24px rgba(30,120,240,.45);z-index:8;', '<img src="' + IMG.mascot + '" alt="" style="width:100%;height:100%;display:block">');
      el(hm, abs(18, 652) + 'font-size:21px;font-weight:800;letter-spacing:-.01em;', T.daily);
      u.list = el(hm, abs(18, 686, 354) + 'display:flex;flex-direction:column;');
      u.addItem = function (emo, bg, t, s, animate) {
        var wrap = el(null, 'overflow:hidden;flex:none;');
        el(wrap, 'height:60px;margin-bottom:8px;border-radius:18px;background:#1b2336;display:flex;align-items:center;gap:12px;padding:0 12px;',
          '<div style="width:40px;height:40px;border-radius:50%;background:' + bg + ';display:grid;place-items:center;font-size:20px">' + emo + '</div><div><div style="font-size:15px;font-weight:700">' + t + '</div><div style="font-size:13px;color:#aab2c6;margin-top:2px">' + s + '</div></div>');
        u.list.insertBefore(wrap, u.list.firstChild);
        if (animate) { wrap.animate([{ height: '0px', opacity: 0 }, { height: '68px', opacity: 1 }], { duration: 520, easing: OUT }); wrap.firstChild.animate([{ transform: 'translateY(-10px) scale(.96)' }, { transform: 'none' }], { duration: 520, easing: OUT }); }
      };
      u.addItem('🥤', '#fff', T.cola, '330 ml');
      var tb = el(hm, abs(110, 770, 170, 56) + 'border-radius:28px;background:rgba(22,30,48,.94);box-shadow:inset 0 0 0 1px rgba(80,110,190,.35);z-index:8;');
      el(tb, abs(4, 4, 82, 48) + 'border-radius:24px;background:rgba(255,255,255,.1);');
      el(tb, abs(4, 8, 82) + 'display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10.5px;font-weight:600;color:#3d9bff;', icon('home', 22, '#3d9bff', false, 2.2) + T.home);
      el(tb, abs(86, 8, 80) + 'display:flex;flex-direction:column;align-items:center;gap:3px;font-size:10.5px;font-weight:600;', icon('user', 22, '#fff', false, 2) + T.you);
      u.dim = el(hm, 'position:absolute;inset:0;background:rgba(24,28,38,.72);-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);opacity:0;z-index:6;');
      u.menu = [['fork', '#66bb6a', T.menu[0]], ['run', '#ff9800', T.menu[1]], ['cup', '#42a5f5', T.menu[2]], ['target', '#7e57c2', T.menu[3]], ['paw', '#ec407a', T.menu[4]], ['share', '#8b5cf6', T.menu[5]]].map(function (m, i) {
        var y = 287 + i * 58;
        var row = el(hm, abs(0, y - 22, 372, 44) + 'z-index:7;pointer-events:none;');
        var pill = el(row, 'position:absolute;right:62px;top:6px;height:32px;padding:0 13px;border-radius:16px;background:#0e131f;display:flex;align-items:center;font-size:16px;font-weight:800;white-space:nowrap;opacity:0;', m[2]);
        var dot = el(row, abs(328, 0, 44, 44) + 'border-radius:50%;background:' + m[1] + ';box-shadow:0 0 18px ' + m[1] + '88;display:grid;place-items:center;opacity:0;', icon(m[0], 22, '#fff', m[0] === 'paw', 2.4));
        return { row: row, pill: pill, dot: dot, dy: 641 - y };
      });
      /* CAMERA */
      var cam = el(R, 'position:absolute;inset:0;z-index:10;background:#000;transform:translateY(100%);');
      u.cam = cam;
      el(cam, 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;', null, 'img').src = IMG.camera;
      u.freeze = el(cam, 'position:absolute;inset:0;background:rgba(5,10,18,.35);opacity:0;');
      u.shutterFx = el(cam, abs(157, 721, 76, 76) + 'border-radius:50%;background:#fff;opacity:0;');
      u.scan = el(cam, abs(67, 306, 256, 3) + 'background:linear-gradient(90deg,rgba(52,211,153,0),#34d399,rgba(52,211,153,0));box-shadow:0 0 18px #34d399;opacity:0;');
      function chip(x, y, t) {
        var g = el(cam, abs(x, y, 0, 0) + 'opacity:0;');
        el(g, abs(-7, -7, 14, 14) + 'border-radius:50%;background:#34d399;box-shadow:0 0 0 5px rgba(52,211,153,.3);');
        el(g, abs(14, -15) + 'white-space:nowrap;padding:7px 11px;border-radius:14px;background:rgba(10,14,22,.82);font-size:13px;font-weight:700;', t);
        return g;
      }
      u.chips = [chip(104, 380, T.cola + ' · <span style="color:#34d399">140 kcal</span>'), chip(150, 612, T.pizza + ' · <span style="color:#34d399">940 kcal</span>')];
      if (T.camFix) {
        var top = el(cam, abs(0, 104, 390, 56) + '-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);background:rgba(34,34,30,.3);');
        el(top, abs(15, 6) + 'font-size:12.5px;font-weight:700;color:rgba(255,255,255,.72);', 'Recent meals');
        var chipCss = 'height:25px;border-radius:13px;background:rgba(70,70,66,.72);box-shadow:inset 0 0 0 1px rgba(255,255,255,.12);display:flex;align-items:center;gap:6px;padding:0 10px;font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;box-sizing:border-box;';
        el(top, abs(15, 26, 62) + chipCss, icon('history', 13, '#fff', false, 2.4) + 'Cola');
        el(top, abs(84, 26, 330) + chipCss, icon('history', 13, '#fff', false, 2.4) + "This meal is one McDonald's Big Mac");
        [[120, 'Barcode'], [193, 'Search'], [268, 'Describe']].forEach(function (b) {
          el(cam, abs(b[0] - 32, 681, 64, 18) + 'border-radius:6px;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);background:rgba(62,50,42,.88);display:grid;place-items:center;font-size:12.5px;font-weight:600;', b[1]);
        });
      }
      u.flash = el(cam, 'position:absolute;inset:0;background:radial-gradient(circle at 50% 45%,#fff 0%,rgba(255,255,255,.85) 35%,rgba(255,255,255,.4) 75%);opacity:0;');
      var rs2 = el(cam, abs(0, 514, 390, 330) + 'border-radius:28px 28px 0 0;background:#111827;transform:translateY(100%);box-shadow:0 -10px 40px rgba(0,0,0,.5);');
      u.result = rs2;
      el(rs2, abs(175, 8, 40, 5) + 'border-radius:3px;background:#3a4256;');
      el(rs2, abs(20, 26) + 'font-size:11.5px;font-weight:700;letter-spacing:.14em;color:#9aa3b8;', T.mealAnalysis);
      el(rs2, abs(20, 46) + 'font-size:20px;font-weight:800;', T.mealName);
      var kc = el(rs2, abs(20, 78) + 'font-size:42px;font-weight:800;letter-spacing:-.02em;color:' + C.green + ';font-variant-numeric:tabular-nums;', '<span>0</span><span style="font-size:18px;color:#fff;margin-left:6px">kcal</span>');
      u.kcal = kc.firstChild;
      u.bars = [[T.protein, 38, 146, '#f06a7a'], [T.carbs, 128, 364, C.orange], [T.fat, 44, 97, C.purple]].map(function (m, i) {
        var y = 142 + i * 36;
        el(rs2, abs(20, y) + 'font-size:13.5px;font-weight:600;', m[0]);
        var v = el(rs2, abs(250, y, 120) + 'text-align:right;font-size:13.5px;font-weight:700;font-variant-numeric:tabular-nums;', '0 / ' + m[2] + ' g');
        var tr = el(rs2, abs(20, y + 20, 350, 6) + 'border-radius:3px;background:' + m[3] + '33;overflow:hidden;');
        var f = el(tr, 'height:100%;width:100%;border-radius:3px;background:' + m[3] + ';transform-origin:0 0;transform:scaleX(0);');
        return { v: v, f: f, g: m[1], max: m[2] };
      });
      u.addBtn = el(rs2, abs(20, 256, 350, 50) + 'border-radius:25px;background:' + C.green + ';display:grid;place-items:center;font-size:17px;font-weight:800;', T.addMeal);

      /* MAP */
      var mp = el(R, 'position:absolute;inset:0;z-index:10;background:#0b1a33;transform:translateY(100%);');
      u.map = mp;
      u.zoom = el(mp, 'position:absolute;inset:0;transform-origin:195px 434px;');
      el(u.zoom, 'position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block;', null, 'img').src = IMG.map;
      u.st = streetMap(mp, T);
      u.gps = el(mp, abs(130, 62, 130, 30) + 'border-radius:15px;background:rgba(12,18,28,.86);display:flex;align-items:center;justify-content:center;gap:7px;font-size:13px;font-weight:700;opacity:0;', '<i style="width:8px;height:8px;border-radius:50%;background:#34d399;box-shadow:0 0 8px #34d399"></i>' + T.gps);
      var pn = el(mp, abs(12, 655, 366, 150) + 'border-radius:28px;background:#141a25;box-shadow:0 10px 40px rgba(0,0,0,.4);');
      u.idle = el(pn, 'position:absolute;inset:0;');
      el(u.idle, abs(14, 14, 338, 54) + 'border-radius:16px;background:#222a38;display:flex;align-items:center;gap:14px;padding:0 18px;box-sizing:border-box;', icon('run', 26, C.cyan, false, 2.2) + '<span style="font-size:19px;font-weight:800;flex:1">' + T.run + '</span>' + icon('chev', 18, '#8a92a6', false, 2.4));
      u.startBtn = el(u.idle, abs(14, 80, 246, 50) + 'border-radius:16px;background:' + C.cyan + ';display:grid;place-items:center;font-size:19px;font-weight:800;', T.start);
      el(u.idle, abs(268, 76, 84, 58) + 'border-radius:16px;background:#222a38;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:13px;font-weight:700;', icon('history', 20, '#fff', false, 2.2) + T.history);
      u.live = el(pn, 'position:absolute;inset:0;opacity:0;');
      var st = el(u.live, abs(14, 16, 338) + 'display:grid;grid-template-columns:1fr 1fr 1fr;');
      u.stat = T.stats.map(function (l, i) {
        var c = el(st, 'text-align:' + (i === 0 ? 'left' : i === 1 ? 'center' : 'right') + ';');
        el(c, 'font-size:10.5px;font-weight:700;letter-spacing:.14em;color:#8a92a6;', l);
        return el(c, 'margin-top:6px;font-size:24px;font-weight:800;letter-spacing:-.02em;font-variant-numeric:tabular-nums;white-space:nowrap;', i === 0 ? '0,00<span style="font-size:13px;color:#8a92a6"> km</span>' : i === 1 ? '00:00' : '–');
      });
      el(u.live, abs(14, 90, 164, 46) + 'border-radius:16px;background:#222a38;display:grid;place-items:center;font-size:16px;font-weight:800;', T.pause);
      u.stopBtn = el(u.live, abs(188, 90, 164, 46) + 'border-radius:16px;background:' + C.red + ';display:grid;place-items:center;font-size:16px;font-weight:800;', T.finish);
      u.markers = [];
      u.sum = el(mp, abs(12, 560, 366, 245) + 'border-radius:28px;background:#141a25;box-shadow:inset 0 0 0 1px rgba(255,255,255,.08),0 20px 60px rgba(0,0,0,.5);opacity:0;z-index:4;padding:22px;box-sizing:border-box;',
        '<div style="font-size:11.5px;font-weight:700;letter-spacing:.14em;color:#8a92a6">' + T.runDone + '</div>' +
        '<div style="margin-top:8px;font-size:46px;font-weight:800;letter-spacing:-.03em">' + T.dist + '<span style="font-size:20px;color:#8a92a6"> km</span></div>' +
        '<div style="margin-top:14px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px">' +
        ['27:14|' + T.time, "5'39\"|" + T.pace, '342|kcal'].map(function (s) { s = s.split('|'); return '<div><div style="font-size:19px;font-weight:800">' + s[0] + '</div><div style="font-size:12px;color:#8a92a6;margin-top:3px">' + s[1] + '</div></div>'; }).join('') + '</div>' +
        '<div style="margin-top:18px;display:inline-flex;align-items:center;gap:7px;padding:9px 13px;border-radius:14px;background:rgba(59,130,246,.18);color:#6aa8ff;font-size:13.5px;font-weight:700">' + icon('drop', 15, '#6aa8ff', true) + T.goalUp + '</div>');

      /* FINGER */
      u.finger = el(R, abs(0, 0, 0, 0) + 'z-index:50;opacity:0;pointer-events:none;');
      u.fdot = el(u.finger, abs(-22, -22, 44, 44) + 'border-radius:50%;background:rgba(255,255,255,.3);box-shadow:0 0 0 1.5px rgba(255,255,255,.75),0 6px 20px rgba(0,0,0,.35);');
      u.fx = 330; u.fy = 900;
      u.finger.style.transform = 'translate(330px,900px)';
      return u;
    }

    function run(u) {
      var R = u.root;
      function fingerTo(x, y, ms) { u.finger.animate([{ transform: 'translate(' + u.fx + 'px,' + u.fy + 'px)' }, { transform: 'translate(' + x + 'px,' + y + 'px)' }], { duration: ms, easing: IO, fill: 'forwards' }); u.fx = x; u.fy = y; return wait(ms); }
      function showFinger(v) { u.finger.animate([{ opacity: v ? 0 : 1 }, { opacity: v ? 1 : 0 }], { duration: 250, fill: 'forwards' }); }
      function tap(t) {
        u.fdot.animate([{ transform: 'scale(1)' }, { transform: 'scale(.78)', offset: .4 }, { transform: 'scale(1)' }], { duration: 320, easing: OUT });
        var rp = el(R, abs(u.fx - 22, u.fy - 22, 44, 44) + 'border-radius:50%;box-shadow:0 0 0 2px rgba(255,255,255,.8);z-index:49;pointer-events:none;');
        rp.animate([{ transform: 'scale(.6)', opacity: 1 }, { transform: 'scale(1.8)', opacity: 0 }], { duration: 520, easing: OUT }).onfinish = function () { rp.remove(); };
        if (t) t.animate([{ transform: 'scale(1)' }, { transform: 'scale(.93)', offset: .35 }, { transform: 'scale(1)' }], { duration: 360, easing: OUT });
        return wait(300);
      }
      function menu(v) {
        u.dim.animate([{ opacity: v ? 0 : 1 }, { opacity: v ? 1 : 0 }], { duration: v ? 320 : 260, fill: 'forwards' });
        u.fabIcon.animate([{ transform: v ? 'rotate(0deg)' : 'rotate(45deg)' }, { transform: v ? 'rotate(45deg)' : 'rotate(0deg)' }], { duration: 380, easing: SPRING, fill: 'forwards' });
        var n = u.menu.length;
        u.menu.forEach(function (m, i) {
          var d = v ? (n - 1 - i) * 38 : i * 18;
          m.dot.animate([{ opacity: v ? 0 : 1, transform: v ? 'translateY(' + m.dy * .5 + 'px) scale(.3)' : 'none' }, { opacity: v ? 1 : 0, transform: v ? 'none' : 'translateY(' + m.dy * .3 + 'px) scale(.4)' }], { duration: v ? 420 : 220, delay: d, easing: v ? SPRING : 'ease-in', fill: 'forwards' });
          m.pill.animate([{ opacity: v ? 0 : 1, transform: v ? 'translateX(14px)' : 'none' }, { opacity: v ? 1 : 0, transform: v ? 'none' : 'translateX(10px)' }], { duration: v ? 360 : 200, delay: d + (v ? 60 : 0), easing: OUT, fill: 'forwards' });
        });
        return wait(v ? (n - 1) * 38 + 420 : 300);
      }
      function closeScreen(s, extra) {
        u.home.getAnimations().forEach(function (a) { a.cancel(); });
        var sa = s.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(60px) scale(.97)' }], { duration: 460, easing: IO, fill: 'forwards' });
        var ha = u.home.animate([{ transform: 'scale(.94)', filter: 'brightness(.6)' }, { transform: 'none', filter: 'brightness(1)' }], { duration: 520, easing: OUT, fill: 'forwards' });
        if (extra) extra.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300, fill: 'forwards' });
        sa.onfinish = function () { s.style.visibility = 'hidden'; };
        return Promise.all([sa.finished, ha.finished]).then(function () { return wait(150); });
      }
      function present(s, v) {
        u.home.getAnimations().forEach(function (a) { a.cancel(); });
        s.animate([{ transform: v ? 'translateY(100%)' : 'none' }, { transform: v ? 'none' : 'translateY(100%)' }], { duration: 560, easing: v ? OUT : IO, fill: 'forwards' });
        u.home.animate([{ transform: v ? 'none' : 'scale(.94)', filter: v ? 'brightness(1)' : 'brightness(.6)' }, { transform: v ? 'scale(.94)' : 'none', filter: v ? 'brightness(.6)' : 'brightness(1)' }], { duration: 560, easing: OUT, fill: 'forwards' });
        return wait(v ? 560 : 720);
      }
      function floatText(x, y, t, col) {
        var f = el(R, abs(x, y) + 'transform:translateX(-50%);font-size:15px;font-weight:800;color:' + col + ';z-index:40;white-space:nowrap;pointer-events:none;', t);
        f.animate([{ opacity: 0, transform: 'translate(-50%,6px)' }, { opacity: 1, transform: 'translate(-50%,-10px)', offset: .3 }, { opacity: 0, transform: 'translate(-50%,-34px)' }], { duration: 1200, easing: OUT }).onfinish = function () { f.remove(); };
      }

      return (async function () {
        await wait(250);
        setRing(u.r.su, 398 / 3150); setRing(u.r.kal, 140 / 2914); setRing(u.r.egz, 20 / 30);
        setRing(u.mac[0].ring, 140 / 2914); setRing(u.mac[1].ring, 35 / 364);
        await wait(1000);
        showFinger(true); await fingerTo(200, 440, 800);
        /* water */
        await tap(u.waterBtn);
        var rp = el(u.home, abs(135, 370, 120, 120) + 'border-radius:50%;box-shadow:0 0 0 3px #3b82f6;pointer-events:none;');
        rp.animate([{ transform: 'scale(1)', opacity: .9 }, { transform: 'scale(1.5)', opacity: 0 }], { duration: 700, easing: OUT }).onfinish = function () { rp.remove(); };
        floatText(195, 350, '+200 ml', '#6aa8ff');
        count(u.suVal, 398, 598, 800, function (v) { return Math.round(v) + ' / 3150 ml'; });
        setRing(u.r.su, 598 / 3150);
        u.addItem('💧', '#1e3a66', T.water, '200 ml', true);
        await wait(1100);
        /* meal */
        await fingerTo(344, 641, 650); await tap(u.fab);
        await menu(true); await wait(200);
        await fingerTo(350, 287, 520); await tap(u.menu[0].dot);
        menu(false); await present(u.cam, true);
        await fingerTo(195, 759, 600); await tap(null);
        u.shutterFx.animate([{ opacity: .9, transform: 'scale(.85)' }, { opacity: 0, transform: 'scale(1)' }], { duration: 300 });
        await wait(120);
        u.flash.animate([{ opacity: 0 }, { opacity: 1, offset: .12 }, { opacity: 0 }], { duration: 520, easing: 'ease-out' });
        await wait(260);
        showFinger(false);
        u.freeze.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, fill: 'forwards' });
        u.scan.animate([{ opacity: 0, transform: 'translateY(0)' }, { opacity: 1, transform: 'translateY(128px)', offset: .25 }, { opacity: 1, transform: 'translateY(256px)', offset: .5 }, { opacity: 1, transform: 'translateY(0)', offset: .95 }, { opacity: 0, transform: 'translateY(0)' }], { duration: 1500, easing: 'ease-in-out' });
        await wait(700);
        u.chips.forEach(function (c, i) { c.animate([{ opacity: 0, transform: 'scale(.6)' }, { opacity: 1, transform: 'none' }], { duration: 450, delay: i * 320, easing: SPRING, fill: 'forwards' }); });
        await wait(1300);
        u.result.animate([{ transform: 'translateY(100%)' }, { transform: 'none' }], { duration: 520, easing: OUT, fill: 'forwards' });
        await wait(250);
        count(u.kcal, 0, 1080, 900, function (v) { return String(Math.round(v)); });
        u.bars.forEach(function (b, i) {
          b.f.animate([{ transform: 'scaleX(0)' }, { transform: 'scaleX(' + (b.g / b.max) + ')' }], { duration: 800, delay: 150 + i * 120, easing: OUT, fill: 'forwards' });
          count(b.v, 0, b.g, 900, function (v) { return Math.round(v) + ' / ' + b.max + ' g'; });
        });
        await wait(1300);
        showFinger(true); await fingerTo(195, 795, 600); await tap(u.addBtn);
        await closeScreen(u.cam);
        count(u.kalVal, 140, 1220, 900, function (v) { return Math.round(v) + ' / 2914 kcal'; });
        count(u.mac[0].val, 140, 1220, 900, function (v) { return String(Math.round(v)); });
        count(u.mac[1].val, 35, 163, 900, function (v) { return String(Math.round(v)); });
        count(u.mac[2].val, 0, 38, 900, function (v) { return String(Math.round(v)); });
        count(u.mac[3].val, 0, 44, 900, function (v) { return String(Math.round(v)); });
        setRing(u.r.kal, 1220 / 2914); setRing(u.mac[0].ring, 1220 / 2914); setRing(u.mac[1].ring, 163 / 364); setRing(u.mac[2].ring, 38 / 146); setRing(u.mac[3].ring, 44 / 97);
        u.addItem('🍕', '#3a2a1a', T.mealName, '1080 kcal', true);
        await wait(1300);
        /* run */
        await fingerTo(344, 641, 650); await tap(u.fab);
        await menu(true); await wait(200);
        await fingerTo(350, 345, 520); await tap(u.menu[1].dot);
        menu(false); await present(u.map, true);
        await fingerTo(146, 761, 600); await tap(u.startBtn);
        showFinger(false);
        u.zoom.animate([{ transform: 'scale(1)', opacity: 1 }, { transform: 'scale(3.4)', opacity: .6 }], { duration: 1000, easing: 'cubic-bezier(.55,0,.9,.5)', fill: 'forwards' });
        u.idle.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 250, fill: 'forwards' });
        u.live.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, delay: 150, fill: 'forwards' });
        u.gps.animate([{ opacity: 0, transform: 'translateY(-8px)' }, { opacity: 1, transform: 'none' }], { duration: 400, delay: 300, fill: 'forwards' });
        var M = u.st, P = M.route, L = P.getTotalLength(), p0 = P.getPointAtLength(0);
        var cam = { x: p0.x, y: p0.y, z: .4, cy: 330 };
        function applyCam() { M.world.style.transform = 'translate(' + (195 - cam.x * cam.z).toFixed(1) + 'px,' + (cam.cy - cam.y * cam.z).toFixed(1) + 'px) scale(' + cam.z.toFixed(3) + ')'; }
        applyCam(); M.setHead(p0, 0); M.animate();
        await wait(550);
        M.layer.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 450, fill: 'forwards' });
        await tween(1000, function (p) { cam.z = .4 + (1.1 - .4) * eo(p); applyCam(); });
        [P, M.glow, M.casing].forEach(function (q) { q.style.strokeDasharray = L; q.style.strokeDashoffset = L; q.setAttribute('opacity', 1); });
        var SPL = [[1, "5'48\""], [2, "5'31\""], [3, "5'19\""], [4, "5'05\""]], shown = 0;
        await tween(7600, function (p) {
          var e = p < .06 ? p * p / .12 : p - .03;
          e = Math.min(1, e / .97);
          [P, M.glow, M.casing].forEach(function (q) { q.style.strokeDashoffset = L * (1 - e); });
          var pt = P.getPointAtLength(L * e), nx = P.getPointAtLength(Math.min(L, L * e + 8));
          var ang = (nx.x === pt.x && nx.y === pt.y) ? 0 : Math.atan2(nx.y - pt.y, nx.x - pt.x) * 180 / Math.PI + 90;
          M.setHead(pt, ang);
          cam.x += (pt.x - cam.x) * .1; cam.y += (pt.y - cam.y) * .1; cam.z += (1 - cam.z) * .03; applyCam();
          u.stat[0].innerHTML = (4.82 * e).toFixed(2).replace('.', T.dec) + '<span style="font-size:13px;color:#8a92a6"> km</span>';
          u.stat[1].textContent = mmss(1634 * e);
          u.stat[2].textContent = e > .03 ? pace(348 - 43 * e) : '–';
          while (shown < SPL.length && e >= SPL[shown][0] / 4.82) {
            var q = P.getPointAtLength(L * SPL[shown][0] / 4.82);
            M.addMark(q, SPL[shown][0], SPL[shown][1], q.x > 560);
            shown++;
          }
        });
        await wait(500);
        showFinger(true); await fingerTo(282, 768, 650); await tap(u.stopBtn);
        u.sum.animate([{ opacity: 0, transform: 'translateY(24px)' }, { opacity: 1, transform: 'none' }], { duration: 520, easing: OUT, fill: 'forwards' });
        u.gps.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 300, fill: 'forwards' });
        (function () { var c0 = { x: cam.x, y: cam.y, z: cam.z, cy: cam.cy }; tween(1100, function (p) { var k = 1 - Math.pow(1 - p, 4); cam.x = c0.x + (520 - c0.x) * k; cam.y = c0.y + (790 - c0.y) * k; cam.z = c0.z + (.47 - c0.z) * k; cam.cy = c0.cy + (285 - c0.cy) * k; applyCam(); }); })();
        showFinger(false);
        await wait(2200);
        await closeScreen(u.map, u.sum);
        count(u.egzVal, 20, 47, 900, function (v) { return Math.round(v) + ' ' + T.min; });
        setRing(u.r.egz, 1);
        count(u.suVal, 3150, 3650, 900, function (v) { return '598 / ' + Math.round(v) + ' ml'; });
        setRing(u.r.su, 598 / 3650);
        floatText(80, 300, T.goalFloat, '#6aa8ff');
        u.addItem('🏃', '#3a2232', T.run, T.dist + ' km · 27:14', true);
        await wait(2600);
      })();
    }

    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    (async function loop() {
      if (reduce) { var s = build(); requestAnimationFrame(function () { setRing(s.r.su, 398 / 3150); setRing(s.r.kal, 140 / 2914); setRing(s.r.egz, 20 / 30); }); return; }
      while (!dead) {
        var u = build();
        u.root.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400 });
        await run(u);
        if (dead) return;
        u.root.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 400, fill: 'forwards' });
        await wait(420);
        u.root.remove();
      }
    })();

    return { destroy: function () { dead = true; ro && ro.disconnect(); io && io.disconnect(); stage.remove(); } };
  }

  window.SuuPhoneTour = { mount: mount };
})();

