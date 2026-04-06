from __future__ import annotations

import json
import logging
from pathlib import Path
from statistics import mean

from sepa.analysis.stock_analysis import sector_breakout_payload
from sepa.data.market_index import market_index_path
from sepa.data.price_history import read_price_series_from_path
from sepa.data.sector_map import get_sector, load_sector_map
from sepa.data.universe import get_symbol_name
from sepa.scoring.factors import (
    breadth_above_ma,
    earnings_proxy,
    near_52w_high,
    near_high_ratio,
    rs_relative,
    to_percentile,
    trend_template_ratio,
    turnover_trend,
    volatility_contraction,
    volume_expansion,
)

logger = logging.getLogger(__name__)


class MinerviniLeaders:
    """Ranks confirmed leaders and setup candidates using LEADER_SCORING_SPEC.md formulas."""

    def __init__(
        self,
        data_dir: Path = Path('data/market-data/ohlcv'),
        signal_root: Path = Path('data/daily-signals'),
        sector_top_n: int = 10,
        stock_top_n: int = 10,
    ) -> None:
        self.data_dir = data_dir
        self.signal_root = signal_root
        self.sector_map = load_sector_map()
        self.sector_top_n = sector_top_n
        self.stock_top_n = stock_top_n

    # ------------------------------------------------------------------
    # Public interface (unchanged)
    # ------------------------------------------------------------------

    def run(self, date_dir: str, as_of_date: str | None = None) -> tuple[list[dict], list[dict]]:
        d = self.signal_root / date_dir
        alpha = self._read_json(d / 'alpha-passed.json', default=[])
        beta = self._read_json(d / 'beta-vcp-candidates.json', default=[])
        gamma = self._read_json(d / 'gamma-insights.json', default={})

        price_cache = self._load_price_cache(as_of_date=as_of_date)
        benchmark = self._load_benchmark(as_of_date=as_of_date)
        sectors = self._rank_sectors(alpha, beta, price_cache, benchmark, as_of_date=as_of_date)
        leaders = self._rank_leader_stocks(alpha, beta, gamma, price_cache, sectors)
        return sectors, leaders

    def run_grouped(self, date_dir: str, as_of_date: str | None = None, per_sector_n: int = 5) -> list[dict]:
        d = self.signal_root / date_dir
        alpha = self._read_json(d / 'alpha-passed.json', default=[])
        beta = self._read_json(d / 'beta-vcp-candidates.json', default=[])
        gamma = self._read_json(d / 'gamma-insights.json', default={})

        price_cache = self._load_price_cache(as_of_date=as_of_date)
        benchmark = self._load_benchmark(as_of_date=as_of_date)
        sectors = self._rank_sectors_all(alpha, beta, price_cache, benchmark, as_of_date=as_of_date)
        return self._rank_leader_stocks_by_sector(alpha, beta, gamma, price_cache, sectors, per_sector_n=per_sector_n, as_of_date=as_of_date)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_price_cache(self, as_of_date: str | None = None) -> dict[str, dict]:
        """Load closes and volumes for all symbols. Returns {symbol: {closes, volumes}}.

        Uses SQLite batch query (fast) with CSV fallback (slow).
        """
        # Fast path: batch read from SQLite
        try:
            from sepa.data.ohlcv_db import read_ohlcv_batch, DB_PATH
            if DB_PATH.exists():
                cache = read_ohlcv_batch(as_of_date=as_of_date, min_rows=50)
                if cache:
                    return cache
        except Exception:
            pass

        # Slow fallback: sequential CSV reads
        cache: dict[str, dict] = {}
        for path in sorted(self.data_dir.glob('*.csv')):
            symbol = path.stem
            rows = read_price_series_from_path(path, as_of_date=as_of_date)
            closes = [r.get('close', 0.0) for r in rows if r.get('close', 0.0) > 0]
            volumes = [r.get('volume', 0.0) for r in rows]
            if len(closes) >= 50:
                cache[symbol] = {'closes': closes, 'volumes': volumes}
        return cache

    def _load_benchmark(self, as_of_date: str | None = None) -> list[float]:
        path = market_index_path('KOSPI')
        if not path.exists():
            return []
        rows = read_price_series_from_path(path, as_of_date=as_of_date)
        return [r.get('close', 0.0) for r in rows if r.get('close', 0.0) > 0]

    # ------------------------------------------------------------------
    # Sector scoring (LEADER_SCORING_SPEC.md section 1)
    # ------------------------------------------------------------------

    def _rank_sectors(
        self,
        alpha: list[dict],
        beta: list[dict],
        price_cache: dict[str, dict],
        benchmark: list[float],
        as_of_date: str | None = None,
    ) -> list[dict]:
        # Group symbols by sector
        sector_symbols: dict[str, list[str]] = {}
        for symbol in price_cache:
            sector = get_sector(symbol, self.sector_map)
            sector_symbols.setdefault(sector, []).append(symbol)

        alpha_set = {r.get('symbol') for r in alpha}
        beta_set = {r.get('symbol') for r in beta}

        # Compute RS per sector
        raw_rs20: dict[str, float] = {}
        raw_rs60: dict[str, float] = {}

        for sector, symbols in sector_symbols.items():
            if len(symbols) < 5:
                continue
            closes_list = [price_cache[s]['closes'] for s in symbols if s in price_cache]
            volumes_list = [price_cache[s]['volumes'] for s in symbols if s in price_cache]
            if len(closes_list) < 5:
                continue

            avg_closes = self._avg_series(closes_list)
            raw_rs20[sector] = rs_relative(avg_closes, benchmark, 20) if benchmark else 0.0
            raw_rs60[sector] = rs_relative(avg_closes, benchmark, 60) if benchmark else 0.0

        if not raw_rs20:
            return []

        rs20_pct = to_percentile(raw_rs20)
        rs60_pct = to_percentile(raw_rs60)

        results: list[dict] = []
        for sector, symbols in sector_symbols.items():
            if sector not in rs20_pct:
                continue

            closes_list = [price_cache[s]['closes'] for s in symbols if s in price_cache]
            volumes_list = [price_cache[s]['volumes'] for s in symbols if s in price_cache]
            universe_count = len(symbols)
            alpha_count = sum(1 for s in symbols if s in alpha_set)
            beta_count = sum(1 for s in symbols if s in beta_set)

            b50 = breadth_above_ma(closes_list, window=50)
            nhr = near_high_ratio(closes_list, threshold=0.80)
            vol_sums = self._sum_series(volumes_list)
            tt = turnover_trend(vol_sums) if vol_sums else 1.0

            # New spec scoring
            sector_score = (
                rs20_pct[sector] * 0.30
                + rs60_pct[sector] * 0.25
                + b50 * 0.15
                + nhr * 0.15
                + min(1.0, tt / 3.0) * 0.15
            )

            # Legacy fields for API/frontend compat
            alpha_ratio = alpha_count / universe_count if universe_count else 0.0
            beta_ratio = beta_count / alpha_count if alpha_count else 0.0
            strength = sector_breakout_payload(sector, as_of_date=as_of_date)
            breakout_state = str(strength.get('breakout_state') or 'sector_not_ready')
            distance = float(strength.get('distance_to_high120_pct') or -100.0)
            volume_participation = float(strength.get('volume_participation_ratio') or 0.0)

            leadership_ready = (
                universe_count >= 5
                and sector_score >= 0.50
                and (breakout_state in {'sector_breakout_confirmed', 'sector_breakout_setup'}
                     or (alpha_ratio >= 0.30 and b50 >= 0.40))
            )
            sector_bucket = (
                'confirmed_leader' if leadership_ready
                else 'watchlist' if sector_score >= 0.35
                else 'emerging'
            )

            results.append({
                'sector': sector,
                'leader_score': round(sector_score * 100.0, 2),
                'sector_score': round(sector_score, 4),
                'rs_20': round(rs20_pct[sector], 4),
                'rs_60': round(rs60_pct[sector], 4),
                'breadth_50ma': round(b50, 4),
                'near_high_ratio': round(nhr, 4),
                'turnover_trend': round(tt, 4),
                'universe_count': universe_count,
                'alpha_count': alpha_count,
                'beta_count': beta_count,
                'alpha_ratio': round(alpha_ratio, 4),
                'beta_ratio': round(beta_ratio, 4),
                'breakout_state': breakout_state,
                'leadership_ready': leadership_ready,
                'sector_bucket': sector_bucket,
                'distance_to_high120_pct': round(distance, 2),
                'volume_participation_ratio': round(volume_participation, 4),
                'sector_rs_percentile': round(rs20_pct[sector] * 100.0, 2),
            })

        results.sort(key=lambda x: (x['leadership_ready'], x['leader_score']), reverse=True)
        return results[:self.sector_top_n]

    def _rank_sectors_all(self, alpha, beta, price_cache, benchmark, as_of_date=None) -> list[dict]:
        saved = self.sector_top_n
        self.sector_top_n = 9999
        result = self._rank_sectors(alpha, beta, price_cache, benchmark, as_of_date=as_of_date)
        self.sector_top_n = saved
        return result

    # ------------------------------------------------------------------
    # Stock scoring (LEADER_SCORING_SPEC.md section 2)
    # ------------------------------------------------------------------

    def _rank_leader_stocks(
        self,
        alpha: list[dict],
        beta: list[dict],
        gamma: dict,
        price_cache: dict[str, dict],
        sectors: list[dict],
    ) -> list[dict]:
        sector_map_data = {row['sector']: row for row in sectors}
        eligible_sectors = {
            row['sector'] for row in sectors
            if row.get('sector_bucket') in ('confirmed_leader', 'watchlist')
        }

        beta_map = {r.get('symbol'): float(r.get('confidence', 0.0)) for r in beta}
        gamma_list = gamma.get('general', []) if isinstance(gamma, dict) else []
        gamma_map = {r.get('symbol'): r for r in gamma_list}

        # Compute beta/gamma inline for stocks not in pre-computed maps
        from sepa.data.fundamentals import eps_growth_snapshot

        # Collect RS raw values for percentile
        rs_raw: dict[str, float] = {}
        for row in alpha:
            sym = row.get('symbol', '')
            if sym in price_cache:
                closes = price_cache[sym]['closes']
                if len(closes) >= 121:
                    rs_raw[sym] = closes[-1] / closes[-121] - 1.0

        rs_pct = to_percentile(rs_raw) if rs_raw else {}

        confirmed: list[dict] = []
        setup: list[dict] = []

        for row in alpha:
            symbol = row.get('symbol', '')
            sector = get_sector(symbol, self.sector_map)
            if eligible_sectors and sector not in eligible_sectors:
                continue
            if symbol not in price_cache:
                continue

            closes = price_cache[symbol]['closes']
            volumes = price_cache[symbol]['volumes']
            checks = row.get('checks', {})

            # Gate: TT >= 5/8
            passed = sum(1 for v in checks.values() if v)
            if passed < 5:
                continue
            # Gate: close > MA50
            if len(closes) >= 50 and closes[-1] <= mean(closes[-50:]):
                continue

            # New spec factors
            tt = trend_template_ratio(checks)
            n52 = near_52w_high(closes)
            vol_exp = volume_expansion(volumes)
            vol_cont = volatility_contraction(closes)
            # Beta: use pre-computed or calculate inline VCP proxy
            if symbol not in beta_map and len(closes) >= 50:
                try:
                    # Simple VCP proxy: volatility contraction + volume dryup
                    atr10 = mean([abs(closes[i] - closes[i-1]) for i in range(-9, 0)])
                    atr50 = mean([abs(closes[i] - closes[i-1]) for i in range(-49, 0)])
                    vol5 = mean(volumes[-5:]) if len(volumes) >= 5 else 0
                    vol50 = mean(volumes[-50:]) if len(volumes) >= 50 else 1
                    contraction = (1.0 - atr10 / atr50) if atr50 > 0 else 0
                    dryup = (1.0 - vol5 / vol50) if vol50 > 0 else 0
                    if contraction > 0 and dryup > 0:
                        beta_map[symbol] = round(min(contraction + dryup, 1.0), 2)
                except Exception:
                    pass

            # Gamma: use pre-computed or calculate inline from EPS
            g_row = gamma_map.get(symbol, {})
            if not g_row:
                try:
                    eps_snap = eps_growth_snapshot(symbol)
                    g_row = {
                        'eps_yoy': eps_snap.get('latest_yoy', 0),
                        'gamma_score': eps_snap.get('growth_hint', 0.5) / 2.0,
                    }
                    gamma_map[symbol] = g_row
                except Exception:
                    pass

            ep = earnings_proxy(
                eps_yoy=g_row.get('eps_yoy'),
                roe=g_row.get('roe'),
                opm=g_row.get('opm'),
            )

            leader_score = min(1.0, (
                min(1.0, rs_pct.get(symbol, 0.5)) * 0.25
                + min(1.0, tt) * 0.20
                + min(1.0, n52) * 0.15
                + min(1.0, vol_exp) * 0.15
                + min(1.0, vol_cont) * 0.15
                + min(1.0, ep) * 0.10
            ))

            sector_row = sector_map_data.get(sector, {})
            sector_ready = bool(sector_row.get('leadership_ready'))

            payload = {
                'symbol': symbol,
                'name': get_symbol_name(symbol),
                'sector': sector,
                'sector_bucket': sector_row.get('sector_bucket', 'watchlist'),
                'sector_leader_score': round(float(sector_row.get('leader_score', 0.0)), 2),
                'sector_leadership_ready': sector_ready,
                'leader_stock_score': round(leader_score * 100.0, 2),
                'leader_score': round(leader_score, 4),
                'rs_120_pct': round(rs_pct.get(symbol, 0.5), 4),
                'trend_template_score': round(tt, 4),
                'near_52w_high': round(n52, 4),
                'volume_expansion': round(vol_exp, 4),
                'volatility_contraction': round(vol_cont, 4),
                'earnings_proxy': round(ep, 4),
                'trend_checks': checks,
                # Legacy fields for API compat
                'alpha_score': round(float(row.get('score', 0.0)), 2),
                'beta_confidence': round(beta_map.get(symbol, 0.0), 2),
                'gamma_score': round(float(g_row.get('gamma_score', 0.0)), 2),
                'ret120': round(rs_raw.get(symbol, 0.0), 4),
                'ret120_pct': round(rs_raw.get(symbol, 0.0) * 100.0, 2),
                'stock_bucket': 'confirmed_leader' if sector_ready else 'setup_candidate',
                'reason': self._build_reason(tt, n52, vol_cont, ep, rs_pct.get(symbol, 0.5)),
                'why': self._build_reason(tt, n52, vol_cont, ep, rs_pct.get(symbol, 0.5)),
            }
            if sector_ready:
                confirmed.append(payload)
            else:
                setup.append(payload)

        # Fallback if nothing found
        if not confirmed and not setup:
            for row in alpha[:self.stock_top_n]:
                symbol = row.get('symbol', '')
                setup.append({
                    'symbol': symbol,
                    'name': get_symbol_name(symbol),
                    'sector': get_sector(symbol, self.sector_map),
                    'leader_stock_score': round(float(row.get('score', 0.0)), 2),
                    'alpha_score': round(float(row.get('score', 0.0)), 2),
                    'stock_bucket': 'setup_candidate',
                    'reason': 'fallback: alpha top rank',
                    'why': 'fallback: alpha top rank',
                })

        confirmed.sort(key=lambda x: x.get('leader_stock_score', 0.0), reverse=True)
        setup.sort(key=lambda x: x.get('leader_stock_score', 0.0), reverse=True)
        limit = max(5, self.stock_top_n)
        return confirmed[:limit] + setup[:limit]

    # ------------------------------------------------------------------
    # Grouped output (for sectors-grouped endpoint)
    # ------------------------------------------------------------------

    def _rank_leader_stocks_by_sector(
        self,
        alpha: list[dict],
        beta: list[dict],
        gamma: dict,
        price_cache: dict[str, dict],
        sectors: list[dict],
        per_sector_n: int = 5,
        as_of_date: str | None = None,
    ) -> list[dict]:
        sector_map_data = {row['sector']: row for row in sectors}
        beta_map = {r.get('symbol'): float(r.get('confidence', 0.0)) for r in beta}
        gamma_list = gamma.get('general', []) if isinstance(gamma, dict) else []
        gamma_map = {r.get('symbol'): float(r.get('gamma_score', 0.0)) for r in gamma_list}

        stocks_by_sector: dict[str, list[dict]] = {}
        for row in alpha:
            symbol = row.get('symbol', '')
            sector = get_sector(symbol, self.sector_map)
            if sector not in sector_map_data:
                continue

            sector_row = sector_map_data.get(sector, {})
            rs = 0.0
            if symbol in price_cache:
                closes = price_cache[symbol]['closes']
                if len(closes) >= 121 and closes[-121] > 0:
                    rs = closes[-1] / closes[-121] - 1.0

            alpha_score = float(row.get('score', 0.0))
            total = alpha_score + rs * 100.0 * 0.10
            spark = self._sparkline(symbol, n=120, as_of_date=as_of_date)

            payload = {
                'symbol': symbol,
                'name': get_symbol_name(symbol),
                'sector': sector,
                'sector_bucket': sector_row.get('sector_bucket', 'watchlist'),
                'sector_leadership_ready': bool(sector_row.get('leadership_ready')),
                'alpha_score': round(alpha_score, 2),
                'beta_confidence': round(beta_map.get(symbol, 0.0), 2),
                'gamma_score': round(gamma_map.get(symbol, 0.0), 2),
                'ret120': round(rs, 4),
                'ret120_pct': round(rs * 100.0, 2),
                'leader_stock_score': round(total, 2),
                'sparkline': spark,
                'price': spark[-1] if spark else None,
            }
            stocks_by_sector.setdefault(sector, []).append(payload)

        grouped: list[dict] = []
        for sector_row in sectors:
            sector = sector_row['sector']
            bucket = sector_row.get('sector_bucket', 'emerging')
            if bucket not in ('confirmed_leader', 'watchlist'):
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sparkline(self, symbol: str, n: int = 60, as_of_date: str | None = None) -> list[float]:
        # DB first (bare code), then CSV fallback
        try:
            from sepa.data.ohlcv_db import read_ohlcv, DB_PATH
            if DB_PATH.exists():
                rows = read_ohlcv(symbol, as_of_date=as_of_date)
                if rows:
                    return [int(round(r['close'])) for r in rows[-n:] if r.get('close', 0) > 0]
        except Exception:
            pass
        path = self.data_dir / f'{symbol}.csv'
        if not path.exists():
            return []
        try:
            closes = [row.get('close', 0.0) for row in read_price_series_from_path(path, as_of_date=as_of_date)]
            return [int(round(c)) for c in closes[-n:] if c > 0]
        except (ValueError, TypeError, KeyError, OSError) as exc:
            logger.warning('sparkline failed for %s: %s', symbol, exc)
            return []

    @staticmethod
    def _build_reason(tt: float, near_high: float, vol_cont: float, ep: float, rs: float) -> str:
        parts: list[str] = []
        if rs >= 0.7:
            parts.append('RS상위')
        if tt >= 0.625:
            parts.append(f'TT{int(tt * 8)}/8')
        if vol_cont >= 0.5:
            parts.append('VCP수축진행')
        if near_high >= 0.9:
            parts.append('신고가근접')
        if ep >= 0.6:
            parts.append('실적양호')
        return '+'.join(parts) if parts else '기본통과'

    @staticmethod
    def _avg_series(series_list: list[list[float]]) -> list[float]:
        if not series_list:
            return []
        max_len = max(len(s) for s in series_list)
        avg: list[float] = []
        for i in range(max_len):
            vals = []
            for s in series_list:
                offset = len(s) - max_len + i
                if 0 <= offset < len(s):
                    vals.append(s[offset])
            avg.append(sum(vals) / len(vals) if vals else 0.0)
        return avg

    @staticmethod
    def _sum_series(series_list: list[list[float]]) -> list[float]:
        if not series_list:
            return []
        max_len = max(len(s) for s in series_list)
        sums: list[float] = []
        for i in range(max_len):
            total = 0.0
            for s in series_list:
                offset = len(s) - max_len + i
                if 0 <= offset < len(s):
                    total += s[offset]
            sums.append(total)
        return sums

    @staticmethod
    def _read_json(path: Path, default):
        if not path.exists():
            return default
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            # Handle envelope-wrapped outputs
            if isinstance(data, dict) and 'items' in data:
                return data['items']
            return data
        except json.JSONDecodeError:
            return default
