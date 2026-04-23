"""Insider-trading screener — DART 임원ㆍ주요주주 특정증권등 소유상황 보고서.

Pulls the last N days of ``pblntf_ty=D`` disclosures, filters rows whose
``report_nm`` contains the Korean "임원ㆍ주요주주특정증권등소유상황보고서" or
"주식등의대량보유상황보고서" token, and surfaces them as a time-sorted list.

Caching
-------
The full universe scan is cached in-memory for ``_CACHE_TTL_SEC`` seconds,
keyed by ``(lookback_days, kind)``. Caller opts out via ``use_cache=False``.

Data source priority
--------------------
1. Live DART list.json (authoritative, 1-minute fresh).
2. ``filings`` table stored via ``Repository.upsert_filings`` (backstop).

We persist every live pull so downstream callers see filings even when the
network is flaky.
"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from typing import Any

import httpx

from ky_adapters.dart import DARTAdapter
from ky_core.storage import Repository

log = logging.getLogger(__name__)

DART_LIST_URL = "https://opendart.fss.or.kr/api/list.json"

# Token classes for filtering
INSIDER_SELF_TOKEN = "임원ㆍ주요주주특정증권등소유상황보고서"
INSIDER_PLAN_TOKEN = "임원ㆍ주요주주특정증권등거래계획보고서"
BULK_OWNERSHIP_TOKEN = "주식등의대량보유상황보고서"

_CACHE_TTL_SEC = 3600.0  # 1h — matches the spec
_CACHE: dict[tuple[int, str], tuple[float, list[dict[str, Any]]]] = {}


def _cache_get(key: tuple[int, str]) -> list[dict[str, Any]] | None:
    hit = _CACHE.get(key)
    if not hit:
        return None
    ts, rows = hit
    if time.time() - ts > _CACHE_TTL_SEC:
        return None
    return rows


def _cache_set(key: tuple[int, str], rows: list[dict[str, Any]]) -> None:
    _CACHE[key] = (time.time(), rows)


def _classify_insider_row(r: dict[str, Any]) -> bool:
    nm = (r.get("report_nm") or "").strip()
    if INSIDER_SELF_TOKEN in nm:
        r["kind"] = "insider"
        return True
    if INSIDER_PLAN_TOKEN in nm:
        r["kind"] = "insider_plan"
        return True
    if BULK_OWNERSHIP_TOKEN in nm:
        r["kind"] = "bulk_ownership"
        return True
    return False


def _fetch_insider_page(
    client: httpx.Client,
    api_key: str,
    start: date,
    end: date,
    page: int,
) -> tuple[int, list[dict[str, Any]], bool]:
    """Fetch one page of pblntf_ty=D. Returns (page, filtered_rows, exhausted)."""
    try:
        resp = client.get(
            DART_LIST_URL,
            params={
                "crtfc_key": api_key,
                "bgn_de": start.strftime("%Y%m%d"),
                "end_de": end.strftime("%Y%m%d"),
                "page_no": page,
                "page_count": 100,
                "pblntf_ty": "D",
            },
        )
    except httpx.HTTPError as exc:
        log.warning("DART insider fetch failed page=%s: %s", page, exc)
        return page, [], True
    if resp.status_code != 200:
        return page, [], True
    body = resp.json()
    if body.get("status") not in ("000", "013"):
        return page, [], True
    rows = body.get("list") or []
    kept = [r for r in rows if _classify_insider_row(r)]
    return page, kept, len(rows) < 100


def _fetch_insider_filings(
    api_key: str,
    lookback_days: int,
    *,
    max_pages: int = 3,
) -> list[dict[str, Any]]:
    """Pull disclosure-type ``D`` rows over ``lookback_days``.

    Pages are fetched in parallel to collapse the DART roundtrip tail — the
    sequential loop was the main contributor to the 6s+ cold latency the QA
    run flagged.
    """
    end = date.today()
    start = end - timedelta(days=lookback_days)
    out: list[dict[str, Any]] = []
    with httpx.Client(timeout=15.0) as client:
        with ThreadPoolExecutor(max_workers=min(4, max_pages)) as ex:
            futures = [
                ex.submit(_fetch_insider_page, client, api_key, start, end, page)
                for page in range(1, max_pages + 1)
            ]
            pending: list[tuple[int, list[dict[str, Any]]]] = []
            exhaust_at: int | None = None
            for fut in as_completed(futures):
                page, rows, exhausted = fut.result()
                if exhausted:
                    exhaust_at = min(page, exhaust_at) if exhaust_at else page
                pending.append((page, rows))
            for page, rows in pending:
                if exhaust_at is not None and page > exhaust_at:
                    continue
                out.extend(rows)
    return out


def recent_insider_filings(
    *,
    lookback_days: int = 7,
    kind: str = "all",
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Return insider-trading disclosures over the lookback window.

    ``kind`` filter:
        - ``all`` — insider reports + bulk-ownership reports
        - ``insider`` — 임원ㆍ주요주주 소유 only
        - ``bulk`` — 5% bulk ownership only
        - ``plan`` — trading-plan reports (pre-disclosure)
    """
    cache_key = (int(lookback_days), str(kind))
    if use_cache:
        hit = _cache_get(cache_key)
        if hit is not None:
            return hit

    adapter = DARTAdapter.from_settings()
    if not adapter.api_key:
        return []

    raw = _fetch_insider_filings(adapter.api_key, lookback_days)

    if kind == "insider":
        raw = [r for r in raw if r["kind"] == "insider"]
    elif kind == "bulk":
        raw = [r for r in raw if r["kind"] == "bulk_ownership"]
    elif kind == "plan":
        raw = [r for r in raw if r["kind"] == "insider_plan"]

    # Sort by filing time (descending), newest first.
    raw.sort(key=lambda r: (r.get("rcept_dt") or "", r.get("rcept_no") or ""), reverse=True)

    out: list[dict[str, Any]] = []
    for r in raw:
        filed_raw = (r.get("rcept_dt") or "").strip()
        filed_iso = (
            f"{filed_raw[0:4]}-{filed_raw[4:6]}-{filed_raw[6:8]}"
            if len(filed_raw) == 8 and filed_raw.isdigit()
            else filed_raw
        )
        # Signal inference — trader-friendly tag
        nm = r.get("report_nm") or ""
        flr = (r.get("flr_nm") or "").strip()
        signal = _infer_insider_signal(nm, flr, r.get("kind", "insider"))
        out.append(
            {
                "date": filed_iso,
                "corp_code": r.get("corp_code"),
                "corp_name": r.get("corp_name"),
                "stock_code": r.get("stock_code"),
                "report_name": nm.strip(),
                "kind": r.get("kind"),
                "filer_name": flr,
                "receipt_no": r.get("rcept_no"),
                "signal": signal,
            }
        )

    # Persist to `filings` table so downstream consumers can read without DART.
    if repo is None:
        try:
            repo = Repository()
        except Exception:  # noqa: BLE001
            repo = None
    if repo is not None and out:
        try:
            repo.upsert_filings(
                [
                    {
                        "source_id": "dart",
                        "corp_code": row["corp_code"] or "",
                        "receipt_no": row["receipt_no"] or "",
                        "filed_at": row["date"] or "",
                        "type": row["report_name"],
                        "summary": row["corp_name"],
                        "meta": {
                            "filer_name": row["filer_name"],
                            "kind": row["kind"],
                            "stock_code": row["stock_code"],
                        },
                    }
                    for row in out
                    if row.get("receipt_no")
                ]
            )
        except Exception:  # noqa: BLE001
            log.exception("insider: persist filings failed")

    if use_cache:
        _cache_set(cache_key, out)
    return out


