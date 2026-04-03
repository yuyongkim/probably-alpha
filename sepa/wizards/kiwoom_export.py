"""키움 HTS 조건검색식 내보내기 모듈.

각 Market Wizards 전략의 조건을 키움 영웅문 HTS에서
조건검색식으로 입력 가능한 텍스트/JSON 형식으로 변환.

Usage:
    from sepa.wizards.kiwoom_export import KiwoomExporter

    exporter = KiwoomExporter()

    # 전체 전략 조건식 목록
    all_conditions = exporter.export_all()

    # 특정 카테고리
    trend_conds = exporter.export_by_category('trend_following')

    # JSON 파일로 저장
    exporter.save_json('kiwoom_conditions.json')

    # 사람이 읽을 수 있는 텍스트
    text = exporter.to_text()
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sepa.wizards.screener import ALL_STRATEGIES, CATEGORY_MAP


# ---------------------------------------------------------------------------
# Category display names
# ---------------------------------------------------------------------------

CATEGORY_DISPLAY = {
    'trend_following': '추세추종',
    'growth_momentum': '성장 모멘텀',
    'swing': '단기 스윙',
    'contrarian_value': '역발상/가치',
    'volatility_contraction': '변동성 수축 돌파',
    'macro_liquidity': '매크로/유동성',
}

BOOK_DISPLAY = {
    'MW1989': 'Market Wizards (1989)',
    'NMW1992': 'New Market Wizards (1992)',
    'SMW2001': 'Stock Market Wizards (2001)',
}


# ---------------------------------------------------------------------------
# Exporter
# ---------------------------------------------------------------------------

class KiwoomExporter:
    """Export wizard strategies as Kiwoom HTS condition formulas."""

    def export_all(self) -> list[dict[str, Any]]:
        """All strategies with 키움 조건식."""
        return [self._strategy_to_dict(cls) for cls in ALL_STRATEGIES]

    def export_by_category(self, category: str) -> list[dict[str, Any]]:
        """Strategies for one category."""
        classes = CATEGORY_MAP.get(category, [])
        return [self._strategy_to_dict(cls) for cls in classes]

    def export_by_trader(self, trader: str) -> list[dict[str, Any]]:
        trader_lower = trader.lower()
        return [
            self._strategy_to_dict(cls)
            for cls in ALL_STRATEGIES
            if cls.trader.lower() == trader_lower
        ]

    def save_json(self, path: str | Path) -> None:
        """Save all conditions to JSON file."""
        data = {
            'title': '시장의 마법사 — 키움 HTS 조건검색식',
            'description': (
                'Jack Schwager 3부작에 등장하는 트레이더별 전략을 '
                '키움 영웅문 HTS 조건검색식으로 변환한 데이터'
            ),
            'total_strategies': len(ALL_STRATEGIES),
            'categories': {
                k: CATEGORY_DISPLAY.get(k, k)
                for k in CATEGORY_MAP
            },
            'strategies': self.export_all(),
            'combined_conditions': self._combined_master_conditions(),
        }
        Path(path).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )

    def to_text(self) -> str:
        """사람이 읽을 수 있는 전체 텍스트 출력."""
        lines: list[str] = []
        lines.append('=' * 70)
        lines.append('시장의 마법사 — 키움 HTS 조건검색식 전체 목록')
        lines.append('=' * 70)
        lines.append('')

        by_cat: dict[str, list[type]] = {}
        for cls in ALL_STRATEGIES:
            by_cat.setdefault(cls.category, []).append(cls)

        for cat, classes in by_cat.items():
            cat_name = CATEGORY_DISPLAY.get(cat, cat)
            lines.append(f'━━━ {cat_name} ━━━')
            lines.append('')

            for cls in classes:
                instance = cls()
                kiwoom = instance.kiwoom_conditions()
                lines.append(f'▶ {cls.name}')
                lines.append(f'  트레이더: {cls.trader}')
                lines.append(f'  출처: {BOOK_DISPLAY.get(cls.book, cls.book)}')
                lines.append(f'  설명: {cls.description_text}')
                lines.append(f'  조건식:')
                for i, cond in enumerate(kiwoom, 1):
                    lines.append(f'    {i}. {cond}')
                lines.append('')

        # Combined master conditions
        lines.append('=' * 70)
        lines.append('통합 마스터 조건식 (유형별)')
        lines.append('=' * 70)
        lines.append('')
        for group in self._combined_master_conditions():
            lines.append(f'■ {group["name"]} ({group["description"]})')
            for i, c in enumerate(group['conditions'], 1):
                lines.append(f'  {i}. {c}')
            lines.append(f'  관련 트레이더: {", ".join(group["traders"])}')
            lines.append('')

        return '\n'.join(lines)

    def _strategy_to_dict(self, cls: type[WizardStrategy]) -> dict[str, Any]:
        instance = cls()
        return {
            'name': cls.name,
            'trader': cls.trader,
            'category': cls.category,
            'category_display': CATEGORY_DISPLAY.get(cls.category, cls.category),
            'book': cls.book,
            'book_display': BOOK_DISPLAY.get(cls.book, cls.book),
            'description': cls.description_text,
            'kiwoom_conditions': instance.kiwoom_conditions(),
            'condition_count': len(instance.kiwoom_conditions()),
        }

    @staticmethod
    def _combined_master_conditions() -> list[dict[str, Any]]:
        """Category-level master conditions for Kiwoom HTS."""
        return [
            {
                'name': '추세추종 마스터',
                'description': 'Dennis, Seykota, Jones, Hite, Bielfeldt, Weiss',
                'traders': ['Richard Dennis', 'Ed Seykota', 'Paul Tudor Jones',
                           'Larry Hite', 'Gary Bielfeldt', 'Al Weiss'],
                'conditions': [
                    '이동평균(종가,50) > 이동평균(종가,150) > 이동평균(종가,200)',
                    '현재가 > 이동평균(종가,50)',
                    '이동평균(종가,200) > 이동평균(종가,200)[22일전]',
                    '현재가 >= MAX(고가, 20)',
                    '거래량 > 이동평균(거래량,20)',
                ],
            },
            {
                'name': '성장 모멘텀 마스터',
                'description': "O'Neil, Ryan, Driehaus, Walton, Cohen",
                'traders': ["William O'Neil", 'David Ryan', 'Richard Driehaus',
                           'Stuart Walton', 'Steve Cohen'],
                'conditions': [
                    '현재가 > 이동평균(종가,150) AND 현재가 > 이동평균(종가,200)',
                    '이동평균(종가,50) > 이동평균(종가,150)',
                    '현재가 >= 52주최저가 × 1.25',
                    '현재가 >= 52주최고가 × 0.75',
                    '거래량 > 이동평균(거래량,50) × 1.5',
                    '시가총액 >= 500억',
                    '[수동] EPS QoQ >= 25%',
                    '[수동] EPS YoY >= 25%',
                ],
            },
            {
                'name': '단기 스윙 마스터',
                'description': 'Schwartz, Raschke, Trout',
                'traders': ['Marty Schwartz', 'Linda Bradford Raschke', 'Monroe Trout'],
                'conditions': [
                    '현재가 > EMA(10)',
                    'RSI(14) > 40 AND RSI(14) < 65',
                    'ADX(14) > 20',
                    '(고가-저가)/종가 < 0.025',
                    '현재가 > 이동평균(종가,50)',
                ],
            },
            {
                'name': '역발상 가치 마스터',
                'description': 'Rogers, Steinhardt, Okumus',
                'traders': ['James B. Rogers Jr.', 'Michael Steinhardt', 'Ahmet Okumus'],
                'conditions': [
                    'PBR < 0.8',
                    'PER < 업종평균PER × 0.6',
                    '부채비율 < 120%',
                    '현재가 < 52주최고가 × 0.55',
                    'RSI(14) < 35',
                    '거래량 > 이동평균(거래량,20) × 1.3',
                ],
            },
            {
                'name': 'VCP/스퀴즈 마스터',
                'description': 'Minervini, Ryan, Weinstein',
                'traders': ['Mark Minervini', 'David Ryan', 'Mark Weinstein'],
                'conditions': [
                    '이동평균(종가,50) > 이동평균(종가,150) > 이동평균(종가,200)',
                    '현재가 > 이동평균(종가,50)',
                    '볼린저밴드폭(20) < 15%',
                    '이동평균(거래량,5) < 이동평균(거래량,50) × 0.6',
                    '현재가 >= 52주최고가 × 0.85',
                    '(고가-저가)/종가 < 0.02',
                ],
            },
            {
                'name': '매크로 유동성 마스터',
                'description': 'Druckenmiller, Lipschutz, Basso',
                'traders': ['Stan Druckenmiller', 'Bill Lipschutz', 'Tom Basso'],
                'conditions': [
                    '이동평균(종가,50) > 이동평균(종가,200)',
                    '거래대금 >= 50억',
                    '외국인순매수(5일) > 0',
                    '(52주최고가 - 현재가) / 현재가 > 0.15',
                    '[계산] R:R >= 3:1',
                    'ATR(14)/현재가 < 0.03',
                ],
            },
        ]
