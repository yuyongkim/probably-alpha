"""Treasury-share / buyback screener.

Pulls DART disclosures across the ``pblntf_ty=B`` (주요사항보고서) and
``pblntf_ty=E`` (거래·지배 관계) groups and surfaces three flavours:

    - 자기주식 취득 결정 / 결과 → "buyback"
    - 자기주식 처분 결정 / 결과 → "dispose"
    - 자기주식 소각 결정 / 완료  → "cancel"

The decision vs. result split lets us distinguish *announced* programs from
*completed* executions. 소각(cancel) is the highest-signal variant — it
permanently reduces share count — so we highlight it separately in the KPI
tile.

Same cache + persistence pattern as ``ky_core.value.insider``.
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

BUYBACK_TOKENS = (
    "자기주식취득",
    "자기주식 취득",
    "자기주식처분",
    "자기주식 처분",
    "자기주식소각",
    "자기주식 소각",
    "자기주식신탁계약",
)

_CACHE_TTL_SEC = 3600.0
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


def _classify(report_nm: str) -> dict[str, str]:
    """Infer (action, status) from the Korean report name.

    action: ``buyback`` / ``dispose`` / ``cancel`` / ``trust``
    status: ``decision`` / ``result``
    """
    nm = report_nm.replace(" ", "")
    if "자기주식소각" in nm:
        action = "cancel"
    elif "자기주식처분" in nm:
        action = "dispose"
    elif "자기주식신탁" in nm:
        action = "trust"
    elif "자기주식취득" in nm:
        action = "buyback"
    else:
        action = "other"
    status = "result" if "결과" in nm else "decision"
    return {"action": action, "status": status}


def _fetch_page(
    client: httpx.Client,
    api_key: str,
    start: date,
    end: date,
    ptype: str,
    page: int,
) -> tuple[str, int, list[dict[str, Any]], bool]:
    """Fetch one (ptype, page). Returns (ptype, page, filtered_rows, exhausted).

    ``exhausted`` is True when the page returned <100 rows (no more to fetch).
    """
    try:
        resp = client.get(
            DART_LIST_URL,
            params={
                "crtfc_key": api_key,
                "bgn_de": start.strftime("%Y%m%d"),
                "end_de": end.strftime("%Y%m%d"),
                "page_no": page,
                "page_count": 100,
                "pblntf_ty": ptype,
            },
        )
    except httpx.HTTPError as exc:
        log.warning("DART buyback fetch failed %s page=%s: %s", ptype, page, exc)
        return ptype, page, [], True
    if resp.status_code != 200:
        return ptype, page, [], True
    body = resp.json()
    if body.get("status") not in ("000", "013"):
        return ptype, page, [], True
    rows = body.get("list") or []
    kept: list[dict[str, Any]] = []
    for r in rows:
        nm = (r.get("report_nm") or "").replace(" ", "")
        if any(tok.replace(" ", "") in nm for tok in BUYBACK_TOKENS):
            kept.append(r)
    return ptype, page, kept, len(rows) < 100


def _fetch_buyback_filings(
    api_key: str,
    lookback_days: int,
    *,
    max_pages: int = 3,
) -> list[dict[str, Any]]:
    """Fetch buyback filings across ptype=B/E in parallel.

    Cold runs historically took ~35s because 10 httpx roundtrips were issued
    sequentially. We now submit them to a small thread pool; DART serves each
    request in roughly 2-4s so 10 concurrent calls collapse to a single
    roundtrip-worst-case. We also lowered ``max_pages`` from 5 to 3 (a 30-day
    buyback window virtually never produces 500 hits per ptype).
    """
    end = date.today()
    start = end - timedelta(days=lookback_days)
    out: list[dict[str, Any]] = []
    tasks = [(pt, pg) for pt in ("B", "E") for pg in range(1, max_pages + 1)]
    with httpx.Client(timeout=15.0) as client:
        with ThreadPoolExecutor(max_workers=min(8, len(tasks))) as ex:
            futures = [
                ex.submit(_fetch_page, client, api_key, start, end, pt, pg)
                for pt, pg in tasks
            ]
            # Track exhaustion per ptype so we stop collecting pages beyond a
            # short result set (e.g. ptype=B exhausted at page 1 → drop pages
            # 2..N from result set).
            exhaust_at: dict[str, int] = {}
            pending: list[tuple[str, int, list[dict[str, Any]]]] = []
            for fut in as_completed(futures):
                ptype, page, rows, exhausted = fut.result()
                if exhausted:
                    cur = exhaust_at.get(ptype)
                    exhaust_at[ptype] = min(page, cur) if cur else page
                pending.append((ptype, page, rows))
            for ptype, page, rows in pending:
                limit = exhaust_at.get(ptype)
                if limit is not None and page > limit:
                    continue
                out.extend(rows)
    return out


def recent_buyback_filings(
    *,
    lookback_days: int = 30,
    action: str = "all",
    repo: Repository | None = None,
    use_cache: bool = True,
) -> list[dict[str, Any]]:
    """Return buyback / dispose / cancel / trust filings.

    ``action`` filter: ``all`` | ``buyback`` | ``dispose`` | ``cancel`` | ``trust``.
    """
    cache_key = (int(lookback_days), str(action))
    if use_cache:
        hit = _cache_get(cache_key)
        if hit is not None:
            return hit

    adapter = DARTAdapter.from_settings()
    if not adapter.api_key:
        return []

    raw = _fetch_buyback_filings(adapter.api_key, lookback_days)

    out: list[dict[str, Any]] = []
    for r in raw:
        meta = _classify(r.get("report_nm") or "")
        if action != "all" and meta["action"] != action:
            continue
        filed_raw = (r.get("rcept_dt") or "").strip()
        filed_iso = (
            f"{filed_raw[0:4]}-{filed_raw[4:6]}-{filed_raw[6:8]}"
            if len(filed_raw) == 8 and filed_raw.isdigit()
            else filed_raw
        )
        out.append(
            {
                "date": filed_iso,
                "corp_code": r.get("corp_code"),
                "corp_name": r.get("corp_name"),
                "stock_code": r.get("stock_code"),
                "report_name": (r.get("report_nm") or "").strip(),
                "action": meta["action"],
                "status": meta["status"],
                "receipt_no": r.get("rcept_no"),
            }
        )

    out.sort(key=lambda r: (r.get("date") or "", r.get("receipt_no") or ""), reverse=True)

    # Persist.
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
                            "action": row["action"],
                            "status": row["status"],
                            "stock_code": row["stock_code"],
                        },
                    }
                    for row in out
                    if row.get("receipt_no")
                ]
            )
        except Exception:  # noqa: BLE001
            log.exception("buyback: persist filings failed")

    if use_cache:
        _cache_set(cache_key, out)
    return out


def buyback_summary(
    *,
    lookback_days: int = 30,
    repo: Repository | None = None,
    use_cache: bool = True,
) -> dict[str, Any]:
    rows = recent_buyback_filings(
        lookback_days=lookback_days,
        action="all",
        repo=repo,
        use_cache=use_cache,
    )
    kpi = {
        "total": len(rows),
        "buyback_decision": sum(1 for r in rows if r["action"] == "buyback" and r["status"] == "decision"),
        "buyback_result": sum(1 for r in rows if r["action"] == "buyback" and r["status"] == "result"),
        "cancel": sum(1 for r in rows if r["action"] == "cancel"),
        "trust": sum(1 for r in rows if r["action"] == "trust"),
        "dispose": sum(1 for r in rows if r["action"] == "dispose"),
        "lookback_days": lookback_days,
    }
    return {"kpi": kpi, "rows": rows}
