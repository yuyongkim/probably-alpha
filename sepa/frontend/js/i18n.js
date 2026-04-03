const STORAGE_KEY = 'sepa.lang';
const SUPPORTED_LANGS = new Set(['ko', 'en']);

let currentLang = resolveInitialLang();

function resolveInitialLang() {
  const url = new URL(window.location.href);
  const queryLang = String(url.searchParams.get('lang') || '').trim().toLowerCase();
  if (SUPPORTED_LANGS.has(queryLang)) {
    window.localStorage.setItem(STORAGE_KEY, queryLang);
    return queryLang;
  }
  const stored = String(window.localStorage.getItem(STORAGE_KEY) || '').trim().toLowerCase();
  if (SUPPORTED_LANGS.has(stored)) return stored;
  return 'ko';
}

function pick(value) {
  if (value && typeof value === 'object' && !Array.isArray(value) && ('ko' in value || 'en' in value)) {
    return value[currentLang] ?? value.ko ?? value.en ?? '';
  }
  return value ?? '';
}

function setText(selector, value) {
  const node = document.querySelector(selector);
  if (node) node.textContent = String(pick(value));
}

function setAttr(selector, attr, value) {
  const node = document.querySelector(selector);
  if (node) node.setAttribute(attr, String(pick(value)));
}

function setMany(selector, values) {
  const nodes = document.querySelectorAll(selector);
  const resolved = pick(values);
  if (!Array.isArray(resolved)) return;
  nodes.forEach((node, index) => {
    if (resolved[index] != null) node.textContent = String(resolved[index]);
  });
}

function setTableHeaders(tbodyId, values) {
  const body = document.getElementById(tbodyId);
  const headers = body?.closest('table')?.querySelectorAll('thead th');
  const resolved = pick(values);
  if (!headers || !Array.isArray(resolved)) return;
  headers.forEach((node, index) => {
    if (resolved[index] != null) node.textContent = String(resolved[index]);
  });
}

function setPanelHeadByRoot(rootSelector, title, caption) {
  const root = document.querySelector(rootSelector);
  if (!root) return;
  const titleNode = root.querySelector('.panel-head h2');
  const captionNode = root.querySelector('.panel-head .panel-caption');
  if (titleNode) titleNode.textContent = String(pick(title));
  if (captionNode) captionNode.textContent = String(pick(caption));
}

function setSubHeadByRoot(rootSelector, title, caption) {
  const root = document.querySelector(rootSelector);
  if (!root) return;
  const titleNode = root.querySelector('.panel-head h3');
  const captionNode = root.querySelector('.panel-head p');
  if (titleNode) titleNode.textContent = String(pick(title));
  if (captionNode) captionNode.textContent = String(pick(caption));
}

function syncButtons() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll('.lang-chip[data-lang]').forEach((button) => {
    button.classList.toggle('is-active', button.dataset.lang === currentLang);
  });
}

