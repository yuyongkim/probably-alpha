// Value screen mocks — DCF / MoS / ROIC / Magic Formula / Piotroski / Altman.

import type { DenseSummaryCell } from "@/components/shared/DenseSummary";
import type { LogEntry } from "@/components/shared/ActivityLog";

/* ---------- DCF ---------- */
export const DCF_KPI: DenseSummaryCell[] = [
  { label: "DCF Models", value: "47", delta: "+3 WoW · 12 updated 7D", tone: "pos" },
  { label: "Avg Upside", value: "+21.4%", delta: "MoS 31.4% Top Decile", tone: "pos" },
  { label: "Fair Value Hit Rate", value: "68.2%", delta: "12M 회귀 기준", tone: "pos" },
  { label: "Deep Value", value: "28", delta: "P/B<1 · PEG<1", tone: "pos" },
  { label: "DART · 24h", value: "142", delta: "14 auto-analyzed" },
  { label: "갱신 필요", value: "6", delta: "공시 반영 전", tone: "neg" },
];

export interface DCFRow {
  rank: string;
  ticker: string;
  code: string;
  sector: string;
  price: string;
  fcf: string;
  wacc: string;
  gTerm: string;
  fair: string;
  upside: string;
  upsideTone: "pos" | "neg" | "neutral";
  mos: string;
  conf: string;
  confTone?: "pos" | "neg" | "neutral";
}

export const DCF_ROWS: DCFRow[] = [
  { rank: "01", ticker: "KT&G", code: "033780", sector: "필수", price: "93,700", fcf: "8,420", wacc: "6.8%", gTerm: "1.5%", fair: "124,000", upside: "+32.3%", upsideTone: "pos", mos: "24.4%", conf: "A", confTone: "pos" },
  { rank: "02", ticker: "기아", code: "000270", sector: "자동차", price: "108,500", fcf: "14,820", wacc: "8.4%", gTerm: "2.0%", fair: "138,000", upside: "+27.2%", upsideTone: "pos", mos: "21.4%", conf: "A", confTone: "pos" },
  { rank: "03", ticker: "현대차", code: "005380", sector: "자동차", price: "231,000", fcf: "18,240", wacc: "8.1%", gTerm: "2.0%", fair: "284,000", upside: "+22.9%", upsideTone: "pos", mos: "18.7%", conf: "A", confTone: "pos" },
  { rank: "04", ticker: "LG전자", code: "066570", sector: "가전", price: "98,200", fcf: "6,140", wacc: "9.2%", gTerm: "1.8%", fair: "117,000", upside: "+19.1%", upsideTone: "pos", mos: "16.1%", conf: "A", confTone: "pos" },
  { rank: "05", ticker: "포스코홀딩스", code: "005490", sector: "철강", price: "342,000", fcf: "22,480", wacc: "9.8%", gTerm: "1.5%", fair: "410,000", upside: "+19.9%", upsideTone: "pos", mos: "16.6%", conf: "B+" },
  { rank: "06", ticker: "하나금융지주", code: "086790", sector: "금융", price: "64,200", fcf: "28,420", wacc: "9.4%", gTerm: "1.8%", fair: "76,000", upside: "+18.4%", upsideTone: "pos", mos: "15.5%", conf: "A", confTone: "pos" },
  { rank: "07", ticker: "삼성전자", code: "005930", sector: "반도체", price: "75,400", fcf: "184,200", wacc: "7.8%", gTerm: "2.2%", fair: "88,000", upside: "+16.7%", upsideTone: "pos", mos: "14.3%", conf: "A", confTone: "pos" },
  { rank: "08", ticker: "KB금융", code: "105560", sector: "금융", price: "78,400", fcf: "32,140", wacc: "9.2%", gTerm: "1.8%", fair: "91,000", upside: "+16.1%", upsideTone: "pos", mos: "13.8%", conf: "A", confTone: "pos" },
  { rank: "09", ticker: "SK하이닉스", code: "000660", sector: "반도체", price: "192,100", fcf: "42,810", wacc: "9.4%", gTerm: "2.5%", fair: "218,000", upside: "+13.5%", upsideTone: "pos", mos: "11.9%", conf: "B+" },
  { rank: "10", ticker: "NAVER", code: "035420", sector: "AI/SW", price: "174,800", fcf: "12,480", wacc: "10.2%", gTerm: "2.5%", fair: "198,000", upside: "+13.3%", upsideTone: "pos", mos: "11.7%", conf: "B+" },
];

