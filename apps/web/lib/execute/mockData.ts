// Mock data for Execute pages — KIS keys absent, so all 17+ subsections are static.
// Numbers mirror the integration mockup so the dense layout renders 100%.
import type {
  AllocationBar,
  Fill,
  LiveQuote,
  LogEntry,
  Position,
  RiskMetric,
  SafetyRail,
  Scenario,
} from "@/types/execute";

export const overviewKpis = [
  { label: "Account Value", value: "₩48,720,410", delta: "+₩1,842,300 · +3.9% Today", tone: "pos" as const },
  { label: "Unrealized P&L", value: "+₩4,218,700", delta: "+9.48% · 평가손익", tone: "pos" as const },
  { label: "YTD Return", value: "+14.2%", delta: "vs KOSPI +8.1%", tone: "pos" as const },
  { label: "Open Positions", value: "12", delta: "KR 9 · US 3 · 미체결 2" },
  { label: "Live Strategies", value: "3 / 5", delta: "2 paused · 0 fault", tone: "pos" as const },
  { label: "KIS Link", value: "● Live", delta: "WS 12ms · 47 sym", tone: "pos" as const },
];

export const overviewMarketCells = [
  { label: "총자산", value: "₩48,720,410", delta: "+3.9%", tone: "pos" as const },
  { label: "예수금", value: "₩4,284,120", delta: "D+2 결제" },
  { label: "매수가능", value: "₩4,184,500", delta: "현금 100%" },
  { label: "증거금", value: "18.4%", delta: "여유 81.6%", tone: "pos" as const },
  { label: "신용한도", value: "₩12,000,000", delta: "미사용" },
  { label: "외화 (USD)", value: "$2,140.80", delta: "+$84 Today", tone: "pos" as const },
  { label: "VaR 95% 1D", value: "₩−742K", delta: "−1.52%" },
  { label: "Today Orders", value: "7 / 9", delta: "체결 78%", tone: "pos" as const },
];

export const positions: Position[] = [
  { ticker: "한미반도체", code: "042700", market: "KR", qty: 30, avg: "118,200", last: "134,500", pnl: "+489K", pct: "+13.8%", change1d: "+3.67", stop: "108,000", target: "162,000", strategy: "SEPA v1", strategyTone: "accent", hold: "18d", tone: "pos" },
  { ticker: "SK하이닉스", code: "000660", market: "KR", qty: 15, avg: "178,500", last: "192,100", pnl: "+204K", pct: "+7.6%", change1d: "+2.34", stop: "165,000", target: "228,000", strategy: "SEPA v1", strategyTone: "accent", hold: "12d", tone: "pos" },
  { ticker: "삼성전자", code: "005930", market: "KR", qty: 50, avg: "72,800", last: "75,400", pnl: "+130K", pct: "+3.6%", change1d: "+1.88", stop: "68,500", target: "84,000", strategy: "QK Top20", hold: "28d", tone: "pos" },
  { ticker: "두산에너빌리티", code: "034020", market: "KR", qty: 40, avg: "22,840", last: "25,820", pnl: "+119K", pct: "+13.0%", change1d: "+3.28", stop: "21,200", target: "31,000", strategy: "SEPA v1", strategyTone: "accent", hold: "22d", tone: "pos" },
  { ticker: "NVIDIA", code: "NVDA", market: "US", qty: 8, avg: "$128.40", last: "$142.18", pnl: "+$110", pct: "+10.7%", change1d: "+1.82", stop: "$118", target: "$172", strategy: "Mag7 Mo", hold: "42d", tone: "pos" },
  { ticker: "HPSP", code: "403870", market: "KR", qty: 12, avg: "28,420", last: "31,200", pnl: "+33K", pct: "+9.8%", change1d: "+4.21", stop: "26,500", target: "38,500", strategy: "SEPA v1", strategyTone: "accent", hold: "8d", tone: "pos" },
  { ticker: "Microsoft", code: "MSFT", market: "US", qty: 4, avg: "$412.80", last: "$428.40", pnl: "+$62", pct: "+3.8%", change1d: "+0.84", stop: "$392", target: "$484", strategy: "Mag7 Mo", hold: "42d", tone: "pos" },
  { ticker: "리노공업", code: "058470", market: "KR", qty: 2, avg: "218,400", last: "224,800", pnl: "+13K", pct: "+2.9%", change1d: "+2.14", stop: "204,000", target: "268,000", strategy: "SEPA v1", strategyTone: "accent", hold: "3d", tone: "pos" },
  { ticker: "KT&G", code: "033780", market: "KR", qty: 20, avg: "91,200", last: "93,700", pnl: "+50K", pct: "+2.7%", change1d: "+0.48", stop: "86,000", target: "124,000", strategy: "Value DCF", hold: "64d", tone: "pos" },
  { ticker: "Alphabet", code: "GOOGL", market: "US", qty: 5, avg: "$158.20", last: "$154.80", pnl: "−$17", pct: "−2.1%", change1d: "−0.42", stop: "$148", target: "$182", strategy: "Mag7 Mo", hold: "42d", tone: "neg" },
  { ticker: "포스코퓨처엠", code: "003670", market: "KR", qty: 8, avg: "248,000", last: "238,400", pnl: "−77K", pct: "−3.9%", change1d: "+0.84", stop: "224,000", target: "294,000", strategy: "QK Top20", hold: "15d", tone: "neg" },
  { ticker: "에코프로비엠", code: "247540", market: "KR", qty: 20, avg: "218,000", last: "204,500", pnl: "−270K", pct: "−6.2%", change1d: "−1.84", stop: "198,000", target: "252,000", strategy: "Watch", strategyTone: "amber", hold: "24d", tone: "neg" },
];

