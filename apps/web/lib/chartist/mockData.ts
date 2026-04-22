// Mock data lifted directly from _integration_mockup.html so the
// non-Today Chartist sub-sections render at full density even before
// live APIs exist. Keep values in sync with the mockup — do not
// fabricate numbers.

export type Hm = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface HeatCell {
  v: string;
  h: Hm;
}

export interface HeatRow {
  name: string;
  cells: HeatCell[];
}

// ---------------------------------------------------------------------------
// Flow · 수급 대시보드
// ---------------------------------------------------------------------------
export const FLOW_SUMMARY = [
  { label: "외국인 당일", value: "+1,247억", delta: "5일 연속 순매수", tone: "pos" as const },
  { label: "기관 당일", value: "+842억", delta: "투신+사모 주도", tone: "pos" as const },
  { label: "프로그램", value: "+584억", delta: "차익 +312 · 비차익 +272", tone: "pos" as const },
  { label: "연기금", value: "+214억", delta: "3일 연속", tone: "pos" as const },
  { label: "개인", value: "−2,087억", delta: "개인 vs 외인+기관", tone: "neg" as const },
  { label: "외인 보유 %", value: "31.8%", delta: "+0.12pp MoM", tone: "pos" as const },
];

export const FLOW_FOREIGN_TOP = [
  { rank: 1, name: "삼성전자", sector: "반도체", d1: 324, d5: 1842, d20: 4281, streak: "12일", pct: 8.7 },
  { rank: 2, name: "SK하이닉스", sector: "반도체", d1: 218, d5: 1124, d20: 2841, streak: "8일", pct: 11.8 },
  { rank: 3, name: "한미반도체", sector: "반도체", d1: 84, d5: 412, d20: 1284, streak: "14일", pct: 22.4 },
  { rank: 4, name: "이수페타시스", sector: "반도체", d1: 62, d5: 284, d20: 842, streak: "7일", pct: 28.3 },
  { rank: 5, name: "두산에너빌리티", sector: "원전", d1: 48, d5: 218, d20: 684, streak: "9일", pct: 19.4 },
  { rank: 6, name: "현대차", sector: "자동차", d1: 42, d5: 184, d20: 412, streak: "4일", pct: 1.4 },
  { rank: 7, name: "KB금융", sector: "금융", d1: 38, d5: 142, d20: 384, streak: "6일", pct: 1.4 },
  { rank: 8, name: "HPSP", sector: "반도체", d1: 32, d5: 124, d20: 342, streak: "8일", pct: 18.7 },
  { rank: 9, name: "NAVER", sector: "AI/SW", d1: 28, d5: 98, d20: 284, streak: "3일", pct: 7.2 },
  { rank: 10, name: "HD현대중공업", sector: "조선", d1: 24, d5: 112, d20: 342, streak: "11일", pct: 8.8 },
];

export const FLOW_INSTITUTION_TOP = [
  { name: "삼성전자", tusin: 82, samo: 48, pension: 124, total: 254 },
  { name: "한미반도체", tusin: 48, samo: 32, pension: 28, total: 108 },
  { name: "SK하이닉스", tusin: 42, samo: 24, pension: 32, total: 98 },
  { name: "두산에너빌리티", tusin: 38, samo: 18, pension: 14, total: 70 },
  { name: "이수페타시스", tusin: 32, samo: 14, pension: 8, total: 54 },
  { name: "현대차", tusin: 28, samo: 12, pension: 12, total: 52 },
  { name: "HPSP", tusin: 24, samo: 12, pension: 8, total: 44 },
  { name: "KB금융", tusin: 18, samo: 8, pension: 14, total: 40 },
  { name: "NAVER", tusin: 22, samo: 8, pension: 6, total: 36 },
  { name: "셀트리온", tusin: 14, samo: 4, pension: 12, total: 30 },
];

export const FLOW_SECTOR_HEATMAP: HeatRow[] = [
  { name: "반도체", cells: [{ v: "+724", h: 6 }, { v: "+3,842", h: 6 }, { v: "+9,282", h: 6 }] },
  { name: "2차전지", cells: [{ v: "+82", h: 4 }, { v: "+184", h: 3 }, { v: "−284", h: 3 }] },
  { name: "AI / SW", cells: [{ v: "+184", h: 5 }, { v: "+682", h: 5 }, { v: "+1,842", h: 5 }] },
  { name: "원전", cells: [{ v: "+148", h: 5 }, { v: "+584", h: 5 }, { v: "+1,482", h: 5 }] },
  { name: "바이오", cells: [{ v: "+18", h: 3 }, { v: "−84", h: 2 }, { v: "−284", h: 2 }] },
  { name: "자동차", cells: [{ v: "+42", h: 4 }, { v: "+184", h: 4 }, { v: "+584", h: 5 }] },
  { name: "조선", cells: [{ v: "+38", h: 4 }, { v: "+184", h: 4 }, { v: "+584", h: 5 }] },
  { name: "금융", cells: [{ v: "+58", h: 4 }, { v: "+182", h: 4 }, { v: "+482", h: 5 }] },
  { name: "방산", cells: [{ v: "−42", h: 2 }, { v: "−284", h: 1 }, { v: "−584", h: 1 }] },
  { name: "화학", cells: [{ v: "−24", h: 2 }, { v: "−84", h: 2 }, { v: "−184", h: 2 }] },
];

// ---------------------------------------------------------------------------
// Themes · 20 테마 로테이션
// ---------------------------------------------------------------------------
export const THEMES_SUMMARY = [
  { label: "주도 테마", value: "HBM", delta: "+8.4% 5D", tone: "pos" as const },
  { label: "급부상 테마", value: "휴머노이드", delta: "12위 → 3위", tone: "pos" as const },
  { label: "약세 전환", value: "방산", delta: "2위 → 15위", tone: "neg" as const },
  { label: "활성 테마", value: "20", delta: "수동 큐레이션" },
  { label: "평균 수익 5D", value: "+3.8%", delta: "KOSPI +0.82% 초과", tone: "pos" as const },
  { label: "신규 테마 대기", value: "3", delta: "검증 중" },
];

