// Tab → sidebar structure. Each tab has an ordered list of groups, each group
// has a label + ordered links. Port of the mockup's .sidebar-group blocks.
// `href` is resolved against the existing Next.js routes; undefined href → "#".
// `sub: true` renders the link with the mockup's └ gutter.
// `count` renders the monospace badge chip.

export interface SidebarLink {
  label: string;
  href?: string;
  count?: number | string;
  sub?: boolean;
}
export interface SidebarGroup {
  label: string;
  links: SidebarLink[];
}

type TabKey =
  | "chartist"
  | "quant"
  | "value"
  | "execute"
  | "research"
  | "admin";

export const SIDEBAR_MAP: Record<TabKey, SidebarGroup[]> = {
  chartist: [
    {
      label: "Chartist · Daily",
      links: [
        { label: "오늘의 주도주", href: "/chartist/today", count: 24 },
      ],
    },
    {
      label: "Scan",
      links: [
        { label: "Leader 전체", href: "/chartist/leaders", count: 142 },
        { label: "섹터 강도", href: "/chartist/sectors", count: 28 },
        { label: "Breadth Monitor", href: "/chartist/breadth" },
        { label: "52주 신고가 돌파", href: "/chartist/breakouts" },
        { label: "실패 돌파 로그" },
      ],
    },
    {
      label: "Market Wizards",
      links: [
        { label: "Market Wizards (개요)", href: "/chartist/wizards" },
        { label: "Minervini · SEPA", sub: true, count: 24 },
        { label: "O'Neil · CANSLIM", sub: true, count: 17 },
        { label: "Darvas · Box", sub: true, count: 9 },
        { label: "Livermore · Pivot", sub: true, count: 12 },
        { label: "Zanger · Gap+Vol", sub: true, count: 6 },
        { label: "Weinstein · Stage 2", sub: true, count: 21 },
      ],
    },
    {
      label: "Global (KIS 해외시세)",
      links: [
        { label: "US Leaders (S&P/NDX)" },
        { label: "JP Leaders (닛케이)" },
        { label: "HK / CN Leaders" },
        { label: "Global Wizards (5 시장)" },
      ],
    },
    {
      label: "한국 시장",
      links: [
        { label: "수급 대시보드" },
        { label: "테마 로테이션", count: 20 },
        { label: "공매도 / 대차" },
        { label: "키움 조건식", count: 7 },
      ],
    },
    {
      label: "Technicals",
      links: [
        { label: "VCP / Base 패턴" },
        { label: "캔들스틱", count: 57 },
        { label: "Divergence" },
        { label: "Ichimoku Cloud" },
        { label: "Volume Profile" },
        { label: "지지 / 저항" },
      ],
    },
    {
      label: "My Desk",
      links: [
        { label: "관심종목 + 알람", count: 38 },
        { label: "매매일지" },
        { label: "Playbook" },
      ],
    },
    {
      label: "Analysis",
      links: [
        { label: "SEPA 백테스트" },
        { label: "선정 히스토리" },
        { label: "트레이더 토론" },
      ],
    },
  ],

  quant: [
    {
      label: "Quant · Screener",
      links: [
        { label: "팩터 스크리너", href: "/quant/factors" },
        { label: "4 학술 전략", href: "/quant/academic", count: 4 },
        { label: "Smart Beta", href: "/quant/smartbeta", count: 6 },
        { label: "QuantKing 사용자정의" },
        { label: "유니버스", count: 2147 },
      ],
    },
    {
      label: "Macro",
      links: [
        { label: "Macro Compass", href: "/quant/macro" },
        { label: "Regime Detection (HMM)", href: "/quant/regime" },
        { label: "섹터 로테이션", href: "/quant/rotation" },
        { label: "매크로 시계열", href: "/quant/macroseries" },
        { label: "상관관계 히트맵", href: "/quant/corr" },
      ],
    },
    {
      label: "Strategies",
      links: [
        { label: "Pair Trading · Stat Arb" },
        { label: "Mean Reversion" },
        { label: "Cross-Asset Momentum" },
        { label: "Calendar Effects" },
      ],
    },
    {
      label: "ML & Alternative",
      links: [
        { label: "ML 팩터 (XGB/LSTM)" },
        { label: "Alternative Data" },
      ],
    },
    {
      label: "Fundamental",
      links: [
        { label: "PIT 재무 엔진", href: "/quant/pit" },
        { label: "Factor IC / IR 분석" },
      ],
    },
    {
      label: "Portfolio",
      links: [
        { label: "포트폴리오 빌더", href: "/quant/portfolio" },
        { label: "Risk Parity" },
        { label: "Minimum Variance" },
        { label: "Black-Litterman" },
        { label: "Kelly / 포지션 사이징" },
      ],
    },
    {
      label: "Backtest",
      links: [
        { label: "전략 백테스트" },
        { label: "워크포워드 (OOS)" },
        { label: "Monte Carlo" },
        { label: "실행 기록" },
        { label: "FDD 데이터 품질" },
      ],
    },
  ],

  value: [
    {
      label: "Value · Valuation",
      links: [
        { label: "DCF 모델", href: "/value/dcf", count: 47 },
        { label: "WACC 계산기", href: "/value/wacc" },
        { label: "재무 트렌드 차트", href: "/value/trend" },
        { label: "Margin of Safety", href: "/value/mos" },
      ],
    },
    {
      label: "Screeners",
      links: [
        { label: "Deep Value (P/B · PEG)", href: "/value/deepvalue" },
        { label: "EV / EBITDA", href: "/value/evebitda" },
        { label: "ROIC / FCF Yield", href: "/value/roic" },
        { label: "Magic Formula", href: "/value/magic" },
        { label: "Piotroski F-Score", href: "/value/piotroski" },
        { label: "Altman Z-Score", href: "/value/altman" },
        { label: "배당주 (성장/귀족)" },
        { label: "동종업계 비교" },
      ],
    },
    {
      label: "Quality & Moat",
      links: [
        { label: "경제적 해자" },
        { label: "사업부문 분석" },
      ],
    },
    {
      label: "Disclosure & Flow",
      links: [
        { label: "DART 공시 자동분석" },
        { label: "사업보고서 Q&A" },
        { label: "증권사 리포트" },
        { label: "내부자 거래 (DART)" },
        { label: "자사주 매입" },
        { label: "애널리스트 컨센서스" },
      ],
    },
    {
      label: "Data & Knowledge",
      links: [
        { label: "원자재 대시보드" },
        { label: "KOSIS 통계" },
        { label: "버핏 지식베이스" },
      ],
    },
  ],

  execute: [
    {
      label: "Execute · KIS",
      links: [
        { label: "계좌 Overview", href: "/execute/overview" },
        { label: "보유 포지션", count: 7 },
        { label: "주문 / 체결" },
        { label: "호가창 L2 + 체결강도" },
        { label: "알고리즘 주문 (TWAP/VWAP)" },
        { label: "WebSocket 실시간" },
      ],
    },
    {
      label: "자산군 (KIS 8 API)",
      links: [
        { label: "국내주식", count: 156 },
        { label: "해외주식 (미·일·홍·상·베)" },
        { label: "국내 선물옵션" },
        { label: "해외 선물옵션" },
        { label: "국내채권", count: 18 },
        { label: "ELW" },
        { label: "ETF / ETN" },
      ],
    },
    {
      label: "Strategy",
      links: [
        { label: "KIS Backtester", count: 10 },
        { label: "Strategy Builder" },
        { label: "배포 전략", count: 3 },
      ],
    },
    {
      label: "MCP · AI",
      links: [
        { label: "MCP — Code Assistant" },
        { label: "MCP — Trading" },
      ],
    },
    {
      label: "Risk",
      links: [
        { label: "모의투자" },
        { label: "증거금 / 리스크" },
      ],
    },
  ],

  research: [
    {
      label: "Papers & Academic",
      links: [
        { label: "논문 아카이브", href: "/research/papers", count: 842 },
        { label: "Fama-French · AQR", href: "/research/ffactor" },
        { label: "논문 재현 (Backtest)", href: "/research/reproduce" },
      ],
    },
    {
      label: "Ideas & Lab",
      links: [
        { label: "아이디어 랩", href: "/research/ideas" },
        { label: "Signal Lab (실험)", href: "/research/signallab" },
        { label: "Failed Strategies", href: "/research/graveyard" },
        { label: "AI Research Agent", href: "/research/airesearch" },
      ],
    },
    {
      label: "Market Intel",
      links: [
        { label: "뉴스 감성 분석", href: "/research/news" },
        { label: "한국 증권사 리포트", href: "/research/krreports" },
        { label: "주간 / 월간 시장 리뷰", href: "/research/review" },
        { label: "시장 사이클 사례", href: "/research/cycles" },
      ],
    },
    {
      label: "Knowledge",
      links: [
        { label: "Knowledge Base RAG", href: "/research/knowledge" },
        { label: "버핏 서한 21년", href: "/research/buffettletters" },
        { label: "블로그 아카이브", href: "/research/blogs" },
        { label: "트레이딩 심리", href: "/research/psychology" },
        { label: "Wizards 인터뷰", href: "/research/interviews" },
      ],
    },
  ],

  admin: [
    {
      label: "Admin · Ops",
      links: [
        { label: "시스템 상태", href: "/admin/status" },
        { label: "데이터 소스 헬스", href: "/admin/data" },
        { label: "파이프라인 Jobs", href: "/admin/pipeline" },
        { label: "FDD 알럿", href: "/admin/fddadmin" },
      ],
    },
    {
      label: "Security",
      links: [
        { label: "API 키 관리", href: "/admin/keys" },
        { label: "감사 로그", href: "/admin/audit" },
      ],
    },
    {
      label: "B2B Ready",
      links: [
        { label: "사용량 / 빌링", href: "/admin/billing" },
        { label: "테넌트", href: "/admin/tenants" },
      ],
    },
  ],
};

export function getTabFromPathname(pathname: string): TabKey | null {
  const seg = pathname.split("/").filter(Boolean)[0] as TabKey | undefined;
  if (!seg) return null;
  return seg in SIDEBAR_MAP ? seg : null;
}

export type { TabKey };
