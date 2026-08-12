/**
 * Suu — Günlük su ihtiyacı hesaplayıcı (kompakt, ana sayfa gömülü sürüm)
 *
 * Formül, uygulamadaki temel hesapla ve su-hesaplayici.html sayfasıyla aynı:
 *   taban  = kilo × 35 ml
 *   cinsiyet: erkek ×1.05
 *   yaş:  <18 ×1.10 · >65 ×0.95
 *   aktivite: 1.0 / 1.1 / 1.3 / 1.5 / 1.7
 *   sonuç 1.5 L – 5.0 L aralığına sıkıştırılır
 *
 * Not: bu yalnızca başlangıç tahminidir. Uygulamada hedef ayrıca hava
 * sıcaklığı, egzersiz ve yenen besinlerin sindirim suyu ile güncellenir.
 *
 * Beklenen HTML: <form data-water-calc> içinde name="age|weight|gender|activity"
 * alanları ve [data-calc-result], [data-calc-liters], [data-calc-cups] elemanları.
 */
(function () {
    'use strict';

    var ACTIVITY = { sedentary: 1.0, light: 1.1, moderate: 1.3, active: 1.5, extra: 1.7 };

    function calculate(age, weight, gender, activity) {
        var ml = weight * 35;
        if (gender === 'male') ml *= 1.05;
        if (age < 18) ml *= 1.10;
        else if (age > 65) ml *= 0.95;
        ml *= ACTIVITY[activity] || 1.0;

        var liters = Math.round((ml / 1000) * 10) / 10;
        liters = Math.max(1.5, Math.min(5.0, liters));

        return { liters: liters, cups: Math.round(liters * 4) };   // ~250 ml bardak
    }

    function init(form) {
        var result = form.querySelector('[data-calc-result]');
        var litersEl = form.querySelector('[data-calc-liters]');
        var cupsEl = form.querySelector('[data-calc-cups]');

        form.addEventListener('submit', function (e) {
            e.preventDefault();

            var data = new FormData(form);
            var age = parseFloat(data.get('age'));
            var weight = parseFloat(data.get('weight'));
            var gender = data.get('gender');
            var activity = data.get('activity');

            if (!(age > 0) || !(weight > 0)) return;

            var out = calculate(age, weight, gender, activity);

            if (litersEl) litersEl.textContent = out.liters.toLocaleString(document.documentElement.lang || 'tr');
            if (cupsEl) cupsEl.textContent = out.cups;
            if (result) {
                result.hidden = false;
                result.setAttribute('aria-live', 'polite');
            }

            if (typeof window.suuTrack === 'function') {
                window.suuTrack('water_calc_submit', {
                    liters: out.liters,
                    activity: activity,
                    lang: (document.documentElement.lang || 'tr').slice(0, 2)
                });
            }
        });
    }

    function boot() {
        document.querySelectorAll('form[data-water-calc]').forEach(init);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