export const THEMES_HEATMAP: HeatRow[] = [
  { name: "HBM", cells: [{ v: "+3.8", h: 6 }, { v: "+8.4", h: 6 }, { v: "+24.2", h: 6 }, { v: "+48.2", h: 6 }, { v: "+82.4", h: 6 }] },
  { name: "AI 반도체", cells: [{ v: "+2.4", h: 5 }, { v: "+6.8", h: 6 }, { v: "+18.4", h: 6 }, { v: "+34.2", h: 6 }, { v: "+58.4", h: 6 }] },
  { name: "휴머노이드 로봇", cells: [{ v: "+4.2", h: 6 }, { v: "+5.8", h: 5 }, { v: "+11.8", h: 5 }, { v: "+14.2", h: 5 }, { v: "+18.4", h: 5 }] },
  { name: "원전 (SMR)", cells: [{ v: "+2.1", h: 5 }, { v: "+5.4", h: 5 }, { v: "+14.7", h: 6 }, { v: "+28.3", h: 6 }, { v: "+42.1", h: 6 }] },
  { name: "전력 인프라", cells: [{ v: "+1.2", h: 4 }, { v: "+3.8", h: 5 }, { v: "+9.4", h: 5 }, { v: "+14.8", h: 5 }, { v: "+18.2", h: 5 }] },
  { name: "2차전지 소재", cells: [{ v: "+1.4", h: 4 }, { v: "+4.2", h: 4 }, { v: "+9.8", h: 5 }, { v: "+2.4", h: 3 }, { v: "+1.8", h: 3 }] },
  { name: "우주항공", cells: [{ v: "+0.8", h: 4 }, { v: "+2.4", h: 4 }, { v: "+3.8", h: 4 }, { v: "+4.8", h: 4 }, { v: "+9.2", h: 5 }] },
  { name: "자율주행", cells: [{ v: "+0.4", h: 4 }, { v: "+0.8", h: 3 }, { v: "+1.2", h: 3 }, { v: "+2.8", h: 4 }, { v: "+4.2", h: 4 }] },
  { name: "저PBR (밸류업)", cells: [{ v: "−0.2", h: 3 }, { v: "−0.8", h: 3 }, { v: "+1.4", h: 3 }, { v: "+4.2", h: 4 }, { v: "+11.8", h: 5 }] },
  { name: "K-뷰티", cells: [{ v: "+0.1", h: 3 }, { v: "−0.4", h: 3 }, { v: "−2.8", h: 2 }, { v: "−6.8", h: 1 }, { v: "−3.4", h: 2 }] },
  { name: "엔터 / K-팝", cells: [{ v: "+0.5", h: 4 }, { v: "+1.3", h: 4 }, { v: "+1.4", h: 3 }, { v: "−2.8", h: 2 }, { v: "+1.2", h: 3 }] },
  { name: "게임", cells: [{ v: "+1.4", h: 5 }, { v: "+2.1", h: 4 }, { v: "+3.8", h: 4 }, { v: "+7.2", h: 5 }, { v: "+12.4", h: 5 }] },
  { name: "음식료 / 라면", cells: [{ v: "+0.3", h: 4 }, { v: "+1.1", h: 4 }, { v: "+2.4", h: 4 }, { v: "+4.8", h: 4 }, { v: "+9.8", h: 5 }] },
  { name: "조선 / LNG", cells: [{ v: "+0.4", h: 4 }, { v: "+1.1", h: 4 }, { v: "+8.4", h: 5 }, { v: "+19.2", h: 6 }, { v: "+31.8", h: 6 }] },
  { name: "바이오 (신약)", cells: [{ v: "+0.7", h: 4 }, { v: "+1.4", h: 4 }, { v: "+2.1", h: 3 }, { v: "−3.4", h: 2 }, { v: "+0.8", h: 3 }] },
  { name: "방산", cells: [{ v: "−0.8", h: 2 }, { v: "−2.1", h: 1 }, { v: "−4.8", h: 1 }, { v: "−2.1", h: 2 }, { v: "+14.2", h: 5 }] },
  { name: "리튬 / 광물자원", cells: [{ v: "−0.2", h: 3 }, { v: "−1.4", h: 2 }, { v: "−4.2", h: 1 }, { v: "−8.4", h: 1 }, { v: "−5.8", h: 2 }] },
  { name: "반도체 소부장", cells: [{ v: "+2.4", h: 5 }, { v: "+4.8", h: 5 }, { v: "+11.4", h: 5 }, { v: "+22.8", h: 6 }, { v: "+38.4", h: 6 }] },
  { name: "의료기기 / 미용", cells: [{ v: "+0.2", h: 3 }, { v: "−0.2", h: 3 }, { v: "−1.8", h: 2 }, { v: "−4.2", h: 2 }, { v: "−2.4", h: 2 }] },
  { name: "클라우드 · SaaS", cells: [{ v: "+0.8", h: 4 }, { v: "+2.4", h: 4 }, { v: "+6.8", h: 5 }, { v: "+12.4", h: 5 }, { v: "+18.2", h: 5 }] },
];

export const THEMES_HBM_DRILLDOWN = [
  { name: "SK하이닉스", weight: "42%", d1: 2.34, m1: 11.8, ytd: 38.4 },
  { name: "한미반도체", weight: "18%", d1: 3.67, m1: 22.4, ytd: 72.4 },
  { name: "이수페타시스", weight: "8%", d1: 5.82, m1: 28.3, ytd: 81.2 },
  { name: "HPSP", weight: "7%", d1: 4.21, m1: 18.7, ytd: 58.2 },
  { name: "삼성전자", weight: "6%", d1: 1.88, m1: 8.7, ytd: 24.8 },
  { name: "리노공업", weight: "5%", d1: 2.14, m1: 14.2, ytd: 42.1 },
  { name: "솔브레인", weight: "4%", d1: 2.41, m1: 12.4, ytd: 34.2 },
];

export const THEMES_RANKS = [
  { name: "HBM", w4: 1, w2: 1, w1: 1, now: 1, trend: "유지 ↑", tone: "pos" },
  { name: "AI 반도체", w4: 2, w2: 2, w1: 2, now: 2, trend: "유지 ↑", tone: "pos" },
  { name: "휴머노이드", w4: 12, w2: 8, w1: 5, now: 3, trend: "급부상 ↑↑↑", tone: "pos" },
  { name: "원전 SMR", w4: 6, w2: 4, w1: 4, now: 4, trend: "상승 ↑", tone: "pos" },
  { name: "반도체 소부장", w4: 7, w2: 6, w1: 6, now: 5, trend: "상승 ↑", tone: "pos" },
  { name: "전력 인프라", w4: 8, w2: 7, w1: 7, now: 6, trend: "상승 ↑", tone: "pos" },
  { name: "조선 LNG", w4: 9, w2: 9, w1: 8, now: 7, trend: "상승 ↑", tone: "pos" },
  { name: "방산", w4: 2, w2: 3, w1: 10, now: 15, trend: "급락 ↓↓↓", tone: "neg" },
  { name: "K-뷰티", w4: 14, w2: 16, w1: 17, now: 18, trend: "하락 ↓", tone: "neg" },
  { name: "리튬", w4: 16, w2: 18, w1: 19, now: 20, trend: "최하 ↓", tone: "neg" },
];

// ---------------------------------------------------------------------------
// Short Interest · 공매도/대차
// ---------------------------------------------------------------------------
export const SHORT_SUMMARY = [
  { label: "공매도 과열", value: "14", delta: "경보 발동", tone: "neg" as const },
  { label: "대차잔고 상위", value: "9.2조", delta: "KOSPI 합계", tone: "neg" as const },
  { label: "공매도 비중 (시장)", value: "4.82%", delta: "+0.18pp WoW", tone: "neg" as const },
  { label: "숏스퀴즈 후보", value: "7", delta: "잔고 高 + 돌파", tone: "pos" as const },
  { label: "공매도 금지", value: "0", delta: "해제 상태" },
  { label: "Cover 비율", value: "0.72", delta: "숏 커버링 증가", tone: "pos" as const },
];

export const SHORT_OVERHEATED = [
  { name: "에코프로", sector: "2차전지", pct: 12.4, balance: "8,482억", delta: "+14.2%", status: "경보", tone: "neg" },
  { name: "LG에너지솔루션", sector: "2차전지", pct: 8.2, balance: "4,842억", delta: "+8.4%", status: "경보", tone: "neg" },
  { name: "포스코퓨처엠", sector: "2차전지", pct: 9.8, balance: "2,148억", delta: "+11.8%", status: "경보", tone: "neg" },
  { name: "삼성바이오로직스", sector: "바이오", pct: 6.4, balance: "1,842억", delta: "+5.8%", status: "주의", tone: "amber" },
  { name: "카카오", sector: "AI/SW", pct: 5.8, balance: "1,242억", delta: "−3.4%", status: "정상", tone: "pos" },
  { name: "셀트리온", sector: "바이오", pct: 4.2, balance: "884억", delta: "−8.4%", status: "축소", tone: "pos" },
  { name: "하이브", sector: "엔터", pct: 7.2, balance: "684억", delta: "+12.4%", status: "경보", tone: "neg" },
  { name: "LG화학", sector: "화학", pct: 5.4, balance: "2,482억", delta: "−2.1%", status: "주의", tone: "amber" },
];

export const SHORT_SQUEEZE = [
  { name: "한미반도체", pct: 3.8, d5: 8.2, trigger: "신고가 돌파", risk: "High" },
  { name: "HPSP", pct: 4.2, d5: 6.2, trigger: "Base 돌파", risk: "High" },
  { name: "이수페타시스", pct: 2.8, d5: 12.4, trigger: "52w 돌파", risk: "Med" },
  { name: "두산에너빌리티", pct: 3.4, d5: 7.9, trigger: "VCP 돌파", risk: "Med" },
  { name: "SK하이닉스", pct: 2.1, d5: 4.2, trigger: "SMA50 돌파", risk: "Low" },
  { name: "포스코홀딩스", pct: 5.2, d5: 3.4, trigger: "Stage 2", risk: "Low" },
  { name: "HD현대중공업", pct: 4.1, d5: 5.8, trigger: "Base 돌파", risk: "Med" },
];

