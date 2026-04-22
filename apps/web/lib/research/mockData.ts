// Mock data for Research pages that have no real API yet.
// Mirrors the integration mockup so dense layout renders cleanly.

export const krreportsKpis = [
  { label: "이번주 리포트", value: "284", delta: "18개 증권사" },
  { label: "Buy 의견", value: "68%", delta: "평균적 낙관" },
  { label: "목표주가 상향", value: "84", delta: "TP Revision", tone: "pos" as const },
  { label: "목표주가 하향", value: "24", delta: "TP Cut", tone: "neg" as const },
  { label: "분석 중 종목", value: "1,247", delta: "멀티 커버리지" },
  { label: "Top 리포트", value: "SK하이닉스", delta: "24 커버" },
];

export const cyclesKpis = [
  { label: "분석 사례", value: "24", delta: "1929 이후" },
  { label: "한국 사례", value: "8", delta: "97 · 00 · 08 · 20 · 22" },
  { label: "Bubble 공통", value: "Narrative", delta: "+ 레버리지" },
  { label: "Recovery 평균", value: "18개월", delta: "최저점→이전고" },
  { label: "Max DD (KR)", value: "−58%", delta: "1997 IMF", tone: "neg" as const },
  { label: "V자 반등 사례", value: "4", delta: "Policy driven", tone: "pos" as const },
];

export const signalLabKpis = [
  { label: "Ideation", value: "34", delta: "초기 아이디어" },
  { label: "Quick Test", value: "18", delta: "간이 백테스트", tone: "amber" as const },
  { label: "Validating", value: "8", delta: "정밀 검증", tone: "pos" as const },
  { label: "Production", value: "4", delta: "운영 투입", tone: "pos" as const },
  { label: "Kill Rate", value: "82%", delta: "대부분 버림" },
  { label: "Avg Development", value: "22일", delta: "Idea → Prod" },
];

export const signalLabRows = [
  { signal: "외인 5일 연속 순매수 + Stage 2", phase: "Prod", phaseTone: "pos", sharpe: "1.84", ic: "0.14", turnover: "저", days: "D+8", next: "규모 확대" },
  { signal: "공매도 과열 해제 + 돌파", phase: "Validating", phaseTone: "pos", sharpe: "2.14", ic: "0.22", turnover: "저", days: "D+14", next: "OOS 검증" },
  { signal: "임원 매수 + PER < 10", phase: "Validating", phaseTone: "amber", sharpe: "1.42", ic: "0.12", turnover: "극저", days: "D+21", next: "표본 확대" },
  { signal: "뉴스 감성 급등 + 거래량", phase: "Test", phaseTone: "amber", sharpe: "0.84", ic: "0.06", turnover: "고", days: "D+3", next: "신호 정제" },
  { signal: "실적 Pre-announcement drift", phase: "Test", phaseTone: "amber", sharpe: "1.24", ic: "0.11", turnover: "극고", days: "D+5", next: "비용 검토" },
  { signal: "Short-interest Z-score 반전", phase: "Idea", phaseTone: "default", sharpe: "—", ic: "—", turnover: "—", days: "—", next: "Quick Test" },
];

export const graveyardKpis = [
  { label: "버린 전략", value: "42", delta: "누적 (3년)" },
  { label: "원인 Top", value: "비용", delta: "14 / 42 (33%)", tone: "neg" as const },
  { label: "Overfit 실패", value: "12", delta: "OOS 붕괴", tone: "neg" as const },
  { label: "레짐 의존", value: "8", delta: "특정 시기만", tone: "neg" as const },
  { label: "구현 불가", value: "6", delta: "유동성/차입" },
  { label: "기타", value: "2", delta: "데이터 오류 등" },
];

export const graveyardRows = [
  { date: "2023-Q4", name: "High-frequency reversal", reason: "비용", reasonTone: "neg", live: "3개월", lesson: "0.1% 수수료에서는 말라죽음. 최소 저비용 브로커 필요" },
  { date: "2024-Q1", name: "Earnings surprise momentum", reason: "과최적화", reasonTone: "neg", live: "2개월", lesson: "IS 샤프 3.2 → OOS 0.4. 극단적 과최적화 사례" },
  { date: "2024-Q2", name: "Low P/E small-cap value", reason: "레짐", reasonTone: "amber", live: "8개월", lesson: "성장주 랠리 구간에서 완전 실패. Value factor cyclical" },
  { date: "2024-Q3", name: "News sentiment daily rebalance", reason: "비용", reasonTone: "neg", live: "4개월", lesson: "일 회전율 120% → 슬리피지+수수료가 알파 초과" },
  { date: "2025-Q1", name: "Pair trading (은행업)", reason: "구조 변화", reasonTone: "amber", live: "5개월", lesson: "공적 M&A로 cointegration 깨짐. 구조적 이벤트 고려" },
];
