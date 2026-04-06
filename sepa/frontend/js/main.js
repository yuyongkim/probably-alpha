import {
  $,
  backtestContext,
  escapeHtml,
  fetchJSON,
  fmtDate,
  log,
  selectedPersistenceWindow,
  setDateInputValue,
  state,
  toDateToken,
} from './core.js?v=1775457857';
import { getLang, setupPageI18n, txt } from './i18n.js?v=1775457857';
import { getAnalysisViewport, getEpsViewport, mainChartIndexFromClientX, renderAnalysisCharts } from './charts.js?v=1775457857';
import { resetPaginationPage } from './renderers/pagination.js?v=1775457857';
import { createRenderers } from './renderers.js?v=1775457857';
import { applyTraderPreset, getFullProfile, renderTraderTabs, traderProfiles } from './trader-tabs.js?v=1775457857';
import { setupTermTips, termTip } from './term-tips.js?v=1775457857';

let initialized = false;
let resizeTimer = null;
let renderers = null;
let analysisRenderFrame = null;
let dragState = null;
let activeTrader = 'default';
let backtestLoaded = false;
let sectionObserver = null;

async function loadLogic(dateDir = '') {
  const base = $('apiBase').value.trim();
  const query = dateDir ? `?date_dir=${encodeURIComponent(dateDir)}` : '';
  const payload = await fetchJSON(`${base}/api/logic/scoring${query}`);
  renderers.renderLogicExplain(payload);
  return payload;
}

async function loadSectorPersistence(sector, dateDir = '') {
  if (!sector) {
    state.sectorPersistence = null;
    renderers.renderPersistenceCards('sectorPersistenceCards', null, 'Sector');
    return null;
  }

  const base = $('apiBase').value.trim();
  const windowDays = selectedPersistenceWindow();
  const query = new URLSearchParams({
    kind: 'sector',
    key: sector,
    date_to: dateDir || state.latestDateDir,
    lookback_days: String(windowDays),
    forward_days: String(windowDays),
    top_n: '5',
  });
  const payload = await fetchJSON(`${base}/api/persistence?${query.toString()}`);
  state.sectorPersistence = payload;
  renderers.renderPersistenceCards('sectorPersistenceCards', payload, 'Sector');
  return payload;
}

async function loadStockPersistence(symbol, dateDir = '') {
  if (!symbol) {
    state.stockPersistence = null;
    renderers.renderPersistenceCards('stockPersistenceCards', null, 'Stock');
    return null;
  }

  const base = $('apiBase').value.trim();
  const windowDays = selectedPersistenceWindow();
  const query = new URLSearchParams({
    kind: 'stock',
    key: symbol,
    date_to: dateDir || state.latestDateDir,
    lookback_days: String(windowDays),
    forward_days: String(windowDays),
    top_n: '10',
  });
  const payload = await fetchJSON(`${base}/api/persistence?${query.toString()}`);
  state.stockPersistence = payload;
  renderers.renderPersistenceCards('stockPersistenceCards', payload, 'Stock');
  return payload;
}

async function loadSectorMembers(sector, dateDir = '', options = {}) {
  const { syncLogic = true, deferPersistence = false } = options;
  if (!sector) {
    renderers.renderSectorMembers(null);
    renderers.renderPersistenceCards('sectorPersistenceCards', null, 'Sector');
    return null;
  }

  const base = $('apiBase').value.trim();
  try {
    if (syncLogic) {
      await loadLogic(dateDir);
    }
    const query = new URLSearchParams({ sector });
    if (dateDir) query.set('date_dir', dateDir);
    const payload = await fetchJSON(`${base}/api/sector-members?${query.toString()}`);
    renderers.renderSectorMembers(payload);
    // Update active-sector highlight without full table rebuild (avoids hover flicker)
    document.querySelectorAll('#sectorRows .clickable-row, #watchSectorRows .clickable-row, #sectorHeatmap .sector-tile').forEach((el) => {
      el.classList.toggle('is-active', el.dataset.sector === state.activeSector);
    });
    const persistencePromise = loadSectorPersistence(payload.sector || sector, payload.date_dir || dateDir);
    if (deferPersistence) {
      void persistencePromise.catch(() => {
        renderers.renderPersistenceCards('sectorPersistenceCards', null, 'Sector');
      });
    } else {
      await persistencePromise;
    }
    return payload;
  } catch (error) {
    $('sectorFocusMeta').textContent = `Failed to load sector drill-down: ${String(error)}`;
    $('sectorMembersRows').innerHTML = '<tr><td colspan="7">Failed to load sector members.</td></tr>';
    renderers.renderPersistenceCards('sectorPersistenceCards', null, 'Sector');
    return null;
  }
}

