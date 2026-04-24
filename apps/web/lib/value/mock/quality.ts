// Value quality mocks — Moat / Segment (SOTP).

import type { DenseSummaryCell } from "@/components/shared/DenseSummary";

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
