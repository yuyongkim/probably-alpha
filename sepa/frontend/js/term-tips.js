import { txt } from './i18n.js?v=1775487695';

const TERM_DEFS = {
  alpha: {
    label: { ko: '알파(Alpha)', en: 'Alpha' },
    desc: {
      ko: '이동평균 정배열, 52주 저점 대비 이격, 52주 고점 근접도, 상대강도 등 미너비니 기본 추세 템플릿을 통과한 강도입니다.',
      en: 'Trend-template strength: moving-average alignment, 52-week proximity, and relative strength.',
    },
  },
  beta: {
    label: { ko: '베타(Beta)', en: 'Beta' },
    desc: {
      ko: '변동성 수축(VCP), 베이스 구조, 눌림의 질 등 차트 구조 신뢰도입니다.',
      en: 'Chart-structure confidence: volatility contraction, base quality, pullback health.',
    },
  },
  gamma: {
    label: { ko: '감마(Gamma)', en: 'Gamma' },
    desc: {
      ko: 'EPS 성장, EPS 가속, 관련 테마를 종합해 차트 해석을 보강하는 실적 점수입니다.',
      en: 'Fundamental reinforcement: EPS growth, EPS acceleration, and supporting context.',
    },
  },
  ret: {
    label: { ko: '120일 수익률', en: '120D Return' },
    desc: {
      ko: '최근 120영업일(약 6개월) 동안의 수익률입니다. 상대강도의 핵심 지표입니다.',
      en: 'Price return over the last 120 trading days (~6 months). Key relative strength measure.',
    },
  },
  leader: {
    label: { ko: '주도주 점수', en: 'Leader Score' },
    desc: {
      ko: 'Alpha, Beta, Gamma, 120일 수익률, 섹터 점수를 가중 합산한 종합 주도주 점수입니다.',
      en: 'Composite score combining Alpha, Beta, Gamma, 120D return, and sector leadership.',
    },
  },
  sector: {
    label: { ko: '섹터 점수', en: 'Sector Score' },
    desc: {
      ko: '섹터의 RS, Alpha 비율, Beta 비율, 돌파 근접도, 거래량 참여를 종합한 섹터 주도 점수입니다.',
      en: 'Sector leadership score from RS, Alpha/Beta breadth, breakout proximity, and volume participation.',
    },
  },
  rs: {
    label: { ko: '상대강도', en: 'R/S' },
    desc: {
      ko: '종목 또는 섹터가 KOSPI/KOSDAQ 지수 대비 얼마나 강한지 보여주는 지표입니다.',
      en: 'Relative strength versus KOSPI/KOSDAQ benchmark index.',
    },
  },
  eps: {
    label: { ko: 'EPS 상태', en: 'EPS Status' },
    desc: {
      ko: '분기 EPS의 성장 상태입니다. strong_growth > positive_growth > stable > mixed > negative 순입니다.',
      en: 'Quarterly EPS growth status. Ranks: strong_growth > positive_growth > stable > mixed > negative.',
    },
  },
  leastResistance: {
    label: { ko: '최소 저항', en: 'Least Resistance' },
    desc: {
      ko: '가격이 가장 쉽게 움직일 수 있는 방향입니다. up이면 공급이 흡수되고 있다는 뜻입니다.',
      en: 'Direction of easiest price movement. "Up" means supply is being absorbed.',
    },
  },
  rr: {
    label: { ko: '손익비', en: 'R/R Ratio' },
    desc: {
      ko: '손익비(Reward-to-Risk)입니다. 목표가까지 이익 대비 손절가까지 손실의 비율입니다.',
      en: 'Reward-to-Risk ratio: potential gain to target versus potential loss to stop.',
    },
  },
  conviction: {
    label: { ko: '확신도', en: 'Conviction' },
    desc: {
      ko: '확신도 등급입니다. A+=최고(강성장+최소저항상승), A=높음(60+), B=보통(50+), C=관찰.',
      en: 'Conviction level. A+=best (strong growth + up least resistance), A=high (60+), B=moderate (50+), C=watch.',
    },
  },
  recommendation: {
    label: { ko: '추천 점수', en: 'Reco Score' },
    desc: {
      ko: 'Alpha, Beta, Gamma, EPS 상태, 최소 저항 방향을 종합한 최종 추천 점수입니다.',
      en: 'Final recommendation score combining Alpha, Beta, Gamma, EPS status, and least resistance.',
    },
  },
  preset_score: {
    label: { ko: '프리셋 점수', en: 'Preset Score' },
    desc: {
      ko: '선택한 트레이더 철학의 가중치로 재계산한 점수입니다. 트레이더마다 다른 기준을 적용합니다.',
      en: 'Score recalculated using the selected trader philosophy weights.',
    },
  },
  sparkline: {
    label: { ko: '추이 차트', en: 'Sparkline' },
    desc: {
      ko: '최근 60일간 종가 추이를 보여주는 미니 차트입니다. 초록=상승, 빨강=하락.',
      en: 'Mini chart showing last 60 days of closing prices. Green=up, Red=down.',
    },
  },
  sector_breakout: {
    label: { ko: '돌파 상태', en: 'Breakout State' },
    desc: {
      ko: '섹터 돌파 상태입니다. Confirmed=돌파 확인, Setup=돌파 임박, Not ready=아직.',
      en: 'Sector breakout state. Confirmed=breakout confirmed, Setup=near breakout, Not ready=pending.',
    },
  },
  confirmed: {
    label: { ko: '주도 확정', en: 'Confirmed' },
    desc: {
      ko: '주도 섹터로 확정됨: 돌파 상태이거나 Alpha/Beta 비율이 50% 이상이고 고점 대비 -8% 이내.',
      en: 'Confirmed as leader sector: breakout state, or Alpha/Beta ratio >=50% and within -8% of high.',
    },
  },
  watchlist: {
    label: { ko: '관심 대상', en: 'Watchlist' },
    desc: {
      ko: '아직 주도 확정은 아니지만 Alpha 비율 20%+ 또는 돌파 점수 22%+로 감시 대상입니다.',
      en: 'Not yet confirmed but worth monitoring: Alpha ratio 20%+ or breakout score 22%+.',
    },
  },
  weekly_perf: {
    label: { ko: '주간 성과', en: 'Weekly Performance' },
    desc: {
      ko: '선택한 트레이더 프리셋으로 매주 재랭킹한 결과의 평균 점수 추이입니다.',
      en: 'Weekly average score trend from re-ranking with the selected trader preset.',
    },
  },
  mkt_cap: {
    label: { ko: '시가총액', en: 'Market Cap' },
    desc: {
      ko: '시가총액: 현재 주가 × 발행주식수. 단위는 억원(B) 또는 조원(T).',
      en: 'Market capitalization: current price × shares outstanding.',
    },
  },
  major_holder: {
    label: { ko: '대주주 비율', en: 'Major Holder' },
    desc: {
      ko: '최대주주 및 특수관계인 지분율입니다. 높을수록 경영권 안정.',
      en: 'Major shareholder and related party ownership ratio.',
    },
  },
};

function escHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

/**
 * Render a label with a native tooltip (title attribute).
 * Hover over the text to see the description — no ? button, no popup.
 */
export function termTip(key, labelOverride) {
  const def = TERM_DEFS[key];
  if (!def) return escHtml(labelOverride || key);
  const label = labelOverride || txt(def.label);
  const desc = txt(def.desc);
  return `<span class="term-tip" title="${escHtml(desc)}">${escHtml(label)}</span>`;
}

/**
 * No-op — kept for backwards compatibility so existing setupTermTips() calls don't break.
 */
export function setupTermTips() {}
