"""On-demand weekly / monthly market review.

The review is not a batch job — it's a *projection* over whatever data
we already have on disk (leader scan, sector rotation, macro compass).
We don't compute anything new; we aggregate.

The output is a plain dict the frontend renders as a card stack:

    {
      "as_of": "2026-04-22",
      "period": "weekly",
      "sections": [
        {"title": "주도 섹터 Top 5", "rows": [{"name": ..., "score": ...}, ...]},
        {"title": "주도 종목 Top 10", "rows": [...]},
        {"title": "매크로 레짐", "rows": [...]},
        {"title": "메모", "rows": [...]}
      ],
      "stale_sources": ["leaders", ...]
    }
"""
from __future__ import annotations

import datetime as dt
import importlib
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _safe_call(mod_path: str, func_name: str, *args, **kwargs) -> Any:
    try:
        mod = importlib.import_module(mod_path)
        fn = getattr(mod, func_name)
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("review: %s.%s failed: %s", mod_path, func_name, exc)
        return None


def build_review(period: str = "weekly") -> Dict[str, Any]:
    """Aggregate the latest leader / sector / macro snapshots.

    ``period`` is just a label for now — the inputs are always "latest".
    We keep it so ``/research/review?period=monthly`` can shift
    to monthly aggregation later.
    """
    today = dt.date.today().isoformat()
    sections: List[Dict[str, Any]] = []
    stale: List[str] = []

    # Macro compass / sectors ---------------------------------------------
    compass = None
    try:
        from ky_core.macro.compass import compute_compass as _cc

        compass = _cc()
    except Exception as exc:  # noqa: BLE001
        logger.warning("review: compute_compass failed: %s", exc)
        stale.append("macro_compass")

    sector_rows: List[Dict[str, Any]] = []
    if compass is not None:
        try:
            for axis_name, detail in list(compass.axes.items())[:5]:
                sector_rows.append(
                    {
                        "name": axis_name,
                        "score": round(float(getattr(detail, "score", 0.0)), 3),
                        "note": getattr(detail, "series_id", ""),
                    }
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("review: compass axes extraction failed: %s", exc)
            stale.append("macro_compass")
    sections.append(
        {
            "title": "매크로 축 Top 5",
            "rows": sector_rows
            or [{"name": "데이터 없음", "score": 0.0, "note": "compass stale"}],
        }
    )

    # Leaders --------------------------------------------------------------
    leaders: List[Dict[str, Any]] = []
    try:
        from ky_core.scanning.leader_scan import scan_leaders as _sl  # noqa: F401

        # scan_leaders typically needs a panel; we try keyword-less, then skip.
        res = _safe_call("ky_core.scanning.leader_scan", "scan_leaders")
        if res is not None:
            try:
                for l in list(res)[:10]:
                    leaders.append(
                        {
                            "symbol": getattr(l, "symbol", ""),
                            "name": getattr(l, "name", ""),
                            "leader_score": round(float(getattr(l, "leader_score", 0.0)), 3),
                            "trend_template": getattr(l, "trend_template", ""),
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("review: leader iteration failed: %s", exc)
                stale.append("leader_scan")
    except Exception:  # noqa: BLE001
        stale.append("leader_scan")
    if not leaders:
        stale.append("leader_scan") if "leader_scan" not in stale else None
    sections.append(
        {
            "title": "주도 종목 Top 10",
            "rows": leaders or [{"name": "데이터 없음", "leader_score": 0.0}],
        }
    )

    # Macro regime ---------------------------------------------------------
    macro_rows: List[Dict[str, Any]] = []
    try:
        from ky_core.macro.regime import classify_regime

        reg = classify_regime(compass=compass) if compass is not None else classify_regime()
        d = reg.to_dict()
        macro_rows.append(
            {
                "name": "현재 레짐",
                "score": d.get("composite", 0.0),
                "note": d.get("current", ""),
            }
        )
        probs = d.get("probabilities", {}) or {}
        for k, v in list(probs.items())[:4]:
            macro_rows.append({"name": k, "score": float(v), "note": "probability"})
    except Exception as exc:  # noqa: BLE001
        logger.warning("review: classify_regime failed: %s", exc)
        stale.append("macro_regime")
    sections.append(
        {
            "title": "매크로 레짐",
            "rows": macro_rows or [{"name": "데이터 없음", "score": 0.0, "note": ""}],
        }
    )

    # Footer memo ---------------------------------------------------------
    sections.append(
        {
            "title": "메모",
            "rows": [
                {
                    "name": f"{period} review",
                    "note": (
                        "이 리포트는 기존 스캔/매크로 데이터를 요약한 '편집본'입니다. "
                        "새로운 계산은 수행하지 않습니다."
                    ),
                }
            ],
        }
    )

    return {
        "as_of": today,
        "period": period,
        "sections": sections,
        "stale_sources": stale,
    }
