"""Back-fill DART DPS history for current-yield > 2% symbols.

Usage:
    python scripts/backfill_dividends.py                     # default: 200 top yield
    python scripts/backfill_dividends.py --limit 400
    python scripts/backfill_dividends.py --min-yield 0.5
    python scripts/backfill_dividends.py --symbols 005930,000660

Strategy:
  1. Read universe ∪ fnguide_snapshots, filter to dividend_yield > min.
  2. Resolve corp_code via DART's corpCode.xml.
  3. For each symbol walk 4 annual filings (covers ~10y of DPS).
  4. Persist to ``dividend_history``.

Summary JSON lands in ``runtime_logs/backfill_dividends_<ts>.json``.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for sub in ("packages/core", "packages/adapters"):
    p = ROOT / sub
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("backfill_dividends")


def _load_corp_code_map(dart) -> dict[str, str]:
    import zipfile
    import io
    import xml.etree.ElementTree as ET

    if not getattr(dart, "api_key", None):
        return {}
    try:
        resp = dart._request(
            "GET",
            f"{dart.base_url}/corpCode.xml",
            params={"crtfc_key": dart.api_key},
            timeout=30.0,
        )
    except Exception as exc:  # noqa: BLE001
        log.error("corpCode download failed: %s", exc)
        return {}
    if resp.status_code != 200:
        return {}
    try:
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        xml_name = next(n for n in zf.namelist() if n.endswith(".xml"))
        root = ET.fromstring(zf.read(xml_name))
    except Exception:  # noqa: BLE001
        return {}
    mapping: dict[str, str] = {}
    for node in root.findall("list"):
        stock = (node.findtext("stock_code") or "").strip()
        corp = (node.findtext("corp_code") or "").strip()
        if stock and corp:
            mapping[stock] = corp
    log.info("corp_code map loaded: %d entries", len(mapping))
    return mapping


def _candidate_symbols(repo, min_yield: float, limit: int) -> list[dict[str, Any]]:
    from sqlalchemy import text
    q = text(
        """
        SELECT u.ticker, u.name, f.payload
          FROM universe u
          JOIN fnguide_snapshots f
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
    for ticker, name, payload_json in rows:
        dy = None
        if payload_json:
            try:
                dy = (json.loads(payload_json) or {}).get("dividend_yield")
            except Exception:  # noqa: BLE001
                dy = None
        try:
            dyv = float(dy) if dy is not None else None
        except (TypeError, ValueError):
            dyv = None
        if dyv is None or dyv < min_yield:
            continue
        out.append({"ticker": ticker, "name": name, "dividend_yield": dyv})
    out.sort(key=lambda r: r["dividend_yield"], reverse=True)
    return out[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--min-yield", type=float, default=2.0,
                        help="Filter by fnguide dividend_yield (%%).")
    parser.add_argument("--symbols", type=str, default=None)
    parser.add_argument("--sleep", type=float, default=0.3)
    args = parser.parse_args()

    from ky_adapters.dart import DARTAdapter, DARTDividendExtractor
    from ky_core.storage import Repository

    repo = Repository()
    dart = DARTAdapter.from_settings()
    extractor = DARTDividendExtractor.from_settings()

    if not extractor.api_key:
        log.error("DART_API_KEY not configured — aborting")
        return 2

    corp_map = _load_corp_code_map(dart)
    if args.symbols:
        candidates = [{"ticker": s.strip(), "name": None, "dividend_yield": None}
                      for s in args.symbols.split(",") if s.strip()]
    else:
        candidates = _candidate_symbols(repo, args.min_yield, args.limit)

    log.info("dividend backfill target: %d symbols", len(candidates))

    stats = {
        "attempted": 0,
        "no_corp_code": 0,
        "no_rows": 0,
        "symbols_ok": 0,
        "rows_persisted": 0,
        "started_at": datetime.utcnow().isoformat(),
        "samples": [],
    }

    for row in candidates:
        ticker = row["ticker"]
        stats["attempted"] += 1
        corp = corp_map.get(ticker)
        if not corp:
            stats["no_corp_code"] += 1
            continue
        try:
            years = extractor.extract_history(ticker, corp)
        except Exception as exc:  # noqa: BLE001
            log.warning("[%s] extract failed: %s", ticker, exc)
            stats["no_rows"] += 1
            continue
        common_rows = [y for y in years if y.share_type == "common" and y.dps is not None]
        if not common_rows:
            stats["no_rows"] += 1
            continue
        persisted = repo.upsert_dividend_history([y.as_row() for y in years])
        stats["rows_persisted"] += persisted
        stats["symbols_ok"] += 1
        if len(stats["samples"]) < 5:
            stats["samples"].append(
                {
                    "symbol": ticker,
                    "name": row.get("name"),
                    "dps_years": [
                        {"period_end": y.period_end, "dps": y.dps}
                        for y in common_rows[-10:]
                    ],
                }
            )
        log.info("[%s] %d DPS years (%s)", ticker, len(common_rows), row.get("name"))
        time.sleep(args.sleep)

    stats["finished_at"] = datetime.utcnow().isoformat()
    runtime = ROOT / "runtime_logs"
    runtime.mkdir(exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = runtime / f"backfill_dividends_{ts}.json"
    out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("summary → %s", out_path)
    log.info(
        "done. attempted=%d ok=%d rows=%d no_corp=%d no_rows=%d",
        stats["attempted"], stats["symbols_ok"], stats["rows_persisted"],
        stats["no_corp_code"], stats["no_rows"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
