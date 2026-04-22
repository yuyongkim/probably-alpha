// Quant mock data — extracted from _integration_mockup.html.
// Used when a real API endpoint is not yet available for a subsection.

import type { DenseSummaryCell } from "@/components/shared/DenseSummary";
import type { MarketStripCell } from "@/components/shared/MarketStripPanel";
import type { HeatLevel } from "@/components/shared/Heatmap";
import type { LogEntry } from "@/components/shared/ActivityLog";

/* ---------- Factors ---------- */
export const FACTORS_MARKET: MarketStripCell[] = [
  { label: "Universe", value: "2,147", delta: "KOSPI + KOSDAQ" },
  { label: "Active Factor", value: "MOM 12-1", delta: "IC 0.124", tone: "pos" },
  { label: "IR (12M)", value: "1.38", delta: "+0.08 QoQ", tone: "pos" },
  { label: "Top Decile", value: "+28.4%", delta: "12M spread +22.1", tone: "pos" },
  { label: "Turnover", value: "48%", delta: "Monthly" },
  { label: "Macro Regime", value: "Expansion", delta: "Compass +0.62", tone: "pos" },
  { label: "Value Spread", value: "1.8σ", delta: "Extreme", tone: "amber" },
  { label: "Rebalance", value: "T-3", delta: "다음 금요일" },
];

export const FACTORS_KPI: DenseSummaryCell[] = [
  { label: "QuantKing P/F", value: "+34.2%", delta: "YTD · α +26.1pp", tone: "pos" },
  { label: "Sharpe", value: "1.42", delta: "3Y · Sortino 2.08", tone: "pos" },
  { label: "MDD", value: "−19.4%", delta: "2022-10 · 회복 완료", tone: "pos" },
  { label: "Hit Rate", value: "61.2%", delta: "월간 기준", tone: "pos" },
  { label: "Long-Short", value: "+18.7%", delta: "β-neutral 12M", tone: "pos" },
  { label: "Factor Crash", value: "−4.2%", delta: "Momentum · 2024-08", tone: "neg" },
];

export const FACTORS_IC: Array<{
  name: string;
  value: number;
  level: HeatLevel;
}> = [
  { name: "Momentum 12-1", value: 0.124, level: 5 },
  { name: "Quality (ROE)", value: 0.087, level: 5 },
  { name: "Growth (EPS)", value: 0.076, level: 5 },
  { name: "Low-Vol", value: 0.054, level: 4 },
  { name: "Value (P/B)", value: 0.031, level: 4 },
  { name: "Size (mkt cap)", value: -0.028, level: 2 },
  { name: "BAB (beta)", value: -0.014, level: 2 },
];

export const FACTORS_QUINTILE = {
  columns: ["Q1 Top", "Q2", "Q3", "Q4", "Q5 Bot", "Q1−Q5"],
  rows: [
    { name: "Value (P/B)", cells: [ ["+18.4",5], ["+14.2",5], ["+9.8",4], ["+4.2",3], ["−2.8",2], ["+21.2",6] ] },
    { name: "Quality (ROE)", cells: [ ["+24.8",6], ["+16.2",5], ["+11.4",4], ["+6.8",3], ["−4.1",2], ["+28.9",6] ] },
    { name: "Momentum 12-1", cells: [ ["+32.4",6], ["+18.8",5], ["+10.2",4], ["+2.4",3], ["−8.4",1], ["+40.8",6] ] },
    { name: "Low-Vol", cells: [ ["+14.8",5], ["+12.4",5], ["+10.8",4], ["+8.2",4], ["+3.4",3], ["+11.4",4] ] },
    { name: "Growth (EPS YoY)", cells: [ ["+28.2",6], ["+17.4",5], ["+9.8",4], ["+4.8",3], ["−3.2",2], ["+31.4",6] ] },
    { name: "Size (inverted)", cells: [ ["+10.4",4], ["+9.2",4], ["+8.4",4], ["+7.8",4], ["+13.2",5], ["−2.8",2] ] },
  ] as Array<{ name: string; cells: Array<[string, HeatLevel]> }>,
};

