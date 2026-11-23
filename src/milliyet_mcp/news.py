"""Stdlib parsing for milliyet.com.tr server-rendered news pages.

Verified live 2026-11-23 against real pages (fixtures in tests/):
- Section pages (/gundem/ 119KB, /ekonomi/ 121KB): a slider
  (cat-slider__link anchors, <strong class="cat-slider__title">)
  plus a list (cat-list-card__link anchors, <strong
  class="cat-list-card__title"> + <span class="cat-list-card__spot">
  summary), plus an authors slider (authors__link anchors:
  <strong class="authors__name"> + <span class="authors__text">).
  Article hrefs are /<section>/<slug>-<7-digit-id>. No pagination
  (/gundem/2/ is 404) — each section page carries ~40 items.
- /son-dakika-haberleri/ (111KB): 4 section boxes (GÜNDEM, EKONOMİ,
  DÜNYA, AKTÜALİTE), 24 timed items of which 14 are text articles
  (the rest are video/gallery pages, excluded), each a
  breaking-news-page__item with
  <time><strong>HH:MM</strong></time> + a breaking-news-contents
  anchor whose <strong> is the title and whose tag span is the
  section name.
- Homepage (241KB): ~93 text-article links across all sections.
- Article pages (99-103KB): full NewsArticle JSON-LD (headline,
  description, author as Person, datePublished/dateModified,
  image as ImageObject, keywords, wordCount, articleSection,
  articleBody as one plain-text block — no newlines).
- Video (/milliyet-tv/) and gallery (/galeri/) pages and the kids
  section (/cocuk/) are NOT text news and are excluded from
  listings; get_article on them raises a clear error.
"""
from __future__ import annotations

import html
import json
import re

CATEGORIES = (
    "gundem", "ekonomi", "dunya", "skorer", "magazin",
    "teknoloji", "egitim", "kultur-sanat", "pembenar", "uzmanpara",
)

CATEGORY_NAMES = {
    "gundem": "Gündem",
    "ekonomi": "Ekonomi",
    "dunya": "Dünya",
    "skorer": "Skorer (Spor)",
    "magazin": "Magazin",
    "teknoloji": "Teknoloji",
    "egitim": "Eğitim",
    "kultur-sanat": "Kültür Sanat",
    "pembenar": "Pembenar",
    "uzmanpara": "Uzmanpara",
}

# Search scans these sections (the site's own /arama/ is disallowed
# in robots.txt, so there is no server-side search to call).
SEARCH_CATEGORIES = ("gundem", "ekonomi", "dunya", "skorer", "magazin")

_TR_UPPER_TO_LOWER = str.maketrans({
    "İ": "i", "I": "ı", "Ş": "ş", "Ğ": "ğ",
    "Ü": "ü", "Ö": "ö", "Ç": "ç",
})


def tr_lower(s: str) -> str:
    """Turkish-aware lowercase (str.lower() mangles İ -> i + dot)."""
    return s.translate(_TR_UPPER_TO_LOWER).lower()


def tr_title(s: str) -> str:
    """Turkish-aware title case for one word (str.title() mangles İ)."""
    s = tr_lower(s.strip())
    return s[:1].upper() + s[1:] if s else s


def _clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- listings

# Bare section labels that appear as extra text lines inside listing
# anchors (e.g. the "Gündem" tag on son-dakika items) — never a summary.
_SECTION_TAGS = {
    "gündem", "dünya", "ekonomi", "spor", "skorer", "magazin",
    "teknoloji", "eğitim", "kültür-sanat", "pembenar", "uzmanpara",
    "milliyet tv", "son dakika", "siyaset", "sağlık", "aktüalite",
}

# Not text news: video pages, photo galleries (also nested under
# sections, e.g. /pembenar/galeri/...), kids' games.
_SKIP_SEGMENTS = ("/galeri/", "/milliyet-tv/", "/cocuk/")

