"""Back-fill DART 사업부문별 매출 for the top-50 KOSPI names.

This is the focused dry-run that validates the 2026-04 segments.py parser
heuristic rewrite (port of F:/SEC disclosure-parser section-scoping). It
mirrors ``backfill_segments.py`` but is tuned for diagnostics:

* Hard-coded top-50 by market cap (universe join, fnguide payload).
* Per-symbol parse-stage log — ``no_corp_code``, ``no_receipt``,
  ``parse_empty`` (heuristic reject / no tables), ``ok``.
* Captures ALL extracted segments per symbol (not just the first 6) so
  we can eyeball whether Samsung→DS/DX/SDC and Hyundai→국내자동차/해외
  actually come through.
* Emits ``runtime_logs/backfill_segments_top50_<ts>.json``.

Usage::

    python scripts/backfill_segments_top50.py
    python scripts/backfill_segments_top50.py --limit 100 --sleep 0.4
    python scripts/backfill_segments_top50.py --symbols 005930,000660,005380

Wire-call budget: ~1 corpCode download + ~2 DART calls × N symbols. With
default sleep=0.5s, a 50-symbol run takes ~90s end-to-end.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
for sub in ("packages/core", "packages/adapters"):
    p = ROOT / sub
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("backfill_segments_top50")


def _load_corp_code_map(dart) -> dict[str, str]:
    """Return ``{symbol → corp_code}`` from DART's corpCode.xml endpoint."""
    import zipfile
    import io
    import xml.etree.ElementTree as ET

    if not getattr(dart, "api_key", None):
        log.warning("DART_API_KEY missing — corp_code map unavailable")
        return {}
    try:
        resp = dart._request(
            "GET",
            f"{dart.base_url}/corpCode.xml",
            params={"crtfc_key": dart.api_key},
            timeout=30.0,
        )
    except Exception as exc:  # noqa: BLE001
        log.error("corp_code download failed: %s", exc)
        return {}
    if resp.status_code != 200 or not resp.content:
        log.error("corp_code HTTP %s", resp.status_code)
        return {}
    try:
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        xml_name = next(n for n in zf.namelist() if n.endswith(".xml"))
        root = ET.fromstring(zf.read(xml_name))
    except Exception as exc:  # noqa: BLE001
        log.error("corp_code parse failed: %s", exc)
        return {}
    mapping: dict[str, str] = {}
    for node in root.findall("list"):
        stock = (node.findtext("stock_code") or "").strip()
        corp = (node.findtext("corp_code") or "").strip()
        if stock and corp:
            mapping[stock] = corp
    log.info("corp_code map loaded: %d entries", len(mapping))
    return mapping


