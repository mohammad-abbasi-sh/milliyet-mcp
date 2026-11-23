# milliyet-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/milliyet-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **میلیّت** (www.milliyet.com.tr) — یکی از بزرگ‌ترین روزنامه‌های ملی ترکیه (از ۱۹۵۰): **خبرهای فوری** (سون داکیکا، همراه با ساعت)، **تیترهای هر بخش**، **متن کامل خبرها**، **جست‌وجوی کلیدواژه** و **فهرست بخش‌ها**.

> بخشی از پروژهٔ «کارخانهٔ MCP ترکیه». وابسته به میلیّت نیست. داده‌ها از صفحه‌های عمومی خود سایت گرفته می‌شود — بدون ورود، بدون کلید API، فقط‌خواندنی.

## برای عامل‌های هوش مصنوعی

- **خبر فوری**: `milliyet_latest` تازه‌ترین خبرها را از صفحهٔ `/son-dakika-haberleri/` برمی‌گرداند (ساعت HH:MM به وقت استانبول، بخش، تیتر، نشانی)، از تازه‌ترین به قدیمی‌ترین.
- **تیترها**: `milliyet_headlines` یک بخش می‌گیرد — `"gundem"` (پیش‌فرض)، `"ekonomi"`، `"dunya"`، `"skorer"`، `"magazin"`، `"teknoloji"`، `"egitim"`، `"kultur-sanat"`، `"pembenar"`، `"uzmanpara"` — و برای هر بخش حدود ۴۰ تیتر برمی‌گرداند (تیتر، نشانی، خلاصه در صورت وجود، نویسنده برای ستون‌ها).
- **متن خبر**: `milliyet_get_article` نشانی کامل یک خبر میلیّت را می‌گیرد و تیتر، نویسنده، تاریخ انتشار/به‌روزرسانی، توضیح، تصویر، کلیدواژه‌ها، تعداد کلمات و متن کامل را برمی‌گرداند (از بلوک NewsArticle JSON-LD صفحه).
- **جست‌وجو**: `milliyet_search_news` صفحهٔ خبر فوری و فهرست‌های گوندم، اکونومی، دونیا، اسکورر و مگزین را با کلیدواژه می‌گردد — `"deprem"`، `"dolar"` — با حساسیت به ترکی (I نقطه‌دار/بی‌نقطه درست مدیریت می‌شود؛ `"İSTANBUL"` با `"İstanbul"` هم‌خوانی دارد).
- **بخش‌ها**: `milliyet_list_sections` بخش‌های قابل‌استفاده با `milliyet_headlines` را با نام ترکی برمی‌گرداند.
- هر پاسخ `fetched_at` (UTC) و `source: milliyet.com.tr` دارد.

## نصب

```bash
uvx milliyet-mcp
```

یا به تنظیمات کلاینت MCP خود اضافه کنید (مثلاً Claude Desktop):

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

## ابزارها

| ابزار | چه می‌کند |
| --- | --- |
| `milliyet_latest` | تازه‌ترین خبرهای فوری، با ساعت، از تازه‌ترین |
| `milliyet_headlines` | تیترهای برتر یک بخش |
| `milliyet_get_article` | متن کامل یک خبر (با نشانی کامل) |
| `milliyet_search_news` | جست‌وجوی کلیدواژه در خبرهای امروز |
| `milliyet_list_sections` | بخش‌های خبری قابل‌استفاده با `milliyet_headlines` |
| `milliyet_health` | آیا milliyet.com.tr در حال حاضر در دسترس است؟ |

## نمونه

خبر فوری، ۲۳ نوامبر ۲۰۲۶:

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

یک خبر، ۲۳ نوامبر ۲۰۲۶:

```json
{ "title": "12 ilde siber suç operasyonu! 5 günde 101 şüpheli yakalandı, 60 tutuklama",
  "author": "Kübra Çelepi",
  "date_published": "2026-11-23T11:57:00+03:00",
  "section": "Gündem", "word_count": 290,
  "keywords": ["siber suç", "operasyon", "tutuklama"],
  "body": "Bakanlığın sanal medya hesabından yapılan açıklamaya göre; Emniyet Genel Müdürlüğü Siber Suçlarla Mücadele Daire Başkanlığı, MASAK ve Cumhuriyet Başsavcılıkları koordinesinde düzenlenen operasyonlarda 101 şüpheli yakalandı. …" }
```

## محدودیت‌ها

- جست‌وجو **پویش صفحهٔ خبر فوری و فهرست‌های اصلی بخش‌ها**ست، نه جست‌وجوی کامل آرشیو: جست‌وجوی خود سایت (`/arama/`) در robots.txt مسدود است و API جست‌وجویی برای فراخوانی وجود ندارد.
- صفحه‌های بخش **صفحه‌بندی ندارند** (`/gundem/2/` خطای ۴۰۴ می‌دهد) — هر یک حدود ۴۰ خبر دارد، پس `milliyet_headlines` فقط صفحهٔ جاری را می‌بیند.
- صفحه‌های **ویدئو** (`/milliyet-tv/`) و **گالری** (`/galeri/`، شامل `/magazin/galeri/` و `/pembenar/galeri/`) و بخش کودکان (`/cocuk/`) خبر متنی نیستند و از فهرست‌ها حذف می‌شوند؛ `milliyet_get_article` برای آن‌ها خطا برمی‌گرداند.
- متن خبرها از بلوک NewsArticle JSON-LD صفحه (`articleBody`، یک بلوک متن ساده) گرفته می‌شود؛ اگر JSON-LD نباشد، پاراگراف‌های HTML به‌عنوان جایگزین استفاده می‌شوند.
- نقشهٔ سایت (`sitemap.xml`) به یک صفحهٔ HTML هدایت می‌شود — نقشهٔ سایت قابل‌استفاده‌ای نیست.
- انتقال با جعل TLS کروم انجام می‌شود؛ درخواست‌ها با فاصلهٔ حدود ۰٫۸ ثانیه فرستاده می‌شوند.

## توسعه

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_news.py -v    # آفلاین، با صفحه‌های ضبط‌شده
.venv/bin/python -m pytest tests/test_live.py -v    # زنده، در برابر www.milliyet.com.tr
.venv/bin/python tests/smoke_live.py                # بررسی روزانهٔ CI
```

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — برای استفادهٔ شخصی و غیرتجاری رایگان است؛ استفادهٔ تجاری به مجوز جداگانه نیاز دارد.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
