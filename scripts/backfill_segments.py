"""Back-fill DART segment (사업부문별 매출) data for the top-N symbols.

Usage:
    python scripts/backfill_segments.py                       # default: top 50
    python scripts/backfill_segments.py --limit 100
    python scripts/backfill_segments.py --symbols 005930,000660

Reads the universe table, ranks by fnguide market_cap (desc), then walks the
OpenDART document.xml endpoint for each corp_code and parses the 사업부문
table. Persists to ``financial_segments``. Emits a JSON summary to
``runtime_logs/backfill_segments_<ts>.json``.

The parser is best-effort; the summary counts success / fail-to-parse /
no-receipt / no-corp-code.
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backfill_segments")


def _load_corp_code_map(dart) -> dict[str, str]:
    """Return ``{symbol → corp_code}`` from DART's corpCode.xml endpoint.

    Cached in memory for the lifetime of the process. Falls back to an empty
    map on any error (caller will then skip symbols with no mapping).
    """
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
    """Top-N symbols by market_cap. Uses fnguide snapshot payload."""
    from sqlalchemy import text
    q = text(
        """
        SELECT u.ticker, u.name, u.sector, f.payload
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
    for ticker, name, sector, payload_json in rows:
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
                "market_cap": float(mcap) if isinstance(mcap, (int, float)) else None,
            }
        )
    out.sort(key=lambda r: (r.get("market_cap") or 0), reverse=True)
    return out[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=50, help="Top N symbols by market cap")
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated override")
    parser.add_argument("--sleep", type=float, default=0.5, help="Seconds between DART calls")
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
        sym_rows = [{"ticker": s.strip(), "name": None, "sector": None, "market_cap": None}
                    for s in args.symbols.split(",") if s.strip()]
    else:
        sym_rows = _candidate_symbols(repo, args.limit)

    log.info("backfill target: %d symbols", len(sym_rows))

    stats = {
        "attempted": 0,
        "no_corp_code": 0,
        "no_receipt": 0,
        "parse_empty": 0,
        "persisted": 0,
        "symbols_ok": 0,
        "started_at": datetime.utcnow().isoformat(),
        "samples": [],
    }

    persisted_rows = 0
    for row in sym_rows:
        ticker = row["ticker"]
        stats["attempted"] += 1
        corp = corp_map.get(ticker)
        if not corp:
            stats["no_corp_code"] += 1
            continue
        try:
            segments = extractor.extract_segments(ticker, corp)
        except Exception as exc:  # noqa: BLE001
            log.warning("extractor failed for %s: %s", ticker, exc)
            stats["parse_empty"] += 1
            continue
        if not segments:
            stats["parse_empty"] += 1
            continue
        payload = [s.as_row() for s in segments]
        n = repo.upsert_segments(payload)
        persisted_rows += n
        stats["symbols_ok"] += 1
        if len(stats["samples"]) < 5:
            stats["samples"].append(
                {
                    "symbol": ticker,
                    "name": row.get("name"),
                    "segments": [
                        {
                            "name": s.segment_name,
                            "revenue": s.revenue,
                            "share": s.revenue_share,
                        }
                        for s in segments[:6]
                    ],
                }
            )
        log.info("[%s] %d segments persisted (%s)", ticker, len(segments), row.get("name"))
        time.sleep(args.sleep)

    stats["persisted"] = persisted_rows
    stats["finished_at"] = datetime.utcnow().isoformat()

    runtime = ROOT / "runtime_logs"
    runtime.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = runtime / f"backfill_segments_{ts}.json"
    out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("summary → %s", out_path)
    log.info(
        "done. attempted=%d ok=%d persisted_rows=%d parse_empty=%d no_corp=%d",
        stats["attempted"], stats["symbols_ok"], stats["persisted"],
        stats["parse_empty"], stats["no_corp_code"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