async function loadAnalysis(symbol, asOfDate = '', context = null, options = {}) {
  const { deferPersistence = false } = options;
  const base = $('apiBase').value.trim();
  state.activeSymbol = symbol;
  state.activeAsOfDate = asOfDate || '';
  state.activeContext = context;
  state.analysisPanOffset = 0;
  state.analysisHoverIndex = null;
  state.analysisHoverYRatio = null;
  state.epsWindowStart = null;

  // Update active-stock highlight without full table rebuild (avoids hover flicker)
  document.querySelectorAll('#stockRows .clickable-row, #setupStockRows .clickable-row, #sectorMembersRows .clickable-row').forEach((el) => {
    el.classList.toggle('is-active', el.dataset.symbol === symbol);
  });

  try {
    const query = state.activeAsOfDate ? `?as_of_date=${encodeURIComponent(state.activeAsOfDate)}` : '';
    const analysis = await fetchJSON(`${base}/api/stock/${encodeURIComponent(symbol)}/analysis${query}`);
    state.activeAnalysis = analysis;
    updateChartRangeControls();
    renderers.renderAnalysisSummary(analysis, context);
    renderAnalysisCharts(analysis);
    const persistencePromise = loadStockPersistence(symbol, state.activeAsOfDate || analysis.as_of_date || state.latestDateDir);
    if (deferPersistence) {
      void persistencePromise.catch(() => {
        renderers.renderPersistenceCards('stockPersistenceCards', null, 'Stock');
      });
    } else {
      await persistencePromise;
    }
  } catch (error) {
    $('analysisMeta').textContent = `Failed to load chart desk: ${String(error)}`;
    renderers.renderPersistenceCards('stockPersistenceCards', null, 'Stock');
  }
}

async function loadBacktest(dateTo = '') {
  const base = $('apiBase').value.trim();
  const period = $('backtestPeriod').value;
  const buckets = $('backtestBucketCount').value;
  const suffix = dateTo ? `&date_to=${encodeURIComponent(dateTo)}` : '';
  const data = await fetchJSON(
    `${base}/api/backtest/leaders?period=${encodeURIComponent(period)}&buckets=${encodeURIComponent(buckets)}&sector_limit=5&stock_limit=10${suffix}`,
  );
  renderers.renderBacktest(data.items || []);
}

