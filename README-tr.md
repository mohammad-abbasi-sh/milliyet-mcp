# milliyet-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/milliyet-mcp

**Milliyet** (www.milliyet.com.tr) için resmi olmayan, **salt okunur** MCP sunucusu — Türkiye'nin en büyük ulusal gazetelerinden biri (1950'den beri): **son dakika haberleri** (saatleriyle), **bölüm manşetleri**, **haberlerin tam metni**, **anahtar kelime araması** ve **bölüm listesi**.

> "Turkey MCP factory" projesinin bir parçasıdır. Milliyet ile bağlantısı yoktur. Veriler Milliyet'in herkese açık sayfalarından alınır — giriş gerekmez, API anahtarı gerekmez, salt okunur.

## Yapay zekâ ajanları için

- **Son dakika**: `milliyet_latest`, `/son-dakika-haberleri/` sayfasındaki en yeni haberleri döndürür (saat HH:MM Avrupa/İstanbul, bölüm, başlık, URL), en yeniden en eskiye.
- **Manşetler**: `milliyet_headlines` bir bölüm alır — `"gundem"` (varsayılan), `"ekonomi"`, `"dunya"`, `"skorer"`, `"magazin"`, `"teknoloji"`, `"egitim"`, `"kultur-sanat"`, `"pembenar"`, `"uzmanpara"` — ve bölüm başına ~40 manşet döndürür (başlık, URL, listede varsa özet, köşe yazılarında yazar).
- **Haber metni**: `milliyet_get_article` tam bir milliyet.com.tr URL'si alır ve başlık, yazar, yayın/güncelleme tarihleri, açıklama, görsel, anahtar kelimeler, kelime sayısı ve tam metni döndürür (sayfadaki NewsArticle JSON-LD bloğundan).
- **Arama**: `milliyet_search_news` son dakika sayfasını ve gündem, ekonomi, dünya, skorer, magazin listelerini anahtar kelimeyle tarar — `"deprem"`, `"dolar"` — Türkçe duyarlıdır (noktalı/noktasız I ayırt edilir, `"İSTANBUL"` `"İstanbul"` ile eşleşir).
- **Bölümler**: `milliyet_list_sections`, `milliyet_headlines` ile kullanılabilen bölümleri Türkçe adlarıyla döndürür.
- Her yanıt `fetched_at` (UTC) ve `source: milliyet.com.tr` taşır.

## Kurulum

```bash
uvx milliyet-mcp
```

Ya da MCP istemcinizin ayarlarına ekleyin (ör. Claude Desktop):

```json
{
  "mcpServers": {
    "milliyet": {
      "command": "uvx",
      "args": ["milliyet-mcp"]
    }
  }
}
```

## Araçlar

| Araç | Ne yapar |
| --- | --- |
| `milliyet_latest` | En yeni son dakika haberleri, saatleriyle, en yeniden |
| `milliyet_headlines` | Bir bölümün öne çıkan manşetleri |
| `milliyet_get_article` | Bir haberin tam metni (tam URL ile) |
| `milliyet_search_news` | Günün haberlerinde anahtar kelime araması |
| `milliyet_list_sections` | `milliyet_headlines` ile kullanılabilen haber bölümleri |
| `milliyet_health` | milliyet.com.tr şu an erişilebilir mi? |

## Örnek

Son dakika, 23 Kasım 2026:

```json
{ "count": 2,
  "articles": [
    { "time": "12:29", "section": "Gündem",
      "title": "Son dakika... Lodos hızını artıracak! Rüzgar fırtınaya dönüşecek: AKOM'dan İstanbul uyarısı",
      "url": "https://www.milliyet.com.tr/gundem/son-dakika-lodos-hizini-artiracak-ruzgar-firtinaya-donusecek-akomdan-istanbul-uyarisi-7706152" },
    { "time": "12:13", "section": "Gündem",
      "title": "Silahlı saldırıda hayatını kaybeden Hilal öğretmeni eşi anlattı! Telefonunu 10 gün sonra açtı, çıkan notlar yürek burktu",
      "url": "https://www.milliyet.com.tr/gundem/silahli-saldirida-hayatini-kaybeden-hilal-ogretmeni-esi-anlatti-telefonunu-10-gun-sonra-acti-cikan-notlar-yurek-burktu-7706088" } ] }
```

Bir haber, 23 Kasım 2026:

```json
{ "title": "12 ilde siber suç operasyonu! 5 günde 101 şüpheli yakalandı, 60 tutuklama",
  "author": "Kübra Çelepi",
  "date_published": "2026-11-23T11:57:00+03:00",
  "section": "Gündem", "word_count": 290,
  "keywords": ["siber suç", "operasyon", "tutuklama"],
  "body": "Bakanlığın sanal medya hesabından yapılan açıklamaya göre; Emniyet Genel Müdürlüğü Siber Suçlarla Mücadele Daire Başkanlığı, MASAK ve Cumhuriyet Başsavcılıkları koordinesinde düzenlenen operasyonlarda 101 şüpheli yakalandı. …" }
```

## Sınırlamalar

- Arama, **son dakika sayfası ile ana bölüm listelerinin taranmasıdır**, tam arşiv araması değildir: sitenin kendi araması (`/arama/`) robots.txt'de engellidir, çağrılabilecek bir arama API'si yoktur.
- Bölüm sayfalarında **sayfalama yoktur** (`/gundem/2/` 404 döner) — her biri ~40 haber taşır, yani `milliyet_headlines` yalnızca güncel sayfayı görür.
- **Video** (`/milliyet-tv/`) ve **galeri** (`/galeri/`, `/magazin/galeri/` ve `/pembenar/galeri/` dahil) sayfaları ile çocuk bölümü (`/cocuk/`) metin haber değildir ve listelerden çıkarılır; `milliyet_get_article` bunlarda hata döndürür.
- Haber metinleri sayfadaki NewsArticle JSON-LD bloğundan (`articleBody`, tek düz metin blok) alınır; JSON-LD yoksa HTML paragraflar yedek olarak kullanılır.
- Sitenin site haritası (`sitemap.xml`) bir HTML sayfasına yönlenir — kullanılabilir bir site haritası değildir.
- Aktarım Chrome TLS taklidi kullanır; istekler ~0,8 sn arayla yapılır.

## Geliştirme

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_news.py -v    # çevrimdışı, kayıtlı örnek sayfalar
.venv/bin/python -m pytest tests/test_live.py -v    # canlı, www.milliyet.com.tr'ye karşı
.venv/bin/python tests/smoke_live.py                # günlük CI kontrolü
```

## Lisans

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — kişisel ve ticari olmayan kullanım için ücretsizdir; ticari kullanım ayrı bir lisans gerektirir.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