function applyDashboardPage() {
  setText('title', { ko: 'SEPA 커맨드 센터', en: 'SEPA Command Center' });
  setText('.page-header .hero-copy h1', { ko: 'SEPA 커맨드 센터', en: 'SEPA Command Center' });
  setText('.page-header .hero-copy .lead', {
    ko: '주도 탐색, 섹터 검증, 차트 검증, 실행 검토를 한 화면 흐름으로 정리한 운영 대시보드입니다.',
    en: 'Reframe the dashboard as one operating sequence: scan confirmed leadership, inspect sector evidence, validate the chart desk, and finish on backtest and recommendation review.',
  });
  setAttr('#apiBase', 'aria-label', { ko: 'API 기본 주소', en: 'API Base URL' });
  setText('#btnRefresh', { ko: '새로고침', en: 'Refresh' });

  setMany('.page-nav .nav-link', {
    ko: ['커맨드 센터', '플레이북 용어', '위저드 인덱스', '전략 프레임', '코리아 프리셋'],
    en: ['Command Center', 'Playbook Terms', 'Wizard Index', 'Strategy Frames', 'Korea Presets'],
  });

  const workflowPanel = document.querySelector('.workflow-panel');
  if (workflowPanel) {
    workflowPanel.querySelector('.panel-head h2').textContent = pick({ ko: 'SEPA 워크플로', en: 'SEPA Workflow' });
    workflowPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '벤치마크의 단계형 흐름은 가져오되, 실제 데이터 파이프라인은 이 프로젝트 기준으로 다시 맵핑합니다.',
      en: 'Borrow the staged page flow from the benchmark, but map every stop to this project\'s actual data pipeline.',
    });
    workflowPanel.querySelector('.panel-head .eyebrow').textContent = pick({ ko: '4단계', en: '4 stages' });
    const steps = workflowPanel.querySelectorAll('.workflow-card__step');
    const titles = workflowPanel.querySelectorAll('.workflow-card strong');
    const captions = workflowPanel.querySelectorAll('.workflow-card p');
    const meta = workflowPanel.querySelectorAll('.workflow-card small');
    const stepLabels = pick({
      ko: ['단계 1', '단계 2', '단계 3', '단계 4'],
      en: ['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4'],
    });
    const titleLabels = pick({
      ko: ['리더 파이프라인', '섹터 랩', '차트 데스크', '검증 및 실행'],
      en: ['Leader Pipeline', 'Sector Lab', 'Chart Desk', 'Validation And Execution'],
    });
    const captionLabels = pick({
      ko: [
        '확정 섹터와 확정 종목부터 열고, 그다음 깊은 분석으로 들어갑니다.',
        '섹터 구성 종목, 지속성, 랭킹 수식을 한곳에서 검증합니다.',
        '가격, 거래량, 상대강도, MACD, EPS를 하나의 데스크에서 확인합니다.',
        '백테스트, 추천 게이트, 오메가 실행 계획으로 마무리합니다.',
      ],
      en: [
        'Start with confirmed sectors and confirmed stocks before opening any deeper analysis.',
        'Drill into sector membership, persistence, and the logic formula used for ranking.',
        'Inspect price, volume, relative strength, MACD, and quarterly EPS on one aligned desk.',
        'Finish on backtest buckets, recommendation gates, and the Omega execution plan.',
      ],
    });
    const metaLabels = pick({
      ko: ['확정 리더십 + 근접 후보', '근거, 맥락, 수식', '단일 종목 검증', '백테스트 + 추천 검토'],
      en: ['Confirmed leadership + near-ready queue', 'Evidence, context, formula', 'Single-stock validation', 'Backtest + recommendation review'],
    });
    steps.forEach((node, index) => { if (stepLabels[index]) node.textContent = stepLabels[index]; });
    titles.forEach((node, index) => { if (titleLabels[index]) node.textContent = titleLabels[index]; });
    captions.forEach((node, index) => { if (captionLabels[index]) node.textContent = captionLabels[index]; });
    meta.forEach((node, index) => { if (metaLabels[index]) node.textContent = metaLabels[index]; });
    setMany('.workflow-panel .section-chip-row .note-pill', {
      ko: ['확정 리더십 우선', '과거 일자 재계산', '참조 페이지는 메인 흐름 밖으로 분리'],
      en: ['Confirmed leadership first', 'Historical date recalculation', 'Research pages moved out of the main flow'],
    });
  }

  setPanelHeadByRoot('.query-panel', { ko: '과거 일자 조회', en: 'Historical Date Query' }, {
    ko: '지원되는 날짜를 선택하면 해당 시점 기준으로 전체 운영 흐름을 다시 계산합니다.',
    en: 'Choose any supported date and rebuild the full operating sequence for that session.',
  });
  setAttr('#asOfDatePicker', 'aria-label', { ko: '조회 날짜', en: 'Historical date' });
  setAttr('#persistenceWindow', 'aria-label', { ko: '지속성 기간', en: 'Persistence window' });
  setMany('#persistenceWindow option', {
    ko: ['63일', '126일', '252일', '504일'],
    en: ['63D', '126D', '252D', '504D'],
  });
  setText('#btnLoadDate', { ko: '날짜 조회', en: 'Load Date' });
  setText('#btnLatestDate', { ko: '최신', en: 'Latest' });
  if (!document.getElementById('dateRangeMeta')?.dataset.dynamic) {
    setText('#dateRangeMeta', { ko: '지원 날짜 범위를 불러오는 중...', en: 'Loading supported date range...' });
  }

  const heroPanels = document.querySelectorAll('.hero-grid .panel');
  if (heroPanels[0]) {
    heroPanels[0].querySelector('h2').textContent = pick({ ko: '일일 브리핑', en: 'Daily Briefing' });
    heroPanels[0].querySelector('.panel-caption').textContent = pick({
      ko: '파이프라인이 장 마감 후 생성한 최신 요약입니다.',
      en: 'Latest after-close note generated by the pipeline.',
    });
    heroPanels[0].querySelector('.eyebrow').textContent = pick({ ko: '최신', en: 'Latest' });
    setMany('.briefing-actions .nav-link', {
      ko: ['리더 파이프라인 열기', '차트 데스크로 이동', '실행 검토 보기'],
      en: ['Open Leader Pipeline', 'Jump To Chart Desk', 'Review Execution'],
    });
  }
  if (heroPanels[1]) {
    heroPanels[1].querySelector('h2').textContent = pick({ ko: '커맨드 레인', en: 'Command Lanes' });
    heroPanels[1].querySelector('.panel-caption').textContent = pick({
      ko: '벤치마크의 메뉴형 탐색 구조는 유지하되, 모든 레인을 SEPA 작업 흐름에 맞춰 재정리했습니다.',
      en: 'Keep the benchmark\'s menu-driven discovery pattern, but remap every lane to SEPA tasks and references.',
    });
    const cards = heroPanels[1].querySelectorAll('.hub-link-card');
    const strongs = [
      { ko: '리더 파이프라인', en: 'Leader Pipeline' },
      { ko: '섹터 랩', en: 'Sector Lab' },
      { ko: '차트 데스크', en: 'Chart Desk' },
      { ko: '실행 검토', en: 'Execution Review' },
      { ko: '플레이북 용어', en: 'Playbook Terms' },
      { ko: '전략 프레임', en: 'Strategy Frames' },
    ];
    const captions = [
      { ko: '확정 섹터, 주도주, 관찰 섹터, 셋업 후보를 먼저 봅니다.', en: 'Confirmed sectors, leader stocks, watchlist sectors, and setup candidates.' },
      { ko: '섹터 드릴다운, 구성 종목 근거, 수식 설명을 묶어 둡니다.', en: 'Sector drill-down, membership evidence, and scoring formula reference.' },
      { ko: '터미널형 차트, EPS 이력, 동일 섹터 비교를 확인합니다.', en: 'Terminal-style charting, EPS history, and same-sector peer comparison.' },
      { ko: '백테스트, 추천, 오메가 계획, 스냅샷 이력을 검토합니다.', en: 'Backtest buckets, recommendations, Omega plans, and snapshot history.' },
      { ko: 'Alpha, Beta, Gamma, EPS 등 운영 용어를 따로 정리합니다.', en: 'Definitions for Alpha, Beta, Gamma, EPS, and other workflow terms.' },
      { ko: '철학 페이지는 메인 흐름을 막지 않게 별도 보조 허브로 둡니다.', en: 'External philosophy pages stay available without crowding the command flow.' },
    ];
    cards.forEach((card, index) => {
      if (card.querySelector('strong')) card.querySelector('strong').textContent = pick(strongs[index]);
      if (card.querySelector('p')) card.querySelector('p').textContent = pick(captions[index]);
    });
  }

  setMany('.kpi-strip .kpi-card label', {
    ko: ['날짜', '총 섹터 수', '주도주 수', 'Alpha 통과', 'Beta 통과', 'Omega 픽', '상태'],
    en: ['Date', 'Total Sectors', 'Leader Stocks', 'Alpha Pass', 'Beta Pass', 'Omega Picks', 'Status'],
  });
  setMany('.kpi-strip .kpi-card p', {
    ko: [
      '대시보드가 표시 중인 실제 영업일.',
      '현재 유니버스에서 추적하는 섹터 수.',
      '현재 주도주로 랭크된 종목 수.',
      '추세 템플릿 통과 수.',
      'VCP와 수축 구조 통과 수.',
      'Omega 최종 실행 후보 수.',
      '데이터 로딩 상태.',
    ],
    en: [
      'Resolved trading date shown by the dashboard.',
      'Tracked sectors inside the current universe.',
      'Stocks currently ranked as leaders.',
      'Trend-template pass count.',
      'VCP and contraction pass count.',
      'Final execution ideas from Omega.',
      'Current load status.',
    ],
  });

  const sectionRoots = document.querySelectorAll('.section-shell');
  const sectionKickers = pick({
    ko: ['1단계', '2단계', '3단계', '4단계'],
    en: ['Stage 1', 'Stage 2', 'Stage 3', 'Stage 4'],
  });
  const sectionTitles = pick({
    ko: ['리더 파이프라인', '섹터 랩', '차트 데스크', '검증 및 실행'],
    en: ['Leader Pipeline', 'Sector Lab', 'Chart Desk', 'Validation And Execution'],
  });
  const sectionCaptions = pick({
    ko: [
      '하루의 시작은 확정 리더십부터 열고, 그다음 근접 후보를 봅니다.',
      '리더십이 보이면 섹터 수준의 근거와 수식 설명으로 이동합니다.',
      '개별 종목은 전체 기술/실적 데스크에서 다시 검증합니다.',
      '마지막은 백테스트, 추천 게이트, 최근 실행 이력으로 닫습니다.',
    ],
    en: [
      'Open the day with confirmed leadership first, then move to the near-ready queue.',
      'Once leadership is visible, move into sector-level proof and formula context.',
      'Validate individual names on the full technical and earnings desk before moving to execution.',
      'Close the loop with bucket validation, recommendation gates, and recent execution history.',
    ],
  });
  const chipSets = pick({
    ko: [
      ['확정 섹터', '확정 종목', '관찰 섹터와 셋업'],
      ['지속성', '구성 종목 랭킹', '수식 감사'],
      ['가격과 거래량', '상대강도', '분기 EPS'],
      ['백테스트 버킷', '추천 게이트', '오메가 계획'],
    ],
    en: [
      ['Confirmed sectors', 'Confirmed stocks', 'Watchlist and setups'],
      ['Persistence', 'Member ranking', 'Formula audit'],
      ['Price and volume', 'Relative strength', 'Quarterly EPS'],
      ['Backtest buckets', 'Recommendation gates', 'Omega plan'],
    ],
  });
  sectionRoots.forEach((root, index) => {
    const kicker = root.querySelector('.section-kicker');
    const title = root.querySelector('.section-header h2');
    const caption = root.querySelector('.section-header .panel-caption');
    const chips = root.querySelectorAll('.section-chip-row .note-pill');
    if (kicker && sectionKickers[index]) kicker.textContent = sectionKickers[index];
    if (title && sectionTitles[index]) title.textContent = sectionTitles[index];
    if (caption && sectionCaptions[index]) caption.textContent = sectionCaptions[index];
    chips.forEach((node, chipIndex) => {
      if (chipSets[index]?.[chipIndex]) node.textContent = chipSets[index][chipIndex];
    });
  });

  const sectorPanel = document.getElementById('sectorRows')?.closest('article');
  if (sectorPanel) {
    sectorPanel.querySelector('.panel-head h2').textContent = pick({ ko: '확정 리더 섹터', en: 'Confirmed Leader Sectors' });
    sectorPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '실제로 리더십으로 전환된 대분류 섹터만 남깁니다.',
      en: 'Only broad sectors that have actually turned into leadership remain here.',
    });
  }
  setTableHeaders('sectorRows', {
    ko: ['#', '섹터', '리더 점수', 'Alpha / 전체', 'Beta', '120일 수익률'],
    en: ['#', 'Sector', 'Leader Score', 'Alpha / Universe', 'Beta', '120D Return'],
  });

  const watchSectorPanel = document.getElementById('watchSectorRows')?.closest('article');
  if (watchSectorPanel) {
    watchSectorPanel.querySelector('.panel-head h2').textContent = pick({ ko: '섹터 관찰 리스트', en: 'Ranked Sector Watchlist' });
    watchSectorPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '상위권이지만 아직 확정 리더는 아닌 섹터를 따로 보여줍니다.',
      en: 'High-ranking sectors that are close, but not yet confirmed as leadership.',
    });
  }
  setTableHeaders('watchSectorRows', {
    ko: ['#', '섹터', '리더 점수', 'Alpha / 전체', 'Beta', '120일 수익률'],
    en: ['#', 'Sector', 'Leader Score', 'Alpha / Universe', 'Beta', '120D Return'],
  });

  const stockPanel = document.getElementById('stockRows')?.closest('article');
  if (stockPanel) {
    stockPanel.querySelector('.panel-head h2').textContent = pick({ ko: '확정 리더 종목', en: 'Confirmed Leader Stocks' });
    stockPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '확정 리더 섹터에 속한 종목만 먼저 보고, 이후 차트 데스크로 넘깁니다.',
      en: 'Stocks inside confirmed leader sectors, ready for deeper chart review.',
    });
  }
  setAttr('#stockFilter', 'placeholder', { ko: '종목명, 코드, 섹터로 필터', en: 'Filter by name, symbol, or sector' });
  setTableHeaders('stockRows', {
    ko: ['#', '종목', '섹터', '리더 점수', 'Alpha', 'Beta', 'Gamma', '120일 수익률'],
    en: ['#', 'Stock', 'Sector', 'Leader Score', 'Alpha', 'Beta', 'Gamma', '120D Return'],
  });

  const setupStockPanel = document.getElementById('setupStockRows')?.closest('article');
  if (setupStockPanel) {
    setupStockPanel.querySelector('.panel-head h2').textContent = pick({ ko: '셋업 후보', en: 'Setup Candidates' });
    setupStockPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '관찰 섹터 안에서 아직 리더는 아니지만 추적할 만한 후보를 분리합니다.',
      en: 'Stocks from ranked watchlist sectors that are worth monitoring before they become leaders.',
    });
  }
  setTableHeaders('setupStockRows', {
    ko: ['#', '종목', '섹터', '리더 점수', 'Alpha', 'Beta', 'Gamma', '120일 수익률'],
    en: ['#', 'Stock', 'Sector', 'Leader Score', 'Alpha', 'Beta', 'Gamma', '120D Return'],
  });
  const sectorDrillPanel = document.getElementById('sectorMembersRows')?.closest('article');
  if (sectorDrillPanel) {
    sectorDrillPanel.querySelector('.panel-head h2').textContent = pick({ ko: '섹터 드릴다운', en: 'Sector Drill-Down' });
    sectorDrillPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '섹터를 클릭하면 구성 종목, 점수 근거, 동일 날짜 지속성을 볼 수 있습니다.',
      en: 'Click a sector to inspect members, rank evidence, and same-date persistence.',
    });
  }
  setTableHeaders('sectorMembersRows', {
    ko: ['#', '종목', '주도 점수', 'Alpha', 'Beta', 'Gamma', '추천'],
    en: ['#', 'Stock', 'Leader Score', 'Alpha', 'Beta', 'Gamma', 'Reco'],
  });

  const logicPanel = document.getElementById('logicExplain')?.closest('article');
  if (logicPanel) {
    logicPanel.querySelector('.panel-head h2').textContent = pick({ ko: '로직과 수식', en: 'Logic and Formula' });
    logicPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '점수 수식, 예시 계산, 미너비니 연결, 과거 활용 메모를 함께 보여줍니다.',
      en: 'Scoring formulas, worked examples, Minervini linkage, and historical usage notes.',
    });
  }

  const backtestPanel = document.getElementById('backtestBuckets')?.closest('section');
  if (backtestPanel) {
    backtestPanel.querySelector('.panel-head h2').textContent = pick({ ko: '백테스트 탐색기', en: 'Backtest Explorer' });
    backtestPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '일간 또는 주간 버킷별 상위 섹터와 상위 종목을 조회합니다.',
      en: 'View top sectors and top stocks by daily or weekly bucket.',
    });
  }
  setAttr('#backtestPeriod', 'aria-label', { ko: '백테스트 주기', en: 'Backtest period' });
  setMany('#backtestPeriod option', { ko: ['주간', '일간'], en: ['Weekly', 'Daily'] });
  setAttr('#backtestBucketCount', 'aria-label', { ko: '백테스트 버킷 수', en: 'Backtest bucket count' });
  setMany('#backtestBucketCount option', { ko: ['최근 6개', '최근 8개', '최근 12개'], en: ['Last 6', 'Last 8', 'Last 12'] });
  setText('#btnBacktest', { ko: '버킷 불러오기', en: 'Load Buckets' });

  const analysisPanel = document.querySelector('.analysis-panel');
  if (analysisPanel) {
    analysisPanel.querySelector('.panel-head .eyebrow').textContent = pick({ ko: '선택 종목 차트 데스크', en: 'Selected Chart Desk' });
    analysisPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '선택한 날짜 기준으로 일봉 가격, 거래량, R/S, MACD, 분기 EPS를 다시 계산합니다.',
      en: 'Daily price, daily volume, relative strength, MACD, and quarterly EPS recalculated for the chosen date.',
    });
  }
  if (!document.getElementById('analysisName')?.dataset.dynamic) {
    setText('#analysisName', { ko: '종목을 선택하세요', en: 'Select a stock' });
    setText('#pickedSymbol', { ko: '종목코드 -', en: 'Code -' });
    setText('#analysisSector', { ko: '섹터 -', en: 'Sector -' });
    setText('#analysisDate', { ko: '날짜 -', en: 'Date -' });
  }
  const chartCards = document.querySelectorAll('.chart-card');
  if (chartCards[0]) {
    chartCards[0].querySelector('h3').textContent = pick({ ko: '메인 트레이딩 차트', en: 'Main Trading Chart' });
    chartCards[0].querySelector('.chart-head p').textContent = pick({
      ko: '가격, 거래량, R/S, MACD를 하나의 시간축에 정렬합니다.',
      en: 'Price, volume, RS, and MACD share one aligned timeline.',
    });
    setMany('.chart-shell-note .chart-note-pill', {
      ko: ['일봉 구조', '우측 가격 레일', '공통 시간축', '증권사형 레이아웃', '휠 확대 / Shift+휠 이동 / 드래그 스크롤', document.getElementById('chartRangeLabel')?.textContent || '120일 표시'],
      en: ['Daily structure', 'Right price rail', 'Unified time axis', 'Broker style layout', 'Wheel zoom / Shift+wheel pan / Drag scroll', document.getElementById('chartRangeLabel')?.textContent || '120D visible'],
    });
  }
  if (chartCards[1]) {
    chartCards[1].querySelector('h3').textContent = pick({ ko: '분기 EPS 차트', en: 'Quarterly EPS Chart' });
    chartCards[1].querySelector('.chart-head p').textContent = pick({
      ko: '분기 EPS 막대와 YoY, 실제 EPS 라벨을 함께 표시합니다.',
      en: 'Quarterly EPS bars with YoY and actual EPS labels.',
    });
  }
  if (chartCards[2]) {
    chartCards[2].querySelector('h3').textContent = pick({ ko: '동일 섹터 비교', en: 'Sector Peers' });
    chartCards[2].querySelector('.chart-head p').textContent = pick({
      ko: '선택 종목을 동일 섹터 종목과 비교합니다.',
      en: 'Compare the selected stock against peers in the same sector.',
    });
  }
  setTableHeaders('sectorPeerRows', {
    ko: ['#', '종목', '주도 점수', 'Beta', '120일 수익률'],
    en: ['#', 'Stock', 'Leader Score', 'Beta', '120D Return'],
  });
  if (!document.getElementById('analysisMeta')?.dataset.dynamic) {
    setText('#analysisMeta', {
      ko: '주도주 또는 백테스트 버킷의 종목을 선택하면 차트 데스크를 불러옵니다.',
      en: 'Pick a leader stock or a stock from a backtest bucket to load the chart desk.',
    });
  }

  const recPanel = document.getElementById('recRows')?.closest('article');
  if (recPanel) {
    recPanel.querySelector('.panel-head h2').textContent = pick({ ko: '추천 종목', en: 'Recommendations' });
    recPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '추천 점수, 게이트, 손익비와 오메가 실행 계획을 한 표에서 나란히 봅니다.',
      en: 'Recommendation score, gates, risk/reward, and the Omega execution plan side by side.',
    });
  }
  setTableHeaders('recRows', {
    ko: ['#', '종목', '섹터', '확신도', '추천 점수', 'EPS 상태', '최소 저항', 'R/R', '오메가 플랜'],
    en: ['#', 'Stock', 'Sector', 'Conviction', 'Reco Score', 'EPS Status', 'Least Resistance', 'R/R', 'Omega Plan'],
  });
  const omegaSection = document.getElementById('omegaRows')?.closest('.subsection');
  if (omegaSection) {
    omegaSection.querySelector('h3').textContent = pick({ ko: 'Omega 실행 계획', en: 'Omega Execution Plan' });
    omegaSection.querySelector('.panel-head p').textContent = pick({
      ko: '진입가, 손절가, 목표가, 수량, 손익비를 명시적으로 표시합니다.',
      en: 'Entry, stop, target, size, and risk/reward with explicit units.',
    });
  }
  if (!document.getElementById('omegaMeta')?.dataset.dynamic) {
    setText('#omegaMeta', {
      ko: '진입가와 목표가는 원, 수량은 주, 손익비는 R 단위로 표시합니다.',
      en: 'Entry and target are shown in KRW. Quantity is shares and risk/reward is in R.',
    });
  }
  setTableHeaders('omegaRows', {
    ko: ['종목', '진입가 (원)', '손절가 (원)', '목표가 (원)', '수량 (주)', 'R/R'],
    en: ['Stock', 'Entry (KRW)', 'Stop (KRW)', 'Target (KRW)', 'Qty (shares)', 'R/R'],
  });

  const historyPanel = document.getElementById('historyRows')?.closest('article');
  if (historyPanel) {
    historyPanel.querySelector('.panel-head h2').textContent = pick({ ko: '추천 이력', en: 'Recommendation History' });
    historyPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '최근 추천 스냅샷과 날짜별 최상위 종목을 보여줍니다.',
      en: 'Recent recommendation snapshots with the top three names by day.',
    });
  }
  setTableHeaders('historyRows', {
    ko: ['날짜', '추천 수', '최상위 종목', '점수'],
    en: ['Date', 'Reco Count', 'Top 3 Names', 'Top Score'],
  });
  if (historyPanel) {
    historyPanel.querySelector('.panel-head .panel-caption').textContent = pick({
      ko: '최근 추천 스냅샷과 날짜별 상위 3개 종목을 함께 보여줍니다.',
      en: 'Recent recommendation snapshots with the top three names by day.',
    });
  }
  setTableHeaders('historyRows', {
    ko: ['날짜', '추천 수', '상위 3개 종목', '최상위 점수'],
    en: ['Date', 'Reco Count', 'Top 3 Names', 'Top Score'],
  });
}

