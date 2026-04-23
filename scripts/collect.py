#!/usr/bin/env python
"""ky-platform data collection runner.

Examples:
    python scripts/collect.py --healthcheck
    python scripts/collect.py --source fred --series GDP,CPIAUCSL --start 2020-01-01
    python scripts/collect.py --source ecos --stat 722Y001 --item 0101000 --freq D \\
        --start 20240101 --end 20241231
    python scripts/collect.py --source eia --series WCESTUS1
    python scripts/collect.py --source exim
    python scripts/collect.py --source dart --corp-code 00126380 --days 30
    python scripts/collect.py --source all-macro --start 2016-01-01

Results are upserted into SQLite (``~/.ky-platform/data/ky.db``).
Logs are written to ``runtime_logs/collect_<timestamp>.log``.
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

# ---- make sibling packages importable ---- #
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "packages" / "adapters", ROOT / "packages" / "core"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from ky_adapters.dart import DARTAdapter
from ky_adapters.ecos import ECOSAdapter
from ky_adapters.eia import EIAAdapter
from ky_adapters.exim import EXIMAdapter
from ky_adapters.fred import FREDAdapter
from ky_adapters.kis import KISAdapter
from ky_adapters.kosis import KOSISAdapter
from ky_core.storage import Repository
from ky_core.storage.presets import (
    ECOS_SERIES,
    EIA_SERIES,
    FRED_SERIES,
    KOSIS_SERIES,
)

LOG_DIR = ROOT / "runtime_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _setup_logging(prefix: str = "collect") -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{prefix}_{ts}.log"
    # Force UTF-8 on Windows stdout so Korean text / em-dashes don't crash.
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.handlers.clear()
    root.addHandler(fh)
    root.addHandler(sh)
    return log_path


log = logging.getLogger("collect")


# --------------------------------------------------------------------------- #
# Healthcheck                                                                 #
# --------------------------------------------------------------------------- #


def cmd_healthcheck() -> int:
    adapters = [
        FREDAdapter.from_settings(),
        ECOSAdapter.from_settings(),
        KOSISAdapter.from_settings(),
        EIAAdapter.from_settings(),
        EXIMAdapter.from_settings(),
        DARTAdapter.from_settings(),
        KISAdapter.from_settings(),
    ]
    failed = 0
    for a in adapters:
        try:
            h = a.healthcheck()
        except Exception as exc:  # noqa: BLE001
            h = {"ok": False, "source_id": a.source_id, "last_error": str(exc)}
        finally:
            a.close()
        status = "OK" if h.get("ok") else "FAIL"
        log.info("healthcheck %-6s %s %s", a.source_id, status, h)
        if not h.get("ok") and a.source_id != "kis":
            failed += 1
    return 0 if failed == 0 else 1


# --------------------------------------------------------------------------- #
# Per-source collectors                                                       #
# --------------------------------------------------------------------------- #


def _parse_date(raw: str | None, default: date) -> date:
    if not raw:
        return default
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    raise SystemExit(f"Invalid date: {raw!r}")


def _ecos_bounds(start_iso: str, end_iso: str, freq: str) -> tuple[str, str]:
    """Translate an ISO (start,end) window into the cycle-specific format ECOS
    expects. ``start_iso``/``end_iso`` are ``YYYY-MM-DD``."""
    s = start_iso.replace("-", "")
    e = end_iso.replace("-", "")
    if freq == "D":
        return s, e  # YYYYMMDD
    if freq == "M":
        return s[:6], e[:6]  # YYYYMM
    if freq == "Q":
        # Map month -> quarter
        def _to_q(d: str) -> str:
            month = int(d[4:6])
            q = (month - 1) // 3 + 1
            return f"{d[:4]}Q{q}"
        return _to_q(s), _to_q(e)
    # Annual
    return s[:4], e[:4]


def collect_fred(series_ids: list[str], start: date, end: date, repo: Repository) -> int:
    fetched = 0
    with FREDAdapter.from_settings() as fred:
        for sid in series_ids:
            log.info("FRED fetching %s %s → %s", sid, start, end)
            try:
                obs = fred.get_series(sid, start=start, end=end)
            except Exception as exc:  # noqa: BLE001
                log.error("FRED %s failed: %s", sid, exc)
                continue
            rows = [o.as_row() for o in obs]
            written = repo.upsert_observations(rows)
            log.info("FRED %s: %d rows upserted", sid, written)
            fetched += written
    return fetched


def collect_ecos(
    series: list[tuple[str, str, str, str]],
    start_iso: str,
    end_iso: str,
    repo: Repository,
) -> int:
    """``series`` is a list of ``(stat_code, item_code, freq, description)``.

    ``start_iso`` / ``end_iso`` are ISO ``YYYY-MM-DD`` bounds; the collector
    translates them per-series into the per-frequency format ECOS needs.
    """
    fetched = 0
    with ECOSAdapter.from_settings() as ecos:
        for item in series:
            # Backwards compatible with the 3-tuple form the CLI still uses.
            if len(item) == 4:
                stat, item_code, freq, desc = item
            else:
                stat, item_code, freq = item  # type: ignore[misc]
                desc = f"{stat}/{item_code}"
            s, e = _ecos_bounds(start_iso, end_iso, freq)
            log.info(
                "ECOS fetching %s/%s freq=%s %s→%s  (%s)",
                stat, item_code, freq, s, e, desc,
            )
            try:
                obs = ecos.get_series(stat, item_code, start=s, end=e, freq=freq)
            except Exception as exc:  # noqa: BLE001
                log.error("ECOS %s/%s failed: %s", stat, item_code, exc)
                continue
            rows = [o.as_row() for o in obs]
            written = repo.upsert_observations(rows)
            log.info("ECOS %s/%s (%s): %d rows", stat, item_code, desc, written)
            fetched += written
    return fetched


def collect_eia(
    entries: list,
    start: str | None,
    end: str | None,
    repo: Repository,
) -> int:
    """Accepts either:

    - a list of bare string series ids (legacy — routed through
      ``get_series``), or
    - a list of ``(path, series_code, description)`` triples — routed
      through ``get_path_series`` (required for the petroleum/natgas
      weeklies in the daily preset).
    """
    fetched = 0
    with EIAAdapter.from_settings() as eia:
        for entry in entries:
            try:
                if isinstance(entry, str):
                    sid = entry
                    log.info("EIA fetching %s (seriesid)", sid)
                    obs = eia.get_series(sid, start=start, end=end)
                else:
                    path, code, desc = entry
                    log.info("EIA fetching %s via %s (%s)", code, path, desc)
                    obs = eia.get_path_series(path, code, start=start, end=end)
                    sid = code
            except Exception as exc:  # noqa: BLE001
                log.error("EIA %s failed: %s", entry, exc)
                continue
            rows = [o.as_row() for o in obs]
            written = repo.upsert_observations(rows)
            log.info("EIA %s: %d rows", sid, written)
            fetched += written
    return fetched


def collect_exim(repo: Repository, target: date | None = None) -> int:
    with EXIMAdapter.from_settings() as exim:
        try:
            rates = exim.get_rates(search_date=target)
        except Exception as exc:  # noqa: BLE001
            log.error("EXIM fetch failed: %s", exc)
            return 0
        rows = [r.as_row() for r in rates]
        written = repo.upsert_observations(rows)
        log.info("EXIM: %d FX rows upserted (target=%s)", written, target)
        return written


def collect_exim_range(
    repo: Repository, start: date, end: date, max_days: int = 400
) -> int:
    """Walk business days inside [start, end] and fetch EXIM rates for each.

    EXIM only publishes one snapshot per business day (weekends return empty)
    so the loop caps iterations to ``max_days`` to keep runs bounded. For the
    default 10-year window we walk forward only the last ``max_days`` business
    days, which is typically enough to bootstrap the FX series.
    """
    total = 0
    # cap window: walk up to max_days calendar days back from `end`.
    span = (end - start).days
    if span > max_days:
        log.info("EXIM range: capping backfill to last %d days (user asked %d)", max_days, span)
        start = end - timedelta(days=max_days)
    cur = start
    with EXIMAdapter.from_settings() as exim:
        while cur <= end:
            # Skip Sat/Sun fast
            if cur.weekday() < 5:
                try:
                    rates = exim.get_rates(search_date=cur)
                except Exception as exc:  # noqa: BLE001
                    log.warning("EXIM %s failed: %s", cur, exc)
                    rates = []
                if rates:
                    rows = [r.as_row() for r in rates]
                    written = repo.upsert_observations(rows)
                    total += written
            cur += timedelta(days=1)
    log.info("EXIM range: %d rows upserted across %s..%s", total, start, end)
    return total


def collect_kosis(
    entries: list[dict],
    start: str | None,
    end: str | None,
    repo: Repository,
) -> int:
    """KOSIS collector.

    Each ``entries`` dict must include ``org_id``, ``tbl_id`` and ``series_id``
    (the label we persist under). ``itm_id`` and ``obj_l1`` are required by
    the upstream API but vary per table — they live in the preset so the
    schema here is intentionally thin.
    """
    if not entries:
        log.warning(
            "KOSIS preset is empty — KOSIS table IDs must be curated via the "
            "KOSIS OpenAPI portal before bulk backfill can run. Skipping."
        )
        return 0
    fetched = 0
    with KOSISAdapter.from_settings() as kosis:
        for cfg in entries:
            org = cfg["org_id"]
            tbl = cfg["tbl_id"]
            sid = cfg["series_id"]
            try:
                rows = kosis.get_data(
                    org_id=org,
                    tbl_id=tbl,
                    item_code=cfg.get("itm_id"),
                    obj_l1=cfg.get("obj_l1"),
                    prd_se=cfg.get("prd_se", "M"),
                    start_prd=start.replace("-", "")[:6] if start else None,
                    end_prd=end.replace("-", "")[:6] if end else None,
                )
            except Exception as exc:  # noqa: BLE001
                log.error("KOSIS %s/%s failed: %s", org, tbl, exc)
                continue
            obs = []
            # When objL1=ALL each KOSIS row carries a different C1 code (e.g.
            # total/male/female or sector sub-code). We splice the C1 code
            # into the series_id so the observations unique key
            # (source_id, series_id, date, owner_id) doesn't collide across
            # obj buckets. sid already includes /ALL as a prefix marker —
            # we replace the trailing ALL with the actual bucket code.
            for row in rows:
                raw_date = (
                    row.get("PRD_DE")
                    or row.get("prdDe")
                    or row.get("prd_de")
                    or ""
                )
                raw_val = row.get("DT") or row.get("dt") or row.get("value")
                try:
                    val = float(str(raw_val).replace(",", "")) if raw_val not in (None, "") else None
                except ValueError:
                    val = None
                date_iso = _kosis_date(raw_date)
                if not date_iso:
                    continue
                c1 = row.get("C1") or row.get("c1")
                itm_in_row = row.get("ITM_ID") or row.get("itmId")
                if sid.endswith("/ALL") and c1:
                    row_sid = sid[: -len("/ALL")] + f"/{c1}"
                elif c1:
                    row_sid = f"{sid}/{c1}"
                else:
                    row_sid = sid
                # Preserve key metadata so downstream consumers can resolve
                # what C1/OBJ/ITM this row belongs to without re-querying.
                meta = {
                    "c1": c1,
                    "c1_nm": row.get("C1_NM"),
                    "itm_id": itm_in_row,
                    "itm_nm": row.get("ITM_NM"),
                    "obj_nm": row.get("C1_OBJ_NM"),
                }
                obs.append(
                    {
                        "source_id": "kosis",
                        "series_id": row_sid,
                        "date": date_iso,
                        "value": val,
                        "unit": row.get("UNIT_NM") or row.get("unitNm"),
                        "meta": meta,
                    }
                )
            # Chunk the upsert so tables like DT_1YL1701 (12k+ rows) don't
            # blow past SQLite's max-SQL-variable cap. Repository.upsert_observations
            # packs 8 columns per row, so 500 rows/chunk = 4k variables which
            # is safe on every SQLite driver in the wild.
            chunk_size = 500
            written = 0
            for i in range(0, len(obs), chunk_size):
                written += repo.upsert_observations(obs[i : i + chunk_size])
            log.info(
                "KOSIS %s/%s (%s): %d rows across %d series",
                org, tbl, sid, written,
                len({o["series_id"] for o in obs}),
            )
            fetched += written
    return fetched


def _kosis_date(raw: str) -> str:
    raw = (raw or "").strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
    if len(raw) == 6 and raw.isdigit():
        return f"{raw[0:4]}-{raw[4:6]}-01"
    if len(raw) == 4 and raw.isdigit():
        return f"{raw}-01-01"
    return ""


def collect_dart(
    corp_code: str | None,
    days: int,
    page_count: int,
    repo: Repository,
) -> int:
    end = date.today()
    start = end - timedelta(days=days)
    with DARTAdapter.from_settings() as dart:
        filings = dart.list_disclosures(
            corp_code=corp_code, start=start, end=end, page_count=page_count
        )
        log.info("DART: fetched %d filings", len(filings))
        rows = [f.as_row() for f in filings]
        return repo.upsert_filings(rows)


# --------------------------------------------------------------------------- #
# DB summary                                                                  #
# --------------------------------------------------------------------------- #


def _summarise_observations(repo: Repository) -> None:
    """Log a per-source summary of the observations table."""
    from sqlalchemy import func, select

    from ky_core.storage.schema import Observation

    with repo.session() as sess:
        stmt = (
            select(
                Observation.source_id,
                func.count(func.distinct(Observation.series_id)).label("n_series"),
                func.count().label("n_rows"),
                func.min(Observation.date).label("d0"),
                func.max(Observation.date).label("d1"),
            )
            .where(Observation.owner_id == repo.owner_id)
            .group_by(Observation.source_id)
        )
        rows = sess.execute(stmt).all()
    log.info("observations summary (owner=%s)", repo.owner_id)
    log.info("  %-10s %8s %10s  %-10s -> %-10s", "source", "series", "rows", "first", "last")
    for r in rows:
        log.info("  %-10s %8d %10d  %-10s -> %-10s", r.source_id, r.n_series, r.n_rows, r.d0, r.d1)


# --------------------------------------------------------------------------- #
# Entrypoint                                                                  #
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ky-platform data collector")
    p.add_argument("--source", type=str, default=None,
                   help="fred | ecos | kosis | eia | exim | dart | all-macro")
    p.add_argument("--healthcheck", action="store_true")
    p.add_argument("--owner-id", type=str, default="self")

    # Common
    p.add_argument("--series", type=str, default=None, help="comma-separated series ids")
    p.add_argument("--start", type=str, default=None)
    p.add_argument("--end", type=str, default=None)

    # ECOS
    p.add_argument("--stat", type=str, default=None, help="ECOS stat_code")
    p.add_argument("--item", type=str, default=None, help="ECOS item_code")
    p.add_argument("--freq", type=str, default="D", help="ECOS freq (D/M/Q/Y)")

    # DART
    p.add_argument("--corp-code", type=str, default=None)
    p.add_argument("--days", type=int, default=30)
    p.add_argument("--page-count", type=int, default=20)

    # Misc
    p.add_argument("--summary", action="store_true",
                   help="print a per-source observations summary and exit")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # Use a distinct log prefix for the full bulk path so operators can easily
    # find the "big" backfill run among per-source files.
    prefix = "collect_bulk" if args.source == "all-macro" else "collect"
    log_path = _setup_logging(prefix)
    log.info("=" * 72)
    log.info("ky-platform collect start: %s", datetime.utcnow().isoformat())
    log.info("log file: %s", log_path)

    if args.healthcheck:
        return cmd_healthcheck()

    repo = Repository(owner_id=args.owner_id)

    if args.summary:
        _summarise_observations(repo)
        return 0

    if not args.source:
        log.error("--source is required (or --healthcheck / --summary)")
        return 2

    t0 = time.perf_counter()
    source = args.source.lower()
    total = 0

    if source == "fred":
        series_ids = args.series.split(",") if args.series else FRED_SERIES
        start = _parse_date(args.start, date.today() - timedelta(days=3650))
        end = _parse_date(args.end, date.today())
        total = collect_fred([s.strip() for s in series_ids if s.strip()], start, end, repo)

    elif source == "ecos":
        start_iso = (args.start or (date.today() - timedelta(days=3650)).isoformat())
        end_iso = (args.end or date.today().isoformat())
        # Keep CLI-path --stat/--item single-series behaviour for convenience
        if args.stat and args.item:
            single = [(args.stat, args.item, args.freq, f"{args.stat}/{args.item}")]
        else:
            single = list(ECOS_SERIES)
        # accept YYYYMMDD shorthand too
        if len(start_iso) == 8 and start_iso.isdigit():
            start_iso = f"{start_iso[:4]}-{start_iso[4:6]}-{start_iso[6:8]}"
        if len(end_iso) == 8 and end_iso.isdigit():
            end_iso = f"{end_iso[:4]}-{end_iso[4:6]}-{end_iso[6:8]}"
        total = collect_ecos(single, start_iso, end_iso, repo)

    elif source == "eia":
        if args.series:
            entries = [s.strip() for s in args.series.split(",") if s.strip()]
        else:
            entries = EIA_SERIES
        total = collect_eia(entries, args.start, args.end, repo)

    elif source == "exim":
        if args.start and args.end:
            s = _parse_date(args.start, date.today())
            e = _parse_date(args.end, date.today())
            total = collect_exim_range(repo, s, e)
        else:
            target = _parse_date(args.start, date.today()) if args.start else None
            total = collect_exim(repo, target=target)

    elif source == "kosis":
        total = collect_kosis(KOSIS_SERIES, args.start, args.end, repo)

    elif source == "dart":
        total = collect_dart(args.corp_code, args.days, args.page_count, repo)

    elif source == "all-macro":
        start_iso = args.start or (date.today() - timedelta(days=3650)).isoformat()
        end_iso = args.end or date.today().isoformat()
        # normalise shorthand
        if len(start_iso) == 8 and start_iso.isdigit():
            start_iso = f"{start_iso[:4]}-{start_iso[4:6]}-{start_iso[6:8]}"
        if len(end_iso) == 8 and end_iso.isdigit():
            end_iso = f"{end_iso[:4]}-{end_iso[4:6]}-{end_iso[6:8]}"
        fred_start = datetime.fromisoformat(start_iso).date()
        fred_end = datetime.fromisoformat(end_iso).date()

        log.info("---- FRED bulk backfill ----")
        total += collect_fred(FRED_SERIES, fred_start, fred_end, repo)
        log.info("---- ECOS bulk backfill ----")
        total += collect_ecos(list(ECOS_SERIES), start_iso, end_iso, repo)
        log.info("---- KOSIS bulk backfill ----")
        total += collect_kosis(KOSIS_SERIES, start_iso, end_iso, repo)
        log.info("---- EIA bulk backfill ----")
        total += collect_eia(EIA_SERIES, None, None, repo)
        log.info("---- EXIM latest snapshot ----")
        total += collect_exim(repo)

        log.info("---- post-run summary ----")
        _summarise_observations(repo)

    else:
        log.error("unknown --source %s", source)
        return 2

    elapsed = time.perf_counter() - t0
    log.info("collect done: total_rows_upserted=%d elapsed=%.2fs", total, elapsed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