export const liveQuotes: LiveQuote[] = [
  { sym: "042700", last: "134,500", chg: "+4,750", vol: "3.8M", bid: "134,400", ask: "134,500", arrow: "▲", tone: "pos" },
  { sym: "000660", last: "192,100", chg: "+4,400", vol: "12.4M", bid: "192,000", ask: "192,100", arrow: "▲", tone: "pos" },
  { sym: "005930", last: "75,400", chg: "+1,400", vol: "28.7M", bid: "75,300", ask: "75,400", arrow: "▲", tone: "pos" },
  { sym: "034020", last: "25,820", chg: "+820", vol: "8.4M", bid: "25,800", ask: "25,820", arrow: "▲", tone: "pos" },
  { sym: "403870", last: "31,200", chg: "+1,260", vol: "2.1M", bid: "31,150", ask: "31,200", arrow: "▲", tone: "pos" },
  { sym: "058470", last: "224,800", chg: "+4,700", vol: "420K", bid: "224,500", ask: "224,800", arrow: "▲", tone: "pos" },
  { sym: "033780", last: "93,700", chg: "+450", vol: "1.8M", bid: "93,600", ask: "93,700", arrow: "▲", tone: "pos" },
  { sym: "003670", last: "238,400", chg: "+2,000", vol: "540K", bid: "238,200", ask: "238,400", arrow: "▲", tone: "pos" },
  { sym: "247540", last: "204,500", chg: "−3,800", vol: "1.2M", bid: "204,400", ask: "204,500", arrow: "▼", tone: "neg" },
  { sym: "007660", last: "84,200", chg: "+4,620", vol: "4.1M", bid: "84,100", ask: "84,200", arrow: "▲", tone: "pos" },
  { sym: "NVDA", last: "$142.18", chg: "+$2.54", vol: "184M", bid: "$142.17", ask: "$142.19", arrow: "▲", tone: "pos" },
  { sym: "MSFT", last: "$428.40", chg: "+$3.58", vol: "24M", bid: "$428.38", ask: "$428.42", arrow: "▲", tone: "pos" },
  { sym: "GOOGL", last: "$154.80", chg: "−$0.65", vol: "32M", bid: "$154.78", ask: "$154.82", arrow: "▼", tone: "neg" },
];

export const assetAllocation: AllocationBar[] = [
  { label: "국내주식", pct: 68, pctLabel: "68.4%", color: "#1B4332" },
  { label: "해외주식", pct: 18, pctLabel: "18.2%", color: "#7FA88A" },
  { label: "현금/MMF", pct: 9, pctLabel: "8.8%", color: "#B08968" },
  { label: "선물/옵션", pct: 3, pctLabel: "2.8%", color: "#D4CFC4" },
  { label: "채권", pct: 2, pctLabel: "1.8%", color: "#D4CFC4" },
];

export const sectorAllocation: AllocationBar[] = [
  { label: "반도체", pct: 42, pctLabel: "42.1%", color: "#2D6A4F" },
  { label: "원전", pct: 12, pctLabel: "12.4%", color: "#7FA88A" },
  { label: "2차전지", pct: 11, pctLabel: "11.2%", color: "#B4CBB8" },
  { label: "US 빅테크", pct: 18, pctLabel: "18.2%", color: "#B08968" },
  { label: "필수", pct: 4, pctLabel: "3.8%", color: "#D4CFC4" },
];

