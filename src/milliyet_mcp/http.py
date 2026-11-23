"""HTTP layer for milliyet_mcp.

milliyet.com.tr serves its homepage, section pages (/gundem/,
/ekonomi/, /dunya/, /skorer/, ...), the breaking-news page
(/son-dakika-haberleri/) and article pages (/<section>/<slug>-<id>)
fully server-rendered — no login, no API key, no session cookies
needed. Plain HTTP 200 with a browser UA (verified live 2026-11-23).
The transport still uses curl-cffi Chrome impersonation, the same
proven pattern as the other Turkey-factory servers. Requests are
kept gentle (one at a time, ~0.8s apart) and read-only.

Caveats found while probing (2026-11-23): the site's own search
(/arama/) is disallowed in robots.txt — keyword search here scans
the breaking-news page plus the main section listings instead.
Section pages have no pagination (/gundem/2/ is 404); each carries
~40 items. sitemap.xml 301-redirects to an HTML page (not a real
sitemap). /son-dakika/ 301-redirects to /son-dakika-haberleri/.
"""
from __future__ import annotations

import time
from urllib.parse import quote

from curl_cffi import requests as _r

BASE = "https://www.milliyet.com.tr"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

_last_fetch = 0.0


class MilliyetError(RuntimeError):
    pass


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport.
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _r.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise MilliyetError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise MilliyetError(f"network error fetching {url}: {last_exc}") from last_exc


def _get(url: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _request(url, _HEADERS)
    except MilliyetError:
        raise
    except Exception as e:
        raise MilliyetError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise MilliyetError(
            "milliyet.com.tr refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise MilliyetError(
            "milliyet.com.tr rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code in (404, 410):
        raise MilliyetError(
            f"page not found (HTTP {resp.status_code}): {url} — check the "
            "category / article URL"
        )
    if resp.status_code != 200:
        raise MilliyetError(f"unexpected HTTP {resp.status_code} fetching {url}")
    return resp.text


def fetch_home_html() -> str:
    return _get(f"{BASE}/")


def fetch_category_html(category: str) -> str:
    """Section listing: /<category>/ (gundem, ekonomi, dunya, ...)."""
    return _get(f"{BASE}/{quote(category)}/")


def fetch_sondakika_html() -> str:
    """Breaking-news page: /son-dakika-haberleri/."""
    return _get(f"{BASE}/son-dakika-haberleri/")


def fetch_article_html(article_url: str) -> str:
    """Article page (full URL or path)."""
    if article_url.startswith("http"):
        url = article_url
    else:
        url = f"{BASE}/{article_url.lstrip('/')}"
    if "milliyet.com.tr" not in url:
        raise MilliyetError(f"not a milliyet.com.tr URL: {article_url}")
    return _get(url)


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `milliyet_health` tool
    and the daily smoke CI.
    """
    url = "https://www.milliyet.com.tr/"
    try:
        fetch_home_html()
    except MilliyetError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
