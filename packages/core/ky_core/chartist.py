"""Chartist domain models + today-bundle producer.

MVP slice: returns mock data shaped like the mockup so the whole
data -> API -> web vertical slice can be wired end-to-end.

# TODO Phase 3: Replace mock with QuantDB/mvp_platform data sources
# (sector strength scoreboard + leader scan + last backtest summary).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class MarketIndex(BaseModel):
    label: str
    value: str
    delta: str
    tone: str = Field(default="neutral")  # pos | neg | neutral


class SummaryKPI(BaseModel):
    label: str
    value: str
    delta: str
    tone: str = Field(default="neutral")


class Leader(BaseModel):
    symbol: str
    name: str
    sector: str
    leader_score: float
    trend_template: str
    rs: float
    d1: float
    d5: float
    m1: float
    vol_x: float
    pattern: str


class Sector(BaseModel):
    rank: int
    name: str
    score: float
    d1: float
    d5: float
    sparkline: List[float]


class TodayBundle(BaseModel):
    date: str
    owner_id: str
    universe_size: int
    market: List[MarketIndex]
    summary: List[SummaryKPI]
    leaders: List[Leader]
    sectors: List[Sector]
    last_backtest_cagr: Optional[float] = None


_MARKET = [
    ("KOSPI", "2,847.32", "+23.14 (+0.82%)", "pos"),
    ("KOSDAQ", "864.11", "+11.48 (+1.34%)", "pos"),
    ("KOSPI200", "385.47", "+2.84 (+0.74%)", "pos"),
    ("VKOSPI", "14.28", "-0.42", "neg"),
    ("USD/KRW", "1,342.50", "-2.80", "neg"),
    ("KR 10Y", "3.02%", "-2bp", "neg"),
    ("외국인 순매수", "+1,247억", "5일 연속", "pos"),
    ("프로그램 매매", "+842억", "차익 +312", "pos"),
]
_SUMMARY = [
    ("Top Sector", "반도체", "+2.14% · RS 0.87", "pos"),
    ("Top Leader", "한미반도체", "TT 8/8 · LS 0.91", "pos"),
    ("52w High", "13.7%", "+1.2pp WoW · 298종목", "pos"),
    ("VCP Stage 3", "24", "돌파 임박", "pos"),
    ("SEPA Pass", "142 / 2,175", "6.53% pass rate", "pos"),
    ("SEPA CAGR", "23.4%", "MDD -19.1% · Sh 1.38", "neg"),
]
_LEADERS = [
    ("042700", "한미반도체", "반도체", 0.91, "8/8", 0.91, 3.67, 8.24, 22.4, 2.1, "VCP"),
    ("403870", "HPSP", "반도체", 0.84, "7/8", 0.84, 4.21, 6.18, 18.7, 1.8, "Base"),
    ("058470", "리노공업", "반도체", 0.76, "7/8", 0.76, 2.14, 5.82, 14.2, 1.5, "VCP"),
    ("007660", "이수페타시스", "반도체", 0.73, "7/8", 0.81, 5.82, 12.41, 28.3, 3.2, "VCP"),
    ("000660", "SK하이닉스", "반도체", 0.72, "6/8", 0.79, 2.34, 4.18, 11.8, 1.2, "B.out"),
    ("005930", "삼성전자", "반도체", 0.72, "6/8", 0.72, 1.88, 3.42, 8.7, 1.0, "B.out"),
    ("247540", "에코프로비엠", "2차전지", 0.79, "7/8", 0.79, -1.84, 2.14, 9.2, 1.4, "VCP"),
    ("003670", "포스코퓨처엠", "2차전지", 0.68, "6/8", 0.71, 0.84, 3.41, 7.8, 1.1, "Base"),
    ("034020", "두산에너빌리티", "원전", 0.71, "7/8", 0.83, 3.28, 7.92, 19.4, 2.4, "VCP"),
    ("068270", "셀트리온", "바이오", 0.64, "6/8", 0.67, 1.42, 2.18, 5.3, 0.9, "Base"),
]
_SECTORS = [
    (1, "반도체", 0.87, 2.14, 6.82, [0.72, 0.76, 0.79, 0.82, 0.84, 0.86, 0.87]),
    (2, "2차전지", 0.74, 1.41, 4.17, [0.68, 0.70, 0.71, 0.72, 0.73, 0.74, 0.74]),
    (3, "AI/SW", 0.68, 1.82, 3.91, [0.55, 0.58, 0.61, 0.63, 0.65, 0.67, 0.68]),
    (4, "원전", 0.63, 2.08, 5.44, [0.52, 0.55, 0.58, 0.60, 0.61, 0.62, 0.63]),
    (5, "바이오", 0.54, 0.72, 1.38, [0.50, 0.52, 0.53, 0.53, 0.54, 0.54, 0.54]),
]


def get_today_bundle(owner_id: str = "self") -> TodayBundle:
    """Return today's Chartist bundle for the given owner (mock)."""
    return TodayBundle(
        date="2026-04-22",
        owner_id=owner_id,
        universe_size=2175,
        market=[MarketIndex(label=a, value=b, delta=c, tone=d) for a, b, c, d in _MARKET],
        summary=[SummaryKPI(label=a, value=b, delta=c, tone=d) for a, b, c, d in _SUMMARY],
        leaders=[
            Leader(
                symbol=r[0], name=r[1], sector=r[2], leader_score=r[3],
                trend_template=r[4], rs=r[5], d1=r[6], d5=r[7], m1=r[8],
                vol_x=r[9], pattern=r[10],
            )
            for r in _LEADERS
        ],
        sectors=[
            Sector(rank=r[0], name=r[1], score=r[2], d1=r[3], d5=r[4], sparkline=r[5])
            for r in _SECTORS
        ],
        last_backtest_cagr=0.234,
    )