export const strategyAllocation: AllocationBar[] = [
  { label: "SEPA v1", pct: 48, pctLabel: "48.2%", color: "#1B4332" },
  { label: "QK Top20", pct: 14, pctLabel: "14.8%", color: "#7FA88A" },
  { label: "Mag7 Mo", pct: 18, pctLabel: "18.2%", color: "#B4CBB8" },
  { label: "Value DCF", pct: 4, pctLabel: "3.8%", color: "#B08968" },
  { label: "Discretionary", pct: 6, pctLabel: "5.8%", color: "#D4CFC4" },
  { label: "Cash", pct: 9, pctLabel: "8.8%", color: "#E6E2DB" },
];

export const recentFills: Fill[] = [
  { time: "15:24:18", side: "BUY", ticker: "한미반도체", qty: 5, price: "133,800", amount: "669,000", venue: "KOSDAQ", strategy: "SEPA v1", strategyTone: "accent" },
  { time: "14:58:42", side: "BUY", ticker: "리노공업", qty: 2, price: "222,000", amount: "444,000", venue: "KOSDAQ", strategy: "SEPA v1", strategyTone: "accent" },
  { time: "13:42:07", side: "SELL", ticker: "에코프로비엠", qty: 5, price: "205,200", amount: "1,026,000", venue: "KOSDAQ", strategy: "Stop Trim", strategyTone: "amber" },
  { time: "11:24:54", side: "BUY", ticker: "두산에너빌리티", qty: 10, price: "25,340", amount: "253,400", venue: "KOSPI", strategy: "SEPA v1", strategyTone: "accent" },
  { time: "10:18:22", side: "BUY", ticker: "SK하이닉스", qty: 3, price: "189,600", amount: "568,800", venue: "KOSPI", strategy: "SEPA v1", strategyTone: "accent" },
  { time: "09:04:18", side: "BUY", ticker: "NVIDIA", qty: 2, price: "$140.20", amount: "$280.40", venue: "NASDAQ", strategy: "Mag7 Mo" },
  { time: "09:02:44", side: "BUY", ticker: "삼성전자", qty: 10, price: "74,800", amount: "748,000", venue: "KOSPI", strategy: "QK Top20" },
];

export const riskMetrics: RiskMetric[] = [
  { metric: "VaR 95% · 1D", value: "−₩742K", status: "OK", statusTone: "pos", limit: "−₩1.5M", valueTone: "neg" },
  { metric: "VaR 99% · 1D", value: "−₩1.24M", status: "OK", statusTone: "pos", limit: "−₩2.4M", valueTone: "neg" },
  { metric: "CVaR 95% · 1D", value: "−₩1.08M", status: "OK", statusTone: "pos", limit: "−₩2.0M", valueTone: "neg" },
  { metric: "Portfolio β", value: "1.18", status: "Mod", statusTone: "default", limit: "≤ 1.3" },
  { metric: "섹터 집중도 · 반도체", value: "42.1%", status: "High", statusTone: "amber", limit: "≤ 40%" },
  { metric: "Max Single · 한미반도체", value: "8.4%", status: "OK", statusTone: "pos", limit: "≤ 15%" },
  { metric: "최대 종목당 손실", value: "−0.78%", status: "OK", statusTone: "pos", limit: "≤ 1% (acct)" },
  { metric: "Rolling MDD · 30D", value: "−4.8%", status: "OK", statusTone: "pos", limit: "≤ −10%", valueTone: "neg" },
  { metric: "Kelly Criterion", value: "0.34", status: "Sub-1/4", statusTone: "default", limit: "—" },
  { metric: "증거금 사용률", value: "18.4%", status: "OK", statusTone: "pos", limit: "≤ 60%" },
];

