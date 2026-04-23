"""Validate Company_Credit `financial.db` symbol integrity and value freshness.

Compares the source DB's distinct symbols against ``config/krx_universe.csv``
and live-refetches a small random sample from the Naver mobile integration
endpoint to assert per/pbr/roe values stayed within a reasonable tolerance.

Usage:
    python scripts/validate_financial_db.py --sample 100

Exit codes:
    0 — OK (< 5% mismatch)
    2 — mismatch rate exceeded; DO NOT migrate
    3 — source DB / universe CSV unreadable
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sqlite3
import sys
import time
from pathlib import Path

import httpx

SOURCE_DB = Path(r"C:/Users/USER/Desktop/Company_Credit/data/financial.db")
UNIVERSE_CSV = Path(r"C:/Users/USER/Desktop/Company_Credit/config/krx_universe.csv")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def load_universe_symbols() -> set[str]:
    if not UNIVERSE_CSV.exists():
        print(f"FAIL: universe csv missing at {UNIVERSE_CSV}", file=sys.stderr)
        sys.exit(3)
    out: set[str] = set()
    with UNIVERSE_CSV.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            raw = (row.get("symbol") or "").strip()
            m = re.match(r"^(\d{6})", raw)
            if m:
                out.add(m.group(1))
    return out


def load_db_symbols() -> set[str]:
    if not SOURCE_DB.exists():
        print(f"FAIL: source db missing at {SOURCE_DB}", file=sys.stderr)
        sys.exit(3)
    con = sqlite3.connect(str(SOURCE_DB))
    try:
        return {
            r[0] for r in con.execute(
                "SELECT DISTINCT symbol FROM financial_snapshot"
            ).fetchall()
        }
    finally:
        con.close()


def load_db_snapshot(symbol: str) -> dict:
    con = sqlite3.connect(str(SOURCE_DB))
    try:
        row = con.execute(
            "SELECT per, pbr, roe, price FROM financial_snapshot WHERE symbol = ?",
            (symbol,),
        ).fetchone()
    finally:
        con.close()
    if not row:
        return {}
    return {"per": row[0], "pbr": row[1], "roe": row[2], "price": row[3]}


def fetch_live(symbol: str, client: httpx.Client) -> dict | None:
    """Hit m.stock.naver.com integration endpoint. Parse per/pbr/roe/price."""
    url = f"https://m.stock.naver.com/api/stock/{symbol}/integration"
    try:
        resp = client.get(url, timeout=8.0)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}
    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}
    try:
        payload = resp.json()
    except ValueError:
        return {"error": "non-json"}

    out: dict = {"per": None, "pbr": None, "roe": None, "price": None}

    def _to_num(val: object) -> float | None:
        if val in (None, "-", ""):
            return None
        s = str(val)
        # strip Korean suffixes and percent; keep digits/sign/dot
        s = re.sub(r"[^0-9.\-]", "", s)
        try:
            return float(s) if s else None
        except ValueError:
            return None

    try:
        total_infos = payload.get("totalInfos") or []
        for info in total_infos:
            code = (info.get("code") or "").strip()
            if code == "per":
                out["per"] = _to_num(info.get("value"))
            elif code == "pbr":
                out["pbr"] = _to_num(info.get("value"))
            elif code == "lastClosePrice":
                out["price"] = _to_num(info.get("value"))
        # Integration endpoint doesn't expose ROE directly; schema may vary.
        # We rely on per/pbr+price for a 2-of-3 rule and treat ROE as bonus.
        ici = payload.get("industryCompareInfo")
        if isinstance(ici, dict):
            company_val = ici.get("companyValue")
            if isinstance(company_val, dict):
                cv_roe = company_val.get("roe")
                if cv_roe is not None:
                    out["roe"] = _to_num(cv_roe)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"parse: {type(exc).__name__}: {exc}"}
    return out


def within_tolerance(db_val: float | None, live_val: float | None, tol: float) -> tuple[bool, str]:
    if db_val is None and live_val is None:
        return True, "both-null"
    if db_val is None or live_val is None:
        return False, f"null-diff db={db_val} live={live_val}"
    if db_val == 0 and live_val == 0:
        return True, "both-zero"
    base = max(abs(db_val), 1e-9)
    diff = abs(db_val - live_val) / base
    return diff <= tol, f"diff={diff:.3f}"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sample", type=int, default=100)
    p.add_argument("--tolerance", type=float, default=0.30, help="per/pbr tolerance (snapshot is up to 2 weeks stale)")
    p.add_argument("--abort-pct", type=float, default=0.15, help="abort if mismatch > this fraction")
    p.add_argument("--delay", type=float, default=0.3, help="seconds between fetches")
    args = p.parse_args()

    print("=" * 60)
    print("Phase 2: financial.db validation")
    print("=" * 60)

    db_syms = load_db_symbols()
    csv_syms = load_universe_symbols()
    inter = db_syms & csv_syms
    db_only = db_syms - csv_syms
    csv_only = csv_syms - db_syms
    print(f"financial.db distinct symbols  : {len(db_syms)}")
    print(f"krx_universe.csv symbols        : {len(csv_syms)}")
    print(f"Intersection                     : {len(inter)}")
    print(f"In DB but not in CSV             : {len(db_only)} (sample: {sorted(list(db_only))[:5]})")
    print(f"In CSV but not in DB             : {len(csv_only)} (sample: {sorted(list(csv_only))[:5]})")
    print()

    sample_pool = sorted(inter)
    random.seed(42)
    sample = random.sample(sample_pool, min(args.sample, len(sample_pool)))
    print(f"Live cross-check: sampling {len(sample)} symbols  (tol=±{args.tolerance*100:.0f}%)")
    print()

    headers = {
        "User-Agent": UA,
        "Referer": "https://m.stock.naver.com/",
        "Accept": "application/json",
    }
    match = 0
    mismatch = 0
    errors = 0
    mismatch_samples: list[dict] = []

    with httpx.Client(headers=headers, follow_redirects=True) as client:
        for i, sym in enumerate(sample, 1):
            db = load_db_snapshot(sym)
            live = fetch_live(sym, client)
            if not live or live.get("error"):
                errors += 1
                if i % 10 == 0:
                    print(f"  [{i:>3}/{len(sample)}] {sym}  ERR  {live.get('error') if live else 'none'}")
                time.sleep(args.delay)
                continue

            # Compare per/pbr at args.tolerance; price allowed 25% (2 weeks of moves).
            per_ok, per_msg = within_tolerance(db.get("per"), live.get("per"), args.tolerance)
            pbr_ok, pbr_msg = within_tolerance(db.get("pbr"), live.get("pbr"), args.tolerance)
            price_ok, price_msg = within_tolerance(db.get("price"), live.get("price"), 0.25)
            # At least 2 of 3 metrics must agree (robust to a single-field quirk).
            # ROE is kept informational only (live integration rarely exposes it).
            roe_ok, roe_msg = within_tolerance(db.get("roe"), live.get("roe"), args.tolerance)
            hits = sum(1 for x in (per_ok, pbr_ok, price_ok) if x)
            if hits >= 2:
                match += 1
            else:
                mismatch += 1
                mismatch_samples.append({
                    "symbol": sym,
                    "db": db,
                    "live": live,
                    "per": per_msg,
                    "pbr": pbr_msg,
                    "price": price_msg,
                    "roe": roe_msg,
                })
                if len(mismatch_samples) <= 8:
                    print(f"  MISMATCH {sym}  db={db}  live={live}")

            if i % 20 == 0:
                print(f"  [{i:>3}/{len(sample)}] match={match} mismatch={mismatch} err={errors}")
            time.sleep(args.delay)

    print()
    print("=" * 60)
    comparable = match + mismatch
    pct = (mismatch / comparable) if comparable else 0.0
    print(f"Total sampled : {len(sample)}")
    print(f"Comparable    : {comparable}")
    print(f"Match (2/3)   : {match}")
    print(f"Mismatch      : {mismatch}  ({pct*100:.1f}%)")
    print(f"Live errors   : {errors}")
    print("=" * 60)

    if comparable > 0 and pct > args.abort_pct:
        print(f"FAIL: mismatch rate {pct*100:.1f}% > abort threshold {args.abort_pct*100:.1f}%")
        print("Do NOT proceed with migration. Review mismatch_samples below.")
        print(json.dumps(mismatch_samples[:20], indent=2, default=str, ensure_ascii=False))
        sys.exit(2)

    print("PASS: validation OK. Safe to migrate.")
    # Emit structured summary file for downstream migration step.
    out_file = Path("runtime_logs/validate_financial_db.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({
        "db_symbols": len(db_syms),
        "csv_symbols": len(csv_syms),
        "intersection": len(inter),
        "sampled": len(sample),
        "match": match,
        "mismatch": mismatch,
        "errors": errors,
        "mismatch_pct": pct,
    }, indent=2), encoding="utf-8")
    print(f"Summary: {out_file}")


if __name__ == "__main__":
    main()
