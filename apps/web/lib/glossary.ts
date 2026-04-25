// Plain-text glossary of jargon used across the platform.
// Wrap a term in <Term k="...">표시할 텍스트</Term> to attach a hover/tap
// tooltip that explains it.
//
// Style: 1-2 short sentences in Korean. Optional source attribution.
// Keep entries factual — no marketing prose.

export interface GlossaryEntry {
  /** Optional canonical label shown above body in the tooltip. Defaults to the key. */
  label?: string;
  /** Plain Korean explanation, 1-2 sentences. */
  body: string;
  /** Where the concept comes from (book/author/agency). Optional. */
  source?: string;
}

export const glossary: Record<string, GlossaryEntry> = {
  // ───── Trading patterns / philosophy ────────────────────────────────
  SEPA: {
    label: "SEPA — Specific Entry Point Analysis",
    body: "Mark Minervini가 정립한 성장주 매수 시점 분석법. Trend Template 8조건과 VCP 패턴을 결합해 진입 타이밍을 정한다.",
    source: "Trade Like a Stock Market Wizard, 2013",
  },
  "Trend Template": {
    label: "Trend Template (TT)",
    body: "Minervini의 8가지 추세 조건 (SMA50>150>200, 200일선 상승 등). 8개 중 5개 이상 통과해야 Alpha 통과로 본다.",
    source: "Minervini",
  },
  TT: {
    label: "TT — Trend Template",
    body: "Minervini의 8가지 추세 조건. 'TT 8/8'은 8개 모두 통과 의미.",
    source: "Minervini",
  },
  VCP: {
    label: "VCP — Volatility Contraction Pattern",
    body: "주가 변동성과 거래량이 점진적으로 줄어드는 수축 패턴. 신고가 돌파 직전의 전형적 베이스 형태.",
    source: "Minervini",
  },
  RS: {
    label: "RS — Relative Strength",
    body: "동일 기간 시장 대비 종목의 상대 강도. 보통 상위 30% (RS>=70) 이상을 주도주 후보로 본다.",
    source: "O'Neil, Minervini",
  },
  CANSLIM: {
    label: "CANSLIM",
    body: "William O'Neil의 7가지 매수 기준 (Current EPS, Annual EPS, New product, Supply/demand, Leader, Institutional, Market direction).",
    source: "How to Make Money in Stocks, 1988",
  },
  "Darvas Box": {
    label: "Darvas Box",
    body: "Nicolas Darvas의 박스권 돌파 매매. 주가가 박스 상단을 거래량과 함께 돌파할 때 진입.",
    source: "How I Made $2,000,000 in the Stock Market",
  },
  Stage: {
    label: "Weinstein Stage",
    body: "Stan Weinstein의 4단계 사이클 (1=바닥/축적, 2=상승, 3=고점/분배, 4=하락). 2단계 진입 종목만 매수.",
    source: "Secrets for Profiting in Bull and Bear Markets",
  },

  // ───── Quant / value ratios ─────────────────────────────────────────
  "Magic Formula": {
    body: "Joel Greenblatt의 종목 선정법. 자본수익률(ROIC)과 이익수익률(EBIT/EV)을 함께 상위로 랭크.",
    source: "The Little Book That Beats the Market, 2005",
  },
  "Piotroski F-Score": {
    label: "Piotroski F-Score",
    body: "9개 재무지표 (수익성·레버리지·운영효율) 합산 점수. 8-9점이면 펀더멘털 양호.",
    source: "Piotroski 2000",
  },
  "Altman Z-Score": {
    label: "Altman Z-Score",
    body: "기업 부도 가능성 예측 모델. Z<1.81 = 위험, Z>2.99 = 안전 영역.",
    source: "Altman 1968",
  },
  "Fama-French": {
    label: "Fama-French Factor Model",
    body: "주식 수익률을 시장(MKT)·소형주(SMB)·가치주(HML) 등 팩터로 설명하는 모델. 3-factor가 1993, 5-factor가 2015.",
    source: "Fama & French, JFE 1993 / 2015",
  },
  QMJ: {
    label: "QMJ — Quality Minus Junk",
    body: "Asness·Frazzini·Pedersen의 품질 팩터. 수익성·성장성·안정성·배당 우량 종목 매수, 그 반대 매도.",
    source: "AQR 2013",
  },
  DCF: {
    label: "DCF — Discounted Cash Flow",
    body: "미래 잉여현금흐름(FCF)을 자본비용으로 할인해 기업 내재가치를 산출.",
  },
  WACC: {
    label: "WACC — Weighted Average Cost of Capital",
    body: "자기자본비용과 부채비용을 자본구조로 가중평균한 자본비용. DCF의 할인율로 사용.",
  },
  ROIC: {
    label: "ROIC — Return on Invested Capital",
    body: "투하자본 대비 영업이익 비율. 사업 자체의 수익성 지표 (ROE의 상위 개념).",
  },
  ROE: {
    label: "ROE — Return on Equity",
    body: "자기자본 대비 순이익. 주주 자본을 얼마나 효율적으로 굴리는지.",
  },
  PER: {
    label: "PER — Price-to-Earnings Ratio",
    body: "주가 / 주당순이익. 낮을수록 저평가지만 산업·성장률 보정 필요.",
  },
  PBR: {
    label: "PBR — Price-to-Book Ratio",
    body: "주가 / 주당순자산. 1배 미만이면 청산가치 이하.",
  },
  PEG: {
    label: "PEG — PER ÷ Growth",
    body: "PER을 EPS 성장률로 나눈 값. Lynch는 1배 이하를 매력 영역으로 봤다.",
    source: "Peter Lynch",
  },
  "EV/EBITDA": {
    label: "EV/EBITDA",
    body: "기업가치(시총+순부채) ÷ 영업현금흐름. 자본구조 영향을 배제한 밸류에이션.",
  },
  EPS: {
    label: "EPS — Earnings Per Share",
    body: "주당 순이익. EPS YoY (전년 대비) 성장률이 +25% 이상이면 SEPA Alpha 통과 기준.",
  },
  FCF: {
    label: "FCF — Free Cash Flow",
    body: "영업현금흐름 − CapEx. DCF의 입력값.",
  },
  Moat: {
    label: "Economic Moat — 경제적 해자",
    body: "경쟁사가 쉽게 뺏을 수 없는 지속 경쟁우위. 5가지 원천: 비용우위·전환비용·네트워크 효과·무형자산·규모.",
    source: "Morningstar / Buffett",
  },

  // ───── 데이터 소스 ──────────────────────────────────────────────────
  KIS: {
    label: "KIS — 한국투자증권 OpenAPI",
    body: "국내 상장 종목 시세·호가·체결·계좌 주문을 위한 공식 REST + WebSocket API.",
  },
  DART: {
    label: "DART — 전자공시시스템",
    body: "금융감독원이 운영하는 상장사 공시 시스템. 정기보고서·주요사항보고서 등 PIT 재무 원천.",
  },
  FnGuide: {
    label: "FnGuide",
    body: "한국 상장사 재무·컨센서스·차트 데이터 제공. 모바일/웹 스냅샷이 본 플랫폼의 보조 소스.",
  },
  BOK: {
    label: "한국은행 (Bank of Korea)",
    body: "통화신용정책보고서·경제전망보고서·국제경제리뷰 등 공식 거시 보고서 발간 기관.",
  },
  ECOS: {
    label: "ECOS — Economic Statistics System",
    body: "한국은행 운영 거시통계 API. 환율·기준금리·통화량·국제수지 시계열 제공.",
  },
  FRED: {
    label: "FRED — Federal Reserve Economic Data",
    body: "미국 세인트루이스 연준 운영 거시 시계열 DB. 80만 개 시리즈, 정부·국제기구 데이터 통합.",
  },
  KOSIS: {
    label: "KOSIS — 국가통계포털",
    body: "통계청 운영 한국 거시 통계 API. 인구·고용·물가·소득 등.",
  },
  EIA: {
    label: "EIA — U.S. Energy Information Administration",
    body: "미국 에너지부 산하 통계청. 유가·재고·생산량 시계열 공식 출처.",
  },
  EXIM: {
    label: "EXIM — 한국수출입은행",
    body: "공시 환율 API 제공. KRW/USD 등 주요 통화 매매 기준율.",
  },

  // ───── 시장 / 거래 ──────────────────────────────────────────────────
  KOSPI: {
    label: "KOSPI — Korea Composite Stock Price Index",
    body: "한국거래소 유가증권시장 종합지수. 대형주 위주.",
  },
  KOSDAQ: {
    label: "KOSDAQ — 코스닥",
    body: "한국거래소 코스닥시장 지수. 중소·기술주 위주.",
  },
  ETF: {
    label: "ETF — Exchange-Traded Fund",
    body: "거래소에서 주식처럼 사고파는 펀드. KODEX·TIGER·ACE 등 운용사가 발행.",
  },
  OHLCV: {
    label: "OHLCV — Open/High/Low/Close/Volume",
    body: "일봉 5요소: 시가·고가·저가·종가·거래량. 본 플랫폼의 원천 시세 데이터 단위.",
  },
  PIT: {
    label: "PIT — Point-in-Time",
    body: "공시 시점 기준의 재무 데이터. 백테스트에서 미래정보 누출 (look-ahead bias)을 막는 핵심 개념.",
  },
  CapEx: {
    label: "CapEx — Capital Expenditure",
    body: "유·무형자산 투자액. 설비/공장/소프트웨어 등 미래 수익원 확보를 위한 지출.",
  },
  EBITDA: {
    body: "이자·세금·감가상각 차감 전 이익. 자본구조·세제와 무관한 영업 현금창출력 근사치.",
  },
  HBM: {
    label: "HBM — High Bandwidth Memory",
    body: "GPU·AI 가속기에 적층된 고대역폭 D램. SK하이닉스·삼성전자가 주요 공급사.",
  },

  // ───── 기술 ─────────────────────────────────────────────────────────
  RAG: {
    label: "RAG — Retrieval-Augmented Generation",
    body: "LLM이 답하기 전 외부 지식베이스에서 관련 청크를 검색해 컨텍스트로 주입하는 구조. 환각을 줄이고 출처를 명시 가능.",
  },
  "BGE-M3": {
    label: "BGE-M3",
    body: "BAAI 다국어 임베딩 모델 (568M, 1024-dim). 한↔영 혼합 검색에서 OpenAI ada-002와 동급.",
    source: "BAAI 2024",
  },
  TFIDF: {
    label: "TF-IDF",
    body: "단어 빈도(TF)와 역문서빈도(IDF)를 곱한 통계 기반 가중치. 키워드 매칭에 강하고 비용이 0원.",
  },

  // ───── 거시 / 정책 ──────────────────────────────────────────────────
  "기준금리": {
    body: "한국은행이 정하는 정책금리. 콜금리·예금금리·대출금리에 모두 영향.",
  },
  CPI: {
    label: "CPI — Consumer Price Index",
    body: "소비자물가지수. 가구가 일상적으로 구매하는 재화·서비스 가격 변화를 추적.",
  },
  YoY: {
    label: "YoY — Year over Year",
    body: "전년 동기 대비 증감률. 계절성을 제거한 기본 비교 지표.",
  },
  QoQ: {
    label: "QoQ — Quarter over Quarter",
    body: "전분기 대비. 단기 추세 확인에 사용.",
  },
};