export const activityLog: LogEntry[] = [
  { time: "15:24:18", tag: "FILL", tagClass: "buy", sym: "042700", symLabel: "한미반도체", msg: "5주 매수 체결 · 133,800 · SEPA v1 size up" },
  { time: "15:18:42", tag: "STOP", tagClass: "alert", sym: "247540", symLabel: "에코프로비엠", msg: "−6.2% · Stop 198,000 근접 (−3.2%) · 주시" },
  { time: "14:58:42", tag: "FILL", tagClass: "buy", sym: "058470", symLabel: "리노공업", msg: "2주 신규 진입 · SEPA TT 7/8 + VCP Stage 3" },
  { time: "14:42:18", tag: "RISK", tagClass: "alert", msg: "반도체 섹터 42.1% > 40% 한도 · 리밸런스 권고" },
  { time: "13:42:07", tag: "FILL", tagClass: "sell", sym: "247540", symLabel: "에코프로비엠", msg: "5주 매도 · 205,200 · Partial trim (25%)" },
  { time: "13:38:24", tag: "SYS", tagClass: "sys", msg: "QK Top20 리밸런스 시그널 · 삼성전자 ADD · 신풍제약 DROP" },
  { time: "11:24:54", tag: "FILL", tagClass: "buy", sym: "034020", symLabel: "두산에너빌리티", msg: "10주 추가 매수 · 25,340 · Pyramid #2" },
  { time: "10:18:22", tag: "FILL", tagClass: "buy", sym: "000660", symLabel: "SK하이닉스", msg: "3주 매수 · HBM3E 가이던스 반영" },
  { time: "09:14:08", tag: "SYS", tagClass: "sys", msg: "전략 SEPA AutoPick v1 · 오늘 시그널 3건 · 모두 size within limit" },
  { time: "09:08:42", tag: "DART", tagClass: "alert", sym: "005380", symLabel: "현대차", msg: "자사주 1조 소각 공시 · DCF FV +4.8% 재계산 예약" },
  { time: "09:02:44", tag: "FILL", tagClass: "buy", sym: "005930", symLabel: "삼성전자", msg: "10주 매수 · 74,800 · QK Top20 월간 리밸" },
  { time: "09:00:12", tag: "SYS", tagClass: "sys", msg: "KIS WebSocket 연결 · 47 심볼 구독 · 12ms p95" },
  { time: "08:52:08", tag: "SYS", tagClass: "sys", msg: "Mag7 Mo 전략 · US 프리마켓 +0.8% · 개장 후 3건 BUY 예정" },
  { time: "04-21 21:04", tag: "SYS", tagClass: "sys", msg: "야간 배치 · SEPA pass 142 · DCF 재계산 12 · FDD clean 98.4%" },
  { time: "04-21 18:30", tag: "STRAT", tagClass: "alert", msg: "US Mag7 Momentum 전략 재개 (PAUSED → LIVE) · 지연시간 우려 해소" },
];

export const aiPrompts: string[] = [
  "내 포지션 중 stop-loss 조건 맞는 것 찾아서 시장가로 정리해줘",
  "반도체 섹터 비중을 35%까지 줄이는 리밸런스 플랜 제시",
  "오늘 체결된 주문 중 내 SEPA 규칙 어긴 것 있는지 감사",
  "내 계좌 전체 내일 예정 배당/공시/실적 이벤트 요약",
];

export const mcpTradeKpis = [
  { label: "MCP 세션 상태", value: "● Active", delta: "OAuth valid 13h", tone: "pos" as const },
  { label: "오늘 AI 주문", value: "4", delta: "모두 성공", tone: "pos" as const },
  { label: "오늘 AI 조회", value: "142", delta: "시세/잔고/체결" },
  { label: "주문 한도 (건당)", value: "계좌 20%", delta: "Safety Rail", tone: "pos" as const },
  { label: "확인 필요 주문", value: "2", delta: "대기 중", tone: "amber" as const },
  { label: "30D AI 성과", value: "+8.2%", delta: "vs 직접 +6.4%", tone: "pos" as const },
];

export const scenarios: Scenario[] = [
  { name: "손절 자동 정리", trigger: "Stop hit", action: "SELL 시장가", actionTone: "neg", safety: "No confirm", safetyTone: "pos" },
  { name: "신호 통과 자동 진입", trigger: "TT 8/8 + VCP", action: "BUY TWAP 30m", actionTone: "pos", safety: ">5% 시 확인", safetyTone: "amber" },
  { name: "익절 분할", trigger: "+15% 도달", action: "1/3 매도", actionTone: "pos", safety: "No confirm", safetyTone: "pos" },
  { name: "Wizards 통과 Top3 진입", trigger: "매일 15:20", action: "각 5% BUY", actionTone: "pos", safety: "시장 확인", safetyTone: "amber" },
  { name: "섹터 순위 역전 청산", trigger: "섹터 Top1 → Top5 하락", action: "해당 종목 청산", actionTone: "neg", safety: "확인", safetyTone: "amber" },
  { name: "공매도 과열 회피", trigger: "공매도 잔고 10%↑", action: "진입 보류", actionTone: "default", safety: "No order", safetyTone: "pos" },
  { name: "실적 직전 청산", trigger: "T-1 (실적 전일)", action: "이벤트 리스크 회피", actionTone: "neg", safety: "확인", safetyTone: "amber" },
  { name: "Rebalance 주기", trigger: "매주 금요일 15:20", action: "목표 비중 조정", actionTone: "default", safety: "요약 후 확인", safetyTone: "amber" },
  { name: "외화 자동 환전 + 주문", trigger: "US/JP 진입 신호", action: "환전 → BUY", actionTone: "pos", safety: "환율 스프레드 확인", safetyTone: "amber" },
  { name: "연말 세제 정리", trigger: "12월 특정 주간", action: "손실 종목 매도", actionTone: "neg", safety: "확인", safetyTone: "amber" },
  { name: "VKOSPI 급등 시 축소", trigger: "VKOSPI > 25", action: "포지션 −30%", actionTone: "neg", safety: "확인", safetyTone: "amber" },
  { name: "대량 매매 감지", trigger: "종목 블록딜", action: "알림 + 분석", actionTone: "default", safety: "No order", safetyTone: "pos" },
];