export const FACTORS_CORR = {
  columns: ["V", "Q", "M", "LV", "G", "Sz"],
  rows: [
    { name: "Value", cells: [ ["1.00",6], ["+0.24",4], ["−0.38",2], ["+0.18",4], ["−0.42",2], ["+0.54",5] ] },
    { name: "Quality", cells: [ ["+0.24",4], ["1.00",6], ["+0.28",4], ["+0.48",5], ["+0.34",4], ["−0.22",2] ] },
    { name: "Momentum", cells: [ ["−0.38",2], ["+0.28",4], ["1.00",6], ["−0.04",3], ["+0.52",5], ["−0.28",2] ] },
    { name: "Low-Vol", cells: [ ["+0.18",4], ["+0.48",5], ["−0.04",3], ["1.00",6], ["+0.08",3], ["−0.44",2] ] },
    { name: "Growth", cells: [ ["−0.42",2], ["+0.34",4], ["+0.52",5], ["+0.08",3], ["1.00",6], ["−0.18",3] ] },
    { name: "Size", cells: [ ["+0.54",5], ["−0.22",2], ["−0.28",2], ["−0.44",2], ["−0.18",3], ["1.00",6] ] },
  ] as Array<{ name: string; cells: Array<[string, HeatLevel]> }>,
};

export const FACTORS_ACTIVITY: LogEntry[] = [
  { time: "04-21 21:04", tag: "sys", message: "Composite rank 갱신 · 상위 20 중 4개 교체 · Turnover 48%" },
  { time: "04-21 20:58", tag: "buy", tagLabel: "ADD", message: "329180 HD현대중공업 Q1 진입 · Momentum +0.72 급등" },
  { time: "04-21 20:58", tag: "sell", tagLabel: "DROP", message: "010950 S-Oil Q1 → Q3 강등 · EPS 추정치 하향 −12%" },
  { time: "04-21 20:52", tag: "alert", tagLabel: "IC", message: "Momentum IC 12M 평균 0.108 → 0.124 상승 · 신호 강화" },
  { time: "04-18 16:02", tag: "sys", message: "Monthly rebalance 완료 · 상위 30 포트폴리오 +2.4% (vs BM +0.8%)" },
  { time: "04-15 09:14", tag: "alert", tagLabel: "RISK", message: "Value 팩터 spread 1.8σ · 10년래 극단 · Mean reversion 주의" },
  { time: "04-12 21:04", tag: "sys", message: "Factor correlation matrix 재산출 · Momentum-Growth 0.52 → 0.58" },
  { time: "04-08 10:22", tag: "alert", tagLabel: "FDD", message: "PIT 재무 품질 점검 · 2,141 / 2,175 clean · 3 critical 제외" },
];

/* ---------- QuantKing strategies ---------- */
export const STRATEGY_CARDS = [
  { label: "Top20 Momentum", value: "+34.2%", meta: "YTD · MDD −24.7%", chip: "LIVE", chipTone: "pos" },
  { label: "Low-Vol Blend", value: "+14.8%", meta: "YTD · Sharpe 1.42", chip: "LIVE", chipTone: "pos" },
  { label: "Value+Quality", value: "+21.3%", meta: "YTD · Sharpe 1.28", chip: "PAPER" },
  { label: "Small-Cap Growth", value: "+29.1%", meta: "YTD · MDD −31.4%", chip: "PAPER" },
  { label: "Dividend Aristocrat KR", value: "+9.2%", meta: "YTD · Yield 4.8%", chip: "PAPER" },
  { label: "Sector Rotation", value: "+18.6%", meta: "YTD · Macro-driven", chip: "PAPER" },
] as Array<{ label: string; value: string; meta: string; chip: string; chipTone?: "pos" | "neg" }>;

