"""MCP server: unofficial read-only access to milliyet.com.tr news."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import news as _N

mcp = FastMCP("milliyet-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for milliyet.com.tr, one of Türkiye's
biggest national newspapers (founded 1950) — breaking news, headlines
by section, full article text, keyword search, and the section list.
Data comes from the site's server-rendered pages — no login, no API
key. Section pages (/<category>/: gundem, ekonomi, dunya, skorer,
magazin, teknoloji, egitim, kultur-sanat, pembenar, uzmanpara) list
~40 headlines each with no pagination. The breaking-news page
(/son-dakika-haberleri/) lists the newest items with times, grouped
by section. Article pages carry a full NewsArticle JSON-LD block
(title, author, publish/modify dates, description, image, keywords,
word count, full body text). Keyword search scans the breaking-news
page plus the main section listings (the site's own /arama/ search is
disallowed in robots.txt, so there is no server-side search to call).
Video (/milliyet-tv/) and gallery (/galeri/) pages are not text news
and are excluded from listings. Read-only; transport uses Chrome TLS
impersonation; requests are spaced ~0.8s apart.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — Turkey MCP factory.\
"""


_SOURCE = "milliyet.com.tr"
_DISCLAIMER = "Unofficial read-only data from milliyet.com.tr; verify on the site before acting on it."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


def _validate_limit(limit: int, lo: int = 1, hi: int = 30) -> int:
    if not lo <= limit <= hi:
        raise ValueError(f"limit must be between {lo} and {hi}")
    return limit


@mcp.tool()
def milliyet_headlines(category: str = "gundem", limit: int = 10) -> str:
    """Top headlines in one Milliyet section. category: "gundem"
    (default), "ekonomi", "dunya", "skorer", "magazin", "teknoloji",
    "egitim", "kultur-sanat", "pembenar", "uzmanpara". limit 1..30.
    Returns headlines (title, article URL, summary when the listing
    carries one, author for columnist pieces)."""
    try:
        category = (category or "gundem").strip().lower()
        if category not in _N.CATEGORIES:
            raise ValueError(
                f"category must be one of {', '.join(_N.CATEGORIES)}"
            )
        _validate_limit(limit)
        html_text = _http.fetch_category_html(category)
        rows = _N.parse_listing(html_text)
    except (ValueError, _http.MilliyetError) as e:
        return _err(e)
    return _ok({
            "category": category,
            "count": min(limit, len(rows)),
            "headlines": rows[:limit],
        })


@mcp.tool()
def milliyet_latest(limit: int = 10) -> str:
    """Latest Milliyet breaking news (son dakika), newest first.
    limit 1..30. Returns items (time HH:MM Europe/Istanbul, section,
    title, article URL) from the /son-dakika-haberleri/ page."""
    try:
        _validate_limit(limit)
        html_text = _http.fetch_sondakika_html()
        rows = _N.parse_sondakika(html_text)
    except (ValueError, _http.MilliyetError) as e:
        return _err(e)
    return _ok({"count": min(limit, len(rows)), "articles": rows[:limit]})


@mcp.tool()
def milliyet_get_article(article_url: str) -> str:
    """Full text of one Milliyet article. article_url: the article's
    milliyet.com.tr URL (as returned by the headlines/latest/search
    tools, e.g. "https://www.milliyet.com.tr/gundem/12-ilde-siber-suc-
    operasyonu-5-gunde-101-supheli-yakalandi-60-tutuklama-7706106").
    Returns title, author, publish/modify dates, description, image,
    keywords, word count and the full body text. Video and gallery
    pages have no article text and return an error."""
    try:
        if not article_url or not article_url.strip():
            raise ValueError("article_url must not be empty")
        html_text = _http.fetch_article_html(article_url.strip())
        data = _N.parse_article(html_text)
    except (ValueError, _http.MilliyetError) as e:
        return _err(e)
    return _ok(data)


@mcp.tool()
def milliyet_search_news(query: str, limit: int = 10) -> str:
    """Keyword search over today's Milliyet news: scans the
    breaking-news page plus the gundem, ekonomi, dunya, skorer and
    magazin listings, matching the keyword in titles and summaries.
    query: e.g. "ekonomi", "deprem", "dolar". limit 1..30. Note: the
    site's own /arama/ search is disallowed in robots.txt, so this
    searches the current listings instead of a search backend."""
    try:
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        _validate_limit(limit)
        q = _N.tr_lower(query.strip())
        rows: list[dict] = []
        seen: set[str] = set()

        def _scan(candidates: list[dict]) -> None:
            for r in candidates:
                if r["url"] in seen:
                    continue
                seen.add(r["url"])
                hay = _N.tr_lower(f"{r.get('title', '')} {r.get('summary', '')}")
                if q in hay:
                    rows.append(r)

        _scan(_N.parse_sondakika(_http.fetch_sondakika_html()))
        for category in _N.SEARCH_CATEGORIES:
            if len(rows) >= limit:
                break
            _scan(_N.parse_listing(_http.fetch_category_html(category)))
    except (ValueError, _http.MilliyetError) as e:
        return _err(e)
    return _ok({"query": query.strip(),
         "count": min(limit, len(rows)), "articles": rows[:limit]})


@mcp.tool()
def milliyet_list_sections() -> str:
    """Milliyet news sections usable with milliyet_headlines, with
    their Turkish display names. No arguments."""
    return _ok({
        "sections": [
            {"slug": slug, "name": _N.CATEGORY_NAMES[slug]}
            for slug in _N.CATEGORIES
        ],
    })


@mcp.tool()
def milliyet_health() -> str:
    """Check whether milliyet.com.tr is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
