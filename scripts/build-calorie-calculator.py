#!/usr/bin/env python3
"""
Suu — Kalori açığı hesaplayıcı sayfaları (7 dil)

Search Console (2026-10-14): "kalori açığı nasıl hesaplanır / nasıl yapılır",
"как создать дефицит калорий", "come andare in deficit calorico",
"як зробити дефіцит калорій" gibi sorgular 30.–50. sırada kalıyordu; sitede
hesaplayıcı yoktu. Bu script su hesaplayıcının (su-hesaplayici.html ailesi)
yapısını izleyen, kendi içinde çalışan 7 sayfa üretir.

Hesap (sayfadaki JS):
  · Bazal metabolizma: Mifflin-St Jeor (1990) — erkek 10·kg + 6,25·cm − 5·yaş + 5,
    kadın … − 161. Frankenfield 2005 derlemesine göre en güvenilir denklem
    (bireylerin çoğunda ölçülenin ±%10'u içinde).
  · Günlük ihtiyaç = bazal × aktivite katsayısı (1,2 / 1,375 / 1,55 / 1,725 / 1,9).
  · Hedefler: −250 / −500 / −750 kcal; hiçbir hedef uzman gözetimi olmadan
    önerilen alt sınırın (kadın 1.200, erkek 1.500 kcal — Harvard Health)
    altına inmez. Haftalık tahmin açık × 7 / 7.700 kcal (ilk haftalar için
    kaba tahmin; Hall 2011: kilo yanıtı yavaş, yarılanma ~1 yıl).

Hreflang bloğu yazılmaz: content/page-registry.json → root
"calorie-deficit-calculator" ailesinden inject-hreflang.py ekler.

Kullanım:
    python3 scripts/build-calorie-calculator.py            # önizleme
    python3 scripts/build-calorie-calculator.py --apply
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://suuapp.com"
GENERATED = "ÜRETİLMİŞ DOSYA — kaynak: scripts/build-calorie-calculator.py"

REFS = [
    ("Mifflin MD et al. — A new predictive equation for resting energy expenditure in healthy individuals. Am J Clin Nutr, 1990", "https://pubmed.ncbi.nlm.nih.gov/2305711/"),
    ("Frankenfield D et al. — Comparison of predictive equations for resting metabolic rate in healthy nonobese and obese adults: a systematic review. J Am Diet Assoc, 2005", "https://pubmed.ncbi.nlm.nih.gov/15883556/"),
    ("Hall KD et al. — Quantification of the effect of energy imbalance on bodyweight. Lancet, 2011", "https://pubmed.ncbi.nlm.nih.gov/21872751/"),
    ("CDC — Losing Weight", "https://www.cdc.gov/healthy-weight-growth/losing-weight/index.html"),
    ("Harvard Health Publishing — Calorie counting made easy", "https://www.health.harvard.edu/staying-healthy/calorie-counting-made-easy"),
]

ACT_KEYS = ["sedentary", "light", "moderate", "active", "extra"]
ACT_MULT = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "extra": 1.9}
ACT_ICON = {"sedentary": "🪑", "light": "🚶", "moderate": "🏃", "active": "🏋️", "extra": "🔥"}

L: dict[str, dict] = {}

L["tr"] = dict(
    file="kalori-acigi-hesaplayici.html", lang="tr", dir="ltr", locale="tr_TR", num="tr-TR",
    home="/", blog="blog.html", faq_page="faq.html", llms="/llms.txt", llms_full="/llms-full.txt",
    nav=["Ana Sayfa", "Blog", "SSS"],
    title="Kalori Açığı Hesaplayıcı — Günde Kaç Kalori Almalıyım? | Suu",
    desc="Yaş, kilo, boy ve aktiviteden günlük kalori ihtiyacını ve güvenli kalori açığını saniyeler içinde hesapla. Mifflin-St Jeor formülü, ücretsiz.",
    keywords="kalori açığı hesaplama, kalori açığı hesaplayıcı, günlük kalori ihtiyacı hesaplama, kalori açığı nasıl hesaplanır, kilo vermek için kaç kalori almalıyım, bazal metabolizma hesaplama, tdee hesaplama",
    og_title="Kalori Açığı Hesaplayıcı — Günde Kaç Kalori Almalıyım?",
    og_desc="Günlük kalori ihtiyacını ve kilo vermek için güvenli hedefini hesapla. Ücretsiz, bilimsel formülle.",
    app_name="Suu Kalori Açığı Hesaplayıcı",
    app_desc="Yaş, kilo, boy, cinsiyet ve aktivite düzeyinden günlük kalori ihtiyacını ve güvenli kalori açığı hedeflerini hesaplayan ücretsiz çevrim içi araç.",
    badge="🔥 Ücretsiz Çevrim İçi Araç", h1="Kalori Açığı<br>Hesaplayıcı",
    sub="Günlük kalori ihtiyacını ve kilo vermek için güvenli hedefini birkaç saniyede öğren.",
    s1="Kişisel bilgilerin", age="Yaş", weight="Kilo (kg)", height="Boy (cm)", sex="Cinsiyet (formül için)",
    male="♂ Erkek", female="♀ Kadın", ph_age="ör. 30", ph_weight="ör. 75", ph_height="ör. 170",
    next="Devam", back="Geri", calc="Hesapla", recalc="Yeniden hesapla",
    s2="Aktivite düzeyin",
    acts={"sedentary": ("Hareketsiz", "Masa başı, egzersiz yok"), "light": ("Hafif", "Haftada 1–3 gün"),
          "moderate": ("Orta", "Haftada 3–5 gün"), "active": ("Aktif", "Haftada 6–7 gün"),
          "extra": ("Çok aktif", "Fiziksel iş + antrenman")},
    err_age="Geçerli bir yaş gir (18–80)", err_weight="Geçerli bir kilo gir (35–250 kg)",
    err_height="Geçerli bir boy gir (130–220 cm)", err_sex="Cinsiyetini seç", err_act="Aktivite düzeyini seç",
    tdee="Günlük ihtiyacın (kilonu korumak için)", bmr="Bazal metabolizma", kcal="kcal/gün",
    targets="Kilo vermek için günlük hedefin",
    plans=[("Hafif", "−250 kcal"), ("Orta · önerilen", "−500 kcal"), ("Güçlü", "−750 kcal")],
    week="≈ {v} kg/hafta", floor_note="Bu hedef, uzman gözetimi olmadan önerilen alt sınıra ({f} kcal) yükseltildi.",
    low_note="Hesaplanan ihtiyacın, uzman gözetimi olmadan önerilen alt sınırın ({f} kcal) altında. Kalori açığı yerine bir diyetisyen ya da hekimle plan yap.",
    adapt="Haftalık tahmin ilk haftalar için kabadır: kilo verdikçe harcaman da azalır ve kayıp yavaşlar. Bu yüzden tartıya değil, 3–4 haftalık ortalamaya bak.",
    cta_h="Hedefini Suu'da takip et", cta_p="Hesapladığın hedefi Suu'ya gir; öğününü sesle ya da fotoğrafla kaydet, GPS'li antrenmanın yaktığını aynı günde gör.",
    how_h="Nasıl hesaplıyoruz?",
    how_p=["Önce bazal metabolizmanı (dinlenirken harcadığın enerji) Mifflin-St Jeor denklemiyle hesaplıyoruz: erkeklerde 10 × kilo + 6,25 × boy − 5 × yaş + 5, kadınlarda aynı toplam − 161.{r1} Sistematik bir derlemede bu denklem, yaygın formüller arasında bireylerin çoğunda ölçülen değerin ±%10'u içinde kalan en güvenilir denklem çıktı; yine de kişisel sapma olabilir.{r2}",
           "Sonra bunu aktivite katsayısıyla çarpıp günlük ihtiyacını (kilonu korumak için gereken kaloriyi) buluyoruz. Kilo vermek için bu ihtiyacın 250–750 kcal altına iniyoruz."],
    act_table=("Aktivite düzeyi", "Katsayı"),
    safe_h="Ne kadar açık güvenli?",
    safe_items=["CDC'ye göre haftada yaklaşık 0,5–1 kg veren kişilerin kiloyu geri alma olasılığı daha düşük; bu, çoğu kişi için günde yaklaşık 500 kcal'lik bir açığa denk geliyor.{r4}",
                "Harvard Health, uzman gözetimi olmadan kalori alımının kadınlarda günde 1.200, erkeklerde 1.500 kcal'nin altına inmemesini öneriyor; hesaplayıcı hiçbir hedefi bu sınırın altına indirmez.{r5}",
                "Kilo vermek doğrusal ilerlemez: vücut ağırlığı enerji değişimine yavaş yanıt verir ve kilo azaldıkça harcama da azalır.{r3} Birkaç haftada bir hesabı yeni kilonla tekrarla."],
    faq_h="Sık sorulan sorular",
    faq=[("Kalori açığı nasıl hesaplanır?", "Önce günlük ihtiyacını bul: bazal metabolizmanı (Mifflin-St Jeor denklemi) aktivite katsayınla çarp. Kilo vermek için bu sayının 250–750 kcal altına in. Örneğin günlük ihtiyacın 2.200 kcal ise 1.700 kcal'lik hedef 500 kcal'lik bir açıktır."),
         ("Kilo vermek için günde kaç kalori almalıyım?", "Günlük ihtiyacından yaklaşık 500 kcal az: bu, çoğu kişide haftada 0,5 kg civarı kayıp demek. Uzman gözetimi olmadan kadınlarda 1.200, erkeklerde 1.500 kcal'nin altına inme."),
         ("Kalori açığıyla haftada kaç kilo verilir?", "Kaba hesapla günde 500 kcal açık haftada yaklaşık 0,45 kg eder. Ama bu ilk haftalar için bir tahmin; kilo verdikçe harcaman azalır ve kayıp yavaşlar, ilk günlerdeki hızlı düşüşün bir kısmı da sudur."),
         ("Bazal metabolizma ile günlük kalori ihtiyacı aynı şey mi?", "Hayır. Bazal metabolizma tamamen dinlenirken harcadığın enerji; günlük ihtiyaç ise buna günlük hareket ve egzersizin eklenmiş hâli. Kilo vermek için hedefini bazal metabolizmaya değil günlük ihtiyaca göre kur."),
         ("Bu hesaplayıcı herkes için uygun mu?", "18 yaş üstü sağlıklı yetişkinler için genel bir tahmindir. Hamileysen, emziriyorsan, kronik bir hastalığın, yeme bozukluğu geçmişin varsa ya da ilaç kullanıyorsan hedefini bir diyetisyen veya hekimle belirle.")],
    refs_h="Kaynaklar", local_ref=("T.C. Sağlık Bakanlığı — Türkiye Beslenme Rehberi (TÜBER) 2022", "https://hsgm.saglik.gov.tr/tr/web-uygulamalarimiz/357.html"),
    rel_h="İlgili araç ve yazılar",
    related=[("Blog", "/blog/kalori-acigi.html", "Kalori açığı nedir ve nasıl oluşturulur?"),
             ("Blog", "/blog/makro-hesaplama.html", "Makro hesaplama: protein, karbonhidrat, yağ"),
             ("Rehber", "/blog/neden-kilo-veremiyorum.html", "Neden kilo veremiyorum? 7 neden"),
             ("Araç", "/su-hesaplayici.html", "Günlük su ihtiyacı hesaplayıcı")],
    disclaimer="Bu araç genel bilgi verir, tıbbi tavsiye değildir. Kişisel ihtiyacın için bir sağlık uzmanına danış.",
    footer_home="Ana Sayfa", footer_priv="Gizlilik", dev="Geliştiren", city="İstanbul, Türkiye",
)

L["en"] = dict(
    file="calorie-deficit-calculator.html", lang="en", dir="ltr", locale="en_US", num="en-US",
    home="/hosgeldiniz-en.html", blog="blog-en.html", faq_page="faq-en.html", llms="/llms-en.txt", llms_full="/llms-full-en.txt",
    nav=["Home", "Blog", "FAQ"],
    title="Calorie Deficit Calculator — How Many Calories Should I Eat? | Suu",
    desc="Work out your daily calorie needs and a safe calorie deficit from age, weight, height and activity in seconds. Mifflin-St Jeor equation, free.",
    keywords="calorie deficit calculator, how to calculate calorie deficit, daily calorie needs calculator, how many calories should i eat to lose weight, tdee calculator, bmr calculator, maintenance calories",
    og_title="Calorie Deficit Calculator — How Many Calories Should I Eat?",
    og_desc="Find your daily calorie needs and a safe target for losing weight. Free and science-based.",
    app_name="Suu Calorie Deficit Calculator",
    app_desc="A free online tool that calculates daily calorie needs and safe calorie deficit targets from age, weight, height, sex and activity level.",
    badge="🔥 Free Online Tool", h1="Calorie Deficit<br>Calculator",
    sub="Find your daily calorie needs and a safe target for losing weight in a few seconds.",
    s1="Your details", age="Age", weight="Weight (kg)", height="Height (cm)", sex="Sex (for the equation)",
    male="♂ Male", female="♀ Female", ph_age="e.g. 30", ph_weight="e.g. 75", ph_height="e.g. 170",
    next="Continue", back="Back", calc="Calculate", recalc="Recalculate",
    s2="Your activity level",
    acts={"sedentary": ("Sedentary", "Desk job, no exercise"), "light": ("Light", "1–3 days a week"),
          "moderate": ("Moderate", "3–5 days a week"), "active": ("Active", "6–7 days a week"),
          "extra": ("Very active", "Physical job + training")},
    err_age="Enter a valid age (18–80)", err_weight="Enter a valid weight (35–250 kg)",
    err_height="Enter a valid height (130–220 cm)", err_sex="Select your sex", err_act="Select your activity level",
    tdee="Your daily needs (to maintain weight)", bmr="Basal metabolic rate", kcal="kcal/day",
    targets="Your daily target for losing weight",
    plans=[("Mild", "−250 kcal"), ("Moderate · recommended", "−500 kcal"), ("Strong", "−750 kcal")],
    week="≈ {v} kg/week", floor_note="This target was raised to the recommended minimum without professional supervision ({f} kcal).",
    low_note="Your estimated needs are below the recommended minimum without professional supervision ({f} kcal). Rather than a deficit, plan with a dietitian or doctor.",
    adapt="The weekly estimate is rough and applies to the first weeks: as you lose weight you burn less, so progress slows. Judge by your 3–4-week average, not a single weigh-in.",
    cta_h="Track your target in Suu", cta_p="Enter your target in Suu, log meals by voice or photo, and see what your GPS workout burned on the same day.",
    how_h="How we calculate it",
    how_p=["First we estimate your basal metabolic rate (the energy you burn at rest) with the Mifflin-St Jeor equation: 10 × weight + 6.25 × height − 5 × age + 5 for men, and the same sum − 161 for women.{r1} In a systematic review it was the most reliable of the common equations, predicting within ±10% of measured values in most people — individual error is still possible.{r2}",
           "We then multiply it by an activity factor to get your daily needs (the calories that keep your weight stable). To lose weight we go 250–750 kcal below that."],
    act_table=("Activity level", "Factor"),
    safe_h="How big a deficit is safe?",
    safe_items=["According to the CDC, people who lose about 1–2 pounds (0.5–1 kg) a week are more likely to keep the weight off; for most people that's roughly a 500 kcal daily deficit.{r4}",
                "Harvard Health advises that, without professional supervision, intake shouldn't fall below 1,200 kcal a day for women or 1,500 for men; the calculator never sets a target below that.{r5}",
                "Weight loss isn't linear: body weight responds slowly to a change in energy, and as you lose weight you burn less.{r3} Re-run the calculation with your new weight every few weeks."],
    faq_h="Frequently asked questions",
    faq=[("How do you calculate a calorie deficit?", "First find your daily needs: multiply your basal metabolic rate (Mifflin-St Jeor equation) by your activity factor. To lose weight, eat 250–750 kcal below that. If your daily needs are 2,200 kcal, a 1,700 kcal target is a 500 kcal deficit."),
         ("How many calories should I eat to lose weight?", "About 500 kcal less than your daily needs — for most people that's around 0.5 kg a week. Without professional supervision, don't go below 1,200 kcal for women or 1,500 for men."),
         ("How much weight will I lose with a calorie deficit?", "Roughly, a 500 kcal daily deficit equals about 0.45 kg a week. That's an estimate for the first weeks: as you lose weight you burn less and progress slows, and part of the fast early drop is water."),
         ("Is BMR the same as daily calorie needs?", "No. BMR is the energy you burn at complete rest; daily needs add everyday movement and exercise on top. Base your weight-loss target on daily needs, not BMR."),
         ("Is this calculator right for everyone?", "It's a general estimate for healthy adults over 18. If you are pregnant or breastfeeding, have a long-term condition or a history of eating disorders, or take medication, set your target with a dietitian or doctor.")],
    refs_h="Sources", local_ref=("NHS — Understanding calories", "https://www.nhs.uk/live-well/healthy-weight/managing-your-weight/understanding-calories/"),
    rel_h="Related tools & articles",
    related=[("Blog", "/blog/en/calorie-deficit.html", "What is a calorie deficit?"),
             ("Blog", "/blog/en/macro-calculation.html", "How to calculate your macros"),
             ("Guide", "/blog/en/why-am-i-not-losing-weight.html", "Why am I not losing weight?"),
             ("Tool", "/water-calculator.html", "Daily water intake calculator")],
    disclaimer="This tool provides general information and is not medical advice. Consult a healthcare professional for your individual needs.",
    footer_home="Home", footer_priv="Privacy", dev="Developed by", city="Istanbul, Turkey",
)

L["ar"] = dict(
    file="hasibat-al-ajz-al-harari.html", lang="ar", dir="rtl", locale="ar_SA", num="ar-EG-u-nu-latn",
    home="/hosgeldiniz-ar.html", blog="blog-ar.html", faq_page="faq-ar.html", llms="/llms-ar.txt", llms_full="/llms-full-ar.txt",
    nav=["الرئيسية", "المدونة", "الأسئلة الشائعة"],
    title="حاسبة العجز الحراري — كم سعرة أحتاج يوميًا؟ | Suu",
    desc="احسب احتياجك اليومي من السعرات وعجزًا حراريًا آمنًا من العمر والوزن والطول والنشاط في ثوانٍ. معادلة Mifflin-St Jeor، مجانًا.",
    keywords="حاسبة العجز الحراري, كيف أحسب العجز الحراري, حساب السعرات اليومية, كم سعرة أحتاج لإنقاص الوزن, حساب معدل الأيض الأساسي, حاسبة السعرات",
    og_title="حاسبة العجز الحراري — كم سعرة أحتاج يوميًا؟",
    og_desc="احسب احتياجك اليومي من السعرات وهدفًا آمنًا لإنقاص الوزن. مجانية ومبنية على العلم.",
    app_name="حاسبة العجز الحراري من Suu",
    app_desc="أداة مجانية على الإنترنت تحسب الاحتياج اليومي من السعرات وأهداف العجز الحراري الآمنة من العمر والوزن والطول والجنس ومستوى النشاط.",
    badge="🔥 أداة مجانية على الإنترنت", h1="حاسبة<br>العجز الحراري",
    sub="اعرف احتياجك اليومي من السعرات وهدفًا آمنًا لإنقاص الوزن في ثوانٍ.",
    s1="بياناتك", age="العمر", weight="الوزن (كغ)", height="الطول (سم)", sex="الجنس (للمعادلة)",
    male="♂ ذكر", female="♀ أنثى", ph_age="مثلًا 30", ph_weight="مثلًا 75", ph_height="مثلًا 170",
    next="متابعة", back="رجوع", calc="احسب", recalc="أعد الحساب",
    s2="مستوى نشاطك",
    acts={"sedentary": ("خامل", "عمل مكتبي بلا رياضة"), "light": ("خفيف", "1–3 أيام أسبوعيًا"),
          "moderate": ("متوسط", "3–5 أيام أسبوعيًا"), "active": ("نشيط", "6–7 أيام أسبوعيًا"),
          "extra": ("نشيط جدًا", "عمل بدني + تمارين")},
    err_age="أدخل عمرًا صحيحًا (18–80)", err_weight="أدخل وزنًا صحيحًا (35–250 كغ)",
    err_height="أدخل طولًا صحيحًا (130–220 سم)", err_sex="اختر الجنس", err_act="اختر مستوى النشاط",
    tdee="احتياجك اليومي (للحفاظ على الوزن)", bmr="معدل الأيض الأساسي", kcal="سعرة/يوم",
    targets="هدفك اليومي لإنقاص الوزن",
    plans=[("خفيف", "−250 سعرة"), ("متوسط · مُوصى به", "−500 سعرة"), ("قوي", "−750 سعرة")],
    week="≈ {v} كغ/أسبوع", floor_note="رُفع هذا الهدف إلى الحد الأدنى الموصى به دون إشراف مختص ({f} سعرة).",
    low_note="احتياجك المقدّر أقل من الحد الأدنى الموصى به دون إشراف مختص ({f} سعرة). بدل العجز الحراري، خطّط مع أخصائي تغذية أو طبيب.",
    adapt="التقدير الأسبوعي تقريبي ويخص الأسابيع الأولى: كلما نقص وزنك قلّ ما تحرقه فيتباطأ النقص. احكم بمتوسط 3–4 أسابيع لا بوزنة واحدة.",
    cta_h="تابع هدفك في Suu", cta_p="أدخل هدفك في Suu، وسجّل وجباتك بالصوت أو بالصورة، وشاهد ما أحرقه تمرينك عبر GPS في اليوم نفسه.",
    how_h="كيف نحسبها؟",
    how_p=["نقدّر أولًا معدل الأيض الأساسي (الطاقة التي تحرقها في الراحة) بمعادلة Mifflin-St Jeor: للرجال 10 × الوزن + 6.25 × الطول − 5 × العمر + 5، وللنساء المجموع نفسه − 161.{r1} وفي مراجعة منهجية كانت الأكثر موثوقية بين المعادلات الشائعة، إذ تقع ضمن ±10% من القيمة المقيسة لدى معظم الناس، وقد يبقى خطأ فردي.{r2}",
           "ثم نضربه في معامل النشاط لنحصل على احتياجك اليومي (السعرات التي تحافظ على وزنك). ولإنقاص الوزن ننزل عنه 250–750 سعرة."],
    act_table=("مستوى النشاط", "المعامل"),
    safe_h="ما حجم العجز الآمن؟",
    safe_items=["وفق CDC، فمن يفقدون نحو 0.5–1 كغ أسبوعيًا أكثر قدرة على الحفاظ على وزنهم الجديد؛ وهذا يعادل لدى معظم الناس عجزًا يوميًا قدره نحو 500 سعرة.{r4}",
                "توصي Harvard Health بألا يقل المدخول دون إشراف مختص عن 1,200 سعرة يوميًا للنساء و1,500 للرجال، ولا تضع الحاسبة أي هدف دون ذلك.{r5}",
                "إنقاص الوزن ليس خطيًا: يستجيب وزن الجسم ببطء لتغيّر الطاقة، وكلما نقص وزنك قلّ ما تحرقه.{r3} أعد الحساب بوزنك الجديد كل بضعة أسابيع."],
    faq_h="الأسئلة الشائعة",
    faq=[("كيف أحسب العجز الحراري؟", "اعرف أولًا احتياجك اليومي: اضرب معدل الأيض الأساسي (معادلة Mifflin-St Jeor) في معامل نشاطك. ولإنقاص الوزن تناول أقل منه بـ250–750 سعرة. فإن كان احتياجك 2,200 سعرة فهدف 1,700 سعرة عجز قدره 500 سعرة."),
         ("كم سعرة أتناول يوميًا لإنقاص الوزن؟", "أقل من احتياجك اليومي بنحو 500 سعرة، وهذا يعني لدى معظم الناس نحو 0.5 كغ أسبوعيًا. ولا تنزل دون إشراف مختص عن 1,200 سعرة للنساء و1,500 للرجال."),
         ("كم كيلوغرامًا أفقد أسبوعيًا بالعجز الحراري؟", "تقريبيًا، عجز يومي قدره 500 سعرة يعادل نحو 0.45 كغ أسبوعيًا. لكنه تقدير للأسابيع الأولى؛ فكلما نقص وزنك قلّ ما تحرقه وتباطأ النقص، وجزء من الهبوط السريع في البداية ماء."),
         ("هل معدل الأيض الأساسي هو الاحتياج اليومي نفسه؟", "لا. معدل الأيض الأساسي هو الطاقة التي تحرقها في راحة تامة، أما الاحتياج اليومي فيضيف إليه الحركة اليومية والتمارين. ابنِ هدف إنقاص الوزن على الاحتياج اليومي لا على الأيض الأساسي."),
         ("هل تناسب هذه الحاسبة الجميع؟", "هي تقدير عام للبالغين الأصحاء فوق 18 عامًا. إن كنتِ حاملًا أو مرضعًا، أو لديك مرض مزمن أو تاريخ مع اضطرابات الأكل، أو تتناول أدوية، فحدد هدفك مع أخصائي تغذية أو طبيب.")],
    refs_h="المصادر", local_ref=("منظمة الصحة العالمية — السمنة وزيادة الوزن (صحيفة وقائع)", "https://www.who.int/ar/news-room/fact-sheets/detail/obesity-and-overweight"),
    rel_h="أدوات ومقالات ذات صلة",
    related=[("مدونة", "/blog/ar/al-ajz-al-harari.html", "ما هو العجز الحراري؟"),
             ("مدونة", "/blog/ar/hisab-al-macro.html", "حساب الماكروز"),
             ("دليل", "/blog/ar/limadha-la-yanqus-wazni.html", "لماذا لا ينقص وزني؟"),
             ("أداة", "/water-calculator-ar.html", "حاسبة احتياج الماء اليومي")],
    disclaimer="تقدم هذه الأداة معلومات عامة وليست نصيحة طبية. استشر مختصًا صحيًا لاحتياجاتك الشخصية.",
    footer_home="الرئيسية", footer_priv="الخصوصية", dev="تطوير", city="إسطنبول، تركيا",
)

L["ru"] = dict(
    file="kalkulyator-deficita-kalorij.html", lang="ru", dir="ltr", locale="ru_RU", num="ru-RU",
    home="/hosgeldiniz-ru.html", blog="blog-ru.html", faq_page="faq-ru.html", llms="/llms-ru.txt", llms_full="/llms-full-ru.txt",
    nav=["Главная", "Блог", "FAQ"],
    title="Калькулятор дефицита калорий — сколько калорий мне нужно? | Suu",
    desc="Рассчитайте суточную норму калорий и безопасный дефицит по возрасту, весу, росту и активности за секунды. Формула Миффлина — Сан Жеора, бесплатно.",
    keywords="калькулятор дефицита калорий, как рассчитать дефицит калорий, как создать дефицит калорий, суточная норма калорий, сколько калорий нужно чтобы похудеть, калькулятор основного обмена",
    og_title="Калькулятор дефицита калорий — сколько калорий мне нужно?",
    og_desc="Узнайте суточную норму калорий и безопасную цель для похудения. Бесплатно и на научной основе.",
    app_name="Калькулятор дефицита калорий Suu",
    app_desc="Бесплатный онлайн-инструмент, который рассчитывает суточную потребность в калориях и безопасные цели дефицита по возрасту, весу, росту, полу и активности.",
    badge="🔥 Бесплатный онлайн-инструмент", h1="Калькулятор<br>дефицита калорий",
    sub="Узнайте суточную норму калорий и безопасную цель для похудения за несколько секунд.",
    s1="Ваши данные", age="Возраст", weight="Вес (кг)", height="Рост (см)", sex="Пол (для формулы)",
    male="♂ Мужской", female="♀ Женский", ph_age="напр. 30", ph_weight="напр. 75", ph_height="напр. 170",
    next="Далее", back="Назад", calc="Рассчитать", recalc="Пересчитать",
    s2="Уровень активности",
    acts={"sedentary": ("Сидячий", "Офис, без тренировок"), "light": ("Лёгкий", "1–3 дня в неделю"),
          "moderate": ("Умеренный", "3–5 дней в неделю"), "active": ("Активный", "6–7 дней в неделю"),
          "extra": ("Очень активный", "Физический труд + спорт")},
    err_age="Введите корректный возраст (18–80)", err_weight="Введите корректный вес (35–250 кг)",
    err_height="Введите корректный рост (130–220 см)", err_sex="Выберите пол", err_act="Выберите уровень активности",
    tdee="Суточная норма (чтобы сохранить вес)", bmr="Основной обмен", kcal="ккал/день",
    targets="Ваша дневная цель для похудения",
    plans=[("Мягкий", "−250 ккал"), ("Умеренный · рекомендуем", "−500 ккал"), ("Сильный", "−750 ккал")],
    week="≈ {v} кг/неделю", floor_note="Цель поднята до рекомендуемого минимума без наблюдения специалиста ({f} ккал).",
    low_note="Ваша расчётная норма ниже рекомендуемого минимума без наблюдения специалиста ({f} ккал). Вместо дефицита составьте план с диетологом или врачом.",
    adapt="Недельная оценка грубая и относится к первым неделям: по мере похудения расход снижается, и потеря веса замедляется. Ориентируйтесь на среднее за 3–4 недели, а не на одно взвешивание.",
    cta_h="Следите за целью в Suu", cta_p="Внесите цель в Suu, записывайте еду голосом или по фото и смотрите расход GPS-тренировки в тот же день.",
    how_h="Как мы считаем",
    how_p=["Сначала оцениваем основной обмен (энергию в покое) по формуле Миффлина — Сан Жеора: для мужчин 10 × вес + 6,25 × рост − 5 × возраст + 5, для женщин та же сумма − 161.{r1} В систематическом обзоре она оказалась самой надёжной из распространённых формул — у большинства людей в пределах ±10% от измеренного значения, хотя индивидуальная ошибка возможна.{r2}",
           "Затем умножаем на коэффициент активности и получаем суточную норму (калории, при которых вес стабилен). Для похудения опускаемся на 250–750 ккал ниже."],
    act_table=("Уровень активности", "Коэффициент"),
    safe_h="Какой дефицит безопасен?",
    safe_items=["По данным CDC, люди, которые теряют около 0,5–1 кг в неделю, чаще удерживают результат; для большинства это примерно 500 ккал дефицита в день.{r4}",
                "Harvard Health советует без наблюдения специалиста не опускаться ниже 1200 ккал в день для женщин и 1500 для мужчин; калькулятор не ставит цель ниже этого порога.{r5}",
                "Похудение идёт не по прямой: вес медленно реагирует на изменение энергии, а по мере похудения расход снижается.{r3} Пересчитывайте норму с новым весом каждые несколько недель."],
    faq_h="Частые вопросы",
    faq=[("Как рассчитать дефицит калорий?", "Сначала найдите суточную норму: умножьте основной обмен (формула Миффлина — Сан Жеора) на коэффициент активности. Для похудения ешьте на 250–750 ккал меньше. Если норма 2200 ккал, цель 1700 ккал — это дефицит 500 ккал."),
         ("Сколько калорий есть, чтобы похудеть?", "Примерно на 500 ккал меньше суточной нормы — для большинства это около 0,5 кг в неделю. Без наблюдения специалиста не опускайтесь ниже 1200 ккал для женщин и 1500 для мужчин."),
         ("Сколько кг в неделю уходит при дефиците калорий?", "Грубо, дефицит 500 ккал в день — около 0,45 кг в неделю. Но это оценка для первых недель: по мере похудения расход снижается и потеря замедляется, а часть быстрого снижения в начале — вода."),
         ("Основной обмен и суточная норма — одно и то же?", "Нет. Основной обмен — энергия в полном покое; суточная норма добавляет к нему повседневное движение и тренировки. Цель для похудения стройте от суточной нормы, а не от основного обмена."),
         ("Подходит ли калькулятор всем?", "Это общая оценка для здоровых взрослых старше 18 лет. Если вы беременны или кормите грудью, есть хроническое заболевание, расстройство пищевого поведения в анамнезе или вы принимаете лекарства, определите цель с диетологом или врачом.")],
    refs_h="Источники", local_ref=("ВОЗ — Ожирение и избыточный вес (информационный бюллетень)", "https://www.who.int/ru/news-room/fact-sheets/detail/obesity-and-overweight"),
    rel_h="Связанные инструменты и статьи",
    related=[("Блог", "/blog/ru/deficit-kalorij.html", "Что такое дефицит калорий"),
             ("Блог", "/blog/ru/raschet-makrosov.html", "Расчёт макросов"),
             ("Руководство", "/blog/ru/pochemu-ne-hudeyu.html", "Почему я не худею?"),
             ("Инструмент", "/water-calculator-ru.html", "Калькулятор нормы воды")],
    disclaimer="Инструмент даёт общую информацию и не является медицинской консультацией. По индивидуальным вопросам обратитесь к специалисту.",
    footer_home="Главная", footer_priv="Конфиденциальность", dev="Разработчик", city="Стамбул, Турция",
)

L["de"] = dict(
    file="kaloriendefizit-rechner.html", lang="de", dir="ltr", locale="de_DE", num="de-DE",
    home="/hosgeldiniz-de.html", blog="blog-de.html", faq_page=None, llms="/llms-de.txt", llms_full="/llms-full-de.txt",
    nav=["Start", "Blog"],
    title="Kaloriendefizit-Rechner — Wie viele Kalorien brauche ich? | Suu",
    desc="Berechne deinen täglichen Kalorienbedarf und ein sicheres Kaloriendefizit aus Alter, Gewicht, Größe und Aktivität in Sekunden. Mifflin-St-Jeor-Formel, kostenlos.",
    keywords="kaloriendefizit rechner, kaloriendefizit berechnen, kalorienbedarf berechnen, wie viele kalorien zum abnehmen, grundumsatz berechnen, gesamtumsatz rechner",
    og_title="Kaloriendefizit-Rechner — Wie viele Kalorien brauche ich?",
    og_desc="Berechne deinen täglichen Kalorienbedarf und ein sicheres Ziel zum Abnehmen. Kostenlos und wissenschaftlich fundiert.",
    app_name="Suu Kaloriendefizit-Rechner",
    app_desc="Kostenloses Online-Tool, das den täglichen Kalorienbedarf und sichere Kaloriendefizit-Ziele aus Alter, Gewicht, Größe, Geschlecht und Aktivität berechnet.",
    badge="🔥 Kostenloses Online-Tool", h1="Kaloriendefizit-<br>Rechner",
    sub="Finde in wenigen Sekunden deinen täglichen Kalorienbedarf und ein sicheres Ziel zum Abnehmen.",
    s1="Deine Angaben", age="Alter", weight="Gewicht (kg)", height="Größe (cm)", sex="Geschlecht (für die Formel)",
    male="♂ Männlich", female="♀ Weiblich", ph_age="z. B. 30", ph_weight="z. B. 75", ph_height="z. B. 170",
    next="Weiter", back="Zurück", calc="Berechnen", recalc="Neu berechnen",
    s2="Dein Aktivitätslevel",
    acts={"sedentary": ("Sitzend", "Bürojob, kein Sport"), "light": ("Leicht", "1–3 Tage pro Woche"),
          "moderate": ("Mittel", "3–5 Tage pro Woche"), "active": ("Aktiv", "6–7 Tage pro Woche"),
          "extra": ("Sehr aktiv", "Körperliche Arbeit + Training")},
    err_age="Gib ein gültiges Alter ein (18–80)", err_weight="Gib ein gültiges Gewicht ein (35–250 kg)",
    err_height="Gib eine gültige Größe ein (130–220 cm)", err_sex="Wähle dein Geschlecht", err_act="Wähle dein Aktivitätslevel",
    tdee="Dein täglicher Bedarf (Gewicht halten)", bmr="Grundumsatz", kcal="kcal/Tag",
    targets="Dein Tagesziel zum Abnehmen",
    plans=[("Leicht", "−250 kcal"), ("Mittel · empfohlen", "−500 kcal"), ("Stark", "−750 kcal")],
    week="≈ {v} kg/Woche", floor_note="Dieses Ziel wurde auf das empfohlene Minimum ohne fachliche Begleitung angehoben ({f} kcal).",
    low_note="Dein geschätzter Bedarf liegt unter dem empfohlenen Minimum ohne fachliche Begleitung ({f} kcal). Plane statt eines Defizits lieber mit einer Ernährungsfachkraft oder ärztlich.",
    adapt="Die Wochenschätzung ist grob und gilt für die ersten Wochen: Je mehr du abnimmst, desto weniger verbrauchst du, und es geht langsamer. Orientier dich am Schnitt über 3–4 Wochen, nicht an einer einzelnen Wiegung.",
    cta_h="Verfolge dein Ziel in Suu", cta_p="Trag dein Ziel in Suu ein, erfasse Mahlzeiten per Sprache oder Foto und sieh am selben Tag, was dein GPS-Training verbrannt hat.",
    how_h="So rechnen wir",
    how_p=["Zuerst schätzen wir deinen Grundumsatz (die Energie in Ruhe) mit der Mifflin-St-Jeor-Formel: Männer 10 × Gewicht + 6,25 × Größe − 5 × Alter + 5, Frauen dieselbe Summe − 161.{r1} In einer systematischen Übersicht war sie die zuverlässigste der gängigen Formeln und lag bei den meisten Menschen innerhalb von ±10 % des gemessenen Werts — individuelle Abweichungen bleiben möglich.{r2}",
           "Dann multiplizieren wir mit einem Aktivitätsfaktor und erhalten deinen täglichen Bedarf (die Kalorien, bei denen dein Gewicht stabil bleibt). Zum Abnehmen gehen wir 250–750 kcal darunter."],
    act_table=("Aktivitätslevel", "Faktor"),
    safe_h="Wie groß darf das Defizit sein?",
    safe_items=["Laut CDC halten Menschen, die etwa 0,5–1 kg pro Woche abnehmen, ihr Gewicht eher; für die meisten entspricht das rund 500 kcal Defizit pro Tag.{r4}",
                "Harvard Health rät, ohne fachliche Begleitung nicht unter 1.200 kcal pro Tag bei Frauen und 1.500 bei Männern zu gehen; der Rechner setzt kein Ziel darunter.{r5}",
                "Abnehmen verläuft nicht linear: Das Körpergewicht reagiert langsam auf eine Energieänderung, und je mehr du abnimmst, desto weniger verbrauchst du.{r3} Rechne alle paar Wochen mit deinem neuen Gewicht neu."],
    faq_h="Häufige Fragen",
    faq=[("Wie berechne ich ein Kaloriendefizit?", "Ermittle zuerst deinen täglichen Bedarf: Grundumsatz (Mifflin-St-Jeor-Formel) mal Aktivitätsfaktor. Zum Abnehmen isst du 250–750 kcal weniger. Liegt dein Bedarf bei 2.200 kcal, ist ein Ziel von 1.700 kcal ein Defizit von 500 kcal."),
         ("Wie viele Kalorien sollte ich zum Abnehmen essen?", "Etwa 500 kcal weniger als deinen täglichen Bedarf — für die meisten rund 0,5 kg pro Woche. Ohne fachliche Begleitung nicht unter 1.200 kcal (Frauen) bzw. 1.500 kcal (Männer)."),
         ("Wie viel nehme ich mit einem Kaloriendefizit pro Woche ab?", "Grob gerechnet ergibt ein Defizit von 500 kcal pro Tag etwa 0,45 kg pro Woche. Das ist eine Schätzung für die ersten Wochen: Mit sinkendem Gewicht verbrauchst du weniger, es geht langsamer, und ein Teil des schnellen Anfangsverlusts ist Wasser."),
         ("Sind Grundumsatz und Tagesbedarf dasselbe?", "Nein. Der Grundumsatz ist die Energie in völliger Ruhe; der Tagesbedarf rechnet Alltagsbewegung und Training dazu. Richte dein Abnehmziel am Tagesbedarf aus, nicht am Grundumsatz."),
         ("Ist der Rechner für alle geeignet?", "Er ist eine allgemeine Schätzung für gesunde Erwachsene ab 18. Bist du schwanger oder stillst, hast eine chronische Erkrankung oder Essstörungen in der Vorgeschichte oder nimmst Medikamente, leg dein Ziel mit einer Ernährungsfachkraft oder ärztlich fest.")],
    refs_h="Quellen", local_ref=("Deutsche Gesellschaft für Ernährung — Gut essen und trinken: die DGE-Empfehlungen", "https://www.dge.de/gesunde-ernaehrung/gut-essen-und-trinken/dge-empfehlungen/"),
    rel_h="Passende Tools und Artikel",
    related=[("Blog", "/blog/de/kaloriendefizit.html", "Was ist ein Kaloriendefizit?"),
             ("Blog", "/blog/de/makroberechnung.html", "Makros berechnen"),
             ("Ratgeber", "/blog/de/warum-nehme-ich-nicht-ab.html", "Warum nehme ich nicht ab?"),
             ("Ratgeber", "/blog/de/gehen-oder-laufen-abnehmen.html", "Gehen oder Laufen zum Abnehmen?")],
    disclaimer="Dieses Tool bietet allgemeine Informationen und ersetzt keine medizinische Beratung. Für deinen persönlichen Bedarf wende dich an Fachpersonal.",
    footer_home="Start", footer_priv="Datenschutz", dev="Entwickelt von", city="Istanbul, Türkei",
)

L["it"] = dict(
    file="calcolatore-deficit-calorico.html", lang="it", dir="ltr", locale="it_IT", num="it-IT",
    home="/hosgeldiniz-it.html", blog="blog-it.html", faq_page=None, llms="/llms-it.txt", llms_full="/llms-full-it.txt",
    nav=["Home", "Blog"],
    title="Calcolatore deficit calorico — quante calorie mi servono? | Suu",
    desc="Calcola il fabbisogno calorico giornaliero e un deficit calorico sicuro da età, peso, altezza e attività in pochi secondi. Formula di Mifflin-St Jeor, gratis.",
    keywords="calcolatore deficit calorico, come calcolare il deficit calorico, come andare in deficit calorico, fabbisogno calorico giornaliero, quante calorie per dimagrire, calcolo metabolismo basale",
    og_title="Calcolatore deficit calorico — quante calorie mi servono?",
    og_desc="Scopri il tuo fabbisogno calorico giornaliero e un obiettivo sicuro per dimagrire. Gratis e su base scientifica.",
    app_name="Calcolatore del deficit calorico di Suu",
    app_desc="Strumento online gratuito che calcola il fabbisogno calorico giornaliero e obiettivi di deficit sicuri da età, peso, altezza, sesso e livello di attività.",
    badge="🔥 Strumento online gratuito", h1="Calcolatore<br>deficit calorico",
    sub="Scopri in pochi secondi il tuo fabbisogno calorico giornaliero e un obiettivo sicuro per dimagrire.",
    s1="I tuoi dati", age="Età", weight="Peso (kg)", height="Altezza (cm)", sex="Sesso (per la formula)",
    male="♂ Uomo", female="♀ Donna", ph_age="es. 30", ph_weight="es. 75", ph_height="es. 170",
    next="Avanti", back="Indietro", calc="Calcola", recalc="Ricalcola",
    s2="Il tuo livello di attività",
    acts={"sedentary": ("Sedentario", "Lavoro d'ufficio, niente sport"), "light": ("Leggero", "1–3 giorni a settimana"),
          "moderate": ("Moderato", "3–5 giorni a settimana"), "active": ("Attivo", "6–7 giorni a settimana"),
          "extra": ("Molto attivo", "Lavoro fisico + allenamento")},
    err_age="Inserisci un'età valida (18–80)", err_weight="Inserisci un peso valido (35–250 kg)",
    err_height="Inserisci un'altezza valida (130–220 cm)", err_sex="Seleziona il sesso", err_act="Seleziona il livello di attività",
    tdee="Il tuo fabbisogno giornaliero (per mantenere il peso)", bmr="Metabolismo basale", kcal="kcal/giorno",
    targets="Il tuo obiettivo giornaliero per dimagrire",
    plans=[("Lieve", "−250 kcal"), ("Moderato · consigliato", "−500 kcal"), ("Deciso", "−750 kcal")],
    week="≈ {v} kg/settimana", floor_note="Questo obiettivo è stato alzato al minimo consigliato senza supervisione professionale ({f} kcal).",
    low_note="Il tuo fabbisogno stimato è sotto il minimo consigliato senza supervisione professionale ({f} kcal). Invece di un deficit, pianifica con un dietista o un medico.",
    adapt="La stima settimanale è approssimativa e vale per le prime settimane: man mano che dimagrisci consumi meno e il calo rallenta. Guarda la media di 3–4 settimane, non una singola pesata.",
    cta_h="Segui il tuo obiettivo con Suu", cta_p="Inserisci il tuo obiettivo in Suu, registra i pasti a voce o con una foto e guarda nello stesso giorno cosa ha bruciato il tuo allenamento GPS.",
    how_h="Come lo calcoliamo",
    how_p=["Prima stimiamo il metabolismo basale (l'energia a riposo) con la formula di Mifflin-St Jeor: uomini 10 × peso + 6,25 × altezza − 5 × età + 5, donne la stessa somma − 161.{r1} In una revisione sistematica è risultata la più affidabile tra le formule comuni, entro il ±10% del valore misurato nella maggior parte delle persone — un errore individuale resta possibile.{r2}",
           "Poi la moltiplichiamo per un fattore di attività e otteniamo il fabbisogno giornaliero (le calorie che mantengono stabile il peso). Per dimagrire scendiamo di 250–750 kcal."],
    act_table=("Livello di attività", "Fattore"),
    safe_h="Quanto deficit è sicuro?",
    safe_items=["Secondo i CDC, chi perde circa 0,5–1 kg a settimana mantiene più facilmente il risultato; per la maggior parte delle persone equivale a circa 500 kcal di deficit al giorno.{r4}",
                "Harvard Health consiglia, senza supervisione professionale, di non scendere sotto 1.200 kcal al giorno per le donne e 1.500 per gli uomini; il calcolatore non imposta mai un obiettivo inferiore.{r5}",
                "Dimagrire non è lineare: il peso risponde lentamente a un cambiamento di energia e, man mano che dimagrisci, consumi meno.{r3} Ripeti il calcolo con il nuovo peso ogni qualche settimana."],
    faq_h="Domande frequenti",
    faq=[("Come si calcola il deficit calorico?", "Prima trova il fabbisogno giornaliero: metabolismo basale (formula di Mifflin-St Jeor) per il fattore di attività. Per dimagrire mangia 250–750 kcal in meno. Se il fabbisogno è 2.200 kcal, un obiettivo di 1.700 kcal è un deficit di 500 kcal."),
         ("Quante calorie mangiare per dimagrire?", "Circa 500 kcal in meno del fabbisogno giornaliero: per la maggior parte delle persone vuol dire circa 0,5 kg a settimana. Senza supervisione professionale non scendere sotto 1.200 kcal (donne) o 1.500 (uomini)."),
         ("Quanto si perde a settimana con il deficit calorico?", "In modo approssimativo, un deficit di 500 kcal al giorno vale circa 0,45 kg a settimana. È una stima per le prime settimane: man mano che dimagrisci consumi meno e il calo rallenta, e parte della discesa rapida iniziale è acqua."),
         ("Metabolismo basale e fabbisogno giornaliero sono la stessa cosa?", "No. Il metabolismo basale è l'energia consumata a riposo completo; il fabbisogno giornaliero aggiunge il movimento quotidiano e l'allenamento. Basa l'obiettivo per dimagrire sul fabbisogno giornaliero, non sul basale."),
         ("Il calcolatore va bene per tutti?", "È una stima generale per adulti sani sopra i 18 anni. Se sei in gravidanza o allatti, hai una malattia cronica o una storia di disturbi alimentari o assumi farmaci, stabilisci l'obiettivo con un dietista o un medico.")],
    refs_h="Fonti", local_ref=("CREA — Linee guida per una sana alimentazione (revisione 2018)", "https://www.crea.gov.it/web/alimenti-e-nutrizione/-/linee-guida-per-una-sana-alimentazione-2018"),
    rel_h="Strumenti e articoli correlati",
    related=[("Blog", "/blog/it/deficit-calorico.html", "Che cos'è il deficit calorico?"),
             ("Blog", "/blog/it/calcolo-macro.html", "Calcolo dei macro"),
             ("Guida", "/blog/it/perche-non-dimagrisco.html", "Perché non dimagrisco?"),
             ("Guida", "/blog/it/camminare-o-correre-per-dimagrire.html", "Camminare o correre per dimagrire?")],
    disclaimer="Questo strumento fornisce informazioni generali e non è un consiglio medico. Per le tue esigenze personali rivolgiti a un professionista sanitario.",
    footer_home="Home", footer_priv="Privacy", dev="Sviluppato da", city="Istanbul, Turchia",
)

L["uk"] = dict(
    file="kalkulyator-defitsytu-kaloriy.html", lang="uk", dir="ltr", locale="uk_UA", num="uk-UA",
    home="/hosgeldiniz-uk.html", blog="blog-uk.html", faq_page=None, llms="/llms-uk.txt", llms_full="/llms-full-uk.txt",
    nav=["Головна", "Блог"],
    title="Калькулятор дефіциту калорій — скільки калорій мені треба? | Suu",
    desc="Розрахуй добову норму калорій і безпечний дефіцит за віком, вагою, зростом і активністю за секунди. Формула Міффліна — Сан Жеора, безкоштовно.",
    keywords="калькулятор дефіциту калорій, як розрахувати дефіцит калорій, як зробити дефіцит калорій, добова норма калорій, скільки калорій щоб схуднути, калькулятор основного обміну",
    og_title="Калькулятор дефіциту калорій — скільки калорій мені треба?",
    og_desc="Дізнайся добову норму калорій і безпечну ціль для схуднення. Безкоштовно й на науковій основі.",
    app_name="Калькулятор дефіциту калорій Suu",
    app_desc="Безкоштовний онлайн-інструмент, що розраховує добову потребу в калоріях і безпечні цілі дефіциту за віком, вагою, зростом, статтю й активністю.",
    badge="🔥 Безкоштовний онлайн-інструмент", h1="Калькулятор<br>дефіциту калорій",
    sub="Дізнайся добову норму калорій і безпечну ціль для схуднення за кілька секунд.",
    s1="Твої дані", age="Вік", weight="Вага (кг)", height="Зріст (см)", sex="Стать (для формули)",
    male="♂ Чоловіча", female="♀ Жіноча", ph_age="напр. 30", ph_weight="напр. 75", ph_height="напр. 170",
    next="Далі", back="Назад", calc="Розрахувати", recalc="Перерахувати",
    s2="Рівень активності",
    acts={"sedentary": ("Сидячий", "Офіс, без тренувань"), "light": ("Легкий", "1–3 дні на тиждень"),
          "moderate": ("Помірний", "3–5 днів на тиждень"), "active": ("Активний", "6–7 днів на тиждень"),
          "extra": ("Дуже активний", "Фізична праця + спорт")},
    err_age="Введи коректний вік (18–80)", err_weight="Введи коректну вагу (35–250 кг)",
    err_height="Введи коректний зріст (130–220 см)", err_sex="Обери стать", err_act="Обери рівень активності",
    tdee="Добова норма (щоб зберегти вагу)", bmr="Основний обмін", kcal="ккал/день",
    targets="Твоя денна ціль для схуднення",
    plans=[("М'який", "−250 ккал"), ("Помірний · радимо", "−500 ккал"), ("Сильний", "−750 ккал")],
    week="≈ {v} кг/тиждень", floor_note="Ціль піднято до рекомендованого мінімуму без нагляду фахівця ({f} ккал).",
    low_note="Твоя розрахункова норма нижча за рекомендований мінімум без нагляду фахівця ({f} ккал). Замість дефіциту склади план із дієтологом або лікарем.",
    adapt="Тижнева оцінка груба й стосується перших тижнів: що більше ти худнеш, то менше витрачаєш, і втрата ваги сповільнюється. Орієнтуйся на середнє за 3–4 тижні, а не на одне зважування.",
    cta_h="Стеж за ціллю в Suu", cta_p="Внеси ціль у Suu, записуй їжу голосом або за фото й дивись витрату GPS-тренування того ж дня.",
    how_h="Як ми рахуємо",
    how_p=["Спершу оцінюємо основний обмін (енергію в спокої) за формулою Міффліна — Сан Жеора: для чоловіків 10 × вага + 6,25 × зріст − 5 × вік + 5, для жінок та сама сума − 161.{r1} У систематичному огляді вона виявилася найнадійнішою з поширених формул — у більшості людей у межах ±10% від виміряного значення, хоча індивідуальна похибка можлива.{r2}",
           "Потім множимо на коефіцієнт активності й отримуємо добову норму (калорії, за яких вага стабільна). Для схуднення опускаємося на 250–750 ккал нижче."],
    act_table=("Рівень активності", "Коефіцієнт"),
    safe_h="Який дефіцит безпечний?",
    safe_items=["За даними CDC, люди, які втрачають близько 0,5–1 кг на тиждень, частіше утримують результат; для більшості це приблизно 500 ккал дефіциту на день.{r4}",
                "Harvard Health радить без нагляду фахівця не опускатися нижче 1200 ккал на день для жінок і 1500 для чоловіків; калькулятор не ставить ціль нижче цього порогу.{r5}",
                "Схуднення йде не по прямій: вага повільно реагує на зміну енергії, а що більше ти худнеш, то менше витрачаєш.{r3} Перераховуй норму з новою вагою раз на кілька тижнів."],
    faq_h="Часті запитання",
    faq=[("Як розрахувати дефіцит калорій?", "Спершу знайди добову норму: помнож основний обмін (формула Міффліна — Сан Жеора) на коефіцієнт активності. Для схуднення їж на 250–750 ккал менше. Якщо норма 2200 ккал, ціль 1700 ккал — це дефіцит 500 ккал."),
         ("Скільки калорій їсти, щоб схуднути?", "Приблизно на 500 ккал менше за добову норму — для більшості це близько 0,5 кг на тиждень. Без нагляду фахівця не опускайся нижче 1200 ккал для жінок і 1500 для чоловіків."),
         ("Скільки кг на тиждень іде при дефіциті калорій?", "Грубо, дефіцит 500 ккал на день — це близько 0,45 кг на тиждень. Але це оцінка для перших тижнів: що більше ти худнеш, то менше витрачаєш і втрата сповільнюється, а частина швидкого зниження на початку — вода."),
         ("Основний обмін і добова норма — це одне й те саме?", "Ні. Основний обмін — енергія в повному спокої; добова норма додає до нього повсякденний рух і тренування. Ціль для схуднення будуй від добової норми, а не від основного обміну."),
         ("Чи підходить калькулятор усім?", "Це загальна оцінка для здорових дорослих старших за 18 років. Якщо ти вагітна чи годуєш груддю, маєш хронічну хворобу, розлад харчової поведінки в анамнезі або приймаєш ліки, визнач ціль із дієтологом чи лікарем.")],
    refs_h="Джерела", local_ref=("Центр громадського здоров'я України — 12 кроків до здорового харчування", "https://phc.org.ua/news/12-krokiv-do-zdorovogo-kharchuvannya"),
    rel_h="Пов'язані інструменти й статті",
    related=[("Блог", "/blog/uk/defitsyt-kaloriy.html", "Що таке дефіцит калорій"),
             ("Блог", "/blog/uk/rozrakhunok-makrosiv.html", "Розрахунок макросів"),
             ("Посібник", "/blog/uk/chomu-ya-ne-khudnu.html", "Чому я не худну?"),
             ("Посібник", "/blog/uk/khodba-chy-bih.html", "Ходьба чи біг для схуднення?")],
    disclaimer="Інструмент надає загальну інформацію й не є медичною порадою. З індивідуальних питань звернися до фахівця.",
    footer_home="Головна", footer_priv="Конфіденційність", dev="Розробник", city="Стамбул, Туреччина",
)


def e(s: str) -> str:
    return html.escape(s, quote=True)


def sup(text: str) -> str:
    for i in range(1, 7):
        text = text.replace("{r%d}" % i, f'<sup><a href="#ref{i}">{i}</a></sup>')
    return text


def strip_sup(text: str) -> str:
    import re
    return re.sub(r"\{r\d\}", "", text)


def render(lang: str, c: dict) -> str:
    url = f"{BASE}/{c['file']}"
    rtl = c["dir"] == "rtl"
    font_link = ("https://fonts.googleapis.com/css2?family=Noto+Sans+Arabic:wght@300..800&display=swap" if rtl
                 else "https://fonts.googleapis.com/css2?family=Inter:wght@300..900&display=swap")
    font_family = "'Noto Sans Arabic'" if rtl else "'Inter'"
    refs = REFS + [c["local_ref"]]
    nav_hrefs = [c["home"], "/" + c["blog"]] + (["/" + c["faq_page"]] if c.get("faq_page") else [])
    nav = "\n".join(f'        <a href="{h}">{e(t)}</a>' for h, t in zip(nav_hrefs, c["nav"]))
    app_ld = {
        "@context": "https://schema.org", "@type": "WebApplication", "name": c["app_name"],
        "description": c["app_desc"], "url": url, "applicationCategory": "HealthApplication",
        "operatingSystem": "Web", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "author": {"@type": "Organization", "@id": f"{BASE}/#organization", "name": "Suu", "url": BASE},
        "inLanguage": lang,
    }
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": lang,
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in c["faq"]]}
    acts = "\n".join(
        f'                <button class="activity-btn" id="act_{k}" onclick="selectActivity(\'{k}\')"><span class="act-icon">{ACT_ICON[k]}</span><span class="act-label">{e(c["acts"][k][0])}</span><span class="act-desc">{e(c["acts"][k][1])}</span></button>'
        for k in ACT_KEYS)
    act_rows = "\n".join(
        f'                <tr><td><strong>{e(c["acts"][k][0])}</strong> — {e(c["acts"][k][1])}</td><td>{str(ACT_MULT[k]).replace(".", "," if lang not in ("en", "ar") else ".")}</td></tr>'
        for k in ACT_KEYS)
    plans = "\n".join(
        f'                    <div class="plan" id="plan{i}"><div class="plan-head"><span class="plan-name">{e(n)}</span><span class="plan-def">{e(d)}</span></div><div class="plan-kcal"><span id="t{i}">—</span> <small>{e(c["kcal"])}</small></div><div class="plan-week" id="w{i}"></div><div class="plan-note" id="n{i}"></div></div>'
        for i, (n, d) in enumerate(c["plans"]))
    how = "\n".join(f"        <p>{sup(p)}</p>" for p in c["how_p"])
    safe = "\n".join(f"            <li>{sup(x)}</li>" for x in c["safe_items"])
    faqs = "\n".join(
        f'            <div class="faq-item"><div class="faq-q" onclick="toggleFaq(this)">{e(q)} <i class="fas fa-chevron-down faq-icon"></i></div><div class="faq-a">{e(a)}</div></div>'
        for q, a in c["faq"])
    refs_html = "\n".join(f'            <li id="ref{i}"><a href="{h}" target="_blank" rel="noopener">{e(t)}</a></li>' for i, (t, h) in enumerate(refs, 1))
    related = "\n".join(
        f'            <a class="rel-card" href="{h}"><div class="rel-tag">{e(tag)}</div><div class="rel-title">{e(t)}</div></a>'
        for tag, h, t in c["related"])
    js_strings = json.dumps({
        "err_age": c["err_age"], "err_weight": c["err_weight"], "err_height": c["err_height"],
        "err_sex": c["err_sex"], "err_act": c["err_act"], "week": c["week"], "floor": c["floor_note"],
        "low": c["low_note"], "num": c["num"],
    }, ensure_ascii=False)
    mult_js = json.dumps(ACT_MULT)
    side = "right" if rtl else "left"

    return f"""<!DOCTYPE html>