/* ---------- Smart Beta heatmap ---------- */
export const SMARTBETA_KPI: DenseSummaryCell[] = [
  { label: "Low Volatility", value: "+14.8%", delta: "YTD · Sh 1.82", tone: "pos" },
  { label: "Quality", value: "+21.4%", delta: "YTD · Sh 1.54", tone: "pos" },
  { label: "Momentum", value: "+34.2%", delta: "YTD · Sh 1.42", tone: "pos" },
  { label: "Value", value: "+9.8%", delta: "YTD · Sh 0.98", tone: "pos" },
  { label: "Equal Weight", value: "+18.2%", delta: "KOSPI 대비 +10pp", tone: "pos" },
  { label: "High Dividend", value: "+12.4%", delta: "YTD · Yield 5.8%", tone: "pos" },
];

export const SMARTBETA_HEATMAP = {
  columns: ["1M", "3M", "6M", "1Y", "3Y"],
  rows: [
    { name: "Low Volatility", cells: [ ["+1.2",4], ["+4.8",5], ["+8.4",5], ["+14.8",5], ["+28.4",6] ] },
    { name: "Quality", cells: [ ["+2.4",5], ["+6.8",5], ["+12.4",5], ["+21.4",6], ["+48.2",6] ] },
    { name: "Momentum 12-1", cells: [ ["+4.8",6], ["+12.4",6], ["+22.4",6], ["+34.2",6], ["+68.4",6] ] },
    { name: "Value", cells: [ ["+0.4",3], ["+2.8",4], ["+4.2",4], ["+9.8",5], ["+14.2",4] ] },
    { name: "Equal Weight (KOSPI)", cells: [ ["+2.8",5], ["+8.4",5], ["+11.2",5], ["+18.2",6], ["+34.2",6] ] },
    { name: "High Dividend", cells: [ ["+1.4",4], ["+3.8",4], ["+6.8",5], ["+12.4",5], ["+22.8",5] ] },
    { name: "Quality-Minus-Junk", cells: [ ["+3.2",5], ["+9.8",6], ["+18.4",6], ["+28.4",6], ["+54.8",6] ] },
    { name: "Betting-Against-Beta", cells: [ ["+1.8",4], ["+4.2",4], ["+6.8",4], ["+11.2",5], ["+22.4",5] ] },
  ] as Array<{ name: string; cells: Array<[string, HeatLevel]> }>,
};

/* ---------- Regime ---------- */
export const REGIME_KPI: DenseSummaryCell[] = [
  { label: "현재 레짐", value: "Bull Low-Vol", delta: "Prob 78%", tone: "pos" },
  { label: "전환 확률 (30D)", value: "18%", delta: "Bull→Correction" },
  { label: "레짐 지속 평균", value: "84일", delta: "현재 42일 경과" },
  { label: "레짐별 전략", value: "4", delta: "자동 전환" },
  { label: "Regime 기반 CAGR", value: "+28.4%", delta: "vs B&H +18.2%", tone: "pos" },
  { label: "False Signal Rate", value: "14%", delta: "조기 경보 오탐" },
];

export const REGIME_STATES = [
  { label: "Bull Low-Vol (현재)", pct: 78, color: "var(--pos)", active: true },
  { label: "Bull High-Vol", pct: 14, color: "var(--amber)", active: false },
  { label: "Correction", pct: 6, color: "var(--amber)", active: false },
  { label: "Bear", pct: 2, color: "var(--neg)", active: false },
];

/* ---------- Pairs ---------- */
export const PAIRS_KPI: DenseSummaryCell[] = [
  { label: "활성 페어", value: "14", delta: "cointegrated" },
  { label: "Z-Score > 2", value: "6", delta: "진입 시그널", tone: "pos" },
  { label: "Z-Score 회귀", value: "4", delta: "청산 시그널", tone: "pos" },
  { label: "Half-life 평균", value: "18일", delta: "회귀 주기" },
  { label: "YTD 수익률", value: "+12.4%", delta: "Market Neutral", tone: "pos" },
  { label: "Sharpe", value: "2.14", delta: "낮은 상관성", tone: "pos" },
];