export const mcpActivity: LogEntry[] = [
  { time: "15:28:42", tag: "AI·BUY", tagClass: "buy", msg: "\"한미반도체 VCP 돌파 · 계좌 5% 진입\" → FILLED 30주 @ 134,500" },
  { time: "15:24:18", tag: "CONFIRM", tagClass: "alert", msg: "\"에코프로비엠 손절 조건 확인\" → 사용자 승인 대기 (20주 청산)" },
  { time: "15:12:04", tag: "AI·SELL", tagClass: "sell", msg: "\"HPSP 목표가 도달 · 1/3 익절\" → FILLED 4주 @ 31,200" },
  { time: "14:58:21", tag: "DENIED", tagClass: "sys", msg: "\"에코프로 공매도 과열 · 진입 보류\" → Safety Rail 발동" },
  { time: "14:42:08", tag: "QUERY", tagClass: "sys", msg: "\"내 포지션 중 Stop 근처인 것\" → 답변: 에코프로비엠 (−1.8% from Stop)" },
  { time: "13:18:52", tag: "AI·BUY", tagClass: "buy", msg: "\"두산에너빌리티 Base 돌파 + Vol 2× · TWAP 30m\" → FILLED 50주 avg 21,820" },
  { time: "11:24:14", tag: "QUERY", tagClass: "sys", msg: "\"오늘 US 신호 중 한국 공급망 연결 종목\" → 답변: NVDA·AVGO 상위 + 한미/SK하이닉스 동반" },
  { time: "10:42:08", tag: "CONFIRM", tagClass: "alert", msg: "\"Mag7 Momentum 전략 리밸런싱 초안\" → 사용자 확인 후 진행" },
  { time: "09:18:42", tag: "SYS", tagClass: "sys", msg: "MCP 세션 갱신 · OAuth token 13h valid" },
];

export const safetyRails: SafetyRail[] = [
  { idx: "①", label: "건당 주문 ≤ 계좌 20%", pct: "Hard", fill: 100 },
  { idx: "②", label: "일일 총 주문 ≤ 계좌 50%", pct: "Hard", fill: 100 },
  { idx: "③", label: "신규 진입 → 사용자 확인", pct: "5% 초과", fill: 80, color: "amber" },
  { idx: "④", label: "손절 매도 → 자동 (No confirm)", pct: "Auto", fill: 100 },
  { idx: "⑤", label: "익절 매도 → 자동", pct: "Auto", fill: 100 },
  { idx: "⑥", label: "VKOSPI > 30 → 신규 진입 금지", pct: "Hard", fill: 100 },
  { idx: "⑦", label: "신용/대주 거래 → 영구 차단", pct: "Hard", fill: 100 },
  { idx: "⑧", label: "선물옵션 → 사용자 확인 필수", pct: "Always", fill: 100 },
  { idx: "⑨", label: "감사 로그 전량 기록", pct: "Always", fill: 100 },
  { idx: "⑩", label: "비정상 패턴 감지 시 차단", pct: "Auto", fill: 100 },
];

export const mcpAskExamples: string[] = [
  "\"보유 포지션 중 손절 조건 맞는 것 자동 정리\"",
  "\"오늘 Wizards 6/6 통과 종목 중 상위 3개 각 5% 진입\"",
  "\"Mag7 중 Base 돌파한 거 있으면 TWAP 30분 매수\"",
  "\"내일 SK하이닉스 실적 발표 · 포지션 반 청산해줘\"",
  "\"VKOSPI 20 돌파 시 전 포지션 30% 축소 자동 세팅\"",
  "\"KIS Backtester로 Magic Formula 재검증 후 Live 전환\"",
  "\"이번주 체결 내역 요약 + 매매일지 초안 작성\"",
];