// ---------------------------------------------------------------------------
// Kiwoom 조건식 7종
// ---------------------------------------------------------------------------
export const KIWOOM_CONDITIONS = [
  { id: "01", name: "이동평균 골든크로스", pass: 34, desc: "SMA 20 > SMA 60 (최근 5일)" },
  { id: "02", name: "거래량 급증 2배+", pass: 48, desc: "금일 거래량 ≥ 20일 평균 × 2" },
  { id: "03", name: "외국인 연속 순매수", pass: 28, desc: "5일 연속 순매수" },
  { id: "04", name: "신고가 돌파", pass: 31, desc: "52주 신고가 경신 종목" },
  { id: "05", name: "RSI 과매도 반등", pass: 12, desc: "RSI 30 이하 → 40 상향 돌파" },
  { id: "06", name: "볼린저 상단 돌파", pass: 22, desc: "종가 > 볼린저 상단 + 거래량 확증" },
  { id: "07", name: "MACD 골든크로스", pass: 19, desc: "MACD > Signal + Histogram 양전환" },
];

// ---------------------------------------------------------------------------
// Candlestick · 57종 스캐너
// ---------------------------------------------------------------------------
export const CANDLESTICK_SUMMARY = [
  { label: "오늘 패턴 발견", value: "142", delta: "전 유니버스", tone: "pos" as const },
  { label: "강세 패턴", value: "84", delta: "Bullish", tone: "pos" as const },
  { label: "약세 패턴", value: "48", delta: "Bearish", tone: "neg" as const },
  { label: "반전 패턴", value: "10", delta: "Reversal" },
  { label: "최고 신뢰도", value: "Hammer", delta: "72.4% 승률", tone: "pos" as const },
  { label: "평균 +5일 수익", value: "+2.84%", delta: "강세 패턴", tone: "pos" as const },
];

export const CANDLESTICK_HITS = [
  { name: "한미반도체", pattern: "Marubozu Bull", type: "Continuation", wr: 68.2, avg5: 3.42, volx: 2.1, cf: "VCP 돌파", tone: "pos" },
  { name: "HPSP", pattern: "Bullish Engulf", type: "Reversal", wr: 64.8, avg5: 2.84, volx: 1.8, cf: "Base 돌파", tone: "pos" },
  { name: "두산에너빌리티", pattern: "3 White Soldiers", type: "Continuation", wr: 71.2, avg5: 4.12, volx: 2.4, cf: "Stage 2", tone: "pos" },
  { name: "이수페타시스", pattern: "Hammer", type: "Reversal", wr: 72.4, avg5: 5.82, volx: 3.2, cf: "VCP+52w", tone: "pos" },
  { name: "리노공업", pattern: "Morning Star", type: "Reversal", wr: 69.4, avg5: 3.24, volx: 1.5, cf: "VCP", tone: "pos" },
  { name: "SK하이닉스", pattern: "Piercing Line", type: "Reversal", wr: 62.4, avg5: 2.34, volx: 1.2, cf: "Breakout", tone: "pos" },
  { name: "에코프로비엠", pattern: "Evening Star", type: "Reversal", wr: 64.8, avg5: -2.82, volx: 1.4, cf: "Stage 3 경고", tone: "neg" },
  { name: "삼성SDI", pattern: "Dark Cloud", type: "Reversal", wr: 58.2, avg5: -1.42, volx: 0.9, cf: "약세", tone: "neg" },
  { name: "아모레퍼시픽", pattern: "Shooting Star", type: "Reversal", wr: 61.2, avg5: -2.14, volx: 1.1, cf: "고점 경고", tone: "neg" },
  { name: "하이브", pattern: "Doji", type: "Indecision", wr: null, avg5: 1.84, volx: 1.0, cf: "관망", tone: "neutral" },
];

// ---------------------------------------------------------------------------
// Divergence · RSI/MACD/OBV
// ---------------------------------------------------------------------------
export const DIVERGENCE_SUMMARY = [
  { label: "RSI Bull Div", value: "18", delta: "가격 ↓ RSI ↑", tone: "pos" as const },
  { label: "RSI Bear Div", value: "12", delta: "가격 ↑ RSI ↓", tone: "neg" as const },
  { label: "MACD Bull Div", value: "9", delta: "반전 가능성", tone: "pos" as const },
  { label: "MACD Bear Div", value: "14", delta: "조정 경고", tone: "neg" as const },
  { label: "OBV Divergence", value: "7", delta: "거래량 괴리" },
  { label: "Hidden Bull", value: "11", delta: "추세 지속 신호", tone: "pos" as const },
];

export const DIVERGENCE_BULL = [
  { name: "셀트리온", ind: "RSI", rsi: 38.4, d5: -2.4, str: "강함", tone: "pos" },
  { name: "카카오", ind: "RSI + MACD", rsi: 42.1, d5: -1.8, str: "강함", tone: "pos" },
  { name: "포스코홀딩스", ind: "MACD", rsi: 44.8, d5: -1.2, str: "보통", tone: "amber" },
  { name: "NAVER", ind: "OBV", rsi: 48.2, d5: -0.8, str: "보통", tone: "amber" },
  { name: "LG화학", ind: "RSI", rsi: 34.2, d5: -3.8, str: "강함", tone: "pos" },
  { name: "아모레퍼시픽", ind: "MACD", rsi: 38.8, d5: -4.2, str: "보통", tone: "amber" },
];

export const DIVERGENCE_BEAR = [
  { name: "에코프로비엠", ind: "RSI + MACD", rsi: 72.4, d5: 2.1, str: "강함", tone: "neg" },
  { name: "삼성SDI", ind: "RSI", rsi: 68.8, d5: 1.4, str: "보통", tone: "amber" },
  { name: "하이브", ind: "MACD", rsi: 71.2, d5: 0.8, str: "강함", tone: "neg" },
  { name: "LG에너지솔루션", ind: "OBV", rsi: 64.2, d5: 1.4, str: "보통", tone: "amber" },
  { name: "에코프로", ind: "RSI + MACD + OBV", rsi: 74.8, d5: 2.8, str: "매우 강함", tone: "neg" },
  { name: "포스코퓨처엠", ind: "RSI", rsi: 66.8, d5: 0.4, str: "보통", tone: "amber" },
];

// ---------------------------------------------------------------------------
// Ichimoku
// ---------------------------------------------------------------------------
export const ICHIMOKU_SUMMARY = [
  { label: "구름 위 (Bullish)", value: "487", delta: "22.4% 유니버스", tone: "pos" as const },
  { label: "구름 아래 (Bearish)", value: "1,242", delta: "57.1%", tone: "neg" as const },
  { label: "구름 내부 (중립)", value: "446", delta: "20.5%" },
  { label: "오늘 구름 돌파", value: "14", delta: "Bullish cross", tone: "pos" as const },
  { label: "TK Cross Bull", value: "23", delta: "Tenkan > Kijun", tone: "pos" as const },
  { label: "완벽 신호", value: "8", delta: "3-cross align", tone: "pos" as const },
];

export const ICHIMOKU_ROWS = [
  { name: "한미반도체", sector: "반도체", tk: "Bull", vsc: "위", ch: "위", thick: 8.4, status: "Strong Bull", tone: "pos" },
  { name: "HPSP", sector: "반도체", tk: "Bull", vsc: "위", ch: "위", thick: 7.2, status: "Strong Bull", tone: "pos" },
  { name: "이수페타시스", sector: "반도체", tk: "Bull", vsc: "위", ch: "위", thick: 9.8, status: "Strong Bull", tone: "pos" },
  { name: "두산에너빌리티", sector: "원전", tk: "Bull", vsc: "위", ch: "위", thick: 6.8, status: "Strong Bull", tone: "pos" },
  { name: "리노공업", sector: "반도체", tk: "Bull", vsc: "위", ch: "위", thick: 5.4, status: "Bull", tone: "pos" },
  { name: "SK하이닉스", sector: "반도체", tk: "Bull", vsc: "위", ch: "위", thick: 4.8, status: "Bull", tone: "pos" },
  { name: "HD현대중공업", sector: "조선", tk: "Bull", vsc: "위", ch: "위", thick: 3.8, status: "Moderate", tone: "amber" },
  { name: "현대차", sector: "자동차", tk: "Bull", vsc: "위", ch: "위", thick: 3.2, status: "Moderate", tone: "amber" },
];