export interface PairRow {
  long: string;
  short: string;
  z: string;
  zTone: "pos" | "neg" | "neutral";
  halfLife: string;
  corr: string;
  pValue: string;
  signal: string;
  signalTone?: "pos" | "neg" | "neutral";
}
export const PAIRS_ROWS: PairRow[] = [
  { long: "현대차", short: "기아", z: "+2.4", zTone: "pos", halfLife: "14d", corr: "0.88", pValue: "0.002", signal: "Open Long", signalTone: "pos" },
  { long: "삼성전자", short: "SK하이닉스", z: "−2.1", zTone: "neg", halfLife: "22d", corr: "0.84", pValue: "0.008", signal: "Open Short", signalTone: "neg" },
  { long: "KB금융", short: "신한지주", z: "+0.4", zTone: "neutral", halfLife: "12d", corr: "0.92", pValue: "0.001", signal: "Hold" },
  { long: "POSCO홀딩스", short: "현대제철", z: "+2.8", zTone: "pos", halfLife: "18d", corr: "0.78", pValue: "0.012", signal: "Open Long", signalTone: "pos" },
  { long: "LG화학", short: "롯데케미칼", z: "−1.4", zTone: "neg", halfLife: "24d", corr: "0.82", pValue: "0.015", signal: "Watch" },
  { long: "NAVER", short: "카카오", z: "+1.8", zTone: "pos", halfLife: "28d", corr: "0.74", pValue: "0.024", signal: "Watch" },
  { long: "HMM", short: "팬오션", z: "+2.2", zTone: "pos", halfLife: "16d", corr: "0.84", pValue: "0.006", signal: "Open Long", signalTone: "pos" },
];

/* ---------- Mean Reversion ---------- */
export const MEANREV_KPI: DenseSummaryCell[] = [
  { label: "매수 후보", value: "42", delta: "RSI(2) < 10", tone: "pos" },
  { label: "BB 하단 터치", value: "28", delta: "2σ 이탈" },
  { label: "평균 회귀 (5D)", value: "+3.2%", delta: "역사 평균", tone: "pos" },
  { label: "Win Rate", value: "68%", delta: "단기 전략", tone: "pos" },
  { label: "Avg Hold", value: "3.4일", delta: "빠른 회전" },
  { label: "YTD", value: "+18.4%", delta: "높은 turnover", tone: "pos" },
];

export interface MeanRevRow {
  ticker: string;
  rsi: string;
  bb: string;
  z: string;
  rs: string;
  expected: string;
  grade: string;
  gradeTone?: "pos" | "neg" | "neutral";
}
export const MEANREV_ROWS: MeanRevRow[] = [
  { ticker: "셀트리온", rsi: "4.2", bb: "0.02", z: "−2.8", rs: "0.54", expected: "+3.8%", grade: "A", gradeTone: "pos" },
  { ticker: "카카오", rsi: "6.8", bb: "0.08", z: "−2.4", rs: "0.68", expected: "+3.2%", grade: "A", gradeTone: "pos" },
  { ticker: "아모레퍼시픽", rsi: "8.4", bb: "0.12", z: "−2.1", rs: "0.38", expected: "+2.4%", grade: "B+" },
  { ticker: "LG화학", rsi: "9.1", bb: "0.14", z: "−1.8", rs: "0.42", expected: "+2.1%", grade: "B+" },
  { ticker: "하이브", rsi: "11.2", bb: "0.18", z: "−1.6", rs: "0.48", expected: "+1.4%", grade: "B" },
];

/* ---------- Calendar Effects ---------- */
export const CALENDAR_KPI: DenseSummaryCell[] = [
  { label: "최강 월", value: "12월", delta: "+3.8% 평균 (20Y)", tone: "pos" },
  { label: "최약 월", value: "9월", delta: "−1.2% 평균", tone: "neg" },
  { label: "1월 효과", value: "+2.4%", delta: "KOSDAQ 소형주", tone: "pos" },
  { label: "실적 Pre-window", value: "+1.8%", delta: "T-5~T-1", tone: "pos" },
  { label: "월요일 효과", value: "−0.12%", delta: "KR 시장", tone: "neg" },
  { label: "Halloween", value: "+8.4%", delta: "Nov-Apr vs May-Oct", tone: "pos" },
];

