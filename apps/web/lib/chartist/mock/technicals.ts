// Technicals · short / kiwoom / candlestick / divergence / ichimoku / vprofile.
// Grouped because each section is small and they share the same consumption
// pattern (a summary row + a rows table).

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
