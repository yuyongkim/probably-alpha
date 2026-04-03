from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Iterable

from sepa.data.price_history import format_date_token, read_price_series_from_path
from sepa.data.universe import get_symbol_name

logger = logging.getLogger(__name__)


@dataclass
class SymbolMetrics:
    symbol: str
    close: float
    sma50: float
    sma150: float
    sma200: float
    sma200_prev20: float
    high52: float
    low52: float
    ret120: float
    valid: bool
    reason: str = ""


class AlphaScreener:
    """Minervini Trend Template 기반 Alpha 스크리너 (CSV 입력).

    Config: config/minervini_config.json의 ``alpha`` 섹션에서 파라미터 로드.
    - min_tt_pass: TT 8조건 중 최소 통과 개수 (기본 5)
    - rs_threshold: RS 백분위 임계값 (기본 70)
    - c5_low52_multiplier: 52주 저점 대비 배수 (기본 1.30)
    - hard_gates: 필수 통과 조건 키 목록
    """

    def __init__(
        self,
        data_dir: Path = Path(".omx/artifacts/market-data/ohlcv"),
        audit_dir: Path = Path(".omx/artifacts/audit-logs"),
        top_n: int = 0,
        rs_threshold: float | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.audit_dir = audit_dir
        self.top_n = top_n
        self._config = self._load_config()
        self.rs_threshold = rs_threshold if rs_threshold is not None else self._config.get("rs_threshold", 70.0)
        self._min_tt_pass = self._config.get("min_tt_pass", 5)
        self._c5_multiplier = self._config.get("c5_low52_multiplier", 1.30)
        self._c6_multiplier = self._config.get("c6_high52_multiplier", 0.75)
        self._hard_gates = set(self._config.get("hard_gates", ["c2_close_gt_sma50", "c7_rs_ge_threshold"]))

    @staticmethod
    def _load_config() -> dict:
        config_path = Path("config/minervini_config.json")
        if config_path.exists():
            return json.loads(config_path.read_text(encoding="utf-8")).get("alpha", {})
        return {}

    def run(self, as_of_date: str | None = None) -> list[dict]:
        metrics = self._collect_all_metrics(as_of_date=as_of_date)
        valid = [m for m in metrics if m.valid]

        if not valid:
            self._audit("alpha", "no valid symbols after preprocessing")
            return []

        rs_map = self._percentile_map({m.symbol: m.ret120 for m in valid})
        today = format_date_token(as_of_date) if as_of_date else datetime.now().strftime("%Y-%m-%d")

        results: list[dict] = []
        for m in valid:
            rs = rs_map.get(m.symbol, 0.0)
            checks = {
                "c1_sma50_gt_sma150_gt_sma200": m.sma50 > m.sma150 > m.sma200,
                "c2_close_gt_sma50": m.close > m.sma50,
                "c3_sma150_gt_sma200": m.sma150 > m.sma200,
                "c4_sma200_rising": m.sma200 > m.sma200_prev20,
                "c5_close_gte_130pct_52wl": m.close >= (self._c5_multiplier * m.low52 if m.low52 > 0 else m.close),
                "c6_close_gte_75pct_52wh": m.close >= (self._c6_multiplier * m.high52 if m.high52 > 0 else m.close),
                "c7_rs_ge_threshold": rs >= self.rs_threshold,
                "c8_close_gt_sma200": m.close > m.sma200,
            }

            # Hard gates: must pass (c2 close>SMA50, c7 RS threshold)
            hard_gate_fail = any(not checks[k] for k in self._hard_gates if k in checks)
            if hard_gate_fail:
                continue

            # Minimum 5/8 TT conditions must pass
            passed_count = sum(1 for v in checks.values() if v)
            if passed_count < self._min_tt_pass:
                continue

            score = round((passed_count * 10.0) + (rs * 0.2), 2)
            results.append(
                {
                    "date": today,
                    "symbol": m.symbol,
                    "name": get_symbol_name(m.symbol),
                    "score": score,
                    "rs_percentile": round(rs, 2),
                    "checks": checks,
                    "reason": "trend_template_pass",
                }
            )

        results.sort(key=lambda x: (x["score"], x["rs_percentile"]), reverse=True)
        if self.top_n > 0:
            return results[: self.top_n]
        return results

    def _collect_all_metrics(self, as_of_date: str | None = None) -> list[SymbolMetrics]:
        """Load all symbols and compute metrics. Uses DB batch when available."""
        csv_files = list(self._iter_csv_files())
        # Only use DB batch when scanning the real data dir (not test dirs)
        if csv_files and str(self.data_dir) == str(Path('.omx/artifacts/market-data/ohlcv')):
            try:
                from sepa.data.ohlcv_db import read_ohlcv_batch, DB_PATH
                if DB_PATH.exists():
                    batch = read_ohlcv_batch(as_of_date=as_of_date, min_rows=200)
                    if batch:
                        return [self._metrics_from_closes(sym, data['closes']) for sym, data in batch.items()]
            except Exception:
                pass
        # Fallback: CSV
        return [self._collect_metrics(path, as_of_date=as_of_date) for path in csv_files]

    def _metrics_from_closes(self, symbol: str, closes: list[float]) -> SymbolMetrics:
        """Compute metrics from pre-loaded close prices."""
        if len(closes) < 200:
            return SymbolMetrics(symbol, 0, 0, 0, 0, 0, 0, 0, 0, False, "insufficient_history")
        close = closes[-1]
        sma50 = mean(closes[-50:])
        sma150 = mean(closes[-150:])
        sma200 = mean(closes[-200:])
        sma200_prev20 = mean(closes[-220:-20]) if len(closes) >= 220 else sma200
        w = closes[-252:] if len(closes) >= 252 else closes
        high52 = max(w)
        low52 = min(w)
        base = closes[-121] if len(closes) >= 121 else closes[0]
        ret120 = (close / base - 1.0) if base > 0 else 0.0
        return SymbolMetrics(symbol=symbol, close=close, sma50=sma50, sma150=sma150,
                             sma200=sma200, sma200_prev20=sma200_prev20, high52=high52,
                             low52=low52, ret120=ret120, valid=True)

    def _iter_csv_files(self) -> Iterable[Path]:
        if not self.data_dir.exists():
            self._audit("alpha", f"data dir not found: {self.data_dir}")
            return []
        return sorted(self.data_dir.glob("*.csv"))

    def _collect_metrics(self, path: Path, as_of_date: str | None = None) -> SymbolMetrics:
        symbol = path.stem
        try:
            rows = self._read_ohlcv(path, as_of_date=as_of_date)
            closes = [r["close"] for r in rows if r["close"] > 0]
            if len(closes) < 200:
                return SymbolMetrics(symbol, 0, 0, 0, 0, 0, 0, 0, 0, False, "insufficient_history")

            close = closes[-1]
            sma50 = mean(closes[-50:])
            sma150 = mean(closes[-150:])
            sma200 = mean(closes[-200:])
            sma200_prev20 = mean(closes[-220:-20]) if len(closes) >= 220 else sma200

            w = closes[-252:] if len(closes) >= 252 else closes
            high52 = max(w)
            low52 = min(w)

            base_idx = -121 if len(closes) >= 121 else 0
            base = closes[base_idx]
            ret120 = (close / base - 1.0) if base > 0 else 0.0

            return SymbolMetrics(
                symbol=symbol,
                close=close,
                sma50=sma50,
                sma150=sma150,
                sma200=sma200,
                sma200_prev20=sma200_prev20,
                high52=high52,
                low52=low52,
                ret120=ret120,
                valid=True,
            )
        except (ValueError, TypeError, KeyError, IndexError, OSError) as e:
            logger.warning('alpha parse error for %s: %s', symbol, e)
            self._audit("alpha", f"{symbol} parse error: {e}")
            return SymbolMetrics(symbol, 0, 0, 0, 0, 0, 0, 0, 0, False, "parse_error")

    @staticmethod
    def _read_ohlcv(path: Path, as_of_date: str | None = None) -> list[dict[str, float]]:
        return [{'close': row.get('close', 0.0)} for row in read_price_series_from_path(path, as_of_date=as_of_date)]

    @staticmethod
    def _percentile_map(ret_by_symbol: dict[str, float]) -> dict[str, float]:
        items = sorted(ret_by_symbol.items(), key=lambda x: x[1])
        n = len(items)
        if n == 1:
            return {items[0][0]: 100.0}
        out: dict[str, float] = {}
        for i, (s, _) in enumerate(items):
            out[s] = (i / (n - 1)) * 100.0
        return out

    def _audit(self, component: str, message: str) -> None:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        p = self.audit_dir / f"{component}-{ts}.log"
        p.write_text(json.dumps({"timestamp": ts, "message": message}, ensure_ascii=False), encoding="utf-8")