async function refresh(dateDir = '', _retried = false) {
  const base = $('apiBase').value.trim();
  const token = toDateToken(dateDir);
  const dateQuery = token ? `?date_dir=${encodeURIComponent(token)}` : '';
  $('kpiStatus').textContent = txt({ ko: '로딩 중', en: 'Loading' });
  state.requestedDateDir = token;
  backtestLoaded = false;
  [
    'confirmedSectors',
    'watchSectors',
    'confirmedStocks',
    'setupStocks',
    'recommendations',
    'omegaPlan',
    'recommendationHistory',
    'backtestBuckets',
  ].forEach((key) => resetPaginationPage(key));

  try {
    // Single combined request instead of 10 parallel requests
    const dashboard = await fetchJSON(`${base}/api/dashboard${dateQuery}`);

    const summary = dashboard.summary;
    const briefing = dashboard.briefing;
    const sectors = dashboard.sectors;
    const stocks = dashboard.stocks;
    const recs = dashboard.recommendations;
    const omega = dashboard.omega;
    const history = dashboard.history;
    const logic = dashboard.logic;
    const catalog = dashboard.catalog;
    const sectorGrouped = dashboard.sectors_grouped;

    state.latestSectors = sectors.items || [];
    state.latestStocks = stocks.items || [];
    state.latestRecommendations = recs.items || [];
    state.latestOmega = omega.items || {};
    state.history = history.items || [];
    state.sectorGroupedItems = sectorGrouped.items || [];
    state.latestDateDir = summary.date_dir || sectors.date_dir || logic.date_dir || '';

    $('kpiDate').textContent = fmtDate(summary.date_dir || '-');
    $('kpiAlpha').textContent = summary.counts?.alpha ?? 0;
    $('kpiBeta').textContent = summary.counts?.beta ?? 0;
    $('kpiPicks').textContent = summary.counts?.picks ?? 0;
    $('kpiStatus').textContent = txt({ ko: '정상', en: 'OK' });
    $('briefingBox').textContent = getLang() === 'ko'
      ? (briefing.items?.message_ko || briefing.items?.message_en || txt({ ko: '브리핑이 없습니다.', en: 'No briefing available.' }))
      : (briefing.items?.message_en || briefing.items?.message_ko || txt({ ko: '브리핑이 없습니다.', en: 'No briefing available.' }));
    setDateInputValue(state.latestDateDir);

    renderers.renderCatalog(catalog, summary);
    renderers.renderRecommendations(state.latestRecommendations);
    renderers.renderOmega(state.latestOmega);
    renderers.renderHistory(state.history);
    renderers.renderLogicExplain(logic);
    renderers.renderSectorGroupedView(sectorGrouped.items || []);
    updateChartRangeControls();
    applyTraderView(activeTrader);

    // Sector members: load immediately but don't block
    const initialSector = state.latestSectors.find((item) => item.sector_bucket === 'confirmed_leader' || item.leadership_ready)?.sector
      || state.latestSectors[0]?.sector;
    if (initialSector) {
      void loadSectorMembers(initialSector, state.latestDateDir, { syncLogic: false, deferPersistence: true }).catch(() => {});
    } else {
      renderers.renderSectorMembers(null);
      renderers.renderPersistenceCards('sectorPersistenceCards', null, 'Sector');
    }

    // Analysis: fire-and-forget (don't block page render)
    const initialSymbol = state.latestStocks.find((item) => item.symbol === state.activeSymbol)?.symbol
      || state.latestStocks.find((item) => item.stock_bucket === 'confirmed_leader' || item.sector_leadership_ready)?.symbol
      || state.latestStocks[0]?.symbol;
    if (initialSymbol) {
      void loadAnalysis(initialSymbol, state.latestDateDir, null, { deferPersistence: true }).catch(() => {});
    } else {
      renderers.renderPersistenceCards('stockPersistenceCards', null, 'Stock');
    }

    // Backtest: lazy-load when #execution-hub scrolls into view
    ensureBacktestObserver();

    log([
      txt({ ko: `${summary.date_dir} 로드 완료`, en: `Loaded ${summary.date_dir}` }),
      token && token !== summary.date_dir
        ? txt({ ko: `요청 ${fmtDate(token)} -> 계산 ${fmtDate(summary.date_dir)}`, en: `Resolved ${fmtDate(token)} -> ${fmtDate(summary.date_dir)}` })
        : txt({ ko: `날짜 ${fmtDate(summary.date_dir)}`, en: `Date ${fmtDate(summary.date_dir)}` }),
      txt({ ko: `Alpha ${summary.counts?.alpha ?? 0}`, en: `Alpha ${summary.counts?.alpha ?? 0}` }),
      txt({ ko: `Beta ${summary.counts?.beta ?? 0}`, en: `Beta ${summary.counts?.beta ?? 0}` }),
      txt({ ko: `섹터 ${catalog?.sector_count ?? 0}`, en: `Sectors ${catalog?.sector_count ?? 0}` }),
      txt({ ko: `주도주 ${summary.counts?.leader_stocks ?? state.latestStocks.length}`, en: `Leader stocks ${summary.counts?.leader_stocks ?? state.latestStocks.length}` }),
    ].join('\n'));
  } catch (error) {
    if (token && !_retried) {
      log(txt({
        ko: `${fmtDate(token)} 데이터 없음 → 최신 날짜로 자동 전환합니다.`,
        en: `No data for ${fmtDate(token)} → falling back to latest date.`,
      }));
      return refresh('', true);
    }
    $('kpiStatus').textContent = txt({ ko: '오류', en: 'ERROR' });
    log(txt({
      ko: `오류: ${String(error)}\nAPI 서버와 생성된 산출물을 확인하세요.`,
      en: `Error: ${String(error)}\nCheck API server and generated files.`,
    }));
  }
}

