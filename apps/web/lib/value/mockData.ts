// Value mock data — extracted from _integration_mockup.html.

import type { DenseSummaryCell } from "@/components/shared/DenseSummary";
import type { HeatLevel } from "@/components/shared/Heatmap";
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

/* ---------- Moat ---------- */
export const MOAT_KPI: DenseSummaryCell[] = [
  { label: "Wide Moat", value: "14", delta: "지속 경쟁우위", tone: "pos" },
  { label: "Narrow Moat", value: "68", delta: "부분적", tone: "pos" },
  { label: "No Moat", value: "다수", delta: "범용 경쟁" },
  { label: "10Y ROIC 평균", value: "22.4%", delta: "Wide Moat 그룹", tone: "pos" },
  { label: "5Y 매출 CAGR", value: "+14.8%", delta: "Wide Moat 그룹", tone: "pos" },
  { label: "밸류 프리미엄", value: "+24%", delta: "PER 프리미엄" },
];

export interface MoatRow {
  ticker: string;
  source: string;
  roic: string;
  vol: string;
  margin: string;
  marginTone?: "pos" | "neg" | "amber";
  label: string;
  labelTone?: "pos" | "amber";
}
export const MOAT_ROWS: MoatRow[] = [
  { ticker: "삼성전자", source: "Scale · IP · Brand", roic: "18.4", vol: "Low", margin: "안정", marginTone: "pos", label: "Wide · 장기", labelTone: "pos" },
  { ticker: "SK하이닉스", source: "Scale · IP (HBM)", roic: "14.2", vol: "Med", margin: "상승", marginTone: "pos", label: "Wide", labelTone: "pos" },
  { ticker: "NAVER", source: "Network (검색)", roic: "16.8", vol: "Low", margin: "안정", marginTone: "pos", label: "Wide", labelTone: "pos" },
  { ticker: "카카오", source: "Network (메신저)", roic: "14.4", vol: "Med", margin: "압박", marginTone: "amber", label: "Narrow", labelTone: "amber" },
  { ticker: "KT&G", source: "Brand · 규제 진입장벽", roic: "18.8", vol: "Low", margin: "안정", marginTone: "pos", label: "Wide · 장기", labelTone: "pos" },
  { ticker: "한미반도체", source: "IP · Switching (HBM 장비)", roic: "32.4", vol: "Med", margin: "상승", marginTone: "pos", label: "Wide", labelTone: "pos" },
  { ticker: "리노공업", source: "IP · 고객 전환비용", roic: "28.2", vol: "Low", margin: "안정", marginTone: "pos", label: "Wide", labelTone: "pos" },
  { ticker: "삼성바이오로직스", source: "Scale · Regulatory", roic: "12.8", vol: "Low", margin: "확장", marginTone: "pos", label: "Wide", labelTone: "pos" },
];

/* ---------- Segment (SOTP) ---------- */
export const SEGMENT_KPI: DenseSummaryCell[] = [
  { label: "다각화 기업", value: "284", delta: "2+ segments" },
  { label: "SOTP > Mkt", value: "48", delta: "부분합 > 시총", tone: "pos" },
  { label: "Hidden Value", value: "17", delta: "지주/복합", tone: "pos" },
  { label: "Spin-off 잠재", value: "9", delta: "분할 시나리오", tone: "pos" },
  { label: "부문 margin spread", value: "24pp", delta: "평균" },
  { label: "SOTP discount", value: "−18%", delta: "지주사 평균" },
];

export interface SegmentRow {
  ticker: string;
  segments: string;
  mcap: string;
  sotp: string;
  discount: string;
  core: string;
}
export const SEGMENT_ROWS: SegmentRow[] = [
  { ticker: "삼성물산", segments: "5", mcap: "28.4", sotp: "42.8", discount: "−33.6%", core: "건설·상사·패션·리조트·삼성전자" },
  { ticker: "LG", segments: "4", mcap: "14.2", sotp: "21.8", discount: "−34.9%", core: "LG화학·LG전자·LG CNS·LG U+" },
  { ticker: "SK", segments: "6", mcap: "12.8", sotp: "18.4", discount: "−30.4%", core: "SK하이닉스·이노베이션·텔레콤" },
  { ticker: "GS", segments: "3", mcap: "4.8", sotp: "7.2", discount: "−33.3%", core: "정유·유통·건설" },
  { ticker: "CJ", segments: "5", mcap: "2.8", sotp: "4.2", discount: "−33.3%", core: "엔터·물류·식품·바이오·ENM" },
];

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