export const DCF_ACTIVITY: LogEntry[] = [
  { time: "20:14", tag: "sys", message: "야간 DCF 배치 완료 · 47 모델 중 12 재계산 · 공시 기반 반영" },
  { time: "15:28", tag: "alert", tagLabel: "DART", message: "005380 현대차 자사주 소각 반영 · FV 272,000 → 284,000 (+4.4%)" },
  { time: "14:58", tag: "alert", tagLabel: "EPS", message: "005930 삼성전자 1Q 컨센 상회 · FCF 추정치 +6.2% · FV 86→88K" },
  { time: "10:18", tag: "buy", tagLabel: "FV↑", message: "000660 SK하이닉스 HBM 가이던스 반영 · Upside +13.5%" },
  { time: "09:24", tag: "sell", tagLabel: "FV↓", message: "247540 에코프로비엠 수주 축소 · FV 218K → 188K (−13.8%)" },
  { time: "04-21", tag: "sys", message: "WACC 파라미터 주간 갱신 · KR 10Y 3.04→3.02% · ERP 유지 6.8%" },
  { time: "04-21", tag: "alert", tagLabel: "RISK", message: "바이오기업A 감사의견 거절 · 유니버스 제외" },
  { time: "04-20", tag: "sys", message: "신규 DCF 3건 추가 · HD현대중공업 · 한화오션 · 삼성중공업" },
];

/* ---------- MoS ---------- */
export const MOS_KPI: DenseSummaryCell[] = [
  { label: "MoS ≥ 40%", value: "23", delta: "최우량", tone: "pos" },
  { label: "MoS 30-40%", value: "48", delta: "좋음", tone: "pos" },
  { label: "MoS 20-30%", value: "84", delta: "보통" },
  { label: "MoS < 20%", value: "412", delta: "불안", tone: "neg" },
  { label: "Avg MoS", value: "31.4%", delta: "Top Decile 42%", tone: "pos" },
  { label: "Net-Net (Graham)", value: "7", delta: "NCAV > Mkt Cap", tone: "pos" },
];

export interface MoSRow {
  ticker: string;
  fair: string;
  price: string;
  mos: string;
  upside: string;
  ncav: string;
  pb: string;
  grade: string;
  gradeTone?: "pos" | "neg" | "neutral";
}
export const MOS_ROWS: MoSRow[] = [
  { ticker: "KT&G", fair: "124,000", price: "93,700", mos: "+32.3", upside: "+32", ncav: "0.38", pb: "1.24", grade: "A", gradeTone: "pos" },
  { ticker: "기아", fair: "138,000", price: "108,500", mos: "+27.2", upside: "+27", ncav: "0.42", pb: "0.84", grade: "A", gradeTone: "pos" },
  { ticker: "현대차", fair: "292,000", price: "218,000", mos: "+33.9", upside: "+34", ncav: "0.48", pb: "0.78", grade: "A", gradeTone: "pos" },
  { ticker: "포스코홀딩스", fair: "410,000", price: "342,000", mos: "+19.9", upside: "+20", ncav: "0.52", pb: "0.64", grade: "B+" },
  { ticker: "LG전자", fair: "117,000", price: "98,200", mos: "+19.1", upside: "+19", ncav: "0.62", pb: "0.88", grade: "B+" },
  { ticker: "KB금융", fair: "82,000", price: "68,400", mos: "+19.9", upside: "+20", ncav: "0.71", pb: "0.52", grade: "B+" },
  { ticker: "신한지주", fair: "58,000", price: "48,400", mos: "+19.8", upside: "+20", ncav: "0.74", pb: "0.48", grade: "B+" },
  { ticker: "삼성물산", fair: "184,000", price: "148,500", mos: "+23.9", upside: "+24", ncav: "0.58", pb: "0.72", grade: "A", gradeTone: "pos" },
  { ticker: "현대건설기계", fair: "78,000", price: "58,400", mos: "+33.6", upside: "+34", ncav: "1.08", pb: "0.82", grade: "A (Net-Net)", gradeTone: "pos" },
];

/* ---------- ROIC / FCF Yield ---------- */
export const ROIC_KPI: DenseSummaryCell[] = [
  { label: "ROIC > 20%", value: "84", delta: "Quality", tone: "pos" },
  { label: "FCF Yield > 8%", value: "142", delta: "현금창출", tone: "pos" },
  { label: "Both ≥ 상위 30%", value: "48", delta: "Quality Compounder", tone: "pos" },
  { label: "시장 ROIC median", value: "9.4%", delta: "KOSPI avg" },
  { label: "시장 FCF Yield", value: "4.8%", delta: "KOSPI avg" },
  { label: "5Y ROIC 변동성", value: "Low", delta: "안정적 복리", tone: "pos" },
];

export interface ROICRow {
  ticker: string;
  sector: string;
  roic5y: string;
  roic1y: string;
  fcf: string;
  revCagr: string;
  leverage: string;
  grade: string;
  gradeTone?: "pos" | "neg" | "neutral";
}
export const ROIC_ROWS: ROICRow[] = [
  { ticker: "한미반도체", sector: "반도체", roic5y: "34.8", roic1y: "42.1", fcf: "4.8", revCagr: "+28", leverage: "−0.2", grade: "A+", gradeTone: "pos" },
  { ticker: "리노공업", sector: "반도체", roic5y: "28.4", roic1y: "32.1", fcf: "6.2", revCagr: "+18", leverage: "−0.8", grade: "A+", gradeTone: "pos" },
  { ticker: "HPSP", sector: "반도체", roic5y: "32.1", roic1y: "38.4", fcf: "5.4", revCagr: "+42", leverage: "−0.4", grade: "A+", gradeTone: "pos" },
  { ticker: "KT&G", sector: "필수소비재", roic5y: "18.4", roic1y: "19.2", fcf: "8.4", revCagr: "+4", leverage: "0.2", grade: "A", gradeTone: "pos" },
  { ticker: "NAVER", sector: "AI/SW", roic5y: "14.8", roic1y: "16.2", fcf: "5.2", revCagr: "+12", leverage: "−0.6", grade: "A", gradeTone: "pos" },
  { ticker: "삼성전자", sector: "반도체", roic5y: "16.2", roic1y: "18.4", fcf: "6.8", revCagr: "+8", leverage: "−2.1", grade: "A", gradeTone: "pos" },
];