function ensureBacktestObserver() {
  const target = document.getElementById('execution-hub');
  if (!target) return;

  if (sectionObserver) {
    sectionObserver.disconnect();
  }

  sectionObserver = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting && !backtestLoaded && state.latestDateDir) {
          backtestLoaded = true;
          void loadBacktest(state.latestDateDir).catch(() => {});
        }
      }
    },
    { rootMargin: '200px' },
  );
  sectionObserver.observe(target);
}

function applyTraderView(traderId) {
  activeTrader = traderId || 'default';
  renderTraderTabs('traderTabs', activeTrader);

  const metaEl = $('traderPresetMeta');
  const formulaEl = $('traderPresetFormula');
  const sectorLab = document.getElementById('sector-lab');

  if (activeTrader === 'default') {
    if (metaEl) metaEl.textContent = txt({ ko: 'SEPA 기본', en: 'Default SEPA' });
    if (formulaEl) formulaEl.style.display = 'none';
    if (sectorLab) sectorLab.hidden = true;
    renderers.renderSectorRows(state.latestSectors);
    renderers.renderStockRows(state.latestStocks);
    renderers.renderSectorGroupedView(state.sectorGroupedItems || []);
    return;
  }

  const result = applyTraderPreset(
    activeTrader,
    state.latestSectors,
    state.latestStocks,
    state.latestRecommendations,
  );

  if (!result) {
    if (metaEl) metaEl.textContent = txt({ ko: 'SEPA 기본', en: 'Default SEPA' });
    if (formulaEl) formulaEl.style.display = 'none';
    if (sectorLab) sectorLab.hidden = true;
    renderers.renderSectorRows(state.latestSectors);
    renderers.renderStockRows(state.latestStocks);
    return;
  }

  // Show Sector Lab when a trader is selected
  if (sectorLab) sectorLab.hidden = false;

  const { profile, sectors, stocks } = result;
  if (metaEl) metaEl.textContent = `${profile.name} · ${profile.style}`;
  if (formulaEl) {
    formulaEl.textContent = profile.preset.formula;
    formulaEl.style.display = 'block';
  }

  const retaggedSectors = sectors.map((item) => ({
    ...item,
    leader_score: item.preset_score,
    _original_leader_score: item.original_leader_score,
  }));

  const retaggedStocks = stocks.map((item) => ({
    ...item,
    leader_stock_score: item.preset_score,
    _original_leader_stock_score: item.original_leader_stock_score,
  }));

  renderers.renderSectorRows(retaggedSectors);
  renderers.renderStockRows(retaggedStocks);

  // Update At A Glance to match the preset's sector ranking
  const savedSectors = state.latestSectors;
  state.latestSectors = retaggedSectors;
  renderers.renderSectorGroupedView(state.sectorGroupedItems || []);
  state.latestSectors = savedSectors;
}

function rerenderActiveAnalysis() {
  if (!state.activeAnalysis) return;
  renderers.renderAnalysisSummary(state.activeAnalysis, state.activeContext);
  renderAnalysisCharts(state.activeAnalysis);
}

function requestAnalysisRender() {
  if (analysisRenderFrame) return;
  analysisRenderFrame = window.requestAnimationFrame(() => {
    analysisRenderFrame = null;
    rerenderActiveAnalysis();
  });
}

function currentViewport() {
  return getAnalysisViewport(state.activeAnalysis);
}

function currentEpsViewport() {
  return getEpsViewport(state.activeAnalysis);
}

function updateChartRangeControls() {
  const label = $('chartRangeLabel');
  const current = Number(state.analysisWindowDays || 0);
  const viewport = currentViewport();
  document.querySelectorAll('[data-range-days]').forEach((button) => {
    const value = Number(button.dataset.rangeDays || 0);
    button.classList.toggle('is-active', value === current);
  });

  if (!label) return;
  if (!viewport.total) {
    label.textContent = current > 0
      ? txt({ ko: `${current}일 표시`, en: `${current}D visible` })
      : txt({ ko: '전체 구간 표시', en: 'All history visible' });
    return;
  }
  label.textContent = current > 0
    ? txt({
      ko: `${viewport.windowSize}일 표시 · 과거 ${viewport.panOffset}일 이동`,
      en: `${viewport.windowSize}D visible · ${viewport.panOffset}D back`,
    })
    : txt({ ko: '전체 구간 표시', en: 'All history visible' });
}

