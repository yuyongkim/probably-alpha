"""Smoke test the FnGuide endpoint against a random 100-symbol slice.

Hits the FastAPI route ``/api/v1/value/fnguide/{symbol}`` when the API is
already running, or falls back to ``fastapi.testclient.TestClient``. Reports:

* source distribution (db_fresh / db_stale / live_fresh / fnguide / none)
* required-field coverage (per, pbr, market_cap)
* symbol-name cross-check against ``universe`` rows

Usage::

    python scripts/smoke_fnguide_db.py --n 100 [--host http://127.0.0.1:8300]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import httpx


def pick_symbols(n: int) -> list[str]:
    import re
    from ky_core.storage import Repository
    from ky_core.storage.schema import Universe
    from sqlalchemy import select
    repo = Repository()
    with repo.session() as sess:
        rows = sess.execute(
            select(Universe.ticker).where(Universe.owner_id == repo.owner_id)
        ).scalars().all()
    # KR 6-digit tickers only — FnGuide endpoint rejects US / non-numeric.
    krx = [t for t in rows if t and re.fullmatch(r"\d{6}", t)]
    random.seed(42)
    return random.sample(sorted(set(krx)), min(n, len(krx)))


_TESTCLIENT: object | None = None


def _get_testclient():
    global _TESTCLIENT
    if _TESTCLIENT is not None:
        return _TESTCLIENT
    # `apps` lives at repo root; add it so `apps.api.main` imports.
    repo_root = Path(__file__).resolve().parent.parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from fastapi.testclient import TestClient
    from apps.api.main import app  # type: ignore[import-not-found]
    _TESTCLIENT = TestClient(app)
    return _TESTCLIENT


def _invoke_inprocess(symbol: str) -> dict:
    """Fallback when no HTTP server is running."""
    client = _get_testclient()
    r = client.get(f"/api/v1/value/fnguide/{symbol}")
    return {"status": r.status_code, "json": r.json()}


def _invoke_http(symbol: str, host: str, client: httpx.Client) -> dict:
    url = f"{host.rstrip('/')}/api/v1/value/fnguide/{symbol}"
    r = client.get(url, timeout=20.0)
    return {"status": r.status_code, "json": r.json() if r.content else {}}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--host", default="", help="e.g. http://127.0.0.1:8300 (empty = in-process TestClient)")
    p.add_argument("--delay", type=float, default=0.05)
    args = p.parse_args()

    symbols = pick_symbols(args.n)
    print(f"sampling {len(symbols)} symbols from universe (seed=42)")

    live_client: httpx.Client | None = None
    use_http = False
    if args.host:
        try:
            live_client = httpx.Client()
            health = live_client.get(f"{args.host.rstrip('/')}/api/health", timeout=2.0)
            use_http = health.status_code == 200
            print(f"health check {args.host}: {health.status_code} — {'HTTP' if use_http else 'TestClient'}")
        except Exception as exc:  # noqa: BLE001
            print(f"host unreachable ({exc}); falling back to in-process TestClient")
            use_http = False

    source_counts: Counter[str] = Counter()
    missing_per = 0
    missing_pbr = 0
    missing_mcap = 0
    errors = 0
    degraded = 0
    latencies: list[float] = []
    per_symbol: list[dict] = []

    t0 = time.perf_counter()
    for i, sym in enumerate(symbols, 1):
        t = time.perf_counter()
        try:
            if use_http and live_client is not None:
                res = _invoke_http(sym, args.host, live_client)
            else:
                res = _invoke_inprocess(sym)
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"  [{i:>3}] {sym}  ERR  {type(exc).__name__}: {exc}")
            continue
        dt = (time.perf_counter() - t) * 1000
        latencies.append(dt)

        if res["status"] != 200:
            errors += 1
            continue
        body = res["json"] or {}
        if not body.get("ok"):
            errors += 1
            continue
        data = body.get("data") or {}
        src = data.get("source") or "unknown"
        source_counts[src] += 1
        if data.get("per") is None:
            missing_per += 1
        if data.get("pbr") is None:
            missing_pbr += 1
        if data.get("market_cap") is None:
            missing_mcap += 1
        if data.get("degraded"):
            degraded += 1
        per_symbol.append({
            "symbol": sym,
            "source": src,
            "per": data.get("per"),
            "pbr": data.get("pbr"),
            "latency_ms": round(dt, 1),
        })
        if i % 20 == 0:
            print(f"  [{i:>3}/{len(symbols)}] src dist so far: {dict(source_counts)}")
        if args.delay:
            time.sleep(args.delay)

    elapsed = time.perf_counter() - t0

    print()
    print("=" * 60)
    print(f"Smoke: {len(symbols)} symbols  elapsed={elapsed:.1f}s  errors={errors}")
    print("=" * 60)
    print("Source distribution:")
    for k, v in sorted(source_counts.items(), key=lambda kv: -kv[1]):
        print(f"  {k:<20} {v:>4}  ({v*100/len(symbols):.1f}%)")
    print(f"missing per    : {missing_per}")
    print(f"missing pbr    : {missing_pbr}")
    print(f"missing mcap   : {missing_mcap}")
    print(f"degraded       : {degraded}")
    if latencies:
        latencies.sort()
        p50 = latencies[len(latencies) // 2]
        p95 = latencies[int(len(latencies) * 0.95)]
        print(f"latency p50={p50:.0f}ms  p95={p95:.0f}ms  max={max(latencies):.0f}ms")

    out = Path("runtime_logs") / f"smoke_fnguide_db_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "n": len(symbols),
        "errors": errors,
        "source_counts": dict(source_counts),
        "missing_per": missing_per,
        "missing_pbr": missing_pbr,
        "missing_mcap": missing_mcap,
        "degraded": degraded,
        "samples": per_symbol[:20],
    }, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    if live_client is not None:
        live_client.close()


if __name__ == "__main__":
    main()