_ARTICLE_RE = re.compile(
    r'<a\b[^>]*href="([^"]+-\d{7})"[^>]*>(.*?)</a>', re.S
)


def parse_listing(html_text: str) -> list[dict]:
    """Article links on a listing page -> [{url, title, summary?,
    author?}]."""
    by_url: dict[str, dict] = {}
    for href, inner in _ARTICLE_RE.findall(html_text):
        if any(seg in href for seg in _SKIP_SEGMENTS):
            continue
        url = href if href.startswith("http") else \
            "https://www.milliyet.com.tr" + href
        # Columnist card: author name in <strong>, column title in
        # the <span class="authors__text"> — the title is the column.
        m_author = re.search(
            r'<strong[^>]*class="[^"]*authors__name[^"]*"[^>]*>(.*?)</strong>',
            inner, re.S,
        )
        m_col = re.search(
            r'<span[^>]*class="[^"]*authors__text[^"]*"[^>]*>(.*?)</span>',
            inner, re.S,
        )
        text = html.unescape(re.sub(r"<[^>]+>", "\n", inner))
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if m_author and m_col:
            row = {
                "url": url,
                "title": _clean(m_col.group(1)),
                "author": _clean(m_author.group(1)),
            }
        else:
            strongs = [
                _clean(s)
                for s in re.findall(r"<strong[^>]*>(.*?)</strong>", inner, re.S)
            ]
            strongs = [s for s in strongs if s]
            if strongs:
                title = max(strongs, key=len)
            elif lines:
                title = lines[0]
            else:
                continue  # image anchor; the text anchor carries it
            row = {"url": url, "title": title}
            rest = [
                ln for ln in lines
                if ln != title and ln.lower() not in _SECTION_TAGS
            ]
            summary = " ".join(rest).strip()
            if summary:
                row["summary"] = summary[:400]
        prev = by_url.get(url)
        if prev is None or len(row["title"]) > len(prev.get("title", "")):
            by_url[url] = row
    return list(by_url.values())


# ---------------------------------------------------------------- son dakika

_ITEM_RE = re.compile(
    r'<div class="breaking-news-page__item">'
    r'.*?<strong>(\d{2}:\d{2})</strong>'
    r'.*?<a[^>]*href="([^"]+-\d{7})"[^>]*>(.*?)</a>',
    re.S,
)
_BOX_RE = re.compile(
    r'<h3 class="breaking-news-page__title[^"]*">([^<]+)</h3>'
    r'(.*?)(?=<h3 class="breaking-news-page__title|</section>|$)',
    re.S,
)


def parse_sondakika(html_text: str) -> list[dict]:
    """Breaking-news page -> [{time, section, url, title}] in page
    order (newest first)."""
    rows: list[dict] = []
    boxes = _BOX_RE.findall(html_text)
    if not boxes:
        # Fallback: no section boxes found — parse items without a
        # section label rather than returning nothing.
        for time, href, inner in _ITEM_RE.findall(html_text):
            if any(seg in href for seg in _SKIP_SEGMENTS):
                continue
            title = _strong_title(inner)
            if title:
                rows.append({
                    "time": time,
                    "url": "https://www.milliyet.com.tr" + href,
                    "title": title,
                })
        return rows
    for section, block in boxes:
        for time, href, inner in _ITEM_RE.findall(block):
            if any(seg in href for seg in _SKIP_SEGMENTS):
                continue
            title = _strong_title(inner)
            if not title:
                continue
            rows.append({
                "time": time,
                "section": tr_title(section),
                "url": "https://www.milliyet.com.tr" + href,
                "title": title,
            })
    return rows


def _strong_title(inner: str) -> str:
    strongs = [
        _clean(s)
        for s in re.findall(r"<strong[^>]*>(.*?)</strong>", inner, re.S)
    ]
    strongs = [s for s in strongs if s]
    if strongs:
        return max(strongs, key=len)
    text = html.unescape(re.sub(r"<[^>]+>", "\n", inner))
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    return lines[0] if lines else ""