function setAnalysisWindowDays(days) {
  const total = state.activeAnalysis?.close_series?.length || 0;
  if (!total) {
    state.analysisWindowDays = Number(days);
    updateChartRangeControls();
    return;
  }
  const raw = Number(days || 0);
  const next = raw > 0 ? Math.min(Math.max(Math.round(raw), 20), total) : 0;
  state.analysisWindowDays = next >= total ? 0 : next;
  const viewport = currentViewport();
  if (state.analysisPanOffset > viewport.maxOffset) {
    state.analysisPanOffset = viewport.maxOffset;
  }
  updateChartRangeControls();
  requestAnalysisRender();
}

function setAnalysisPanOffset(offset) {
  const viewport = currentViewport();
  const next = Math.min(Math.max(Math.round(offset), 0), viewport.maxOffset);
  if (next === state.analysisPanOffset) return;
  state.analysisPanOffset = next;
  updateChartRangeControls();
  requestAnalysisRender();
}

function setEpsWindowStart(start) {
  const epsViewport = currentEpsViewport();
  const next = Math.min(Math.max(Math.round(Number(start) || 0), 0), epsViewport.maxStart);
  if (state.epsWindowStart === next) return;
  state.epsWindowStart = next;
  requestAnalysisRender();
}

function zoomAnalysis(deltaY) {
  const viewport = currentViewport();
  if (!viewport.total) return;
  const nextWindow = deltaY < 0
    ? Math.max(20, Math.round(viewport.windowSize * 0.84))
    : Math.min(viewport.total, Math.round(viewport.windowSize * 1.2));
  setAnalysisWindowDays(nextWindow >= viewport.total ? 0 : nextWindow);
}

function panAnalysis(deltaBars) {
  if (!deltaBars) return;
  setAnalysisPanOffset(state.analysisPanOffset + deltaBars);
}

function finishChartDrag(mainChart) {
  if (!dragState) return;
  if (mainChart?.releasePointerCapture && dragState.pointerId != null) {
    try {
      mainChart.releasePointerCapture(dragState.pointerId);
    } catch {
      // ignore
    }
  }
  dragState = null;
  mainChart?.classList.remove('is-dragging');
}

function chartPointerYRatio(mainChart, clientY) {
  if (!mainChart) return null;
  const rect = mainChart.getBoundingClientRect();
  if (!rect.height) return null;
  const ratio = (clientY - rect.top) / rect.height;
  return Math.min(Math.max(ratio, 0), 1);
}

function bindMainChartInteractions() {
  const mainChart = $('mainChart');
  if (!mainChart) return;

  mainChart.addEventListener('wheel', (event) => {
    if (!state.activeAnalysis) return;
    event.preventDefault();

    if (event.shiftKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) {
      const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
      panAnalysis(Math.round(delta / 36));
      return;
    }

    zoomAnalysis(event.deltaY);
  }, { passive: false });

  mainChart.addEventListener('pointerdown', (event) => {
    if (!state.activeAnalysis || event.button !== 0) return;
    const viewport = currentViewport();
    dragState = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startPanOffset: viewport.panOffset,
      windowSize: viewport.windowSize,
    };
    state.analysisHoverIndex = mainChartIndexFromClientX(mainChart, event.clientX, viewport.rows.length);
    state.analysisHoverYRatio = chartPointerYRatio(mainChart, event.clientY);
    mainChart.classList.add('is-dragging');
    if (mainChart.setPointerCapture) {
      try {
        mainChart.setPointerCapture(event.pointerId);
      } catch {
        // ignore
      }
    }
    requestAnalysisRender();
  });

  mainChart.addEventListener('pointermove', (event) => {
    if (!state.activeAnalysis) return;
    const viewport = currentViewport();
    if (!viewport.rows.length) return;

    if (dragState && dragState.pointerId === event.pointerId) {
      const plotWidth = Math.max(1, (mainChart.clientWidth || 1280) - 60 - 128);
      const pxPerBar = plotWidth / Math.max(1, dragState.windowSize - 1);
      const deltaBars = Math.round((dragState.startX - event.clientX) / Math.max(1, pxPerBar));
      setAnalysisPanOffset(dragState.startPanOffset + deltaBars);
      return;
    }

    const nextIndex = mainChartIndexFromClientX(mainChart, event.clientX, viewport.rows.length);
    const nextYRatio = chartPointerYRatio(mainChart, event.clientY);
    if (nextIndex !== state.analysisHoverIndex || nextYRatio !== state.analysisHoverYRatio) {
      state.analysisHoverIndex = nextIndex;
      state.analysisHoverYRatio = nextYRatio;
      requestAnalysisRender();
    }
  });

  mainChart.addEventListener('pointerup', () => finishChartDrag(mainChart));
  mainChart.addEventListener('pointercancel', () => finishChartDrag(mainChart));
  mainChart.addEventListener('lostpointercapture', () => finishChartDrag(mainChart));
  mainChart.addEventListener('mouseleave', () => {
    if (dragState) return;
    if (state.analysisHoverIndex == null) return;
    state.analysisHoverIndex = null;
    state.analysisHoverYRatio = null;
    requestAnalysisRender();
  });
}

