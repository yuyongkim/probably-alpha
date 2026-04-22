"""Chartist domain models + today-bundle producer.

MVP slice: returns mock data shaped like the mockup so the whole
data -> API -> web vertical slice can be wired end-to-end.

# TODO Phase 3: Replace mock with QuantDB/mvp_platform data sources
# (sector strength scoreboard + leader scan + last backtest summary).
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Core index + summary + existing models ---------------------

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


# ---------- New panel models ------------------------------------------

class SectorHeatRow(BaseModel):
    """One row of the 28-sector x 5-period heatmap.

    Each period has a signed pct value and a color bucket (0..6)
    that the UI renders as `.hm-cell.h0 .. .h6` backgrounds.
    """
    name: str
    p1d: float
    p1d_h: int
    p1w: float
    p1w_h: int
    p1m: float
    p1m_h: int
    p3m: float
    p3m_h: int
    pytd: float
    pytd_h: int


class Breakout(BaseModel):
    ticker: str           # 사람이 읽는 종목명
    symbol: str           # 6-digit code
    market: str           # KOSPI / KOSDAQ
    pct_up: float         # 1D % up
    vol_x: float          # volume multiple
    sector: str


class WizardCount(BaseModel):
    name: str                       # 'Minervini', 'O'Neil', ...
    condition: str                  # 'SEPA 8-cond VCP'
    pass_count: int
    total: int                      # universe size
    delta_vs_yesterday: int


class StageBucket(BaseModel):
    name: str             # 'Stage 1 (초기)', 'Breakout', 'Fail (손절)', ...
    count: int
    pct: float            # width of the bar, 0..100
    color_hint: str       # CSS hex for the bar fill (mockup palette)


class LogEvent(BaseModel):
    time: str             # 'HH:MM:SS'
    tag: str              # BUY | SELL | VCP | EPS | DART | BRK | SYS
    symbol: Optional[str] = None
    message: str


class UpcomingEvent(BaseModel):
    date: str             # '04-23 16:00'
    ticker_or_event: str  # '삼성전자 실적' or 'FOMC 의사록'
    type: str             # 'Earnings' | 'Macro'
    consensus_eps: Optional[str] = None   # '1,842' or '2.4%' or '—'
    note: str


# ---------- Top-level bundle ------------------------------------------

class TodayBundle(BaseModel):
    date: str
    owner_id: str
    universe_size: int
    market: List[MarketIndex]
    summary: List[SummaryKPI]
    leaders: List[Leader]
    sectors: List[Sector]
    heatmap: List[SectorHeatRow]
    breakouts: List[Breakout]
    wizards_pass: List[WizardCount]
    stage_dist: List[StageBucket]
    activity_log: List[LogEvent]
    upcoming_events: List[UpcomingEvent]
    last_backtest_cagr: Optional[float] = None


# ---------- Mock fixtures (sourced from _integration_mockup.html) -----

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

# heatmap rows: (name, (p1d, h), (p1w, h), (p1m, h), (p3m, h), (pytd, h))
_HEATMAP = [
    ("반도체",         (2.14, 6), (6.82, 6), (18.4, 6), (34.2, 6), (48.7, 6)),
    ("2차전지",        (1.41, 5), (4.17, 5), (9.8, 5),  (4.2, 4),  (1.8, 3)),
    ("AI / 소프트웨어", (1.82, 5), (3.91, 5), (11.2, 5), (24.8, 6), (38.4, 6)),
    ("원전",           (2.08, 5), (5.44, 5), (14.7, 6), (28.3, 6), (42.1, 6)),
    ("바이오",         (0.72, 4), (1.38, 4), (2.1, 3),  (-3.4, 2), (0.8, 3)),
    ("조선",           (0.38, 4), (1.14, 4), (8.4, 5),  (19.2, 6), (31.8, 6)),
    ("자동차",         (0.28, 4), (-0.42, 3),(1.2, 3),  (3.8, 4),  (8.4, 5)),
    ("방산",           (-0.84, 2),(-2.14, 1),(-4.8, 1), (-2.1, 2), (14.2, 5)),
    ("화장품",         (0.14, 4), (-0.38, 3),(-2.4, 2), (-6.8, 1), (-2.1, 2)),
    ("금융 (은행)",    (-0.18, 3),(-0.71, 3),(1.4, 3),  (4.1, 4),  (9.8, 5)),
    ("철강",           (-0.34, 3),(-1.14, 3),(2.8, 4),  (4.2, 4),  (3.8, 4)),
    ("화학",           (-0.42, 3),(-1.84, 2),(-3.1, 2), (-7.4, 1), (-2.8, 2)),
    ("정유",           (0.08, 3), (1.24, 4), (2.8, 4),  (3.1, 4),  (1.2, 3)),
    ("유통",           (-0.28, 3),(-0.94, 3),(-2.8, 2), (-4.2, 2), (-3.4, 2)),
    ("게임",           (1.42, 5), (2.14, 4), (3.8, 4),  (7.2, 5),  (12.4, 5)),
    ("엔터테인먼트",   (0.48, 4), (1.28, 4), (1.4, 3),  (-2.8, 2), (1.2, 3)),
    ("여행/항공",      (-0.14, 3),(-0.84, 3),(0.8, 3),  (3.8, 4),  (4.2, 4)),
    ("제약",           (0.32, 4), (0.41, 3), (-1.4, 2), (-3.8, 2), (-0.8, 3)),
    ("건설",           (-0.74, 2),(-2.14, 2),(-4.2, 1), (-8.4, 1), (-11.2, 1)),
    ("통신",           (-0.08, 3),(0.14, 3), (0.8, 3),  (2.4, 4),  (3.1, 4)),
]

_BREAKOUTS = [
    ("이수페타시스", "007660", "KOSDAQ", 5.82, 3.2, "반도체"),
    ("HPSP",         "403870", "KOSDAQ", 4.21, 1.8, "반도체"),
    ("한미반도체",   "042700", "KOSDAQ", 3.67, 2.1, "반도체"),
    ("두산에너빌리티","034020", "KOSPI",  3.28, 2.4, "원전"),
    ("SFA반도체",    "036540", "KOSDAQ", 2.84, 1.7, "반도체"),
    ("동진쎄미켐",   "005290", "KOSDAQ", 2.54, 1.9, "반도체"),
    ("솔브레인",     "357780", "KOSDAQ", 2.41, 1.4, "반도체"),
    ("파크시스템스", "140860", "KOSDAQ", 2.14, 1.6, "반도체"),
    ("티에스이",     "131290", "KOSDAQ", 1.97, 1.3, "반도체"),
    ("ISC",          "095340", "KOSDAQ", 1.84, 1.2, "반도체"),
]

_WIZARDS = [
    ("Minervini",       "SEPA 8-cond VCP",    24, 2175, +3),
    ("O'Neil",          "CANSLIM",            17, 2175, +1),
    ("Darvas",          "Breakout + Vol",      9, 2175, -2),
    ("Livermore",       "Line of Least Res.", 12, 2175, +2),
    ("Zanger",          "Gap + Vol + HOD",     6, 2175, +4),
    ("Weinstein",       "Stage 2 SMA30",      21, 2175, +2),
    ("교집합 (전체)",    "6 프리셋 모두",        3, 2175,  0),
]

# Stage bucket palette sourced from mockup inline styles:
# Stage1 #D8E2DC · Stage2 #B4CBB8 · Stage3 #7FA88A · Breakout #2D6A4F
# Extended #B08968 · Fail #BC4B51
_STAGES = [
    ("Stage 1 (초기)",   47, 58.0, "#D8E2DC"),
    ("Stage 2 (수축)",   34, 42.0, "#B4CBB8"),
    ("Stage 3 (돌파 전)",24, 29.0, "#7FA88A"),
    ("Breakout",         18, 22.0, "#2D6A4F"),
    ("Extended",         10, 12.0, "#B08968"),
    ("Fail (손절)",       4,  5.0, "#BC4B51"),
]

_LOG = [
    ("15:28:42", "BUY",  "042700", "한미반도체 신고가 돌파 · Vol 2.1× · TT 8/8"),
    ("15:24:18", "VCP",  "403870", "HPSP Stage 3 진입 · 수축 3파 · 돌파 대기"),
    ("15:21:07", "BUY",  "007660", "이수페타시스 52w 돌파 · 거래량 3.2×"),
    ("15:18:33", "EPS",  "058470", "리노공업 1Q 실적 컨센서스 상회 · EPS +28%"),
    ("15:14:52", "SELL", "247540", "에코프로비엠 Stage 2 실패 · 손절 -1.84%"),
    ("15:08:14", "DART", "005380", "현대차 자사주 1조원 소각 발표"),
    ("15:02:47", "SYS",  None,     "섹터 강도 갱신 · 반도체 5주 연속 1위 · RS 0.87"),
    ("14:58:21", "BRK",  "034020", "두산에너빌리티 신고가 · SMP 상승 수혜"),
    ("14:54:08", "BUY",  "000660", "SK하이닉스 SMA50 돌파 · 외인 매수"),
    ("14:47:42", "SYS",  None,     "Macro Compass 업데이트 · Expansion 유지 · +0.62"),
]

_EVENTS = [
    ("04-23 16:00", "삼성전자 실적",    "Earnings", "1,842", "DS 회복 확인"),
    ("04-24 09:30", "FOMC 의사록",      "Macro",    "—",     "금리 경로"),
    ("04-24 16:00", "LG에너지솔루션",   "Earnings", "412",   "ESS 수주"),
    ("04-25 08:30", "미국 GDP 1Q",      "Macro",    "2.4%",  "예상 2.1%"),
    ("04-25 16:00", "SK하이닉스",       "Earnings", "4,284", "HBM ASP"),
    ("04-26 15:00", "한은 금통위",      "Macro",    "—",     "동결 예상"),
    ("04-27 08:30", "미 PCE 3월",       "Macro",    "2.6%",  "물가 추이"),
    ("04-29 16:00", "현대차 실적",      "Earnings", "3,124", "미국 판매"),
    ("05-01 21:30", "미 ISM 제조업",    "Macro",    "49.2",  "확장/수축"),
    ("05-02 21:30", "미 고용지표",      "Macro",    "172K",  "실업률 4.1%"),
]


# ---------- Factory ---------------------------------------------------

def _build_heatmap() -> List[SectorHeatRow]:
    out: List[SectorHeatRow] = []
    for name, d1, w1, m1, m3, ytd in _HEATMAP:
        out.append(SectorHeatRow(
            name=name,
            p1d=d1[0], p1d_h=d1[1],
            p1w=w1[0], p1w_h=w1[1],
            p1m=m1[0], p1m_h=m1[1],
            p3m=m3[0], p3m_h=m3[1],
            pytd=ytd[0], pytd_h=ytd[1],
        ))
    return out


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
        heatmap=_build_heatmap(),
        breakouts=[
            Breakout(ticker=r[0], symbol=r[1], market=r[2], pct_up=r[3], vol_x=r[4], sector=r[5])
            for r in _BREAKOUTS
        ],
        wizards_pass=[
            WizardCount(name=r[0], condition=r[1], pass_count=r[2], total=r[3],
                        delta_vs_yesterday=r[4])
            for r in _WIZARDS
        ],
        stage_dist=[
            StageBucket(name=r[0], count=r[1], pct=r[2], color_hint=r[3])
            for r in _STAGES
        ],
        activity_log=[
            LogEvent(time=r[0], tag=r[1], symbol=r[2], message=r[3])
            for r in _LOG
        ],
        upcoming_events=[
            UpcomingEvent(date=r[0], ticker_or_event=r[1], type=r[2],
                          consensus_eps=r[3], note=r[4])
            for r in _EVENTS
        ],
        last_backtest_cagr=0.234,
    )
