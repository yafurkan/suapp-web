/* Suu — ana sayfa "tek sistem" scroll bölümü. Bağımlılık yok; scroll + rAF.
   Scroll ilerlemesi → aktif adım (3) + adım içi ilerleme (local 0–1) →
   progress bar, ekran görüntüsü, çipler ve kalori adımında kamera sahnesi.
   Yapışkan alan nav'ın altında durur (top: --nav-h), bu yüzden ilerleme
   pencere yerine .suu-sticky'nin yüksekliği ve ofsetiyle hesaplanır. */
(function () {
  function init(root) {
    var scroller = root.querySelector('.suu-scroller');
    var sticky = root.querySelector('.suu-sticky');
    var steps = [].slice.call(root.querySelectorAll('.suu-step'));
    var dots = [].slice.call(root.querySelectorAll('.suu-dots i'));
    var shots = [].slice.call(root.querySelectorAll('.suu-shot'));
    var chips = [].slice.call(root.querySelectorAll('.suu-chip'));
    var wrap = root.querySelector('.suu-phone-wrap');
    var phone = root.querySelector('.suu-phone');
    var cam = root.querySelector('.suu-cam');
    var q = function (s) { return cam.querySelector(s); };
    var frame = q('.suu-frame'), scan = q('.suu-scan'), t1 = q('[data-tag="1"]'), t2 = q('[data-tag="2"]'), shutter = q('.suu-shutter'), sheet = q('.suu-sheet');
    var rtl = getComputedStyle(root).direction === 'rtl';
    var N = steps.length, raf = 0, navH = 0, stickyH = 0;

    function layout() {
      navH = parseFloat(getComputedStyle(sticky).top) || 0;
      stickyH = sticky.clientHeight;
      var w = document.documentElement.clientWidth, h = stickyH, mobile = w < 860;
      var ph = mobile ? Math.min(472, w * 0.58 * 2.05, h * 0.5) : Math.min(656, h * 0.86 - 40);
      ph = Math.round(ph); var pw = Math.round(ph / 2.05), k = pw / 320;
      wrap.style.setProperty('--pw', pw + 'px'); wrap.style.setProperty('--ph', ph + 'px'); wrap.style.setProperty('--k', k);
      var bez = 10 * k, iw = pw - 2 * bez, ih = ph - 2 * bez;
      cam.style.height = Math.round(300 * ih / iw) + 'px';
      cam.style.transform = 'scale(' + (iw / 300) + ')';
      t2.style.top = Math.round(300 * ih / iw * 0.64) + 'px';
      // Çipler telefona göre yüzdeyle yerleşir; uzun çeviriler (RU/DE, 375 px)
      // ekran kenarından taşmasın diye 12 px içeride tutulur.
      var wl = wrap.getBoundingClientRect().left;
      chips.forEach(function (c) {
        var j = +c.dataset.j;
        var pct = parseFloat(mobile ? (j === 0 ? '-18%' : '48%') : (j === 1 && w < 1240 ? '30%' : c.dataset.x)) / 100;
        var cw = c.offsetWidth, x = rtl ? pw - pct * pw - cw : pct * pw;
        c.style.left = Math.round(Math.max(12 - wl, Math.min(x, w - 12 - wl - cw))) + 'px';
        c.style.top = mobile ? (j === 0 ? '8%' : '78%') : c.dataset.y;
      });
      return mobile;
    }
    var mobile = layout();

    function total() { return Math.max(1, scroller.offsetHeight - stickyH); }

    function update() {
      raf = 0;
      var r = scroller.getBoundingClientRect();
      var p = Math.min(1, Math.max(0, (navH - r.top) / total()));
      var pos = Math.min(N - 0.0001, p * N), a = Math.floor(pos), local = pos - a;

      steps.forEach(function (s, i) {
        s.classList.toggle('is-active', i === a);
        s.querySelector('.suu-bar').style.width = (i < a ? 100 : i === a ? local * 100 : 0) + '%';
      });
      dots.forEach(function (d, i) { d.classList.toggle('is-active', i === a); });
      shots.forEach(function (im, i) {
        im.classList.toggle('is-active', i === a);
        var sc = +(im.dataset.scroll || 0);
        im.style.transform = i === a && sc ? 'translateY(' + (-sc * local) + '%)' : '';
      });
      chips.forEach(function (c) {
        c.classList.toggle('is-on', +c.dataset.step === a && local > 0.12 + (+c.dataset.j) * 0.2);
      });
      wrap.style.setProperty('--glow', steps[a].style.getPropertyValue('--c'));
      if (!mobile) phone.style.setProperty('--tilt', ((rtl ? 2 : -2) + (rtl ? -4 : 4) * p).toFixed(2) + 'deg');

      var L = a === 1 ? local : 0; // kalori adımı = 2. adım
      cam.classList.toggle('is-on', L > 0.2);
      frame.classList.toggle('is-on', L > 0.2 && L < 0.66);
      scan.classList.toggle('is-on', L > 0.28 && L < 0.6);
      scan.style.top = Math.min(100, Math.max(0, (L - 0.28) / 0.3 * 100)) + '%';
      t1.classList.toggle('is-on', L > 0.4);
      t2.classList.toggle('is-on', L > 0.5);
      shutter.classList.toggle('is-on', L > 0.2 && L < 0.62);
      sheet.classList.toggle('is-on', L > 0.62);
    }
    function req() { if (!raf) raf = requestAnimationFrame(update); }

    steps.forEach(function (s, i) {
      s.addEventListener('click', function (e) {
        if (e.target.closest('a')) return;
        var top = scroller.getBoundingClientRect().top + window.scrollY - navH + total() * ((i + 0.5) / N);
        window.scrollTo({ top: top, behavior: 'smooth' });
      });
    });

    // Bölüm ekranda değilken scroll dinleyicisi çalışmasın
    var active = false;
    new IntersectionObserver(function (en) {
      var v = en[0].isIntersecting;
      if (v && !active) { window.addEventListener('scroll', req, { passive: true }); active = true; req(); }
      if (!v && active) { window.removeEventListener('scroll', req); active = false; }
    }, { rootMargin: '200px 0px' }).observe(scroller);
    window.addEventListener('resize', function () { mobile = layout(); req(); });
    update();
  }
  function boot() { [].forEach.call(document.querySelectorAll('.suu-features'), init); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
