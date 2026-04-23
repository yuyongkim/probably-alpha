"""Naver news search + lightweight keyword-based sentiment.

The adapter is intentionally tiny: we either hit Naver Open API (requires
``NAVER_CLIENT_ID`` / ``NAVER_CLIENT_SECRET``) or fall back to scraping
the mobile finance search page.  In both cases we strip tags, keep the
headline + snippet, and score each item with a Korean finance-oriented
keyword lexicon.

This module is *not* a generic news engine.  It exists so the Research
"뉴스 감성 분석" sub-section can show real, dated headlines with a
defensible sentiment chip — instead of a stub card.
"""
from __future__ import annotations

import html
import logging
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Sentiment lexicon                                                           #
# --------------------------------------------------------------------------- #

_POSITIVE = (
    "호재", "상승", "돌파", "급등", "반등", "흑자", "성장", "최고가", "신고가",
    "수혜", "개선", "상향", "호실적", "어닝 서프라이즈", "서프라이즈", "매수",
    "강세", "회복", "확대",
)
_NEGATIVE = (
    "악재", "하락", "급락", "손실", "적자", "감익", "쇼크", "하향", "부진",
    "둔화", "리콜", "소송", "조사", "제재", "경고", "매도", "약세", "위기",
    "축소", "감소",
)


def _score_sentiment(text: str) -> Dict[str, Any]:
    """Return ``{score, label, pos_hits, neg_hits}`` in [-1, 1]."""
    t = text or ""
    pos = [w for w in _POSITIVE if w in t]
    neg = [w for w in _NEGATIVE if w in t]
    n = len(pos) + len(neg)
    if n == 0:
        return {"score": 0.0, "label": "neutral", "pos_hits": [], "neg_hits": []}
    score = (len(pos) - len(neg)) / n
    if score > 0.2:
        label = "positive"
    elif score < -0.2:
        label = "negative"
    else:
        label = "neutral"
    return {
        "score": round(score, 3),
        "label": label,
        "pos_hits": pos[:6],
        "neg_hits": neg[:6],
    }


def _strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    return html.unescape(s).strip()


# --------------------------------------------------------------------------- #
# Data class                                                                  #
# --------------------------------------------------------------------------- #


@dataclass
class NewsItem:
    title: str
    description: str
    link: str
    pub_date: str
    source: str
    sentiment_score: float
    sentiment_label: str
    pos_hits: List[str]
    neg_hits: List[str]


# --------------------------------------------------------------------------- #
# Fetch                                                                       #
# --------------------------------------------------------------------------- #


def _naver_openapi_search(query: str, display: int = 10) -> Optional[List[Dict[str, Any]]]:
    cid = os.getenv("NAVER_CLIENT_ID")
    cs = os.getenv("NAVER_CLIENT_SECRET")
    if not (cid and cs and httpx is not None):
        return None
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": cs}
    params = {"query": query, "display": display, "sort": "date"}
    try:
        with httpx.Client(timeout=10.0) as c:
            r = c.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            return data.get("items", []) or []
    except Exception as exc:  # pragma: no cover
        logger.warning("Naver OpenAPI news failed: %s", exc)
        return None


# search.naver.com renders news hits as origin-site anchors; the title text
# lives inside the anchor's child span.  We match (href, inner_html) pairs that
# point outside the naver.com family.
_NEWS_ANY_A = re.compile(
    r'<a[^>]+href="(https?://(?!(?:search|n|m|news|cc|logins)\.|[^/]*naver\.com)[^"]+)"[^>]*>(.*?)</a>',
    re.S | re.I,
)


def _naver_finance_scrape(query: str, display: int = 10) -> List[Dict[str, Any]]:
    """Fallback: scrape search.naver.com news results. OpenAPI-shaped dicts."""
    if httpx is None:
        return []
    url = "https://search.naver.com/search.naver"
    params = {"where": "news", "query": query, "sort": "1"}
    try:
        with httpx.Client(
            timeout=10.0,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            follow_redirects=True,
        ) as c:
            r = c.get(url, params=params)
            r.raise_for_status()
            html_body = r.text
    except Exception as exc:
        logger.warning("Naver search news scrape failed: %s", exc)
        return []

    out: List[Dict[str, Any]] = []
    seen: set = set()
    for link, inner in _NEWS_ANY_A.findall(html_body):
        title = _strip_html(inner)
        # Filter: titles are usually 15..160 chars, not domain strings.
        if len(title) < 15 or len(title) > 180:
            continue
        if title.startswith("http") or "네이버" == title:
            continue
        key = title[:60]
        if key in seen:
            continue
        seen.add(key)
        # Best-effort domain as "source"
        try:
            domain = link.split("//", 1)[1].split("/", 1)[0]
        except Exception:
            domain = ""
        out.append(
            {
                "title": title,
                "description": "",
                "originallink": domain,
                "link": link,
                "pubDate": "",
            }
        )
        if len(out) >= display:
            break
    return out


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def search_news(query: str, display: int = 10) -> Dict[str, Any]:
    """Return up to ``display`` news items scored with a keyword lexicon.

    The response envelope always includes ``source="naver_openapi"`` or
    ``"naver_finance_scrape"`` so the frontend can surface which path was
    used.  If neither works we return an empty list with ``stale=True``.
    """
    if not query or not query.strip():
        return {"query": query, "items": [], "source": "noop", "stale": True}

    raw = _naver_openapi_search(query, display=display)
    source = "naver_openapi"
    if raw is None:
        raw = _naver_finance_scrape(query, display=display)
        source = "naver_finance_scrape"

    items: List[NewsItem] = []
    pos_n = neg_n = neu_n = 0
    agg_score = 0.0
    for rec in raw:
        title = _strip_html(rec.get("title", ""))
        desc = _strip_html(rec.get("description", ""))
        link = rec.get("link") or rec.get("originallink") or ""
        pub = rec.get("pubDate", "")
        origin = rec.get("originallink") or rec.get("source") or ""
        combined = f"{title} {desc}"
        sent = _score_sentiment(combined)
        if sent["label"] == "positive":
            pos_n += 1
        elif sent["label"] == "negative":
            neg_n += 1
        else:
            neu_n += 1
        agg_score += float(sent["score"])
        items.append(
            NewsItem(
                title=title,
                description=desc,
                link=link,
                pub_date=pub,
                source=origin,
                sentiment_score=float(sent["score"]),
                sentiment_label=sent["label"],
                pos_hits=sent["pos_hits"],
                neg_hits=sent["neg_hits"],
            )
        )

    n = len(items)
    avg = round(agg_score / n, 3) if n else 0.0
    return {
        "query": query,
        "items": [asdict(it) for it in items],
        "source": source,
        "stale": n == 0,
        "summary": {
            "n": n,
            "avg_score": avg,
            "positive": pos_n,
            "negative": neg_n,
            "neutral": neu_n,
        },
    }