function applyGlossaryPage() {
  setText('title', { ko: 'SEPA 플레이북 용어', en: 'SEPA Playbook Terms' });
  setText('.page-header .hero-copy h1', { ko: '플레이북 용어', en: 'Playbook Terms' });
  setText('.page-header .hero-copy .lead', {
    ko: '대시보드, 섹터 랭킹, 종목 랭킹, 미너비니 스크리닝에서 쓰는 용어를 별도 페이지로 정리합니다.',
    en: 'A separate reference page for the terms used across the dashboard, sector ranking, stock ranking, and Minervini-style screening workflow.',
  });
  setMany('.toolbar .nav-link--button', { ko: ['커맨드 센터', '전략 프레임'], en: ['Command Center', 'Strategy Frames'] });
  setMany('.page-nav .nav-link', {
    ko: ['커맨드 센터', '플레이북 용어', '위저드 인덱스', '전략 프레임', '코리아 프리셋'],
    en: ['Command Center', 'Playbook Terms', 'Wizard Index', 'Strategy Frames', 'Korea Presets'],
  });
  setMany('.note-strip .note-pill', {
    ko: ['Alpha / Beta / Gamma 정의', 'RS, MACD, EPS, 최소 저항', '대시보드 밖으로 분리된 참조 페이지'],
    en: ['Alpha / Beta / Gamma definitions', 'RS, MACD, EPS, least resistance', 'Reference-only page, moved out of the dashboard'],
  });
  setText('.panel-head h2', { ko: '핵심 용어', en: 'Core Terms' });
  setText('.panel-head .panel-caption', {
    ko: '용어는 API에서 불러오며, 메인 대시보드보다 가볍게 유지합니다.',
    en: 'This page loads the glossary from the API and keeps the main dashboard lighter.',
  });
}

