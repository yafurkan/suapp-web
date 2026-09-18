#!/usr/bin/env python3
"""
Suu — Varlık ayrımı (entity disambiguation) alanlarını şemaya ekler.

Neden var: "suu" aramasında Southern Utah University (SUU) çıkıyor; bizim
uygulamayı onun önüne geçirmek ne mümkün ne de mantıklı (navigasyonel sorgu).
Doğru hedef, Google ve LLM'lerin "Suu (uygulama)" ile "SUU (üniversite)"yi iki
AYRI varlık olarak tutması. schema.org'un `disambiguatingDescription` alanı tam
olarak bunun için var.

Nereye yazar: yalnızca varlığın ASIL tanımlandığı sayfalar — Organization
düğümünde sameAs taşıyan 9 sayfa. Blog yazılarındaki publisher kısayolları
aynı @id'yi işaret ettiği için oralara kopyalamak gürültüden ibaret olurdu.

Kullanım:
    python3 scripts/enrich-entity-disambiguation.py            # önizleme
    python3 scripts/enrich-entity-disambiguation.py --apply
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGES = {
    "index.html": "tr",
    "hosgeldiniz-en.html": "en",
    "hosgeldiniz-ar.html": "ar",
    "hosgeldiniz-de.html": "de",
    "hosgeldiniz-it.html": "it",
    "hosgeldiniz-ru.html": "ru",
    "hosgeldiniz-uk.html": "uk",
    "hosgeldiniz-hi.html": "hi",
    "suu-for-claude.html": "en",
}

ORG_ID = "https://suuapp.com/#organization"
APP_IDS = ("https://suuapp.com/#suuapp-ios", "https://suuapp.com/#suuapp-android")

UPTODOWN = "https://com-sutakip-suutakippro.en.uptodown.com/android"

ORG_ALT = ["Suu App", "Suu Takip", "suuapp.com"]
APP_ALT = ["Suu App", "Suu Water Tracker", "Suu Calorie Counter", "Suu Su Takibi"]

TEXT = {
    "tr": {
        "org_desc": "Suu; su takibi, fotoğraftan kalori sayımı ve GPS'li egzersiz takibini yapay zekâyla tek uygulamada birleştiren bağımsız bir mobil uygulama geliştiricisidir.",
        "org_disamb": "Suu, iOS ve Android için bir mobil sağlık uygulamasıdır; adı Türkçedeki \"su\" kelimesinden gelir. Bir üniversite veya eğitim kurumu değildir ve Southern Utah University (SUU) ile hiçbir bağı yoktur.",
        "app_disamb": "Su, kalori ve egzersiz takibi yapan bir mobil sağlık uygulaması. Southern Utah University'nin SUU adlı öğrenci uygulamasından farklı, bağımsız bir uygulamadır.",
    },
    "en": {
        "org_desc": "Suu is an independent mobile app developer. Its app combines water tracking, photo-based calorie counting and GPS exercise tracking with AI in a single app.",
        "org_disamb": "Suu is a mobile health app for iOS and Android; the name means \"water\" in Turkish. It is not a university or an educational institution and is not affiliated with Southern Utah University (SUU).",
        "app_disamb": "A mobile health app for water, calorie and exercise tracking. It is a different, independent app from the SUU student app published by Southern Utah University.",
    },
    "ar": {
        "org_desc": "Suu مطوّر تطبيقات مستقل؛ يجمع تطبيقه بين تتبع الماء وحساب السعرات من الصورة وتتبع التمارين عبر GPS بالذكاء الاصطناعي في تطبيق واحد.",
        "org_disamb": "Suu تطبيق صحي للهواتف على iOS وAndroid، واسمه يعني \"الماء\" بالتركية. ليس جامعة ولا مؤسسة تعليمية، ولا صلة له بجامعة Southern Utah University (SUU).",
        "app_disamb": "تطبيق صحي لتتبع الماء والسعرات والتمارين. وهو تطبيق مستقل ومختلف عن تطبيق الطلاب SUU الصادر عن Southern Utah University.",
    },
    "de": {
        "org_desc": "Suu ist ein unabhängiger Mobile-App-Entwickler. Die App verbindet Wasser-Tracking, Kalorienzählung per Foto und GPS-Trainingsaufzeichnung mit KI in einer einzigen App.",
        "org_disamb": "Suu ist eine mobile Gesundheits-App für iOS und Android; der Name bedeutet auf Türkisch \"Wasser\". Es handelt sich nicht um eine Universität oder Bildungseinrichtung und es besteht keine Verbindung zur Southern Utah University (SUU).",
        "app_disamb": "Eine mobile Gesundheits-App für Wasser-, Kalorien- und Trainings-Tracking. Sie ist eine eigenständige App und nicht die SUU-Studierenden-App der Southern Utah University.",
    },
    "it": {
        "org_desc": "Suu è uno sviluppatore indipendente di app mobili. La sua app unisce monitoraggio dell'acqua, conteggio delle calorie da foto e tracciamento GPS degli allenamenti con l'AI in un'unica app.",
        "org_disamb": "Suu è un'app mobile per la salute su iOS e Android; il nome significa \"acqua\" in turco. Non è un'università né un istituto scolastico e non ha alcun legame con la Southern Utah University (SUU).",
        "app_disamb": "Un'app mobile per monitorare acqua, calorie ed esercizio fisico. È un'app indipendente, diversa dall'app per studenti SUU pubblicata dalla Southern Utah University.",
    },
    "ru": {
        "org_desc": "Suu — независимый разработчик мобильных приложений. Его приложение объединяет учёт воды, подсчёт калорий по фото и GPS-трекинг тренировок с ИИ в одном приложении.",
        "org_disamb": "Suu — мобильное приложение для здоровья на iOS и Android; название означает «вода» по-турецки. Это не университет и не учебное заведение, и оно никак не связано с Southern Utah University (SUU).",
        "app_disamb": "Мобильное приложение для учёта воды, калорий и тренировок. Это самостоятельное приложение, отличное от студенческого приложения SUU от Southern Utah University.",
    },
    "uk": {
        "org_desc": "Suu — незалежний розробник мобільних застосунків. Його застосунок поєднує облік води, підрахунок калорій за фото та GPS-трекінг тренувань зі штучним інтелектом в одному застосунку.",
        "org_disamb": "Suu — мобільний застосунок для здоров'я на iOS та Android; назва означає «вода» турецькою. Це не університет і не навчальний заклад, і він не пов'язаний із Southern Utah University (SUU).",
        "app_disamb": "Мобільний застосунок для обліку води, калорій і тренувань. Це самостійний застосунок, відмінний від студентського застосунку SUU від Southern Utah University.",
    },
    "hi": {
        "org_desc": "Suu एक स्वतंत्र मोबाइल ऐप डेवलपर है। इसका ऐप पानी ट्रैकिंग, फ़ोटो से कैलोरी गिनती और GPS एक्सरसाइज़ ट्रैकिंग को AI के साथ एक ही ऐप में जोड़ता है।",
        "org_disamb": "Suu iOS और Android के लिए एक मोबाइल हेल्थ ऐप है; इस नाम का तुर्की में अर्थ \"पानी\" है। यह कोई विश्वविद्यालय या शैक्षिक संस्थान नहीं है और Southern Utah University (SUU) से इसका कोई संबंध नहीं है।",
        "app_disamb": "पानी, कैलोरी और एक्सरसाइज़ ट्रैकिंग के लिए एक मोबाइल हेल्थ ऐप। यह Southern Utah University के SUU छात्र ऐप से अलग, एक स्वतंत्र ऐप है।",
    },
}


def json_line(indent: str, key: str, value) -> str:
    """Şemanın kendi girintisine uyan tek satırlık JSON alanı."""
    return f'{indent}"{key}": {json.dumps(value, ensure_ascii=False)},'


def insert_after_name(text: str, node_id: str, additions: dict) -> tuple[str, int]:
    """node_id'li düğümdeki "name" satırının ardına alanları ekler.

    İki tuzak var, ikisi de kontrol ediliyor:
    1) Aynı @id sayfada REFERANS olarak da geçer ({"@id": ...} tek başına,
       örneğin publisher). Tanım düğümlerinde @id'den hemen önceki satır
       "@type" taşır; referanslarda taşımaz.
    2) Düğümün kendi "name" satırı aranırken girinti düşerse düğümden
       çıkılmış demektir — arama orada durur, komşu düğüme yazılmaz.
    """
    lines = text.split("\n")
    id_needle = f'"@id": "{node_id}"'
    added = 0
    i = 0
    while i < len(lines):
        if id_needle not in lines[i]:
            i += 1
            continue
        indent = re.match(r"\s*", lines[i]).group(0)
        # @type çok satırlı bir dizi olabilir ( ["MobileApplication", ...] ),
        # o yüzden yalnız bir önceki satıra değil, düğümün başına kadar bak.
        is_definition = False
        for k in range(i - 1, max(-1, i - 9), -1):
            line = lines[k]
            if not line.strip():
                continue
            cur = re.match(r"\s*", line).group(0)
            if len(cur) < len(indent):  # düğümün açılış satırına çıktık
                break
            if len(cur) == len(indent) and line.strip().startswith('"@type"'):
                is_definition = True
                break
        if not is_definition:  # referans, tanım değil
            i += 1
            continue
        name_at = None
        for j in range(i + 1, len(lines)):
            line = lines[j]
            if not line.strip():
                continue
            cur = re.match(r"\s*", line).group(0)
            if len(cur) < len(indent):  # düğüm bitti
                break
            if len(cur) == len(indent) and line.strip().startswith('"name":'):
                name_at = j
                break
        if name_at is None:
            i += 1
            continue
        node_text = "\n".join(lines[i:name_at + 40])
        new_lines = [
            json_line(indent, key, value)
            for key, value in additions.items()
            if f'"{key}":' not in node_text
        ]
        if new_lines:
            lines[name_at + 1:name_at + 1] = new_lines
            added += len(new_lines)
            i = name_at + len(new_lines) + 1
        else:
            i += 1
    return "\n".join(lines), added


def add_sameas(text: str) -> tuple[str, int]:
    """Organization düğümündeki sameAs listesine Uptodown kaydını ekler."""
    if UPTODOWN in text:
        return text, 0
    org_idx = text.find(f'"@id": "{ORG_ID}"')
    if org_idx == -1:
        return text, 0
    m = re.compile(r'"sameAs":\s*\[(.*?)\]', re.S).search(text, org_idx)
    if not m:
        return text, 0
    body = m.group(1)
    last = re.search(r'^(\s*)"[^"]+"\s*$', body.rstrip().split("\n")[-1])
    indent = last.group(1) if last else "        "
    new_body = body.rstrip().rstrip(",") + f',\n{indent}"{UPTODOWN}"\n' + indent[:-2]
    text = text[:m.start(1)] + new_body + text[m.end(1):]
    return text, 1


def process(path: Path, lang: str) -> tuple[str, int]:
    text = original = path.read_text(encoding="utf-8")
    t = TEXT[lang]
    total = 0

    text, n = insert_after_name(text, ORG_ID, {
        "alternateName": ORG_ALT,
        "description": t["org_desc"],
        "disambiguatingDescription": t["org_disamb"],
    })
    total += n

    for app_id in APP_IDS:
        text, n = insert_after_name(text, app_id, {
            "alternateName": APP_ALT,
            "disambiguatingDescription": t["app_disamb"],
        })
        total += n

    text, n = add_sameas(text)
    total += n
    return (text if text != original else original), total


def validate(text: str, path: Path) -> None:
    """Dokunduğumuz her JSON-LD bloğu hâlâ geçerli JSON olmalı."""
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', text, re.S):
        try:
            json.loads(m.group(1))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"HATA: {path.name} içinde bozuk JSON-LD → {exc}")


def main() -> int:
    apply = "--apply" in sys.argv
    changed = 0
    for name, lang in PAGES.items():
        path = ROOT / name
        if not path.exists():
            print(f"atlandı (yok): {name}")
            continue
        new_text, n = process(path, lang)
        if n == 0:
            print(f"{name}: değişiklik yok (alanlar zaten var)")
            continue
        validate(new_text, path)
        print(f"{name} [{lang}]: +{n} alan")
        if apply:
            path.write_text(new_text, encoding="utf-8")
        changed += 1
    print(f"\n{changed} sayfa " + ("güncellendi" if apply else "güncellenecek — uygulamak için: --apply"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