/* ---------- Magic Formula ---------- */
export const MAGIC_KPI: DenseSummaryCell[] = [
  { label: "Universe", value: "1,842", delta: "필터 후" },
  { label: "Combined Rank Top 30", value: "30", delta: "매매 유니버스", tone: "pos" },
  { label: "연 목표 수익", value: "+30.8%", delta: "Greenblatt 원본", tone: "pos" },
  { label: "리밸런싱", value: "연 1회", delta: "장기 보유" },
  { label: "YTD 모의 수익", value: "+24.8%", delta: "vs KOSPI +8.1%", tone: "pos" },
  { label: "Hit Rate (2020-)", value: "71%", delta: "5년 중 3.5년 아웃퍼폼", tone: "pos" },
];

export interface MagicRow {
  rank: string;
  ticker: string;
  sector: string;
  ey: string;
  roc: string;
  rankEy: string;
  rankRoc: string;
  combined: string;
}
export const MAGIC_ROWS: MagicRow[] = [
  { rank: "01", ticker: "HMM", sector: "해운", ey: "28.4", roc: "22.4", rankEy: "4", rankRoc: "48", combined: "52" },
  { rank: "02", ticker: "팬오션", sector: "해운", ey: "24.2", roc: "24.8", rankEy: "12", rankRoc: "42", combined: "54" },
  { rank: "03", ticker: "기아", sector: "자동차", ey: "18.4", roc: "28.4", rankEy: "42", rankRoc: "18", combined: "60" },
  { rank: "04", ticker: "현대차", sector: "자동차", ey: "16.2", roc: "24.2", rankEy: "58", rankRoc: "28", combined: "86" },
  { rank: "05", ticker: "KT&G", sector: "소비재", ey: "12.4", roc: "38.4", rankEy: "124", rankRoc: "6", combined: "130" },
];

/* ---------- Piotroski F-Score ---------- */
export const PIOTROSKI_KPI: DenseSummaryCell[] = [
  { label: "F-Score 9/9", value: "14", delta: "최상위", tone: "pos" },
  { label: "F-Score 8", value: "48", delta: "우량", tone: "pos" },
  { label: "F-Score 7", value: "124", delta: "양호", tone: "pos" },
  { label: "F-Score ≤ 3", value: "284", delta: "부실", tone: "neg" },
  { label: "9점 종목 평균 수익", value: "+28%", delta: "학술 재현 (1Y)", tone: "pos" },
  { label: "0점 종목 평균", value: "−14%", delta: "High Distress", tone: "neg" },
];

export interface PiotroskiRow {
  ticker: string;
  sector: string;
  score: string;
  scoreTone?: "pos" | "neg";
  flags: string[];
}
export const PIOTROSKI_ROWS: PiotroskiRow[] = [
  { ticker: "한미반도체", sector: "반도체", score: "9/9", scoreTone: "pos", flags: ["✓","✓","✓","✓","✓","✓"] },
  { ticker: "HPSP", sector: "반도체", score: "9/9", scoreTone: "pos", flags: ["✓","✓","✓","✓","✓","✓"] },
  { ticker: "리노공업", sector: "반도체", score: "9/9", scoreTone: "pos", flags: ["✓","✓","✓","✓","✓","✓"] },
  { ticker: "이수페타시스", sector: "반도체", score: "9/9", scoreTone: "pos", flags: ["✓","✓","✓","✓","✓","✓"] },
  { ticker: "삼성전자", sector: "반도체", score: "8/9", scoreTone: "pos", flags: ["✓","✓","✓","✓","✓","~"] },
  { ticker: "현대차", sector: "자동차", score: "8/9", scoreTone: "pos", flags: ["✓","✓","✓","✓","~","✓"] },
];

/* ---------- Altman ---------- */
export const ALTMAN_KPI: DenseSummaryCell[] = [
  { label: "Safe (Z > 3)", value: "842", delta: "파산 위험 거의 없음", tone: "pos" },
  { label: "Gray Zone", value: "384", delta: "1.8 < Z < 3", tone: "amber" },
  { label: "Distress (Z < 1.8)", value: "124", delta: "경보", tone: "neg" },
  { label: "Extreme Distress", value: "38", delta: "Z < 0", tone: "neg" },
  { label: "Pass Rate", value: "62.4%", delta: "파산 위험 낮음", tone: "pos" },
  { label: "관리종목 중", value: "92%", delta: "Z < 1.8 일치율", tone: "neg" },
];