// ---------------------------------------------------------------------------
// Volume Profile
// ---------------------------------------------------------------------------
export const VPROFILE_SUMMARY = [
  { label: "POC 근접 (±2%)", value: "42", delta: "지지/저항 작용" },
  { label: "VAH 돌파", value: "18", delta: "모멘텀 구간", tone: "pos" as const },
  { label: "VAL 이탈", value: "12", delta: "약세 전환", tone: "neg" as const },
  { label: "HVN 추가", value: "8", delta: "신규 지지대 형성" },
  { label: "LVN 통과", value: "6", delta: "저저항 구간", tone: "pos" as const },
  { label: "Profile 거리 평균", value: "4.2%", delta: "from POC" },
];

export const VPROFILE_ROWS = [
  { name: "한미반도체", price: 134500, poc: 128400, vah: 136200, val: 118800, pos: "VAH 근접", signal: "돌파 대기", tone: "pos" },
  { name: "HPSP", price: 31200, poc: 29800, vah: 31400, val: 27200, pos: "VAH 근접", signal: "돌파 대기", tone: "pos" },
  { name: "두산에너빌리티", price: 21800, poc: 20400, vah: 22100, val: 18800, pos: "POC 위", signal: "지지 확인", tone: "amber" },
  { name: "이수페타시스", price: 47800, poc: 42200, vah: 46800, val: 38400, pos: "VAH 돌파", signal: "모멘텀", tone: "pos" },
  { name: "삼성전자", price: 75400, poc: 72800, vah: 76200, val: 68400, pos: "POC 위", signal: "상승 중", tone: "amber" },
  { name: "에코프로비엠", price: 204500, poc: 212000, vah: 228000, val: 196000, pos: "POC 아래", signal: "약세", tone: "neg" },
  { name: "아모레퍼시픽", price: 139600, poc: 148000, vah: 156000, val: 138000, pos: "VAL 근접", signal: "이탈 경고", tone: "neg" },
];

// ---------------------------------------------------------------------------
// Failed breakouts
// ---------------------------------------------------------------------------
export const FAILED_SUMMARY = [
  { label: "이번주 실패", value: "8", delta: "vs 돌파 31", tone: "neg" as const },
  { label: "실패율", value: "20.5%", delta: "정상 범위 (15-30%)", tone: "pos" as const },
  { label: "평균 손실", value: "−5.8%", delta: "손절 −7% 룰 대비 양호", tone: "neg" as const },
  { label: "주요 원인", value: "거래량 부족", delta: "62% (5/8)" },
  { label: "섹터 집중", value: "바이오", delta: "3건 (Stage 1)", tone: "neg" as const },
  { label: "30일 누적 교훈", value: "24건", delta: "DB 축적 중" },
];

export const FAILED_ROWS = [
  { date: "04-18", name: "메디톡스", bo: 148000, low: 138200, loss: -6.6, cause: "Vol 0.8×", lesson: "거래량 확증 없이 돌파 → 되돌림 · 규칙: Vol 1.5× 미만 진입 금지" },
  { date: "04-17", name: "롯데케미칼", bo: 178000, low: 168400, loss: -5.4, cause: "섹터 약세", lesson: "화학 섹터 RS 0.32 · 섹터 함께 강해야" },
  { date: "04-16", name: "씨젠", bo: 24800, low: 23100, loss: -6.9, cause: "Stage 1", lesson: "Weinstein Stage 1에서 가짜 돌파 빈번" },
  { date: "04-15", name: "하이브", bo: 218000, low: 204500, loss: -6.2, cause: "갭업 후 반락", lesson: "실적 발표 직후 갭업은 페이드 확률 ↑" },
  { date: "04-14", name: "JW중외제약", bo: 38500, low: 36100, loss: -6.2, cause: "Vol 0.6×", lesson: "거래량 부족 (반복)" },
  { date: "04-11", name: "이오플로우", bo: 42200, low: 39400, loss: -6.6, cause: "Stage 1", lesson: "Stage 1 가짜 돌파 (반복)" },
  { date: "04-10", name: "DB하이텍", bo: 62400, low: 58200, loss: -6.7, cause: "TT 4/8", lesson: "Trend Template 5/8 미달 종목 돌파는 신뢰도 낮음" },
  { date: "04-08", name: "아모레퍼시픽", bo: 148000, low: 139600, loss: -5.7, cause: "Vol 0.9×", lesson: "거래량 부족 (3회째 반복)" },
];

// ---------------------------------------------------------------------------
// Watchlist
// ---------------------------------------------------------------------------
export const WATCHLIST_SUMMARY = [
  { label: "관심종목", value: "38", delta: "+3 이번주", tone: "pos" as const },
  { label: "활성 알람", value: "14", delta: "가격/거래량/패턴" },
  { label: "오늘 트리거", value: "7", delta: "장중 발동", tone: "pos" as const },
  { label: "포지션 전환 대기", value: "3", delta: "진입 고려" },
  { label: "30D 알람 정확도", value: "68.4%", delta: "유효 시그널 비율", tone: "pos" as const },
  { label: "평균 보유 기간", value: "18일", delta: "관심 → 진입" },
];

export const WATCHLIST_ITEMS = [
  { name: "한미반도체", tags: ["반도체", "VCP"], price: 134500, from: 18.4, memo: "HBM 주도주 · VCP 돌파 대기", status: "보유 중", tone: "pos" },
  { name: "HPSP", tags: ["반도체"], price: 31200, from: 12.4, memo: "반도체 소부장 Top1 · 실적 확인", status: "진입 대기", tone: "amber" },
  { name: "이수페타시스", tags: ["반도체"], price: 47800, from: 28.4, memo: "너무 멀어짐 · 눌림 대기", status: "관망", tone: "neutral" },
  { name: "두산에너빌리티", tags: ["원전", "VCP"], price: 21800, from: 14.8, memo: "SMR 수주 모멘텀 · 22,500 돌파 시 진입", status: "진입 대기", tone: "amber" },
  { name: "하이브", tags: ["엔터"], price: 204500, from: -8.2, memo: "실적 악재 · 175,000 하향 돌파시 손절", status: "관망", tone: "neg" },
  { name: "HD현대중공업", tags: ["조선"], price: 214000, from: 22.4, memo: "LNG 수주 지속 · Base 돌파 확인", status: "보유 중", tone: "pos" },
  { name: "카카오", tags: ["AI/SW"], price: 42400, from: -2.1, memo: "RSI 다이버전스 · 반등 대기", status: "관망", tone: "amber" },
  { name: "HD한국조선해양", tags: ["조선"], price: 142000, from: 14.2, memo: "HD현대중공업 동반", status: "관망", tone: "neutral" },
];

export const WATCHLIST_ALERTS = [
  { name: "두산에너빌리티", cond: "가격 돌파", target: 22500, cur: 21800, status: "96.9%", tone: "amber" },
  { name: "HPSP", cond: "거래량 2× + 돌파", target: 31500, cur: 31200, status: "99%", tone: "amber" },
  { name: "한미반도체", cond: "VCP 3파 돌파", target: 135200, cur: 134500, status: "99.5%", tone: "amber" },
  { name: "하이브", cond: "하방 손절선", target: 175000, cur: 204500, status: "거리 있음", tone: "neutral" },
  { name: "카카오", cond: "RSI 50 회복", target: 50.0, cur: 42.1, status: "거리 있음", tone: "neutral" },
  { name: "에코프로", cond: "공매도 잔고 경보", target: null, cur: "12.4%", status: "발동", tone: "neg" },
  { name: "SK하이닉스", cond: "실적 발표 (04-25)", target: "D-3", cur: null, status: "대기", tone: "amber" },
];