/* ---------- ML Factor ---------- */
export const MLFACTOR_KPI: DenseSummaryCell[] = [
  { label: "XGBoost IC", value: "0.184", delta: "6M 평균", tone: "pos" },
  { label: "LSTM IC", value: "0.142", delta: "60d seq", tone: "pos" },
  { label: "Ensemble", value: "0.218", delta: "XGB+LSTM", tone: "pos" },
  { label: "Features", value: "84", delta: "가격+재무+매크로" },
  { label: "Top Feature", value: "Mom 12-1", delta: "Importance 0.24" },
  { label: "Retrain 주기", value: "월 1회", delta: "Walk-forward" },
];

/* ---------- Risk Parity ---------- */
export const RISKPARITY_KPI: DenseSummaryCell[] = [
  { label: "자산군", value: "5", delta: "주식/채권/원자재/금/현금" },
  { label: "목표 변동성", value: "10%", delta: "연환산" },
  { label: "Sharpe", value: "1.24", delta: "10Y 백테스트", tone: "pos" },
  { label: "MDD", value: "−11.2%", delta: "낮은 drawdown", tone: "pos" },
  { label: "레버리지", value: "1.4×", delta: "10% 변동성 타겟" },
  { label: "리밸런싱", value: "월 1회", delta: "변동성 변화 반영" },
];

/* ---------- Kelly ---------- */
export const KELLY_KPI: DenseSummaryCell[] = [
  { label: "Full Kelly", value: "18.4%", delta: "per trade" },
  { label: "Half Kelly", value: "9.2%", delta: "권장", tone: "pos" },
  { label: "Quarter Kelly", value: "4.6%", delta: "보수", tone: "pos" },
  { label: "내 Edge (Win%)", value: "58%", delta: "추정", tone: "pos" },
  { label: "Payoff Ratio", value: "2.4", delta: "Avg W / Avg L", tone: "pos" },
  { label: "권장 포지션", value: "7.2%", delta: "Half Kelly + Sh 조정", tone: "pos" },
];

/* ---------- FDD ---------- */
export const FDD_KPI: DenseSummaryCell[] = [
  { label: "Clean", value: "98.4%", delta: "2,141 / 2,175 tickers", tone: "pos" },
  { label: "Warnings", value: "31", delta: "경미한 이상치" },
  { label: "Critical", value: "3", delta: "리포트 필요", tone: "neg" },
  { label: "Last Check", value: "2h ago", delta: "자동 스케줄", tone: "pos" },
];

/* ---------- Runs ---------- */
export interface RunRow {
  runId: string;
  strategy: string;
  period: string;
  cagr: string;
  mdd: string;
  status: string;
}
export const RUNS_ROWS: RunRow[] = [
  { runId: "bt_20260422_143022", strategy: "LeaderSectorStock v2.1", period: "2023-01→2026-04", cagr: "+23.4%", mdd: "−19.1%", status: "COMPLETE" },
  { runId: "bt_20260421_201545", strategy: "QuantKing Top20", period: "2020-01→2026-04", cagr: "+34.2%", mdd: "−24.7%", status: "COMPLETE" },
  { runId: "bt_20260421_090012", strategy: "Value Momentum Blend", period: "2020-01→2026-04", cagr: "+18.9%", mdd: "−15.2%", status: "COMPLETE" },
];

/* ---------- Academic card set (4 strategies summary) ---------- */
export const ACADEMIC_SUMMARY = [
  { label: "Magic Formula (Greenblatt)", value: "+29.8%", sub: "ROC + Earnings Yield · Top30" },
  { label: "Deep Value (Graham)", value: "+18.2%", sub: "Net-net + Low P/B" },
  { label: "Fast Growth", value: "+34.2%", sub: "Revenue + EPS 모멘텀" },
  { label: "Super Quant", value: "+25.6%", sub: "Multi-factor 합성" },
];