def _infer_insider_signal(report_nm: str, filer: str, kind: str) -> str:
    """Best-effort tag: ``insider-buy`` / ``insider-sell`` / ``stake`` / ``plan``.

    DART list.json doesn't carry the sign of the change — that lives inside the
    attached XBRL report. We keep the tag conservative and let the UI surface
    a neutral "공시" chip until we parse the body.
    """
    if kind == "insider_plan":
        return "plan"
    if kind == "bulk_ownership":
        return "stake"
    nm = report_nm
    if "매수" in nm:
        return "insider-buy"
    if "매도" in nm:
        return "insider-sell"
    return "insider"


def insider_summary(
    *,
    lookback_days: int = 7,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    """KPI tile + table payload for /api/v1/value/insider."""
    rows = recent_insider_filings(
        lookback_days=lookback_days,
        kind="all",
        repo=repo,
        use_cache=use_cache,
    )
    kpi = {
        "total": len(rows),
        "insider": sum(1 for r in rows if r["kind"] == "insider"),
        "bulk_ownership": sum(1 for r in rows if r["kind"] == "bulk_ownership"),
        "plan": sum(1 for r in rows if r["kind"] == "insider_plan"),
        "lookback_days": lookback_days,
    }
    return {"kpi": kpi, "rows": rows}
