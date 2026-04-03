from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from sepa.analysis.stock_analysis import sector_breakout_payload
from sepa.data.price_history import read_price_series_from_path
from sepa.data.sector_map import get_sector, load_sector_map
from sepa.data.universe import get_symbol_name

logger = logging.getLogger(__name__)


@dataclass
class SectorStats:
    sector: str
    universe_count: int
    alpha_count: int
    beta_count: int
    avg_ret120: float
    leader_score: float
    alpha_ratio: float
    beta_ratio: float
    breadth_multiplier: float
    breakout_proximity_score: float
    volume_participation_ratio: float
    breakout_state: str
    leadership_ready: bool
    distance_to_high120_pct: float
    sector_bucket: str


class MinerviniLeaders:
    """Ranks confirmed leaders and setup candidates from the Minervini pipeline."""

    def __init__(
        self,
        data_dir: Path = Path('.omx/artifacts/market-data/ohlcv'),
        signal_root: Path = Path('.omx/artifacts/daily-signals'),
        sector_top_n: int = 10,
        stock_top_n: int = 10,
    ) -> None:
        self.data_dir = data_dir
        self.signal_root = signal_root
        self.sector_map = load_sector_map()
        self.sector_top_n = sector_top_n
        self.stock_top_n = stock_top_n

    def run(self, date_dir: str, as_of_date: str | None = None) -> tuple[list[dict], list[dict]]:
        d = self.signal_root / date_dir
        alpha = self._read_json(d / 'alpha-passed.json', default=[])
        beta = self._read_json(d / 'beta-vcp-candidates.json', default=[])
        gamma = self._read_json(d / 'gamma-insights.json', default={})

        ret120 = self._ret120_by_symbol(as_of_date=as_of_date)
        sectors = self._rank_sectors(alpha, beta, ret120, as_of_date=as_of_date)
        leaders = self._rank_leader_stocks(alpha, beta, gamma, ret120, sectors)

        return sectors, leaders

    def run_grouped(self, date_dir: str, as_of_date: str | None = None, per_sector_n: int = 5) -> list[dict]:
        """Return leaders grouped by sector with sparkline data."""
        d = self.signal_root / date_dir
        alpha = self._read_json(d / 'alpha-passed.json', default=[])
        beta = self._read_json(d / 'beta-vcp-candidates.json', default=[])
        gamma = self._read_json(d / 'gamma-insights.json', default={})

        ret120 = self._ret120_by_symbol(as_of_date=as_of_date)
        sectors = self._rank_sectors_all(alpha, beta, ret120, as_of_date=as_of_date)
        return self._rank_leader_stocks_by_sector(alpha, beta, gamma, ret120, sectors, per_sector_n=per_sector_n, as_of_date=as_of_date)

    def _ret120_by_symbol(self, as_of_date: str | None = None) -> dict[str, float]:
        out: dict[str, float] = {}
        for path in sorted(self.data_dir.glob('*.csv')):
            closes = [row.get('close', 0.0) for row in read_price_series_from_path(path, as_of_date=as_of_date)]
            if len(closes) < 121:
                continue
            base = closes[-121]
            if base <= 0:
                continue
            out[path.stem] = closes[-1] / base - 1.0
        return out

    def _sector_bucket(self, *, leadership_ready: bool, universe_count: int, alpha_ratio: float, breakout_score: float) -> str:
        if leadership_ready:
            return 'confirmed_leader'
        if universe_count >= 2 and (alpha_ratio >= 0.20 or breakout_score >= 0.22):
            return 'watchlist'
        return 'emerging'

    def _rank_sectors(
        self,
        alpha: list[dict],
        beta: list[dict],
        ret120: dict[str, float],
        as_of_date: str | None = None,
    ) -> list[dict]:
        universe: dict[str, list[str]] = {}
        for symbol in ret120:
            sector = get_sector(symbol, self.sector_map)
            universe.setdefault(sector, []).append(symbol)

        alpha_by_sector: dict[str, int] = {}
        for row in alpha:
            sector = get_sector(row.get('symbol', ''), self.sector_map)
            alpha_by_sector[sector] = alpha_by_sector.get(sector, 0) + 1

        beta_by_sector: dict[str, int] = {}
        for row in beta:
            sector = get_sector(row.get('symbol', ''), self.sector_map)
            beta_by_sector[sector] = beta_by_sector.get(sector, 0) + 1

        sector_ret: dict[str, float] = {}
        for sector, symbols in universe.items():
            values = [ret120[symbol] for symbol in symbols if symbol in ret120]
            sector_ret[sector] = mean(values) if values else 0.0

        sorted_returns = sorted(sector_ret.values())

        def ret_percentile(value: float) -> float:
            if not sorted_returns:
                return 0.0
            if len(sorted_returns) == 1:
                return 100.0
            idx = sum(1 for current in sorted_returns if current <= value) - 1
            return max(0.0, min(100.0, idx / (len(sorted_returns) - 1) * 100.0))

        ranked: list[SectorStats] = []
        for sector, symbols in universe.items():
            universe_count = len(symbols)
            alpha_count = alpha_by_sector.get(sector, 0)
            beta_count = beta_by_sector.get(sector, 0)
            avg_ret120 = sector_ret.get(sector, 0.0)
            strength = sector_breakout_payload(sector, as_of_date=as_of_date)

            alpha_ratio = alpha_count / universe_count if universe_count else 0.0
            beta_ratio = beta_count / alpha_count if alpha_count else 0.0
            rs_pct = ret_percentile(avg_ret120) / 100.0
            breadth_multiplier = min(1.0, universe_count / 3.0)
            distance = float(strength.get('distance_to_high120_pct') or -100.0)
            breakout_state = str(strength.get('breakout_state') or 'sector_not_ready')
            volume_participation = float(strength.get('volume_participation_ratio') or 0.0)

            if breakout_state == 'sector_breakout_confirmed':
                breakout_score = 1.0
            elif breakout_state == 'sector_breakout_setup':
                breakout_score = 0.78
            else:
                breakout_score = max(0.0, 1.0 - min(abs(distance), 20.0) / 20.0) * 0.45

            score = (
                (rs_pct * 0.32)
                + (alpha_ratio * 0.24)
                + (beta_ratio * 0.14)
                + (breakout_score * 0.18)
                + (volume_participation * 0.12)
            ) * breadth_multiplier * 100.0

            leadership_ready = (
                universe_count >= 2 and (
                    breakout_state in {'sector_breakout_confirmed', 'sector_breakout_setup'}
                    or (distance >= -8.0 and alpha_ratio >= 0.50 and beta_ratio >= 0.50)
                )
            )
            sector_bucket = self._sector_bucket(
                leadership_ready=leadership_ready,
                universe_count=universe_count,
                alpha_ratio=alpha_ratio,
                breakout_score=breakout_score,
            )

            ranked.append(
                SectorStats(
                    sector=sector,
                    universe_count=universe_count,
                    alpha_count=alpha_count,
                    beta_count=beta_count,
                    avg_ret120=avg_ret120,
                    leader_score=score,
                    alpha_ratio=alpha_ratio,
                    beta_ratio=beta_ratio,
                    breadth_multiplier=breadth_multiplier,
                    breakout_proximity_score=breakout_score,
                    volume_participation_ratio=volume_participation,
                    breakout_state=breakout_state,
                    leadership_ready=leadership_ready,
                    distance_to_high120_pct=distance,
                    sector_bucket=sector_bucket,
                )
            )

        ranked.sort(key=lambda item: (item.leadership_ready, item.leader_score), reverse=True)
        return self._sector_dicts(ranked[: self.sector_top_n], ret_percentile)

    def _rank_sectors_all(
        self,
        alpha: list[dict],
        beta: list[dict],
        ret120: dict[str, float],
        as_of_date: str | None = None,
    ) -> list[dict]:
        """Like _rank_sectors but returns ALL sectors (no top_n truncation)."""
        # Delegate sector computation to _rank_sectors but override sector_top_n temporarily
        saved = self.sector_top_n
        self.sector_top_n = 9999
        result = self._rank_sectors(alpha, beta, ret120, as_of_date=as_of_date)
        self.sector_top_n = saved
        return result

    @staticmethod
    def _sector_dicts(ranked: list[SectorStats], ret_percentile) -> list[dict]:
        return [
            {
                'sector': item.sector,
                'universe_count': item.universe_count,
                'alpha_count': item.alpha_count,
                'beta_count': item.beta_count,
                'alpha_ratio': round(item.alpha_ratio, 4),
                'beta_ratio': round(item.beta_ratio, 4),
                'sector_rs_percentile': round(ret_percentile(item.avg_ret120), 2),
                'avg_ret120': round(item.avg_ret120, 4),
                'breadth_multiplier': round(item.breadth_multiplier, 4),
                'breakout_proximity_score': round(item.breakout_proximity_score, 4),
                'volume_participation_ratio': round(item.volume_participation_ratio, 4),
                'breakout_state': item.breakout_state,
                'leadership_ready': item.leadership_ready,
                'sector_bucket': item.sector_bucket,
                'distance_to_high120_pct': round(item.distance_to_high120_pct, 2),
                'leader_score': round(item.leader_score, 2),
            }
            for item in ranked
        ]

    def _rank_leader_stocks(
        self,
        alpha: list[dict],
        beta: list[dict],
        gamma: dict,
        ret120: dict[str, float],
        sectors: list[dict],
    ) -> list[dict]:
        sector_map = {row['sector']: row for row in sectors}
        confirmed_sectors = {
            row['sector']
            for row in sectors
            if row.get('sector_bucket') == 'confirmed_leader' or row.get('leadership_ready')
        }
        watchlist_sectors = {
            row['sector']
            for row in sectors
            if row.get('sector_bucket') == 'watchlist'
        }
        eligible_sectors = confirmed_sectors | watchlist_sectors

        beta_map = {row.get('symbol'): float(row.get('confidence', 0.0)) for row in beta}
        gamma_map = {
            row.get('symbol'): float(row.get('gamma_score', 0.0))
            for row in (gamma.get('general', []) if isinstance(gamma, dict) else [])
        }

        confirmed_candidates: list[dict] = []
        setup_candidates: list[dict] = []
        for row in alpha:
            symbol = row.get('symbol', '')
            sector = get_sector(symbol, self.sector_map)
            if eligible_sectors and sector not in eligible_sectors:
                continue

            alpha_score = float(row.get('score', 0.0))
            beta_conf = beta_map.get(symbol, 0.0)
            gamma_score = gamma_map.get(symbol, 0.0)
            rs = ret120.get(symbol, 0.0)
            sector_row = sector_map.get(sector, {})
            sector_score = float(sector_row.get('leader_score', 0.0))
            sector_ready = bool(sector_row.get('leadership_ready'))
            total = (
                (alpha_score * 0.43)
                + (beta_conf * 4.0)
                + (gamma_score * 3.0)
                + (rs * 100.0 * 0.10)
                + (sector_score * 0.25)
            )
            payload = {
                'symbol': symbol,
                'name': get_symbol_name(symbol),
                'sector': sector,
                'sector_bucket': sector_row.get('sector_bucket', 'watchlist'),
                'sector_leader_score': round(sector_score, 2),
                'sector_leadership_ready': sector_ready,
                'alpha_score': round(alpha_score, 2),
                'beta_confidence': round(beta_conf, 2),
                'gamma_score': round(gamma_score, 2),
                'ret120': round(rs, 4),
                'ret120_pct': round(rs * 100.0, 2),
                'leader_stock_score': round(total, 2),
                'stock_bucket': 'confirmed_leader' if sector_ready else 'setup_candidate',
                'why': 'RS + template + VCP + EPS + sector leadership',
            }
            if sector_ready:
                confirmed_candidates.append(payload)
            else:
                setup_candidates.append(payload)

        if not confirmed_candidates and not setup_candidates:
            for row in alpha[: self.stock_top_n]:
                symbol = row.get('symbol', '')
                setup_candidates.append(
                    {
                        'symbol': symbol,
                        'name': get_symbol_name(symbol),
                        'sector': get_sector(symbol, self.sector_map),
                        'sector_bucket': 'watchlist',
                        'sector_leader_score': 0.0,
                        'sector_leadership_ready': False,
                        'alpha_score': round(float(row.get('score', 0.0)), 2),
                        'beta_confidence': round(beta_map.get(symbol, 0.0), 2),
                        'gamma_score': round(gamma_map.get(symbol, 0.0), 2),
                        'ret120': round(ret120.get(symbol, 0.0), 4),
                        'ret120_pct': round(ret120.get(symbol, 0.0) * 100.0, 2),
                        'leader_stock_score': round(float(row.get('score', 0.0)), 2),
                        'stock_bucket': 'setup_candidate',
                        'why': 'fallback: alpha top rank',
                    }
                )

        confirmed_candidates.sort(
            key=lambda item: (item.get('sector_leader_score', 0.0), item.get('leader_stock_score', 0.0)),
            reverse=True,
        )
        setup_candidates.sort(
            key=lambda item: (item.get('sector_leader_score', 0.0), item.get('leader_stock_score', 0.0)),
            reverse=True,
        )
        per_bucket_limit = max(5, self.stock_top_n)
        return confirmed_candidates[:per_bucket_limit] + setup_candidates[:per_bucket_limit]

    def _sparkline(self, symbol: str, n: int = 60, as_of_date: str | None = None) -> list[float]:
        path = self.data_dir / f'{symbol}.csv'
        if not path.exists():
            return []
        try:
            closes = [row.get('close', 0.0) for row in read_price_series_from_path(path, as_of_date=as_of_date)]
            return [round(c, 2) for c in closes[-n:] if c > 0]
        except (ValueError, TypeError, KeyError, OSError) as exc:
            logger.warning('sparkline failed for %s: %s', symbol, exc)
            return []

    def _rank_leader_stocks_by_sector(
        self,
        alpha: list[dict],
        beta: list[dict],
        gamma: dict,
        ret120: dict[str, float],
        sectors: list[dict],
        per_sector_n: int = 5,
        as_of_date: str | None = None,
    ) -> list[dict]:
        sector_map = {row['sector']: row for row in sectors}
        beta_map = {row.get('symbol'): float(row.get('confidence', 0.0)) for row in beta}
        gamma_map = {
            row.get('symbol'): float(row.get('gamma_score', 0.0))
            for row in (gamma.get('general', []) if isinstance(gamma, dict) else [])
        }

        # Build per-sector stock lists
        stocks_by_sector: dict[str, list[dict]] = {}
        for row in alpha:
            symbol = row.get('symbol', '')
            sector = get_sector(symbol, self.sector_map)
            if sector not in sector_map:
                continue

            alpha_score = float(row.get('score', 0.0))
            beta_conf = beta_map.get(symbol, 0.0)
            gamma_score = gamma_map.get(symbol, 0.0)
            rs = ret120.get(symbol, 0.0)
            sector_row = sector_map.get(sector, {})
            sector_score = float(sector_row.get('leader_score', 0.0))
            sector_ready = bool(sector_row.get('leadership_ready'))
            total = (
                (alpha_score * 0.43)
                + (beta_conf * 4.0)
                + (gamma_score * 3.0)
                + (rs * 100.0 * 0.10)
                + (sector_score * 0.25)
            )
            spark = self._sparkline(symbol, n=120, as_of_date=as_of_date)
            payload = {
                'symbol': symbol,
                'name': get_symbol_name(symbol),
                'sector': sector,
                'sector_bucket': sector_row.get('sector_bucket', 'watchlist'),
                'sector_leadership_ready': sector_ready,
                'alpha_score': round(alpha_score, 2),
                'beta_confidence': round(beta_conf, 2),
                'gamma_score': round(gamma_score, 2),
                'ret120': round(rs, 4),
                'ret120_pct': round(rs * 100.0, 2),
                'leader_stock_score': round(total, 2),
                'sparkline': spark,
                'price': spark[-1] if spark else None,
            }
            stocks_by_sector.setdefault(sector, []).append(payload)

        # Build grouped output: each sector with its top stocks
        grouped: list[dict] = []
        eligible_buckets = {'confirmed_leader', 'watchlist'}
        for sector_row in sectors:
            sector = sector_row['sector']
            bucket = sector_row.get('sector_bucket', 'emerging')
            if bucket not in eligible_buckets:
                continue
            stocks = stocks_by_sector.get(sector, [])
            if not stocks:
                continue
            stocks.sort(key=lambda x: x.get('leader_stock_score', 0.0), reverse=True)
            grouped.append({
                'sector': sector,
                'sector_meta': sector_row,
                'stocks': stocks[:per_sector_n],
            })

        grouped.sort(key=lambda g: g.get('sector_meta', {}).get('leader_score', 0.0), reverse=True)
        return grouped

    @staticmethod
    def _read_json(path: Path, default):
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return default
