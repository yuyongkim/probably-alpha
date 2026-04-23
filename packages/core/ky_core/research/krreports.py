"""Korean brokerage research reports — Naver Finance research scraper.

Scrapes https://finance.naver.com/research/ to surface recent
industry / company / market reports, with best-effort parsing of
"목표주가(상향/하향)" hints from the title.

No API key required — we hit the same public HTML pages the browser
does.  Per-request user-agent + short timeout; soft fail on error.
"""
from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

_BASE = "https://finance.naver.com"
_UA = "Mozilla/5.0 (KY-Platform Research)"


@dataclass
class ReportItem:
    title: str
    broker: str
    published: str
    link: str
    symbol: Optional[str]
    target_price: Optional[str]
    direction: Optional[str]  # "up" | "down" | None
    category: str  # company | industry | market | debriefing | economy


# --------------------------------------------------------------------------- #
# Scraping                                                                    #
# --------------------------------------------------------------------------- #


_CATEGORY_PATHS = {
    "company": "/research/company_list.naver",
    "industry": "/research/industry_list.naver",
    "market": "/research/market_info_list.naver",
    "debriefing": "/research/debriefing_list.naver",
    "economy": "/research/economy_list.naver",
}


_TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S | re.I)
_TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S | re.I)
_A_RE = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip(html: str) -> str:
    return re.sub(r"\s+", " ", _TAG_RE.sub("", html)).strip()


def _detect_direction(title: str) -> Optional[str]:
    t = title
    if "상향" in t or "Buy" in t or "매수" in t or "목표가 상" in t:
        return "up"
    if "하향" in t or "Sell" in t or "매도" in t or "목표가 하" in t:
        return "down"
    return None


def _extract_target_price(title: str) -> Optional[str]:
    # Best-effort: "목표가 89,000원" or "TP 250,000"
    m = re.search(r"(목표가|TP)\s*([\d,]+)", title, re.I)
    if m:
        return m.group(2)
    return None


def _fetch_list(path: str) -> str:
    if httpx is None:
        return ""
    try:
        with httpx.Client(timeout=10.0, headers={"User-Agent": _UA}) as c:
            r = c.get(urljoin(_BASE, path))
            r.encoding = "euc-kr"
            if r.status_code != 200:
                return ""
            return r.text
    except Exception as exc:
        logger.warning("research list fetch failed %s: %s", path, exc)
        return ""


def _parse_rows(html: str, category: str) -> List[ReportItem]:
    if not html:
        return []
    items: List[ReportItem] = []
    for tr in _TR_RE.findall(html):
        tds = _TD_RE.findall(tr)
        if len(tds) < 4:
            continue
        # Columns typically: [제목(+링크), 증권사, 첨부, 작성일] for some
        # pages; company_list is [종목명, 제목, 증권사, 첨부, 작성일].
        title_cell = None
        symbol = None
        broker = ""
        date = ""
        link = ""

        if category == "company" and len(tds) >= 5:
            sym_match = _A_RE.search(tds[0])
            if sym_match:
                symbol = _strip(sym_match.group(2))
            title_cell = tds[1]
            broker = _strip(tds[2])
            date = _strip(tds[4])
        else:
            title_cell = tds[0]
            broker = _strip(tds[1]) if len(tds) > 1 else ""
            date = _strip(tds[-1])

        if not title_cell:
            continue
        a = _A_RE.search(title_cell)
        if not a:
            continue
        link = urljoin(_BASE + "/research/", a.group(1))
        title = _strip(a.group(2))
        if not title or title.startswith("제목"):
            continue

        items.append(
            ReportItem(
                title=title,
                broker=broker,
                published=date,
                link=link,
                symbol=symbol,
                target_price=_extract_target_price(title),
                direction=_detect_direction(title),
                category=category,
            )
        )
    return items


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def list_reports(category: str = "company", limit: int = 20) -> Dict[str, Any]:
    """Return up to ``limit`` recent broker reports for a Naver category."""
    path = _CATEGORY_PATHS.get(category)
    if not path:
        return {
            "category": category,
            "items": [],
            "stale": True,
            "reason": f"unknown category: {category}",
        }
    html = _fetch_list(path)
    items = _parse_rows(html, category)[:limit]

    direction_counts = {"up": 0, "down": 0, "neutral": 0}
    for it in items:
        if it.direction == "up":
            direction_counts["up"] += 1
        elif it.direction == "down":
            direction_counts["down"] += 1
        else:
            direction_counts["neutral"] += 1

    brokers = sorted({it.broker for it in items if it.broker})
    return {
        "category": category,
        "items": [asdict(it) for it in items],
        "count": len(items),
        "stale": not items,
        "summary": {
            "brokers": brokers,
            "broker_count": len(brokers),
            "target_up": direction_counts["up"],
            "target_down": direction_counts["down"],
            "neutral": direction_counts["neutral"],
        },
    }