export const WATCHLIST_LOG = [
  { time: "15:24:18", tag: "PATTERN", sym: "403870", msg: "HPSP Stage 3 진입 · VCP 수축 3파 · 돌파 대기", tagClass: "alert" },
  { time: "14:58:21", tag: "BREAKOUT", sym: "034020", msg: "두산에너빌리티 52주 신고가 갱신 · 22,500 방어선 상향", tagClass: "buy" },
  { time: "14:42:08", tag: "VOL", sym: "007660", msg: "이수페타시스 거래량 3× 급증 · 신고가 돌파", tagClass: "alert" },
  { time: "13:14:42", tag: "SHORT", sym: "086520", msg: "에코프로 공매도 과열 경보 발동 · 12.4%", tagClass: "alert" },
  { time: "11:38:22", tag: "DIV", sym: "035720", msg: "카카오 RSI Bullish Divergence 형성", tagClass: "sys" },
  { time: "10:24:14", tag: "TT", sym: "042700", msg: "한미반도체 TT 8/8 달성 · Perfect score", tagClass: "buy" },
  { time: "09:18:42", tag: "ADD", sym: "267270", msg: "HD현대인프라코어 관심종목 추가 · 방산+원전 테마", tagClass: "sys" },
];

// ---------------------------------------------------------------------------
// Journal
// ---------------------------------------------------------------------------
export const JOURNAL_SUMMARY = [
  { label: "30D 거래 수", value: "17", delta: "11 익절 · 6 손절", tone: "pos" as const },
  { label: "승률", value: "64.7%", delta: "vs 목표 60%", tone: "pos" as const },
  { label: "Avg R (보상/위험)", value: "2.4R", delta: "목표 2R+", tone: "pos" as const },
  { label: "최대 승", value: "+18.4%", delta: "한미반도체", tone: "pos" as const },
  { label: "최대 손실", value: "−7.8%", delta: "손절 룰 내", tone: "neg" as const },
  { label: "실수 Top 원인", value: "충동", delta: "3/6 loss", tone: "neg" as const },
];

export const JOURNAL_ROWS = [
  { date: "04-18", name: "한미반도체", type: "익절", tone: "pos", pl: 18.4, days: 14, wiz: "Minervini", note: "VCP 돌파 + Vol 2× 정석 매매" },
  { date: "04-15", name: "메디톡스", type: "손절", tone: "neg", pl: -6.6, days: 3, wiz: "Darvas", note: "Vol 확증 없이 진입 · 충동" },
  { date: "04-14", name: "두산에너빌리티", type: "익절", tone: "pos", pl: 12.8, days: 8, wiz: "O'Neil", note: "CANSLIM 7/7 · 기관 매집 확인" },
  { date: "04-11", name: "이오플로우", type: "손절", tone: "neg", pl: -7.2, days: 5, wiz: "Weinstein", note: "Stage 1 오판 · 룰 위반" },
  { date: "04-09", name: "SK하이닉스", type: "익절", tone: "pos", pl: 8.2, days: 12, wiz: "Livermore", note: "Pivot 확증 · 피라미드 2단계" },
  { date: "04-05", name: "HPSP", type: "익절", tone: "pos", pl: 14.2, days: 18, wiz: "Minervini", note: "Base 돌파 + 52w 갱신" },
  { date: "04-02", name: "에코프로비엠", type: "손절", tone: "neg", pl: -7.8, days: 6, wiz: "Darvas", note: "섹터 약세 무시 · 개별 돌파만 봄" },
  { date: "03-28", name: "리노공업", type: "익절", tone: "pos", pl: 9.8, days: 10, wiz: "O'Neil", note: "Cup & Handle 정석" },
];

export const JOURNAL_MISTAKES = [
  { icon: "✕", tone: "neg", label: "거래량 확증 없이 진입", pct: 50, txt: "3/6" },
  { icon: "✕", tone: "neg", label: "Stage 1 오판", pct: 33, txt: "2/6" },
  { icon: "✕", tone: "neg", label: "섹터 약세 무시", pct: 33, txt: "2/6" },
  { icon: "~", tone: "amber", label: "손절 지연 (−7% 이상)", pct: 17, txt: "1/6" },
  { icon: "✓", tone: "pos", label: "손절 룰 준수", pct: 83, txt: "5/6" },
];

// ---------------------------------------------------------------------------
// Playbook · 12 체크리스트
// ---------------------------------------------------------------------------
export const PLAYBOOK_SUMMARY = [
  { label: "체크리스트 항목", value: "12", delta: "필수 + 선택" },
  { label: "30D 준수율", value: "78.4%", delta: "17 trades", tone: "pos" as const },
  { label: "미준수 시 손실률", value: "3.4×", delta: "준수 대비", tone: "neg" as const },
  { label: "최빈 누락", value: "Vol 확증", delta: "3/17", tone: "neg" as const },
  { label: "모든 항목 통과", value: "9", delta: "/ 17 trades", tone: "pos" as const },
  { label: "이 중 승률", value: "88.9%", delta: "8 / 9", tone: "pos" as const },
];

export const PLAYBOOK_CHECKS = [
  { n: "①", done: true, label: "섹터 RS > 0.5 확인", time: "09:18" },
  { n: "②", done: true, label: "Trend Template 6/8 이상", time: "09:19" },
  { n: "③", done: true, label: "Weinstein Stage 2 확인", time: "09:19" },
  { n: "④", done: true, label: "VCP/Base 돌파 확증", time: "09:20" },
  { n: "⑤", done: true, label: "거래량 1.5× 이상 확인", time: "09:20" },
  { n: "⑥", done: false, label: "외인/기관 매집 추세", time: "—" },
  { n: "⑦", done: false, label: "공시/실적 확인 (악재 無)", time: "—" },
  { n: "⑧", done: false, label: "손절 −7% 지점 설정", time: "—" },
  { n: "⑨", done: false, label: "목표 +15% (2R+) 설정", time: "—" },
  { n: "⑩", done: false, label: "포지션 크기 계좌 < 20%", time: "—" },
  { n: "⑪", done: false, label: "같은 섹터 동시 <3 종목", time: "—" },
  { n: "⑫", done: false, label: "매매일지 진입 사유 기록", time: "—" },
];

export const PLAYBOOK_STATS = [
  { n: "①", label: "섹터 RS 확인", pct: 100 },
  { n: "②", label: "TT 6/8 이상", pct: 94 },
  { n: "③", label: "Stage 2 확인", pct: 82 },
  { n: "④", label: "패턴 돌파", pct: 94 },
  { n: "⑤", label: "거래량 1.5×", pct: 76, amber: true },
  { n: "⑥", label: "수급 확인", pct: 88 },
  { n: "⑦", label: "공시/실적", pct: 100 },
  { n: "⑧", label: "손절선 설정", pct: 100 },
  { n: "⑨", label: "목표가 설정", pct: 88 },
  { n: "⑩", label: "포지션 < 20%", pct: 100 },
  { n: "⑪", label: "섹터 집중 제한", pct: 94 },
  { n: "⑫", label: "일지 기록", pct: 71, amber: true },
];

// ---------------------------------------------------------------------------
// Backtest
// ---------------------------------------------------------------------------
export const BACKTEST_SUMMARY = [
  { label: "CAGR", value: "23.4%", delta: "3년 평균", tone: "pos" as const },
  { label: "MDD", value: "−19.1%", delta: "2023 Q3", tone: "neg" as const },
  { label: "Sharpe", value: "1.38", delta: "vs KOSPI 0.42", tone: "pos" as const },
  { label: "Win Rate", value: "58.4%", delta: "217 trades" },
];

