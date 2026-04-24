// Value event mocks — Insider / Buyback / Consensus.

import type { DenseSummaryCell } from "@/components/shared/DenseSummary";

/* ---------- Insider ---------- */
export const INSIDER_KPI: DenseSummaryCell[] = [
  { label: "최근 7일 신고", value: "84", delta: "DART 수집" },
  { label: "매수", value: "42", delta: "자신감 시그널", tone: "pos" },
  { label: "매도", value: "38", delta: "주의", tone: "neg" },
  { label: "대규모 매수 (>10억)", value: "7", delta: "강한 시그널", tone: "pos" },
  { label: "CEO 직접 매수", value: "3", delta: "최강 시그널", tone: "pos" },
  { label: "후속 수익률 (30D)", value: "+8.4%", delta: "매수 vs 매도", tone: "pos" },
];

export interface InsiderRow {
  date: string;
  ticker: string;
  who: string;
  type: "매수" | "매도";
  size: string;
  stake: string;
  stakeTone: "pos" | "neg";
  signal: string;
  signalTone: "pos" | "neg" | "neutral";
}
export const INSIDER_ROWS: InsiderRow[] = [
  { date: "04-22", ticker: "한미반도체", who: "CEO", type: "매수", size: "24억", stake: "+0.18pp", stakeTone: "pos", signal: "강한 시그널", signalTone: "pos" },
  { date: "04-21", ticker: "HPSP", who: "부사장", type: "매수", size: "4.2억", stake: "+0.04pp", stakeTone: "pos", signal: "매집", signalTone: "pos" },
  { date: "04-19", ticker: "두산에너빌리티", who: "최대주주", type: "매수", size: "48억", stake: "+0.12pp", stakeTone: "pos", signal: "대규모", signalTone: "pos" },
  { date: "04-18", ticker: "에코프로비엠", who: "상무", type: "매도", size: "8.4억", stake: "−0.08pp", stakeTone: "neg", signal: "주의", signalTone: "neg" },
  { date: "04-17", ticker: "하이브", who: "CFO", type: "매도", size: "12억", stake: "−0.14pp", stakeTone: "neg", signal: "경고", signalTone: "neg" },
  { date: "04-15", ticker: "NAVER", who: "친인척 (배우자)", type: "매수", size: "2.8억", stake: "+0.02pp", stakeTone: "pos", signal: "참고", signalTone: "neutral" },
];

/* ---------- Buyback ---------- */
export const BUYBACK_KPI: DenseSummaryCell[] = [
  { label: "활성 공시 중", value: "42", delta: "진행 중 buyback", tone: "pos" },
  { label: "소각 발표", value: "18", delta: "실질 주주환원", tone: "pos" },
  { label: "시가 > 1% 매입", value: "12", delta: "의미있는 규모", tone: "pos" },
  { label: "3년 연속 buyback", value: "7", delta: "정책화", tone: "pos" },
  { label: "자사주 비율 > 10%", value: "23", delta: "대기중", tone: "pos" },
  { label: "후속 수익률 (90D)", value: "+11.4%", delta: "발표 후 평균", tone: "pos" },
];

export interface BuybackRow {
  ticker: string;
  type: "소각" | "금고주";
  size: string;
  pct: string;
  period: string;
  progress: string;
  progressTone?: "pos" | "neg" | "neutral";
}
export const BUYBACK_ROWS: BuybackRow[] = [
  { ticker: "현대차", type: "소각", size: "1조", pct: "1.8%", period: "24-04 ~ 25-04", progress: "42% 완료", progressTone: "pos" },
  { ticker: "KT&G", type: "소각", size: "3,000억", pct: "2.4%", period: "25-Q1 ~ Q2", progress: "84% 완료", progressTone: "pos" },
  { ticker: "삼성전자", type: "금고주", size: "2조", pct: "0.4%", period: "25-Q2 ~ Q4", progress: "28% 완료" },
  { ticker: "KB금융", type: "소각", size: "4,000억", pct: "1.8%", period: "25-Q1 ~ Q2", progress: "68% 완료", progressTone: "pos" },
  { ticker: "메리츠금융", type: "소각", size: "6,000억", pct: "3.2%", period: "25-Q2 ~ Q4", progress: "14% 완료" },
];

/* ---------- Consensus ---------- */
export const CONSENSUS_KPI: DenseSummaryCell[] = [
  { label: "EPS 상향 (7일)", value: "84", delta: "컨센서스 개선", tone: "pos" },
  { label: "EPS 하향", value: "42", delta: "컨센서스 악화", tone: "neg" },
  { label: "목표가 상향", value: "67", delta: "TP raise", tone: "pos" },
  { label: "투자의견 Upgrade", value: "18", delta: "Hold→Buy, Buy→Strong", tone: "pos" },
  { label: "후속 수익률 (30D)", value: "+6.4%", delta: "Upgrade 후 평균", tone: "pos" },
  { label: "컨센서스 적중률", value: "58%", delta: "6M EPS" },
];

export interface ConsensusRow {
  ticker: string;
  sector: string;
  epsRev: string;
  epsRevTone: "pos" | "neg";
  tpRev: string;
  tpRevTone: "pos" | "neg";
  upgrade: string;
  upgradeTone?: "pos" | "neg";
  covers: string;
  sentiment: string;
  sentimentTone: "pos" | "neg" | "neutral";
}
export const CONSENSUS_ROWS: ConsensusRow[] = [
  { ticker: "SK하이닉스", sector: "반도체", epsRev: "+12.4", epsRevTone: "pos", tpRev: "+8.2", tpRevTone: "pos", upgrade: "3곳", upgradeTone: "pos", covers: "24", sentiment: "Strong Buy", sentimentTone: "pos" },
  { ticker: "삼성전자", sector: "반도체", epsRev: "+8.2", epsRevTone: "pos", tpRev: "+5.4", tpRevTone: "pos", upgrade: "2곳", upgradeTone: "pos", covers: "28", sentiment: "Buy", sentimentTone: "pos" },
  { ticker: "한미반도체", sector: "반도체", epsRev: "+18.4", epsRevTone: "pos", tpRev: "+14.8", tpRevTone: "pos", upgrade: "4곳", upgradeTone: "pos", covers: "18", sentiment: "Strong Buy", sentimentTone: "pos" },
  { ticker: "두산에너빌리티", sector: "원전", epsRev: "+14.2", epsRevTone: "pos", tpRev: "+11.4", tpRevTone: "pos", upgrade: "2곳", upgradeTone: "pos", covers: "14", sentiment: "Buy", sentimentTone: "pos" },
  { ticker: "현대차", sector: "자동차", epsRev: "+6.4", epsRevTone: "pos", tpRev: "+4.8", tpRevTone: "pos", upgrade: "1곳", covers: "22", sentiment: "Buy", sentimentTone: "neutral" },
  { ticker: "에코프로비엠", sector: "2차전지", epsRev: "−8.4", epsRevTone: "neg", tpRev: "−6.8", tpRevTone: "neg", upgrade: "−2곳", upgradeTone: "neg", covers: "16", sentiment: "Downgrade", sentimentTone: "neg" },
  { ticker: "하이브", sector: "엔터", epsRev: "−12.2", epsRevTone: "neg", tpRev: "−14.4", tpRevTone: "neg", upgrade: "−3곳", upgradeTone: "neg", covers: "18", sentiment: "Strong Downgrade", sentimentTone: "neg" },
];