def _candidate_symbols(repo, limit: int) -> list[dict[str, Any]]:
    """Top-N symbols by fnguide-payload market_cap."""
    from sqlalchemy import text
    q = text(
        """
        SELECT u.ticker, u.name, u.sector, u.market, f.payload
          FROM universe u
          LEFT JOIN fnguide_snapshots f
                 ON f.symbol = u.ticker
                AND f.owner_id = u.owner_id
         WHERE u.owner_id = :oid
           AND u.is_etf = 0
           AND u.market IN ('KOSPI','KOSDAQ')
        """
    )
    with repo.session() as sess:
        rows = sess.execute(q, {"oid": repo.owner_id}).fetchall()
    out: list[dict[str, Any]] = []
    for ticker, name, sector, market, payload_json in rows:
        mcap: Optional[float] = None
        if payload_json:
            try:
                payload = json.loads(payload_json)
                mcap = payload.get("market_cap") or payload.get("market_cap_raw")
            except Exception:  # noqa: BLE001
                mcap = None
        out.append(
            {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "market": market,
                "market_cap": float(mcap) if isinstance(mcap, (int, float)) else None,
            }
        )
    out.sort(key=lambda r: (r.get("market_cap") or 0), reverse=True)
    return out[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50, help="Top N by market cap")
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated override (ignores --limit)")
    parser.add_argument("--sleep", type=float, default=0.5, help="Seconds between DART calls")
    parser.add_argument("--dry-run", action="store_true", help="Parse only; skip DB persist")
    args = parser.parse_args()

    from ky_adapters.dart import DARTAdapter, DARTSegmentExtractor
    from ky_core.storage import Repository

    repo = Repository()
    dart = DARTAdapter.from_settings()
    extractor = DARTSegmentExtractor.from_settings()

    if not extractor.api_key:
        log.error("DART_API_KEY not configured — aborting")
        return 2

    corp_map = _load_corp_code_map(dart)
    if args.symbols:
        sym_rows = [
            {"ticker": s.strip(), "name": None, "sector": None, "market": None, "market_cap": None}
            for s in args.symbols.split(",") if s.strip()
        ]
    else:
        sym_rows = _candidate_symbols(repo, args.limit)

    log.info("backfill target: %d symbols (dry_run=%s)", len(sym_rows), args.dry_run)

    stats: dict[str, Any] = {
        "attempted": 0,
        "no_corp_code": 0,
        "no_receipt": 0,
        "parse_empty": 0,
        "extractor_error": 0,
        "persisted_rows": 0,
        "symbols_ok": 0,
        "started_at": datetime.utcnow().isoformat(),
        "per_symbol": [],
        "dry_run": args.dry_run,
    }

    persisted_rows = 0
    for idx, row in enumerate(sym_rows, 1):
        ticker = row["ticker"]
        stats["attempted"] += 1
        corp = corp_map.get(ticker)
        record: dict[str, Any] = {
            "symbol": ticker,
            "name": row.get("name"),
            "sector": row.get("sector"),
            "market_cap": row.get("market_cap"),
            "stage": None,
            "segment_count": 0,
            "segments": [],
        }
        if not corp:
            stats["no_corp_code"] += 1
            record["stage"] = "no_corp_code"
            stats["per_symbol"].append(record)
            log.info("[%d/%d] %s %s — no corp_code",
                     idx, len(sym_rows), ticker, row.get("name") or "")
            continue

        # Stage 1: receipt lookup
        try:
            rcept = extractor.find_latest_annual_receipt(corp)
        except Exception as exc:  # noqa: BLE001
            stats["extractor_error"] += 1
            record["stage"] = "extractor_error"
            record["error"] = f"receipt lookup: {exc}"
            stats["per_symbol"].append(record)
            log.warning("[%d/%d] %s receipt lookup failed: %s",
                        idx, len(sym_rows), ticker, exc)
            time.sleep(args.sleep)
            continue

        if not rcept:
            stats["no_receipt"] += 1
            record["stage"] = "no_receipt"
            stats["per_symbol"].append(record)
            log.info("[%d/%d] %s %s — no annual receipt",
                     idx, len(sym_rows), ticker, row.get("name") or "")
            time.sleep(args.sleep)
            continue

        receipt_no, period_end = rcept
        record["receipt_no"] = receipt_no
        record["period_end"] = period_end

        # Stage 2 + 3: fetch + parse (extract_segments combines both)
        try:
            segments = extractor.extract_segments(ticker, corp)
        except Exception as exc:  # noqa: BLE001
            stats["extractor_error"] += 1
            record["stage"] = "extractor_error"
            record["error"] = f"extract: {exc}"
            stats["per_symbol"].append(record)
            log.warning("[%d/%d] %s extract failed: %s",
                        idx, len(sym_rows), ticker, exc)
            time.sleep(args.sleep)
            continue

        if not segments:
            stats["parse_empty"] += 1
            record["stage"] = "parse_empty"
            stats["per_symbol"].append(record)
            log.info("[%d/%d] %s %s — parse_empty",
                     idx, len(sym_rows), ticker, row.get("name") or "")
            time.sleep(args.sleep)
            continue

        # Stage 4: persist
        record["stage"] = "ok"
        record["segment_count"] = len(segments)
        record["segments"] = [
            {
                "name": s.segment_name,
                "revenue": s.revenue,
                "operating_income": s.operating_income,
                "share": s.revenue_share,
            }
            for s in segments
        ]

        if not args.dry_run:
            payload = [s.as_row() for s in segments]
            n = repo.upsert_segments(payload)
            persisted_rows += n
            record["persisted"] = n
        else:
            record["persisted"] = 0

        stats["symbols_ok"] += 1
        stats["per_symbol"].append(record)
        log.info(
            "[%d/%d] %s %s — %d segments ok",
            idx, len(sym_rows), ticker, row.get("name") or "", len(segments),
        )
        time.sleep(args.sleep)

    stats["persisted_rows"] = persisted_rows
    stats["finished_at"] = datetime.utcnow().isoformat()

    runtime = ROOT / "runtime_logs"
    runtime.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = runtime / f"backfill_segments_top50_{ts}.json"
    out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("summary → %s", out_path)
    log.info(
        "done. attempted=%d ok=%d persisted=%d parse_empty=%d no_corp=%d no_receipt=%d err=%d",
        stats["attempted"], stats["symbols_ok"], stats["persisted_rows"],
        stats["parse_empty"], stats["no_corp_code"], stats["no_receipt"],
        stats["extractor_error"],
    )
    return 0 if stats["symbols_ok"] >= stats["attempted"] * 0.5 else 1


if __name__ == "__main__":
    raise SystemExit(main())