function applyWizardOverviewPage() {
  setText('title', { ko: 'SEPA 전략 프레임', en: 'SEPA Strategy Frames' });
  setText('.page-header .hero-copy h1', { ko: '전략 프레임', en: 'Strategy Frames' });
  setText('.page-header .hero-copy .lead', {
    ko: '자주 참고하는 여섯 명의 트레이더와, 그들의 아이디어가 현재 SEPA 화면에 어떻게 연결되는지 압축해서 보여줍니다.',
    en: 'A compact comparison page for six frequently referenced traders and how their ideas map into the current SEPA dashboard.',
  });
  setMany('.toolbar .nav-link--button', { ko: ['커맨드 센터', '코리아 프리셋'], en: ['Command Center', 'Korea Presets'] });
  setMany('.page-nav .nav-link', {
    ko: ['커맨드 센터', '플레이북 용어', '위저드 인덱스', '전략 프레임', '코리아 프리셋'],
    en: ['Command Center', 'Playbook Terms', 'Wizard Index', 'Strategy Frames', 'Korea Presets'],
  });
  setMany('.note-strip .note-pill', {
    ko: ['가격과 RS 우선', '테마와 리더십 집중', '확신보다 리스크 관리'],
    en: ['Price and RS first', 'Theme and leadership concentration', 'Risk management before conviction'],
  });
  const panels = document.querySelectorAll('.panel');
  if (panels[0]) {
    panels[0].querySelector('h2').textContent = pick({ ko: '핵심 6인 프로필', en: 'Six Anchor Profiles' });
    panels[0].querySelector('.panel-caption').textContent = pick({
      ko: '각 카드에 핵심 철학, 체크리스트, SEPA 연결 지점을 담았습니다.',
      en: 'Each card shows the core philosophy, checklist, and where it maps into SEPA.',
    });
  }
  if (panels[1]) {
    panels[1].querySelector('h2').textContent = pick({ ko: '비교 매트릭스', en: 'Comparison Matrix' });
    panels[1].querySelector('.panel-caption').textContent = pick({
      ko: '무엇을 가장 중시하는지, 어떤 트리거로 진입하는지, 리스크를 어떻게 다루는지 빠르게 비교합니다.',
      en: 'A fast view of what each trader emphasizes most, how they trigger entries, and how they treat risk.',
    });
  }
}