// ---------------------------------------------------------------------------
// Wizards — per-wizard mock
// ---------------------------------------------------------------------------
export interface WizardMock {
  key: string;
  quote: string;
  quoteAttr: string;
  pageMeta: string;
  summary: { label: string; value: string; delta: string; tone?: "pos" | "neg" | "amber" | "neutral" }[];
  passRows: Record<string, string | number>[];
  passHeaders: { key: string; label: string; align?: "left" | "right" }[];
  conditions: { icon: string; iconTone?: "pos" | "amber" | "neg"; label: string; pct: number; amber?: boolean; labelRight: string }[];
  playbook: string;
  sideTitle: string;
  sideSubtitle: string;
}

export const WIZARD_MOCKS: Record<string, WizardMock> = {
  minervini: {
    key: "minervini",
    quote: "Buy high, sell higher. The stock market is a game of probability, not certainty.",
    quoteAttr: "— Mark Minervini · Trade Like a Stock Market Wizard",
    pageMeta: "TREND TEMPLATE 8-COND · VCP · PIVOT · 24 MATCHES TODAY",
    summary: [
      { label: "Pass Rate", value: "1.10%", delta: "24 / 2,175", tone: "pos" },
      { label: "TT 8/8 (Perfect)", value: "7", delta: "모든 조건", tone: "pos" },
      { label: "VCP Stage 3", value: "12", delta: "돌파 임박", tone: "pos" },
      { label: "Pivot 근접 (±2%)", value: "8", delta: "진입가 대기", tone: "pos" },
      { label: "Avg RS", value: "0.82", delta: "상위 18%", tone: "pos" },
      { label: "30D Win Rate", value: "64.3%", delta: "9 / 14 trades", tone: "pos" },
    ],
    passHeaders: [
      { key: "name", label: "Ticker" }, { key: "sector", label: "Sector" },
      { key: "tt", label: "TT", align: "right" }, { key: "rs", label: "RS", align: "right" },
      { key: "stage", label: "Stage" }, { key: "pivot", label: "Pivot", align: "right" },
      { key: "close", label: "Close", align: "right" }, { key: "high52", label: "52wH%", align: "right" },
      { key: "eps", label: "EPS·y", align: "right" },
    ],
    passRows: [
      { name: "한미반도체", code: "042700", sector: "반도체", tt: "8/8", rs: "0.91", stage: "VCP-3", pivot: "135,200", close: "134,500", high52: "98.2", eps: "+42%" },
      { name: "HPSP", code: "403870", sector: "반도체", tt: "8/8", rs: "0.84", stage: "Base", pivot: "31,800", close: "31,200", high52: "96.4", eps: "+31%" },
      { name: "리노공업", code: "058470", sector: "반도체", tt: "8/8", rs: "0.76", stage: "VCP-3", pivot: "284,000", close: "281,500", high52: "94.1", eps: "+28%" },
      { name: "이수페타시스", code: "007660", sector: "반도체", tt: "8/8", rs: "0.81", stage: "VCP-3", pivot: "48,200", close: "47,800", high52: "99.1", eps: "+38%" },
      { name: "두산에너빌리티", code: "034020", sector: "원전", tt: "8/8", rs: "0.83", stage: "VCP-2", pivot: "22,400", close: "21,800", high52: "92.8", eps: "+34%" },
      { name: "에코프로비엠", code: "247540", sector: "2차전지", tt: "7/8", rs: "0.79", stage: "VCP-2", pivot: "210,000", close: "204,500", high52: "87.3", eps: "+22%" },
      { name: "SFA반도체", code: "036540", sector: "반도체", tt: "7/8", rs: "0.72", stage: "Base", pivot: "8,240", close: "8,120", high52: "93.2", eps: "+26%" },
      { name: "파크시스템스", code: "140860", sector: "반도체", tt: "7/8", rs: "0.68", stage: "VCP-2", pivot: "318,000", close: "314,500", high52: "91.7", eps: "+19%" },
      { name: "솔브레인", code: "357780", sector: "반도체", tt: "7/8", rs: "0.71", stage: "VCP-3", pivot: "324,000", close: "319,500", high52: "95.2", eps: "+24%" },
      { name: "동진쎄미켐", code: "005290", sector: "반도체", tt: "7/8", rs: "0.66", stage: "Base", pivot: "52,800", close: "52,100", high52: "89.4", eps: "+17%" },
    ],
    conditions: [
      { icon: "✓", label: "Close > SMA150 > SMA200", pct: 100, labelRight: "100%" },
      { icon: "✓", label: "SMA150 > SMA200", pct: 100, labelRight: "100%" },
      { icon: "✓", label: "SMA200 상승 (1개월)", pct: 96, labelRight: "96%" },
      { icon: "✓", label: "SMA50 > SMA150, SMA200", pct: 100, labelRight: "100%" },
      { icon: "✓", label: "Close > SMA50", pct: 100, labelRight: "100%" },
      { icon: "~", iconTone: "amber", label: "52주 저점 +30% 이상", pct: 87, amber: true, labelRight: "87%" },
      { icon: "✓", label: "52주 고점 −25% 이내", pct: 92, labelRight: "92%" },
      { icon: "✓", label: "RS Rating ≥ 70", pct: 100, labelRight: "100%" },
    ],
    playbook: "TT 8/8 + Stage 3 VCP + Pivot ±2% + Volume 1.5× 돌파 → 진입. 손절은 −7%, 목표는 2R+.",
    sideTitle: "Trend Template 8-조건",
    sideSubtitle: "24 종목 중 통과율",
  },
  oneil: {
    key: "oneil",
    quote: "The market doesn't care about your needs or opinions. It moves based on supply and demand.",
    quoteAttr: "— William J. O'Neil · How to Make Money in Stocks",
    pageMeta: "7-FACTOR GROWTH MODEL · C·A·N·S·L·I·M · 17 MATCHES",
    summary: [
      { label: "Pass Rate", value: "0.78%", delta: "17 / 2,175", tone: "pos" },
      { label: "Cup & Handle", value: "5", delta: "고전 패턴", tone: "pos" },
      { label: "기관 매집 (I)", value: "12", delta: "외인+기관 순매수", tone: "pos" },
      { label: "EPS QoQ ≥ +25%", value: "14", delta: "Current Earnings", tone: "pos" },
      { label: "시장 방향 (M)", value: "Confirmed", delta: "Up-trend", tone: "pos" },
      { label: "30D Win Rate", value: "58.8%", delta: "10 / 17", tone: "pos" },
    ],
    passHeaders: [
      { key: "name", label: "Ticker" }, { key: "sector", label: "Sector" },
      { key: "c", label: "C", align: "right" }, { key: "a", label: "A", align: "right" },
      { key: "n", label: "N", align: "right" }, { key: "s", label: "S", align: "right" },
      { key: "l", label: "L", align: "right" }, { key: "i", label: "I", align: "right" },
      { key: "m", label: "M", align: "right" }, { key: "score", label: "Σ", align: "right" },
    ],
    passRows: [
      { name: "한미반도체", sector: "반도체", c: "A+", a: "A", n: "A", s: "B+", l: "A+", i: "A", m: "✓", score: "97" },
      { name: "HPSP", sector: "반도체", c: "A", a: "A", n: "A-", s: "B", l: "A", i: "A-", m: "✓", score: "91" },
      { name: "이수페타시스", sector: "반도체", c: "A+", a: "A-", n: "A+", s: "A", l: "A", i: "A-", m: "✓", score: "94" },
      { name: "두산에너빌리티", sector: "원전", c: "A", a: "B+", n: "A+", s: "A-", l: "A", i: "A", m: "✓", score: "89" },
      { name: "리노공업", sector: "반도체", c: "B+", a: "A", n: "B", s: "B+", l: "A-", i: "B+", m: "✓", score: "82" },
      { name: "에코프로비엠", sector: "2차전지", c: "B", a: "A", n: "B+", s: "A", l: "B+", i: "B", m: "✓", score: "78" },
      { name: "파크시스템스", sector: "반도체", c: "A-", a: "A-", n: "A", s: "B", l: "B+", i: "B+", m: "✓", score: "81" },
      { name: "SFA반도체", sector: "반도체", c: "A", a: "B+", n: "B+", s: "A-", l: "B+", i: "B", m: "✓", score: "80" },
      { name: "솔브레인", sector: "반도체", c: "A-", a: "A-", n: "B", s: "B+", l: "A-", i: "A-", m: "✓", score: "83" },
      { name: "티에스이", sector: "반도체", c: "A", a: "B+", n: "B+", s: "B", l: "B+", i: "B+", m: "✓", score: "79" },
    ],
    conditions: [
      { icon: "C", label: "Current EPS QoQ ≥ +25%", pct: 88, labelRight: "A−" },
      { icon: "A", label: "Annual EPS 3Y > +25%", pct: 85, labelRight: "A−" },
      { icon: "N", label: "New products · highs", pct: 92, labelRight: "A" },
      { icon: "S", label: "Supply + Demand", pct: 76, labelRight: "B+" },
      { icon: "L", label: "Leader (RS ≥ 80)", pct: 94, labelRight: "A" },
      { icon: "I", label: "Institutional 매집", pct: 82, labelRight: "A−" },
      { icon: "M", label: "Market up-trend", pct: 100, labelRight: "✓" },
    ],
    playbook: "Cup & Handle + Pivot 돌파 + Volume 40% 이상 + 시장 확인된 up-trend. 손절 −8%, 목표 +20%.",
    sideTitle: "CANSLIM 7-factor",
    sideSubtitle: "요소별 평균",
  },
  darvas: {
    key: "darvas",
    quote: "There are no good or bad stocks. There are only stocks that rise in price and stocks that decline in price.",
    quoteAttr: "— Nicolas Darvas · How I Made $2,000,000 in the Stock Market",
    pageMeta: "BOX FORMATION · BREAKOUT · VOLUME · 9 MATCHES",
    summary: [
      { label: "Pass Rate", value: "0.41%", delta: "9 / 2,175", tone: "pos" },
      { label: "Box Ready", value: "5", delta: "돌파 대기", tone: "pos" },
      { label: "Just Broke Out", value: "3", delta: "오늘 돌파", tone: "pos" },
      { label: "Avg Box Height", value: "8.4%", delta: "tight 수렴" },
      { label: "Avg Vol × at BO", value: "2.1×", delta: "거래량 확증", tone: "pos" },
      { label: "30D Win Rate", value: "55.6%", delta: "5 / 9", tone: "pos" },
    ],
    passHeaders: [
      { key: "name", label: "Ticker" }, { key: "sector", label: "Sector" },
      { key: "boxHi", label: "Box Hi", align: "right" }, { key: "boxLo", label: "Box Lo", align: "right" },
      { key: "height", label: "Height%", align: "right" }, { key: "now", label: "Now", align: "right" },
      { key: "volx", label: "Vol×", align: "right" }, { key: "status", label: "Status" },
      { key: "days", label: "Days", align: "right" },
    ],
    passRows: [
      { name: "이수페타시스", sector: "반도체", boxHi: "48,000", boxLo: "42,500", height: "12.9", now: "47,800", volx: "3.2×", status: "BROKE", days: "14" },
      { name: "HPSP", sector: "반도체", boxHi: "31,000", boxLo: "28,400", height: "9.2", now: "31,200", volx: "1.8×", status: "BROKE", days: "9" },
      { name: "한미반도체", sector: "반도체", boxHi: "135,000", boxLo: "124,000", height: "8.9", now: "134,500", volx: "2.1×", status: "READY", days: "11" },
      { name: "두산에너빌리티", sector: "원전", boxHi: "22,200", boxLo: "20,100", height: "10.4", now: "21,800", volx: "2.4×", status: "READY", days: "18" },
      { name: "리노공업", sector: "반도체", boxHi: "285,000", boxLo: "268,000", height: "6.3", now: "281,500", volx: "1.5×", status: "READY", days: "21" },
      { name: "솔브레인", sector: "반도체", boxHi: "325,000", boxLo: "308,000", height: "5.5", now: "319,500", volx: "1.4×", status: "READY", days: "16" },
      { name: "SFA반도체", sector: "반도체", boxHi: "8,200", boxLo: "7,500", height: "9.3", now: "8,120", volx: "1.7×", status: "READY", days: "12" },
      { name: "파크시스템스", sector: "반도체", boxHi: "320,000", boxLo: "298,000", height: "7.4", now: "314,500", volx: "1.6×", status: "WAIT", days: "8" },
      { name: "에코프로비엠", sector: "2차전지", boxHi: "218,000", boxLo: "195,000", height: "11.8", now: "204,500", volx: "1.4×", status: "STOP", days: "24" },
    ],
    conditions: [
      { icon: "✓", label: "52주 신고가 근처 (80%+)", pct: 100, labelRight: "9/9" },
      { icon: "✓", label: "최근 3일 이상 같은 고점 터치", pct: 100, labelRight: "9/9" },
      { icon: "✓", label: "최근 3일 이상 같은 저점 지지", pct: 89, labelRight: "8/9" },
      { icon: "✓", label: "Box Height ≤ 12%", pct: 78, labelRight: "7/9" },
      { icon: "~", iconTone: "amber", label: "Volume 1.5× at Breakout", pct: 67, amber: true, labelRight: "6/9" },
      { icon: "✓", label: "Box 후 시장 up-trend", pct: 100, labelRight: "9/9" },
    ],
    playbook: "Box 돌파 + Vol 1.5× 시 진입. Trailing stop = 새 Box Low. 박스 이탈 시 즉시 청산.",
    sideTitle: "Box 형성 규칙",
    sideSubtitle: "DARVAS RULES",
  },
  livermore: {
    key: "livermore",
    quote: "It never was my thinking that made big money for me. It was my sitting.",
    quoteAttr: "— Jesse Livermore · Reminiscences of a Stock Operator",
    pageMeta: "LINE OF LEAST RESISTANCE · PYRAMID · 12 MATCHES",
    summary: [
      { label: "Pass Rate", value: "0.55%", delta: "12 / 2,175", tone: "pos" },
      { label: "Pivot Confirmed", value: "7", delta: "방향 확증", tone: "pos" },
      { label: "Pyramid Level 2+", value: "4", delta: "추매 구간", tone: "pos" },
      { label: "Line of Least Res.", value: "↑ UP", delta: "시장 방향", tone: "pos" },
      { label: "Avg Hold Days", value: "38d", delta: "sit 원칙" },
      { label: "30D Win Rate", value: "66.7%", delta: "8 / 12", tone: "pos" },
    ],
    passHeaders: [
      { key: "name", label: "Ticker" }, { key: "sector", label: "Sector" },
      { key: "pivot", label: "Pivot", align: "right" }, { key: "now", label: "Now", align: "right" },
      { key: "line", label: "Line" }, { key: "volTrend", label: "Vol Trend", align: "right" },
      { key: "pyramid", label: "Pyramid" }, { key: "hold", label: "Hold", align: "right" },
    ],
    passRows: [
      { name: "한미반도체", sector: "반도체", pivot: "118,000", now: "134,500", line: "↑ Confirmed", volTrend: "Rising", pyramid: "Lv 3", hold: "42d" },
      { name: "HPSP", sector: "반도체", pivot: "27,800", now: "31,200", line: "↑ Confirmed", volTrend: "Rising", pyramid: "Lv 2", hold: "28d" },
      { name: "이수페타시스", sector: "반도체", pivot: "42,500", now: "47,800", line: "↑ Confirmed", volTrend: "Rising", pyramid: "Lv 2", hold: "21d" },
      { name: "두산에너빌리티", sector: "원전", pivot: "19,800", now: "21,800", line: "↑ Confirmed", volTrend: "Rising", pyramid: "Lv 2", hold: "34d" },
      { name: "리노공업", sector: "반도체", pivot: "268,000", now: "281,500", line: "↑ Confirmed", volTrend: "Rising", pyramid: "Lv 1", hold: "18d" },
      { name: "SK하이닉스", sector: "반도체", pivot: "178,000", now: "192,100", line: "↑ Testing", volTrend: "Rising", pyramid: "Lv 1", hold: "12d" },
      { name: "삼성전자", sector: "반도체", pivot: "72,500", now: "75,400", line: "↑ Testing", volTrend: "Stable", pyramid: "Lv 1", hold: "8d" },
      { name: "솔브레인", sector: "반도체", pivot: "305,000", now: "319,500", line: "↑ Confirmed", volTrend: "Rising", pyramid: "Lv 1", hold: "22d" },
    ],
    conditions: [],
    playbook: "Pivot 돌파 + 거래량 → 30% 진입, +5%에서 30% 추매, +10% + 섹터 확증 시 40% 추매. Line of Least Resistance 역전 시 전체 청산.",
    sideTitle: "Pyramid 규칙",
    sideSubtitle: "피라미딩 원칙",
  },
  zanger: {
    key: "zanger",
    quote: "The key is in the volume. The big volume days are the most important days in the life of a stock.",
    quoteAttr: "— Dan Zanger · 29,233% in 23 months",
    pageMeta: "INTRADAY MOMENTUM · 29,000% WORLD RECORD · 6 MATCHES",
    summary: [
      { label: "Pass Rate", value: "0.28%", delta: "6 / 2,175", tone: "pos" },
      { label: "Gap Up ≥ +3%", value: "4", delta: "갭 확증", tone: "pos" },
      { label: "Vol× ≥ 3", value: "5", delta: "거래량 폭발", tone: "pos" },
      { label: "Close vs HOD", value: "96.4%", delta: "종가 = 고가 근접", tone: "pos" },
      { label: "KOSPI Trend", value: "↑ Up-day", delta: "시장 up", tone: "pos" },
      { label: "30D Win Rate", value: "66.7%", delta: "4 / 6", tone: "pos" },
    ],
    passHeaders: [
      { key: "name", label: "Ticker" }, { key: "sector", label: "Sector" },
      { key: "gap", label: "Gap%", align: "right" }, { key: "volx", label: "Vol×", align: "right" },
      { key: "hod", label: "HOD", align: "right" }, { key: "close", label: "Close", align: "right" },
      { key: "cHod", label: "Close/HOD", align: "right" }, { key: "pattern", label: "Pattern" },
    ],
    passRows: [
      { name: "이수페타시스", sector: "반도체", gap: "+4.2", volx: "3.2×", hod: "48,100", close: "47,800", cHod: "99.4%", pattern: "Bull Flag" },
      { name: "HPSP", sector: "반도체", gap: "+3.8", volx: "1.8×", hod: "31,400", close: "31,200", cHod: "99.4%", pattern: "Cup & H" },
      { name: "두산에너빌리티", sector: "원전", gap: "+3.4", volx: "2.4×", hod: "21,900", close: "21,800", cHod: "99.5%", pattern: "Ascending △" },
      { name: "한미반도체", sector: "반도체", gap: "+3.1", volx: "2.1×", hod: "135,000", close: "134,500", cHod: "99.6%", pattern: "Flag" },
      { name: "SFA반도체", sector: "반도체", gap: "+2.8", volx: "1.7×", hod: "8,180", close: "8,120", cHod: "99.3%", pattern: "Pennant" },
      { name: "동진쎄미켐", sector: "반도체", gap: "+2.5", volx: "1.9×", hod: "52,400", close: "52,100", cHod: "99.4%", pattern: "Wedge" },
    ],
    conditions: [
      { icon: "✓", label: "Gap up ≥ +3% (오늘)", pct: 67, labelRight: "4/6" },
      { icon: "✓", label: "Volume ≥ 1.5× 평균", pct: 100, labelRight: "6/6" },
      { icon: "✓", label: "Close ≥ 95% of HOD", pct: 100, labelRight: "6/6" },
      { icon: "✓", label: "Pattern 확인 (Flag, Cup, etc.)", pct: 83, labelRight: "5/6" },
      { icon: "✓", label: "시장 Up-day", pct: 100, labelRight: "6/6" },
      { icon: "~", iconTone: "amber", label: "52주 고점 근접", pct: 83, amber: true, labelRight: "5/6" },
    ],
    playbook: "Gap + Vol + HOD 확인 시 즉시 진입. 손절 −3%, 목표 +5~15%. 보유 1-5일.",
    sideTitle: "Zanger 체크리스트",
    sideSubtitle: "INTRADAY",
  },
  weinstein: {
    key: "weinstein",
    quote: "The best advice I can give you is to never invest in a stock that is trading below its 30-week moving average.",
    quoteAttr: "— Stan Weinstein · Secrets for Profiting in Bull & Bear Markets",
    pageMeta: "4-STAGE LIFECYCLE · 30-WEEK SMA · 21 MATCHES IN STAGE 2",
    summary: [
      { label: "Stage 2 (상승)", value: "21", delta: "0.97% of 2,175", tone: "pos" },
      { label: "Stage 2 진입", value: "6", delta: "최근 2주", tone: "pos" },
      { label: "Stage 2 성숙", value: "11", delta: "8주+ 지속", tone: "pos" },
      { label: "Stage 2 Late", value: "4", delta: "Stage 3 경고", tone: "neg" },
      { label: "SMA30 상승각", value: "+2.8°", delta: "명확한 상승", tone: "pos" },
      { label: "30D Win Rate", value: "71.4%", delta: "15 / 21", tone: "pos" },
    ],
    passHeaders: [
      { key: "name", label: "Ticker" }, { key: "sector", label: "Sector" },
      { key: "stage", label: "Stage" }, { key: "vs", label: "vs SMA30", align: "right" },
      { key: "weeks", label: "Weeks", align: "right" }, { key: "rs", label: "RS vs Mkt", align: "right" },
      { key: "angle", label: "SMA30 Angle" }, { key: "sub", label: "Sub" },
    ],
    passRows: [
      { name: "한미반도체", sector: "반도체", stage: "Stage 2", vs: "+18.4%", weeks: "14", rs: "+24.1", angle: "상승", sub: "중기" },
      { name: "HPSP", sector: "반도체", stage: "Stage 2", vs: "+12.8%", weeks: "11", rs: "+18.2", angle: "상승", sub: "중기" },
      { name: "이수페타시스", sector: "반도체", stage: "Stage 2", vs: "+22.1%", weeks: "8", rs: "+29.4", angle: "급상승", sub: "Late" },
      { name: "리노공업", sector: "반도체", stage: "Stage 2", vs: "+8.4%", weeks: "18", rs: "+12.8", angle: "상승", sub: "성숙" },
      { name: "두산에너빌리티", sector: "원전", stage: "Stage 2", vs: "+14.2%", weeks: "9", rs: "+19.8", angle: "상승", sub: "중기" },
      { name: "에코프로비엠", sector: "2차전지", stage: "Stage 2", vs: "+4.8%", weeks: "3", rs: "+7.2", angle: "완만", sub: "초기" },
      { name: "포스코퓨처엠", sector: "2차전지", stage: "Stage 2", vs: "+3.2%", weeks: "2", rs: "+4.1", angle: "완만", sub: "초기" },
      { name: "SK하이닉스", sector: "반도체", stage: "Stage 2", vs: "+6.8%", weeks: "5", rs: "+11.4", angle: "상승", sub: "중기" },
      { name: "삼성전자", sector: "반도체", stage: "Stage 2", vs: "+2.8%", weeks: "4", rs: "+5.8", angle: "완만", sub: "초기" },
      { name: "셀트리온", sector: "바이오", stage: "Stage 2", vs: "+1.4%", weeks: "1", rs: "+2.1", angle: "완만", sub: "초기" },
    ],
    conditions: [],
    playbook: "Stage 1 → 2 돌파 + 섹터도 Stage 2일 때 진입. Stage 3 경고 시 익절. 손절 = SMA30 하향 이탈.",
    sideTitle: "4-Stage Life-Cycle",
    sideSubtitle: "전체 유니버스 분포",
  },
};