<!-- {GENERATED} -->
<html lang="{lang}" dir="{c['dir']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>{e(c['title'])}</title>
    <meta name="description" content="{e(c['desc'])}">
    <meta name="keywords" content="{e(c['keywords'])}">

    <link rel="canonical" href="{url}">

    <link rel="alternate" type="text/plain" href="{c['llms']}" title="Suu — compact reference for AI assistants">
    <link rel="alternate" type="text/plain" href="{c['llms_full']}" title="Suu — full reference corpus for AI assistants">

    <meta property="og:title" content="{e(c['og_title'])}">
    <meta property="og:description" content="{e(c['og_desc'])}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{BASE}/assets/og-image.png">
    <meta property="og:site_name" content="Suu">
    <meta property="og:locale" content="{c['locale']}">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{e(c['og_title'])}">
    <meta name="twitter:description" content="{e(c['og_desc'])}">
    <meta name="twitter:image" content="{BASE}/assets/og-image.png">

    <link rel="icon" href="/favicon.ico" sizes="any">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
    <script type="application/ld+json">
{json.dumps(app_ld, ensure_ascii=False, indent=2)}
    </script>
    <script type="application/ld+json">
{json.dumps(faq_ld, ensure_ascii=False, indent=2)}
    </script>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preconnect" href="https://cdnjs.cloudflare.com">
    <link href="{font_link}" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ overflow-x: hidden; }}
        body {{ font-family: {font_family}, -apple-system, sans-serif; color: #222; background: #fff8f0; line-height: 1.7; }}
        .navbar {{ background: white; padding: 0 20px; height: 64px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 10px rgba(0,0,0,0.07); position: sticky; top: 0; z-index: 100; }}
        .nav-logo {{ display: flex; align-items: center; gap: 8px; font-size: 20px; font-weight: 800; color: #FB8C00; text-decoration: none; }}
        .nav-links {{ display: flex; gap: 20px; }}
        .nav-links a {{ color: #555; text-decoration: none; font-size: 14px; font-weight: 500; }}
        .nav-links a:hover {{ color: #FB8C00; }}
        .hero {{ background: linear-gradient(135deg, #F57C00 0%, #FB8C00 50%, #FFB74D 100%); color: white; padding: 56px 20px 90px; text-align: center; position: relative; overflow: hidden; }}
        .hero::after {{ content:''; position:absolute; bottom:-1px; left:0; right:0; height:60px; background:#fff8f0; clip-path:ellipse(55% 100% at 50% 100%); }}
        .hero-badge {{ display:inline-block; background:rgba(255,255,255,0.2); padding:5px 16px; border-radius:20px; font-size:12px; font-weight:700; margin-bottom:18px; }}
        .hero h1 {{ font-size:clamp(1.8rem,4vw,2.8rem); font-weight:800; line-height:1.2; max-width:680px; margin:0 auto 14px; }}
        .hero p {{ font-size:1.05rem; opacity:0.95; max-width:540px; margin:0 auto; }}
        .container {{ max-width:900px; margin:0 auto; padding:0 20px; }}
        .section {{ padding:44px 0; }}
        .section-title {{ font-size:clamp(1.3rem,3vw,1.8rem); font-weight:800; color:#1a1a2e; margin-bottom:14px; }}
        .section p, .section li {{ color:#444; margin-bottom:12px; }}
        .section ul {{ padding-{side}:22px; }}
        sup a {{ color:#F57C00; text-decoration:none; font-weight:700; }}
        .calc-card {{ background:white; border-radius:24px; box-shadow:0 8px 40px rgba(245,124,0,0.12); padding:32px; margin:-40px 0 30px; position:relative; z-index:10; }}
        @media(max-width:600px){{ .calc-card{{ padding:22px; }} }}
        .calc-steps {{ display:flex; gap:8px; margin-bottom:26px; }}
        .step-dot {{ flex:1; height:4px; border-radius:4px; background:#e5e7eb; transition:background 0.3s; }}
        .step-dot.active {{ background:#FB8C00; }}
        .step-dot.done {{ background:#FFB74D; }}
        .form-step {{ display:none; }}
        .form-step.active {{ display:block; }}
        .step-title {{ font-size:1.1rem; font-weight:700; color:#1a1a2e; margin-bottom:20px; }}
        .form-grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-bottom:18px; }}
        @media(max-width:600px){{ .form-grid{{ grid-template-columns:1fr; }} }}
        .form-group label {{ display:block; font-size:12px; font-weight:700; color:#888; text-transform:uppercase; letter-spacing:0.4px; margin-bottom:8px; }}
        .form-group input {{ width:100%; padding:12px 16px; border:2px solid #e5e7eb; border-radius:12px; font-size:1rem; font-family:inherit; color:#222; background:white; }}
        .form-group input:focus {{ outline:none; border-color:#FB8C00; }}
        .gender-row {{ display:flex; gap:12px; }}
        .gender-btn {{ flex:1; padding:12px; border:2px solid #e5e7eb; border-radius:12px; background:white; cursor:pointer; font-family:inherit; font-weight:600; color:#555; font-size:0.9rem; }}
        .gender-btn.selected {{ border-color:#FB8C00; background:#fff3e0; color:#E65100; }}
        .activity-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:18px; }}
        .activity-btn {{ padding:12px 10px; border:2px solid #e5e7eb; border-radius:12px; background:white; cursor:pointer; font-family:inherit; text-align:center; }}
        .activity-btn .act-icon {{ font-size:1.4rem; display:block; margin-bottom:6px; }}
        .activity-btn .act-label {{ display:block; font-size:12px; font-weight:700; color:#555; }}
        .activity-btn .act-desc {{ display:block; font-size:10px; color:#999; }}
        .activity-btn.selected {{ border-color:#FB8C00; background:#fff3e0; }}
        .btn-row {{ display:flex; gap:12px; margin-top:8px; }}
        .btn-back {{ padding:14px 22px; border:2px solid #e5e7eb; border-radius:12px; background:white; font-family:inherit; font-weight:700; color:#555; cursor:pointer; }}
        .btn-next {{ flex:1; padding:14px; border:none; border-radius:12px; background:linear-gradient(135deg,#F57C00,#FFB74D); color:white; font-family:inherit; font-weight:700; font-size:1rem; cursor:pointer; }}
        .error-msg {{ background:#fef2f2; border-{side}:4px solid #ef4444; padding:10px 14px; border-radius:8px; font-size:0.88rem; color:#dc2626; margin-bottom:14px; display:none; }}
        .error-msg.show {{ display:block; }}
        .result-top {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:22px; }}
        @media(max-width:600px){{ .result-top{{ grid-template-columns:1fr; }} }}
        .stat {{ background:#fff3e0; border-radius:14px; padding:16px; text-align:center; }}
        .stat-num {{ font-size:1.9rem; font-weight:800; color:#E65100; line-height:1.1; }}
        .stat-label {{ font-size:12px; color:#8a6d55; font-weight:600; }}
        .targets-title {{ font-weight:800; color:#1a1a2e; margin:6px 0 12px; }}
        .plans {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; }}
        @media(max-width:700px){{ .plans{{ grid-template-columns:1fr; }} }}
        .plan {{ border:2px solid #f0e2d0; border-radius:14px; padding:14px; }}
        .plan#plan1 {{ border-color:#FB8C00; background:#fffaf3; }}
        .plan-head {{ display:flex; justify-content:space-between; gap:8px; font-size:12px; font-weight:700; color:#8a6d55; }}
        .plan-kcal {{ font-size:1.5rem; font-weight:800; color:#1a1a2e; margin:6px 0 2px; }}
        .plan-kcal small {{ font-size:0.75rem; color:#888; font-weight:600; }}
        .plan-week {{ font-size:0.85rem; color:#E65100; font-weight:700; }}
        .plan-note {{ font-size:0.75rem; color:#999; margin-top:6px; }}
        .result-msg {{ background:#fff3e0; border-radius:12px; padding:14px 16px; font-size:0.88rem; color:#8a4b00; margin:18px 0; }}
        .low-msg {{ background:#fef2f2; color:#b91c1c; }}
        .app-cta {{ background:linear-gradient(135deg,#F57C00,#FFB74D); border-radius:20px; padding:26px; text-align:center; color:white; margin:18px 0; }}
        .app-cta h3 {{ font-size:1.2rem; font-weight:800; margin-bottom:8px; }}
        .app-cta p {{ opacity:0.95; margin-bottom:16px; font-size:0.9rem; }}
        .store-btns {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }}
        .btn-store {{ display:inline-flex; align-items:center; gap:8px; padding:11px 20px; border-radius:50px; font-weight:700; font-size:0.88rem; text-decoration:none; }}
        .btn-ios {{ background:white; color:#1a1a2e; }}
        .btn-android {{ background:rgba(255,255,255,0.18); color:white; border:2px solid rgba(255,255,255,0.6); }}
        .restart-btn {{ display:inline-flex; align-items:center; gap:8px; padding:12px 22px; border:2px solid #e5e7eb; border-radius:12px; background:white; font-family:inherit; font-weight:600; color:#555; cursor:pointer; }}
        .ref-table {{ width:100%; border-collapse:collapse; background:white; border-radius:14px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.05); margin-top:6px; }}
        .ref-table th {{ background:#1a1a2e; color:white; padding:12px 16px; text-align:start; font-size:12px; font-weight:700; text-transform:uppercase; }}
        .ref-table td {{ padding:11px 16px; font-size:0.9rem; border-bottom:1px solid #f0f0f0; }}
        .faq-list {{ display:flex; flex-direction:column; gap:10px; }}
        .faq-item {{ background:white; border-radius:14px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.04); }}
        .faq-q {{ padding:16px 20px; font-weight:700; color:#1a1a2e; cursor:pointer; display:flex; justify-content:space-between; gap:12px; align-items:center; font-size:0.95rem; }}
        .faq-a {{ padding:0 20px; max-height:0; overflow:hidden; transition:max-height 0.3s ease, padding 0.3s; font-size:0.9rem; color:#555; }}
        .faq-a.open {{ max-height:400px; padding:0 20px 16px; }}
        .faq-icon {{ transition:transform 0.3s; color:#FB8C00; font-size:0.85rem; }}
        .faq-icon.open {{ transform:rotate(180deg); }}
        .refs {{ font-size:0.85rem; padding-{side}:20px; }}
        .refs a {{ color:#8a4b00; word-break:break-word; }}
        .rel-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; }}
        .rel-card {{ background:white; border-radius:14px; padding:18px; box-shadow:0 2px 10px rgba(0,0,0,0.06); text-decoration:none; color:inherit; display:block; }}
        .rel-tag {{ font-size:11px; font-weight:700; color:#F57C00; text-transform:uppercase; margin-bottom:6px; }}
        .rel-title {{ font-weight:700; color:#222; font-size:0.9rem; }}
        .disclaimer {{ font-size:0.82rem; color:#999; margin-top:14px; }}
        footer {{ background:#1a1a2e; color:rgba(255,255,255,0.6); padding:24px 20px; text-align:center; font-size:13px; }}
        footer a {{ color:rgba(255,255,255,0.75); text-decoration:none; margin:0 8px; }}
        @media(max-width:600px){{ .nav-links {{ display:none; }} }}
    </style>
    <script src="/assets/js/analytics.js" defer></script>
    <script src="/assets/js/special-days.js" defer></script>
</head>
<body>

<nav class="navbar">
    <a href="{c['home']}" class="nav-logo"><img src="/assets/brand/suu-badge-128.png" alt="Suu" width="128" height="128" class="suu-logo-badge" style="height:1.6em;width:1.6em;border-radius:50%;vertical-align:-0.4em;box-shadow:0 0 0 1px rgba(255,255,255,.12),0 0 14px rgba(94,170,255,.45);"> Suu</a>
    <div class="nav-links">
{nav}
    </div>
</nav>

<section class="hero">
    <div class="hero-badge">{e(c['badge'])}</div>
    <h1>{c['h1']}</h1>
    <p>{e(c['sub'])}</p>
</section>

<div class="container">
    <div class="calc-card">
        <div class="calc-steps">
            <div class="step-dot active" id="dot1"></div>
            <div class="step-dot" id="dot2"></div>
            <div class="step-dot" id="dot3"></div>
        </div>
        <div class="error-msg" id="errorMsg" role="alert"></div>

        <div class="form-step active" id="step1">
            <div class="step-title">{e(c['s1'])}</div>
            <div class="form-grid">
                <div class="form-group"><label for="age">{e(c['age'])}</label><input type="number" id="age" inputmode="numeric" placeholder="{e(c['ph_age'])}" min="18" max="80"></div>
                <div class="form-group"><label for="weight">{e(c['weight'])}</label><input type="number" id="weight" inputmode="decimal" placeholder="{e(c['ph_weight'])}" min="35" max="250"></div>
                <div class="form-group"><label for="height">{e(c['height'])}</label><input type="number" id="height" inputmode="numeric" placeholder="{e(c['ph_height'])}" min="130" max="220"></div>
            </div>
            <div class="form-group" style="margin-bottom:18px;">
                <label>{e(c['sex'])}</label>
                <div class="gender-row">
                    <button class="gender-btn" id="btnMale" onclick="selectSex('male')">{e(c['male'])}</button>
                    <button class="gender-btn" id="btnFemale" onclick="selectSex('female')">{e(c['female'])}</button>
                </div>
            </div>
            <div class="btn-row"><button class="btn-next" onclick="goStep2()">{e(c['next'])}</button></div>
        </div>

        <div class="form-step" id="step2">
            <div class="step-title">{e(c['s2'])}</div>
            <div class="activity-grid">
{acts}
            </div>
            <div class="btn-row">
                <button class="btn-back" onclick="goStep1()">{e(c['back'])}</button>
                <button class="btn-next" onclick="calculate()"><i class="fas fa-calculator"></i> &nbsp;{e(c['calc'])}</button>
            </div>
        </div>

        <div class="form-step" id="step3">
            <div class="result-top">
                <div class="stat"><div class="stat-num" id="tdeeNum">—</div><div class="stat-label">{e(c['tdee'])} · {e(c['kcal'])}</div></div>
                <div class="stat"><div class="stat-num" id="bmrNum">—</div><div class="stat-label">{e(c['bmr'])} · {e(c['kcal'])}</div></div>
            </div>
            <div class="targets-title">{e(c['targets'])}</div>
            <div class="plans">
{plans}
            </div>
            <div class="result-msg" id="resultMsg">{e(c['adapt'])}</div>
            <div class="app-cta">
                <h3>{e(c['cta_h'])}</h3>
                <p>{e(c['cta_p'])}</p>
                <div class="store-btns">
                    <a href="/app?src=calc-deficit" class="btn-store btn-ios" data-cta="calc-deficit"><i class="fab fa-apple"></i> App Store</a>
                    <a href="/app?src=calc-deficit" class="btn-store btn-android" data-cta="calc-deficit"><i class="fab fa-google-play"></i> Google Play</a>
                </div>
            </div>
            <button class="restart-btn" onclick="restart()"><i class="fas fa-redo"></i> {e(c['recalc'])}</button>
        </div>
    </div>

    <section class="section">
        <h2 class="section-title">{e(c['how_h'])}</h2>
{how}
        <table class="ref-table">
            <thead><tr><th>{e(c['act_table'][0])}</th><th>{e(c['act_table'][1])}</th></tr></thead>
            <tbody>
{act_rows}
            </tbody>
        </table>
    </section>

    <section class="section" style="padding-top:0">
        <h2 class="section-title">{e(c['safe_h'])}</h2>
        <ul>
{safe}
        </ul>
    </section>

    <section class="section" style="padding-top:0">
        <h2 class="section-title">{e(c['faq_h'])}</h2>
        <div class="faq-list">
{faqs}
        </div>
        <p class="disclaimer">{e(c['disclaimer'])}</p>
    </section>

    <section class="section" style="padding-top:0">
        <h2 class="section-title">{e(c['refs_h'])}</h2>
        <ol class="refs">
{refs_html}
        </ol>
    </section>

    <section class="section" style="padding-top:0; padding-bottom:48px;">
        <h2 class="section-title">{e(c['rel_h'])}</h2>
        <div class="rel-grid">
{related}
        </div>
    </section>
</div>

<footer>
    <p>© 2026 Suu &nbsp;|&nbsp;
        <a href="{c['home']}">{e(c['footer_home'])}</a>
        <a href="/gizlilik-politikasi.html">{e(c['footer_priv'])}</a>
    </p>
    <p style="margin-top:6px;font-size:11px;opacity:0.6;">{e(c['dev'])} <a href="https://www.linkedin.com/in/furkanfindikli/" target="_blank" rel="noopener">Furkan Mert Fındıklı</a> — {e(c['city'])}</p>
</footer>

<script>
const S = {js_strings};
const MULT = {mult_js};
let sex = null, activity = null;
function fmt(n) {{ return Math.round(n).toLocaleString(S.num); }}
function fmt1(n) {{ return (Math.round(n * 100) / 100).toLocaleString(S.num, {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}); }}
function showError(msg) {{
    const el = document.getElementById('errorMsg');
    el.textContent = msg; el.classList.add('show');
    setTimeout(() => el.classList.remove('show'), 3500);
}}
function selectSex(s) {{
    sex = s;
    document.getElementById('btnMale').classList.toggle('selected', s === 'male');
    document.getElementById('btnFemale').classList.toggle('selected', s === 'female');
}}
function selectActivity(a) {{
    activity = a;
    Object.keys(MULT).forEach(k => document.getElementById('act_' + k).classList.toggle('selected', k === a));
}}
function val(id) {{ return parseFloat(String(document.getElementById(id).value).replace(',', '.')); }}
function goStep1() {{
    document.getElementById('step2').classList.remove('active');
    document.getElementById('step1').classList.add('active');
    document.getElementById('dot2').classList.remove('active', 'done');
    document.getElementById('dot1').classList.add('active');
}}
function goStep2() {{
    const age = val('age'), weight = val('weight'), height = val('height');
    if (!age || age < 18 || age > 80) {{ showError(S.err_age); return; }}
    if (!weight || weight < 35 || weight > 250) {{ showError(S.err_weight); return; }}
    if (!height || height < 130 || height > 220) {{ showError(S.err_height); return; }}
    if (!sex) {{ showError(S.err_sex); return; }}
    document.getElementById('step1').classList.remove('active');
    document.getElementById('step2').classList.add('active');
    document.getElementById('dot1').classList.remove('active');
    document.getElementById('dot1').classList.add('done');
    document.getElementById('dot2').classList.add('active');
}}
function calculate() {{
    if (!activity) {{ showError(S.err_act); return; }}
    const age = val('age'), weight = val('weight'), height = val('height');
    // Mifflin-St Jeor (1990)
    const bmr = 10 * weight + 6.25 * height - 5 * age + (sex === 'male' ? 5 : -161);
    const tdee = bmr * MULT[activity];
    const floor = sex === 'male' ? 1500 : 1200;   // Harvard Health: uzman gözetimi olmadan alt sınır
    document.getElementById('bmrNum').textContent = fmt(bmr);
    document.getElementById('tdeeNum').textContent = fmt(tdee);
    const msg = document.getElementById('resultMsg');
    const low = tdee <= floor;
    [250, 500, 750].forEach((d, i) => {{
        let target = tdee - d, note = '';
        if (target < floor) {{ target = Math.min(floor, tdee); note = S.floor.replace('{{f}}', fmt(floor)); }}
        const eff = Math.max(0, tdee - target);
        document.getElementById('t' + i).textContent = fmt(target);
        document.getElementById('w' + i).textContent = eff > 0 ? S.week.replace('{{v}}', fmt1(eff * 7 / 7700)) : '';
        document.getElementById('n' + i).textContent = note;
    }});
    if (low) {{ msg.textContent = S.low.replace('{{f}}', fmt(floor)); msg.classList.add('low-msg'); }}
    else {{ msg.classList.remove('low-msg'); }}
    document.getElementById('step2').classList.remove('active');
    document.getElementById('step3').classList.add('active');
    document.getElementById('dot2').classList.remove('active');
    document.getElementById('dot2').classList.add('done');
    document.getElementById('dot3').classList.add('active', 'done');
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}
function restart() {{
    sex = null; activity = null;
    ['age', 'weight', 'height'].forEach(id => document.getElementById(id).value = '');
    ['btnMale', 'btnFemale'].forEach(id => document.getElementById(id).classList.remove('selected'));
    Object.keys(MULT).forEach(k => document.getElementById('act_' + k).classList.remove('selected'));
    document.getElementById('step3').classList.remove('active');
    document.getElementById('step1').classList.add('active');
    document.getElementById('dot1').classList.add('active');
    document.getElementById('dot1').classList.remove('done');
    ['dot2', 'dot3'].forEach(id => document.getElementById(id).classList.remove('active', 'done'));
    document.getElementById('resultMsg').classList.remove('low-msg');
}}
function toggleFaq(el) {{
    el.nextElementSibling.classList.toggle('open');
    el.querySelector('.faq-icon').classList.toggle('open');
}}
</script>
<script src="/lang-switcher.js?v=3" defer></script>
<script src="/assets/js/suu-badge.js?v=2" defer></script>
</body>
</html>
"""


def main() -> int:
    apply = "--apply" in sys.argv
    changed = 0
    for lang, c in L.items():
        out = render(lang, c)
        path = ROOT / c["file"]
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old is not None and "<!-- Hreflang cluster (auto-injected) -->" in old:
            # inject-hreflang.py'nin eklediği bloğu koru (yoksa her build onu düşürür)
            import re
            m = re.search(r"\n    <!-- Hreflang cluster \(auto-injected\) -->\n(?:    <link rel=\"alternate\" hreflang=[^\n]+\n)+", old)
            if m:
                out = out.replace(f'    <link rel="canonical" href="{BASE}/{c["file"]}">\n',
                                  f'    <link rel="canonical" href="{BASE}/{c["file"]}">\n' + m.group(0).lstrip("\n") + "\n", 1)
        status = "yeni" if old is None else ("güncel" if old == out else "değişecek")
        print(f"  {c['file']:<40} {status}")
        if old != out:
            changed += 1
            if apply:
                path.write_text(out, encoding="utf-8")
    print(f"\n{changed} sayfa {'yazıldı' if apply else 'değişecek — ÖNİZLEME'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