/* ---------- Commodities ---------- */
export const COMMODITIES_KPI: DenseSummaryCell[] = [
  { label: "WTI 원유", value: "$82.34", delta: "+1.18% · 재고 −3.2M", tone: "pos" },
  { label: "천연가스 (HH)", value: "$3.48", delta: "+2.14%", tone: "pos" },
  { label: "구리 (LME)", value: "$9,847", delta: "+0.84%", tone: "pos" },
  { label: "금 (NY)", value: "$2,748", delta: "+0.42%", tone: "pos" },
  { label: "BDI 지수", value: "2,142", delta: "+3.8% WoW", tone: "pos" },
  { label: "리튬 (KOMIS)", value: "−8.4%", delta: "5개월 연속 하락", tone: "neg" },
];

export const COMMODITIES_HEATMAP = {
  columns: ["1D", "1W", "1M", "3M", "YTD"],
  rows: [
    { name: "WTI 원유", cells: [["+1.18",5],["+3.82",5],["+7.4",5],["+4.2",4],["+3.8",4]] },
    { name: "Brent 원유", cells: [["+1.24",5],["+3.94",5],["+7.8",5],["+4.4",4],["+4.1",4]] },
    { name: "천연가스 HH", cells: [["+2.14",5],["+2.48",4],["+1.8",4],["−0.4",3],["+0.8",3]] },
    { name: "LNG JKM", cells: [["+0.84",4],["+1.24",4],["+0.4",3],["−2.8",2],["−3.4",2]] },
    { name: "구리 (LME)", cells: [["+0.84",4],["+2.14",5],["+6.8",5],["+12.4",6],["+18.4",6]] },
    { name: "알루미늄 (LME)", cells: [["+0.42",4],["+1.24",4],["+3.2",4],["+7.8",5],["+11.2",5]] },
    { name: "니켈 (LME)", cells: [["−0.84",2],["−2.14",2],["−4.8",1],["−8.4",1],["−3.2",2]] },
    { name: "금 (NY Comex)", cells: [["+0.42",4],["+0.84",4],["+2.4",4],["+6.8",5],["+14.2",6]] },
    { name: "은 (NY Comex)", cells: [["+0.84",4],["+2.14",5],["+4.8",5],["+9.2",5],["+18.4",6]] },
    { name: "리튬 (KOMIS)", cells: [["−0.14",2],["−1.84",2],["−4.2",1],["−8.4",1],["−11.2",1]] },
    { name: "BDI (해운)", cells: [["+1.24",5],["+3.82",5],["+11.4",6],["+18.4",6],["+28.4",6]] },
    { name: "SCFI (컨테이너)", cells: [["+0.82",4],["+1.84",4],["+7.2",5],["+12.4",5],["+18.8",5]] },
  ] as Array<{ name: string; cells: Array<[string, HeatLevel]> }>,
};

export interface CommLinkRow {
  commodity: string;
  ticker: string;
  beta: string;
  corr: string;
  direction: string;
  directionTone: "pos" | "amber" | "neg";
}
export const COMMODITIES_LINKS: CommLinkRow[] = [
  { commodity: "WTI 원유", ticker: "S-Oil", beta: "1.24", corr: "0.78", direction: "Long", directionTone: "pos" },
  { commodity: "WTI 원유", ticker: "SK이노베이션", beta: "1.18", corr: "0.72", direction: "Long", directionTone: "pos" },
  { commodity: "구리", ticker: "풍산", beta: "1.38", corr: "0.84", direction: "Long", directionTone: "pos" },
  { commodity: "구리", ticker: "LS MnM", beta: "1.21", corr: "0.76", direction: "Long", directionTone: "pos" },
  { commodity: "리튬", ticker: "POSCO퓨처엠", beta: "1.62", corr: "0.68", direction: "Long", directionTone: "pos" },
  { commodity: "니켈", ticker: "LG에너지솔루션", beta: "0.84", corr: "0.42", direction: "중립", directionTone: "amber" },
  { commodity: "BDI", ticker: "팬오션", beta: "1.82", corr: "0.88", direction: "Long", directionTone: "pos" },
  { commodity: "BDI", ticker: "HMM", beta: "1.54", corr: "0.78", direction: "Long", directionTone: "pos" },
];

/* ---------- Disclosures ---------- */
export interface DisclosureRow {
  type: string;
  title: string;
  detail: string;
  sentiment: "Positive" | "Negative" | "Risk" | "Neutral";
}
export const DISCLOSURE_ROWS: DisclosureRow[] = [
  { type: "분기보고서", title: "삼성전자 · 1Q26 실적", detail: "영업이익 +18% YoY · 반도체 매출 회복 구간 진입", sentiment: "Positive" },
  { type: "주요사항보고", title: "현대차 · 주주환원 확대", detail: "배당성향 상향 + 자사주 1조원 소각 발표", sentiment: "Positive" },
  { type: "감사보고서", title: "바이오기업A · 감사 의견거절", detail: "계속기업 존속능력 불확실 · 자동 제외 처리", sentiment: "Risk" },
  { type: "특수관계자거래", title: "셀트리온 · 계열사 합병", detail: "합병비율 공정성 검토 필요 · 주주가치 영향 중립", sentiment: "Neutral" },
];