function bindEvents() {
  window.addEventListener('resize', () => {
    if (resizeTimer) window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(rerenderActiveAnalysis, 120);
  });

  $('btnRefresh').addEventListener('click', async () => {
    await refresh('');
  });
  $('btnBacktest').addEventListener('click', async () => {
    backtestLoaded = true;
    await loadBacktest(state.latestDateDir);
  });
  $('btnLoadDate').addEventListener('click', async () => {
    await refresh($('asOfDatePicker').value);
  });
  $('btnLatestDate').addEventListener('click', async () => {
    setDateInputValue(state.catalog?.available_date_max || '');
    await refresh('');
  });
  $('persistenceWindow').addEventListener('change', async () => {
    if (state.activeSector) {
      await loadSectorPersistence(state.activeSector, state.latestDateDir);
    }
    if (state.activeSymbol) {
      await loadStockPersistence(state.activeSymbol, state.activeAsOfDate || state.latestDateDir);
    }
  });
  $('stockFilter').addEventListener('input', () => {
    resetPaginationPage('confirmedStocks');
    resetPaginationPage('setupStocks');
    renderers.renderStockRows(state.latestStocks);
  });

  $('traderTabs')?.addEventListener('click', (event) => {
    const chip = event.target.closest('[data-trader-id]');
    if (!chip) return;
    const dropdown = document.getElementById('traderDropdown');
    if (dropdown) dropdown.value = '';
    applyTraderView(chip.dataset.traderId);
  });

  document.addEventListener('change', (event) => {
    if (event.target.id !== 'traderDropdown') return;
    const value = event.target.value;
    if (value) applyTraderView(value);
  });

  document.querySelectorAll('[data-range-days]').forEach((button) => {
    button.addEventListener('click', () => setAnalysisWindowDays(Number(button.dataset.rangeDays || 0)));
  });
  $('epsRangeBar')?.addEventListener('input', (event) => {
    setEpsWindowStart(event.target.value);
  });

  bindMainChartInteractions();
}

export function initApp() {
  if (initialized) return;
  backtestContext.clear();
  renderers = createRenderers({
    loadSectorMembers,
    loadAnalysis,
    loadLogic,
  });
  setupPageI18n('dashboard', async () => {
    updateChartRangeControls();
    if (initialized) {
      await refresh(state.requestedDateDir || state.latestDateDir || '');
    }
  });
  bindEvents();
  setupTermTips();
  renderTraderTabs('traderTabs', activeTrader);
  updateChartRangeControls();

  // Inject term tooltips into KPI labels
  const kpiMap = { kpiAlphaLabel: 'alpha', kpiBetaLabel: 'beta', kpiPicksLabel: 'recommendation' };
  Object.entries(kpiMap).forEach(([id, key]) => {
    const el = $(id);
    if (el) el.innerHTML = termTip(key, el.textContent);
  });

  refresh();
  initialized = true;
}