function applyWizardKoreaPage() {
  setText('title', { ko: 'SEPA 코리아 프리셋', en: 'SEPA Korea Presets' });
  setText('.page-header .hero-copy h1', { ko: '코리아 프리셋', en: 'Korea Presets' });
  setText('.page-header .hero-copy .lead', {
    ko: '선택한 트레이더 철학으로 현재 주도섹터와 주도주를 다시 랭킹하고, 한국 증시 기준으로 해석합니다.',
    en: 'Re-rank the current leader sectors and leader stocks through a chosen trader philosophy, then inspect the resulting top ideas for the Korean market.',
  });
  setMany('.toolbar .nav-link--button', { ko: ['커맨드 센터', '전략 프레임'], en: ['Command Center', 'Strategy Frames'] });
  setMany('.page-nav .nav-link', {
    ko: ['커맨드 센터', '플레이북 용어', '위저드 인덱스', '전략 프레임', '코리아 프리셋'],
    en: ['Command Center', 'Playbook Terms', 'Wizard Index', 'Strategy Frames', 'Korea Presets'],
  });
  const panels = document.querySelectorAll('.panel');
  if (panels[0]) {
    panels[0].querySelector('h2').textContent = pick({ ko: '트레이더 선택', en: 'Select A Trader' });
    panels[0].querySelector('.panel-caption').textContent = pick({
      ko: '어떤 철학으로 현재 섹터/종목 후보를 다시 랭킹할지 고릅니다.',
      en: 'Pick a profile to see how its rules re-rank the current sector and stock universe.',
    });
  }
  if (panels[1]) {
    panels[1].querySelector('h2').textContent = pick({ ko: '프리셋 랭킹 결과', en: 'Preset Ranking Output' });
    setText('#presetDateMeta', { ko: '프리셋 후보를 불러오는 중...', en: 'Loading preset candidates...' });
    setText('#btnPresetLoadDate', { ko: '날짜 조회', en: 'Load Date' });
    setText('#btnPresetLatest', { ko: '최신', en: 'Latest' });
    setTableHeaders('presetSectorRows', {
      ko: ['#', '섹터', '프리셋 점수', '기본 주도 점수', '핵심 이유'],
      en: ['#', 'Sector', 'Preset Score', 'Base Leader Score', 'Main Reasons'],
    });
    setTableHeaders('presetStockRows', {
      ko: ['#', '종목', '섹터', '프리셋 점수', '기본 주도 점수', '핵심 이유'],
      en: ['#', 'Stock', 'Sector', 'Preset Score', 'Base Leader Score', 'Main Reasons'],
    });
    const cards = panels[1].querySelectorAll('.strategy-card h3');
    if (cards[0]) cards[0].textContent = pick({ ko: '상위 섹터', en: 'Top Sectors' });
    if (cards[1]) cards[1].textContent = pick({ ko: '상위 종목', en: 'Top Stocks' });
  }
}

