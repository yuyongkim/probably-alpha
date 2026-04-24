// Ops mocks · failed / watchlist / journal / playbook / backtest.

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
// Backtest (summary only — detailed run data is served live)
// ---------------------------------------------------------------------------
export const BACKTEST_SUMMARY = [
  { label: "CAGR", value: "23.4%", delta: "3년 평균", tone: "pos" as const },
  { label: "MDD", value: "−19.1%", delta: "2023 Q3", tone: "neg" as const },
  { label: "Sharpe", value: "1.38", delta: "vs KOSPI 0.42", tone: "pos" as const },
  { label: "Win Rate", value: "58.4%", delta: "217 trades" },
];
