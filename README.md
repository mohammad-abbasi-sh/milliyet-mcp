# milliyet-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/milliyet-mcp

Unofficial **read-only** MCP server for **Milliyet** (www.milliyet.com.tr) — one of Türkiye's biggest national newspapers (founded 1950): **breaking news** (son dakika, with times), **headlines by section**, **full article text**, **keyword search**, and the **section list**.

> Part of the "Turkey MCP factory". Not affiliated with Milliyet. Data comes from Milliyet's own server-rendered pages — no login, no API key, read-only.

## For AI agents

- **Breaking news**: `milliyet_latest` returns the newest items from `/son-dakika-haberleri/` (time HH:MM Europe/Istanbul, section, title, URL), newest first.
- **Headlines**: `milliyet_headlines` takes a section — `"gundem"` (default), `"ekonomi"`, `"dunya"`, `"skorer"`, `"magazin"`, `"teknoloji"`, `"egitim"`, `"kultur-sanat"`, `"pembenar"`, `"uzmanpara"` — and returns ~40 headlines per section (title, URL, summary when the listing carries one, author for columnist pieces).
- **Article**: `milliyet_get_article` takes a full milliyet.com.tr URL and returns title, author, publish/modify dates, description, image, keywords, word count and the full body text (from the page's NewsArticle JSON-LD).
- **Search**: `milliyet_search_news` scans the breaking-news page plus the gundem, ekonomi, dunya, skorer and magazin listings by keyword — `"deprem"`, `"dolar"` — Turkish-aware (dotted/dotless I handled, so `"İSTANBUL"` matches `"İstanbul"`).
- **Sections**: `milliyet_list_sections` returns the sections usable with `milliyet_headlines`, with Turkish display names.
- Every response carries `fetched_at` (UTC) and `source: milliyet.com.tr`.

## Install

```bash
uvx milliyet-mcp
```

Or add to your MCP client config (e.g. Claude Desktop):

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

## Tools

| Tool | What it does |
| --- | --- |
| `milliyet_latest` | Latest breaking news (son dakika), newest first, with times |
| `milliyet_headlines` | Top headlines in one section |
| `milliyet_get_article` | Full text of one article (full URL) |
| `milliyet_search_news` | Keyword search over today's news listings |
| `milliyet_list_sections` | News sections usable with `milliyet_headlines` |
| `milliyet_health` | Is milliyet.com.tr reachable right now? |

## Example

Breaking news, 23 November 2026:

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

An article, 23 November 2026:

```json
{ "title": "12 ilde siber suç operasyonu! 5 günde 101 şüpheli yakalandı, 60 tutuklama",
  "author": "Kübra Çelepi",
  "date_published": "2026-11-23T11:57:00+03:00",
  "section": "Gündem", "word_count": 290,
  "keywords": ["siber suç", "operasyon", "tutuklama"],
  "body": "Bakanlığın sanal medya hesabından yapılan açıklamaya göre; Emniyet Genel Müdürlüğü Siber Suçlarla Mücadele Daire Başkanlığı, MASAK ve Cumhuriyet Başsavcılıkları koordinesinde düzenlenen operasyonlarda 101 şüpheli yakalandı. …" }
```

## Caveats

- Search is a **scan of the breaking-news page plus the main section listings**, not a full-archive search: the site's own search (`/arama/`) is disallowed in robots.txt, so there is no search API to call.
- Section pages have **no pagination** (`/gundem/2/` is 404) — each carries ~40 items, so `milliyet_headlines` sees the current page only.
- **Video** (`/milliyet-tv/`) and **gallery** (`/galeri/`, incl. nested `/magazin/galeri/` and `/pembenar/galeri/`) pages and the kids' section (`/cocuk/`) are not text news and are excluded from listings; `milliyet_get_article` on them returns an error.
- Article bodies come from the page's NewsArticle JSON-LD (`articleBody`, one plain-text block); if a page has no JSON-LD, the HTML paragraphs are used as a fallback.
- The site's sitemap (`sitemap.xml`) 301-redirects to an HTML page — it is not a usable sitemap.
- Transport uses Chrome TLS impersonation; requests are spaced ~0.8s apart.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_news.py -v    # offline, recorded fixtures
.venv/bin/python -m pytest tests/test_live.py -v    # live, against www.milliyet.com.tr
.venv/bin/python tests/smoke_live.py                # daily CI probe
```

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
