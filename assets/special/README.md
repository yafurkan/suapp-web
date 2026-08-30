# Özel gün görselleri

`assets/js/special-days.js` içindeki her özel günün `gorsel` alanı buradaki bir
dosyayı işaret eder. Dosya **yoksa** kutlama görselsiz, yalnızca bayrakla
kurulur — kırık görsel hiçbir zaman çıkmaz (script görseli önce `new Image()`
ile dener, ancak yüklenirse DOM'a koyar).

## Dosyalar

| Dosya | Kullanan gün |
|---|---|
| `ataturk.jpg` | 30 Ağustos, 29 Ekim, 19 Mayıs, 23 Nisan |

## Nasıl yerleştirilir

Görsel **kendi en/boy oranında** çerçevelenir; sabit bir orana kırpılmaz. Bayrak
alt kenarına binen bir mühür gibi durur, o yüzden alt orta bölgede kritik bir
ayrıntı olmaması iyi olur.

Yüksekliği alçak pencerelerde `min(46vh, 430px)` ile sınırlanır; taşma olursa
`object-position: 50% 58%` ile üstten kırpılır — yani asıl özne kadrajın orta-alt
bandındaysa kadrajda kalır.

Genişlik en fazla 356 CSS px görüntülenir; retina için ~700 px genişlik yeterli,
daha büyüğü boşuna bayt.

**Telif:** buraya yalnızca kullanım hakkına sahip olduğunuz bir görsel koyun.