# ---------------------------------------------------------------- article

def parse_article(html_text: str) -> dict:
    """Article page -> title, author, dates, description, image,
    keywords, body (full text), word_count, section, url."""
    m = re.search(
        r'<script type="application/ld\+json">(.*?)</script>',
        html_text, re.S,
    )
    if m:
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict) and data.get("@type") == "NewsArticle":
            return _article_from_jsonld(data)
    # Fallback: plain paragraphs inside the article content div.
    return _article_from_html(html_text)


def _article_from_jsonld(data: dict) -> dict:
    out: dict = {}
    out["title"] = _clean(data.get("headline"))
    out["description"] = _clean(data.get("description"))
    author = data.get("author")
    if isinstance(author, dict):
        out["author"] = _clean(author.get("name"))
    elif isinstance(author, str):
        out["author"] = _clean(author)
    out["date_published"] = data.get("datePublished") or ""
    out["date_modified"] = data.get("dateModified") or ""
    image = data.get("image")
    if isinstance(image, dict):
        out["image"] = image.get("url") or ""
    elif isinstance(image, str):
        out["image"] = image
    elif isinstance(image, list) and image:
        first = image[0]
        out["image"] = first.get("url", "") if isinstance(first, dict) else str(first)
    keywords = data.get("keywords")
    if isinstance(keywords, list):
        out["keywords"] = [str(k) for k in keywords if k]
    elif isinstance(keywords, str):
        out["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
    if data.get("wordCount"):
        try:
            out["word_count"] = int(data["wordCount"])
        except (TypeError, ValueError):
            pass
    out["section"] = _clean(data.get("articleSection"))
    page = data.get("mainEntityOfPage")
    if isinstance(page, dict) and page.get("@id"):
        out["url"] = page["@id"]
    body = data.get("articleBody")
    if not body or not str(body).strip():
        raise ValueError("article has no body text (articleBody empty)")
    out["body"] = re.sub(r"\s+", " ", str(body)).strip()
    return {k: v for k, v in out.items() if v not in (None, "", [])}


def _article_from_html(html_text: str) -> dict:
    out: dict = {}
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html_text, re.S)
    if m:
        out["title"] = _clean(m.group(1))
    if not out.get("title"):
        m = re.search(r"<title>(.*?)</title>", html_text, re.S)
        if m:
            out["title"] = _clean(m.group(1)).split(" | Milliyet")[0]

    def _meta(name: str) -> str | None:
        mm = re.search(
            rf'<meta[^>]+(?:property|name)="{re.escape(name)}"[^>]+content="([^"]*)"',
            html_text,
        )
        return html.unescape(mm.group(1)) if mm else None

    out["description"] = _meta("description") or _meta("og:description") or ""
    out["date_published"] = _meta("datePublished") or ""
    out["date_modified"] = _meta("dateModified") or ""
    out["image"] = _meta("og:image") or ""
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html_text)
    if m:
        out["url"] = m.group(1)

    i = html_text.find("news-detail-content")
    if i < 0:
        raise ValueError("no article body found on this page")
    region = html_text[i:i + 60000]
    paras = []
    for pm in re.finditer(r"<p[^>]*>(.*?)</p>", region, re.S):
        text = _clean(pm.group(1))
        if not text:
            continue
        if re.match(r"\d{2}\.\d{2}\.\d{4} - \d{2}:\d{2}", text):
            continue  # date line, not body text
        if text.endswith("(DHA)") or text.endswith("(AA)") or text.endswith("(İHA)"):
            continue  # agency byline, not body text
        paras.append(text)
    if not paras:
        raise ValueError("no article body paragraphs found on this page")
    out["body"] = "\n\n".join(paras)
    out["paragraph_count"] = len(paras)
    return {k: v for k, v in out.items() if v not in (None, "")}
