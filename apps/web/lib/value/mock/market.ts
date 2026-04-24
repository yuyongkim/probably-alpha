// Value market mocks — Commodities and DART disclosures.

import type { DenseSummaryCell } from "@/components/shared/DenseSummary";
import type { HeatLevel } from "@/components/shared/Heatmap";

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
