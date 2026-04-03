from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev

from sepa.data.price_history import read_price_series_from_path
from sepa.data.universe import get_symbol_name


@dataclass
class SwingPoint:
    idx: int
    price: float
    kind: str


class BetaChartist:
    """Rule-based VCP detector."""

    def __init__(
        self,
        data_dir: Path = Path('.omx/artifacts/market-data/ohlcv'),
        audit_dir: Path = Path('.omx/artifacts/audit-logs'),
        min_confidence: float | None = None,
        max_consistency: float | None = None,
    ) -> None:
        self.data_dir = data_dir
        self.audit_dir = audit_dir
        self.min_confidence = float(
            min_confidence
            if min_confidence is not None
            else os.getenv('SEPA_BETA_MIN_CONFIDENCE', '1.8')
        )
        self.max_consistency = float(
            max_consistency
            if max_consistency is not None
            else os.getenv('SEPA_BETA_MAX_CONSISTENCY', '1.9')
        )

    def run(self, alpha_passed: list[dict], as_of_date: str | None = None) -> list[dict]:
        out: list[dict] = []
        for row in alpha_passed:
            symbol = row.get('symbol')
            if not symbol:
                continue

            path = self.data_dir / f'{symbol}.csv'
            if not path.exists():
                self._audit('beta', f'missing csv: {path}')
                continue

            closes, volumes = self._read_series(path, as_of_date=as_of_date)
            if len(closes) < 80:
                continue

            swings = self._find_swings(closes, window=3)
            contractions = self._contractions(swings)
            if len(contractions) >= 2:
                consistency = self._contraction_consistency(contractions)
                waves = min(max(len(contractions), 2), 6)
            else:
                consistency, waves = self._fallback_contraction(closes)

            volume_dryup = self._volume_dryup(volumes)
            confidence = self._confidence(
                waves=waves,
                consistency=consistency,
                volume_dryup=volume_dryup,
            )

            if confidence < self.min_confidence or consistency > self.max_consistency:
                continue

            out.append(
                {
                    'symbol': symbol,
                    'name': get_symbol_name(symbol),
                    'waves': waves,
                    'contraction_ratio': round(consistency, 4),
                    'volume_dryup': round(volume_dryup, 4),
                    'confidence': round(confidence, 2),
                }
            )

        out.sort(key=lambda item: item['confidence'], reverse=True)
        return out

    @staticmethod
    def _read_series(path: Path, as_of_date: str | None = None) -> tuple[list[float], list[float]]:
        rows = read_price_series_from_path(path, as_of_date=as_of_date)
        closes = [row.get('close', 0.0) for row in rows if row.get('close', 0.0) > 0]
        volumes = [max(0.0, row.get('volume', 0.0)) for row in rows if row.get('close', 0.0) > 0]
        return closes, volumes

    @staticmethod
    def _find_swings(closes: list[float], window: int = 3) -> list[SwingPoint]:
        swings: list[SwingPoint] = []
        for index in range(window, len(closes) - window):
            center = closes[index]
            left = closes[index - window:index]
            right = closes[index + 1:index + 1 + window]
            if center >= max(left) and center >= max(right):
                swings.append(SwingPoint(index, center, 'H'))
            elif center <= min(left) and center <= min(right):
                swings.append(SwingPoint(index, center, 'L'))
        return swings

    @staticmethod
    def _contractions(swings: list[SwingPoint]) -> list[float]:
        contractions: list[float] = []
        index = 0
        while index < len(swings) - 1:
            left = swings[index]
            right = swings[index + 1]
            if left.kind == 'H' and right.kind == 'L' and left.price > 0:
                contractions.append((left.price - right.price) / left.price)
                index += 2
            else:
                index += 1
        return [value for value in contractions if value > 0]

    @staticmethod
    def _contraction_consistency(contractions: list[float]) -> float:
        sample = contractions[-4:] if len(contractions) > 4 else contractions
        if len(sample) < 2:
            return 1.0

        ratios: list[float] = []
        for index in range(1, len(sample)):
            previous = sample[index - 1]
            current = sample[index]
            ratios.append((current / previous) if previous > 0 else 1.0)
        return mean(ratios)

    @staticmethod
    def _fallback_contraction(closes: list[float]) -> tuple[float, int]:
        if len(closes) < 90:
            return 1.0, 2

        returns: list[float] = []
        for index in range(1, len(closes)):
            previous = closes[index - 1]
            current = closes[index]
            returns.append((current / previous - 1.0) if previous > 0 else 0.0)

        recent = returns[-20:]
        base = returns[-80:-20] if len(returns) >= 80 else returns[:-20]
        if not recent or not base:
            return 1.0, 2

        recent_vol = pstdev(recent)
        base_vol = pstdev(base)
        ratio = (recent_vol / base_vol) if base_vol > 0 else 1.0
        waves = 3 if ratio < 0.8 else 2
        return ratio, waves

    @staticmethod
    def _volume_dryup(volumes: list[float]) -> float:
        if not volumes:
            return 1.0
        recent = volumes[-20:] if len(volumes) >= 20 else volumes
        base = volumes[-60:] if len(volumes) >= 60 else volumes
        base_mean = mean(base) if base else 0.0
        recent_mean = mean(recent) if recent else 0.0
        if base_mean <= 0:
            return 1.0
        return recent_mean / base_mean

    @staticmethod
    def _confidence(waves: int, consistency: float, volume_dryup: float) -> float:
        wave_score = 1.0 if 2 <= waves <= 4 else (0.6 if waves in (5, 6) else 0.4)

        if consistency <= 0.7:
            consistency_score = 1.0
        elif consistency >= 1.3:
            consistency_score = 0.0
        else:
            consistency_score = (1.3 - consistency) / 0.6

        if volume_dryup <= 0.7:
            volume_score = 1.0
        elif volume_dryup >= 1.2:
            volume_score = 0.0
        else:
            volume_score = (1.2 - volume_dryup) / 0.5

        raw = (wave_score * 0.25) + (consistency_score * 0.5) + (volume_score * 0.25)
        return raw * 10.0

    def _audit(self, component: str, message: str) -> None:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        path = self.audit_dir / f'{component}-{timestamp}.log'
        path.write_text(json.dumps({'timestamp': timestamp, 'message': message}, ensure_ascii=False), encoding='utf-8')