function applyWizardPeoplePage() {
  setText('title', { ko: 'SEPA 위저드 인덱스', en: 'SEPA Wizard Index' });
  setText('.page-header .hero-copy h1', { ko: '위저드 인덱스', en: 'Wizard Index' });
  setText('.page-header .hero-copy .lead', {
    ko: 'Market Wizards 5권에 걸친 인터뷰 인물을 책별로 정리한 참조 페이지입니다.',
    en: 'A full person index covering the five main Market Wizards series volumes, grouped by book and rendered as a browsable reference page.',
  });
  setMany('.toolbar .nav-link--button', { ko: ['전략 프레임', '코리아 프리셋'], en: ['Strategy Frames', 'Korea Presets'] });
  setMany('.page-nav .nav-link', {
    ko: ['커맨드 센터', '플레이북 용어', '위저드 인덱스', '전략 프레임', '코리아 프리셋'],
    en: ['Command Center', 'Playbook Terms', 'Wizard Index', 'Strategy Frames', 'Korea Presets'],
  });
  setMany('.note-strip .note-pill', {
    ko: ['총 73명', '5권 전체 포함', '책별 그룹과 한 줄 소개'],
    en: ['73 people total', 'All five main series volumes', 'Grouped by book with a short one-line profile'],
  });
  const panel = document.querySelector('.panel');
  if (panel) {
    panel.querySelector('h2').textContent = pick({ ko: '시리즈 요약', en: 'Series Summary' });
    panel.querySelector('.panel-caption').textContent = pick({
      ko: 'Market Wizards, The New Market Wizards, Stock Market Wizards, Hedge Fund Market Wizards, Unknown Market Wizards를 포함합니다.',
      en: 'Market Wizards, The New Market Wizards, Stock Market Wizards, Hedge Fund Market Wizards, and Unknown Market Wizards.',
    });
  }
}

const PAGE_APPLIERS = {
  dashboard: applyDashboardPage,
  glossary: applyGlossaryPage,
  'market-wizards-overview': applyWizardOverviewPage,
  'market-wizards-korea': applyWizardKoreaPage,
  'market-wizards-people': applyWizardPeoplePage,
};

export function getLang() {
  return currentLang;
}

export function txt(value) {
  return String(pick(value));
}

export function setLanguage(lang) {
  const next = String(lang || '').trim().toLowerCase();
  if (!SUPPORTED_LANGS.has(next) || next === currentLang) return;
  currentLang = next;
  window.localStorage.setItem(STORAGE_KEY, currentLang);
  syncButtons();
  window.dispatchEvent(new CustomEvent('sepa:langchange', { detail: { lang: currentLang } }));
}

export function setupPageI18n(pageKey, rerender = null) {
  document.querySelectorAll('.lang-chip[data-lang]').forEach((button) => {
    if (button.dataset.bound === '1') return;
    button.dataset.bound = '1';
    button.addEventListener('click', () => setLanguage(button.dataset.lang));
  });

  const apply = () => {
    const applier = PAGE_APPLIERS[pageKey];
    if (applier) applier();
    syncButtons();
  };

  apply();
  if (typeof rerender === 'function') {
    window.addEventListener('sepa:langchange', () => {
      apply();
      rerender(currentLang);
    });
  } else {
    window.addEventListener('sepa:langchange', apply);
  }
}

