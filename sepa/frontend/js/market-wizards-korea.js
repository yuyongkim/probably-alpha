import { getTraderProfile, traderProfiles } from './market-wizards-data.js?v=1775480720';
import { setupPageI18n, txt } from './i18n.js?v=1775480720';
import { termTip, setupTermTips } from './term-tips.js?v=1775480720';
import {
  $,
  escapeHtml,
  fetchJSON,
  fmtDate,
  fmtKrwCompact,
  fmtCompact,
  fmtNum,
  fmtPct,
  fmtPlainPct,
  fmtPrice,
  toDateToken,
} from './core.js?v=1775480720';
import {
  movingAvg,
  sparklineSvg,
  epsBarChart,
  financialAnalysisTable,
  financialTableMarkup,
  sessionMarkup,
  checksMarkup,
  badgeCls,
  renderCompanyProfile,
  setupProfileDialogClose,
  openStockProfile,
} from './renderers/stock-profile.js?v=1775480720';

const DEFAULT_API_BASE = `${window.location.protocol}//${window.location.hostname || '127.0.0.1'}:8000`;

const state = {
  catalog: null,
  dateDir: '',
  requestedDateDir: '',
  sectors: [],
  stocks: [],
  recMap: new Map(),
  weeklyBuckets: [],
};

/* ── Helpers (page-specific) ── */

function clamp(value, min = 0, max = 100) {
  const num = Number(value);
  if (!Number.isFinite(num)) return min;
  return Math.max(min, Math.min(max, num));
}

function setDateInputValue(value) {
  const input = $('presetDatePicker');
  if (!input) return;
  const token = toDateToken(value);
  input.value = /^\d{8}$/.test(token) ? fmtDate(token) : '';
}

function companyCell(item) {
  return `<div class="company-cell"><strong>${escapeHtml(item.name || item.symbol || '-')}</strong><small>${escapeHtml(txt({ ko: '티커', en: 'Ticker' }))} ${escapeHtml(item.symbol || '-')}</small></div>`;
}

function factorLabel(key) {
  const labels = {
    alpha: { ko: 'Alpha', en: 'Alpha' },
    beta: { ko: 'Beta', en: 'Beta' },
    gamma: { ko: 'Gamma', en: 'Gamma' },
    ret: { ko: '120일 수익률', en: '120D return' },
    leader: { ko: '기본 주도 점수', en: 'Base leader score' },
    recommendation: { ko: '추천 점수', en: 'Recommendation score' },
    sector: { ko: '섹터 프리셋 점수', en: 'Sector preset score' },
    rr: { ko: 'R 배수', en: 'R multiple' },
    eps: { ko: 'EPS 상태', en: 'EPS state' },
    leastResistance: { ko: '최소 저항', en: 'Least resistance' },
    rs: { ko: '섹터 RS', en: 'Sector RS' },
  };
  return txt(labels[key] || key);
}

function breakoutLabel(value) {
  const map = {
    sector_breakout_confirmed: { ko: 'Confirmed breakout', en: 'Confirmed breakout' },
    sector_breakout_setup: { ko: 'Breakout setup', en: 'Breakout setup' },
    sector_not_ready: { ko: 'Not ready', en: 'Not ready' },
  };
  return txt(map[String(value || '').trim()] || { ko: String(value || '-'), en: String(value || '-') });
}

/* ── Preset scoring logic ── */

function epsScore(status) {
  const map = { strong_growth: 100, positive_growth: 82, stable_growth: 68, stable: 52, mixed: 38, negative_growth: 10 };
  return map[String(status || '').trim()] ?? 0;
}

function leastResistanceScore(status) {
  const map = { up_least_resistance: 100, breakout_ready: 92, pullback_in_uptrend: 78, range: 52, downtrend: 10 };
  return map[String(status || '').trim()] ?? 0;
}

function rrScore(rrRatio) {
  return clamp((Number(rrRatio || 0) / 2.0) * 100);
}

function normalizedSectorMetrics(item) {
  return {
    rs: clamp(item?.sector_rs_percentile),
    alpha: clamp(Number(item?.alpha_ratio || 0) * 100),
    beta: clamp(Number(item?.beta_ratio || 0) * 100),
    leader: clamp(item?.leader_score),
    ret: clamp(Number(item?.avg_ret120 || 0) * 100),
  };
}

function normalizedStockMetrics(item, sectorScore, rec) {
  const retPct = item?.ret120_pct != null ? item.ret120_pct : (item?.ret120 != null ? Number(item.ret120) * 100 : 0);
  const leaderScore = item?.leader_stock_score ?? item?.avg_leader_stock_score ?? 0;
  // Map actual JSON field names to metric keys
  const ttScore = Number(item?.trend_template_score ?? item?.alpha_score ?? 0);
  const betaConf = Number(item?.beta_confidence ?? item?.vcp_confidence ?? 0);
  const gammaVal = Number(item?.gamma_score ?? 0);
  return {
    alpha: clamp(ttScore * 100),
    beta: clamp(betaConf * 100),
    gamma: clamp(gammaVal * 100),
    ret: clamp(retPct),
    leader: clamp((Number(leaderScore) / 120) * 100),
    recommendation: clamp(rec?.recommendation_score),
    sector: clamp(sectorScore),
    rr: rrScore(rec?.risk_plan?.rr_ratio),
    eps: epsScore(rec?.why?.eps_status),
    leastResistance: leastResistanceScore(rec?.why?.least_resistance),
  };
}

function weightedScore(weights, metrics) {
  return Object.entries(weights || {}).reduce(
    (total, [key, weight]) => total + (Number(weight || 0) * Number(metrics[key] || 0)),
    0,
  );
}

function topReasons(weights, metrics, count = 3) {
  return Object.entries(weights || {})
    .map(([key, weight]) => ({ label: factorLabel(key), contribution: Number(weight || 0) * Number(metrics[key] || 0) }))
    .filter((item) => item.contribution > 0)
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, count)
    .map((item) => item.label);
}

function passesFilters(profile, metrics) {
  const filters = profile?.preset?.filters || {};
  if (filters.minAlpha && metrics.alpha < filters.minAlpha) return false;
  if (filters.minBeta && metrics.beta < filters.minBeta) return false;
  if (filters.minGamma && metrics.gamma < filters.minGamma) return false;
  if (filters.minRecommendation && metrics.recommendation < filters.minRecommendation) return false;
  if (filters.requirePositiveEps && metrics.eps < 68) return false;
  return true;
}

function buildPresetRanking(profile) {
  const sectorScoreMap = new Map();
  const sectorResults = state.sectors
    .map((item) => {
      const metrics = normalizedSectorMetrics(item);
      const presetScore = weightedScore(profile.preset.sectorWeights, metrics);
      sectorScoreMap.set(item.sector, presetScore);
      return { ...item, preset_score: presetScore, reason_labels: topReasons(profile.preset.sectorWeights, metrics) };
    });

  // Build per-sector stock rankings for all sectors first
  const stocksBySector = new Map();
  for (const sector of sectorResults) {
    const sectorStocks = state.stocks
      .filter((item) => item.sector === sector.sector)
      .map((item) => {
        const rec = state.recMap.get(item.symbol) || null;
        const metrics = normalizedStockMetrics(item, sectorScoreMap.get(item.sector) || 0, rec);
        return {
          ...item,
          metrics,
          recommendation_score: rec?.recommendation_score ?? null,
          eps_status: rec?.why?.eps_status ?? '',
          least_resistance: rec?.why?.least_resistance ?? '',
          rr_ratio: rec?.risk_plan?.rr_ratio ?? null,
          preset_score: weightedScore(profile.preset.stockWeights, metrics),
          reason_labels: topReasons(profile.preset.stockWeights, metrics),
        };
      })
      .filter((item) => passesFilters(profile, item.metrics))
      .sort((a, b) => b.preset_score - a.preset_score)
      .slice(0, 5);
    stocksBySector.set(sector.sector, sectorStocks);
  }

  // Only sectors with qualifying stocks are real leader sectors.
  const rankedSectors = sectorResults
    .filter((s) => (stocksBySector.get(s.sector) || []).length > 0)
    .sort((a, b) => {
      return b.preset_score - a.preset_score;
    });

  const topSectors = rankedSectors.slice(0, 5);
  const defaultStocks = stocksBySector.get(topSectors[0]?.sector) || [];
  return { sectors: topSectors, stocksBySector, stocks: defaultStocks };
}

/* ── Rendering ── */

function buttonMarkup(profile, activeId) {
  const active = profile.id === activeId ? 'is-active' : '';
  return `<a class="selector-chip ${active}" href="#${escapeHtml(profile.id)}">${escapeHtml(profile.name)}</a>`;
}

function renderPreset(profile) {
  const presetExplain = $('presetExplain');
  const presetFormula = $('presetFormula');
  const presetSectorRows = $('presetSectorRows');
  const presetStockRows = $('presetStockRows');
  const presetDateMeta = $('presetDateMeta');
  if (!presetExplain || !presetFormula || !presetSectorRows || !presetStockRows || !presetDateMeta) return;

  if (!state.sectors.length || !state.stocks.length) {
    presetExplain.innerHTML = `<div class="definition-card"><label>${escapeHtml(txt({ ko: '상태', en: 'Status' }))}</label><p>${escapeHtml(txt({ ko: '프리셋 후보를 불러오지 못했습니다.', en: 'Preset candidates could not be loaded.' }))}</p></div>`;
    presetFormula.textContent = txt({ ko: '프리셋 수식을 준비하는 중...', en: 'Preparing preset formula...' });
    presetSectorRows.innerHTML = `<tr><td colspan="5">${escapeHtml(txt({ ko: '섹터 데이터가 없습니다.', en: 'No sector data available.' }))}</td></tr>`;
    presetStockRows.innerHTML = `<tr><td colspan="6">${escapeHtml(txt({ ko: '종목 데이터가 없습니다.', en: 'No stock data available.' }))}</td></tr>`;
    return;
  }

  const ranking = buildPresetRanking(profile);
  const requestLabel = state.requestedDateDir && state.requestedDateDir !== state.dateDir
    ? txt({ ko: `요청 ${fmtDate(state.requestedDateDir)} / 계산 ${fmtDate(state.dateDir)}`, en: `Requested ${fmtDate(state.requestedDateDir)} / resolved ${fmtDate(state.dateDir)}` })
    : txt({ ko: `기준일 ${fmtDate(state.dateDir)}`, en: `Base date ${fmtDate(state.dateDir)}` });
  presetDateMeta.textContent = txt({
    ko: `${requestLabel} | 섹터 후보 ${state.sectors.length} | 종목 후보 ${state.stocks.length}`,
    en: `${requestLabel} | sector candidates ${state.sectors.length} | stock candidates ${state.stocks.length}`,
  });

  const filterSummary = [
    profile.preset.filters.minAlpha ? `Alpha ${profile.preset.filters.minAlpha}+` : null,
    profile.preset.filters.minBeta ? `Beta ${profile.preset.filters.minBeta}+` : null,
    profile.preset.filters.minGamma ? `Gamma ${profile.preset.filters.minGamma}+` : null,
    profile.preset.filters.minRecommendation ? `Recommendation ${profile.preset.filters.minRecommendation}+` : null,
    profile.preset.filters.requirePositiveEps ? 'Positive EPS trend required' : null,
  ].filter(Boolean).join(' | ') || txt({ ko: '추가 필터 없음', en: 'No extra filters' });

  presetExplain.innerHTML = `
    <div class="definition-card">
      <label>${escapeHtml(txt({ ko: '해석', en: 'Interpretation' }))}</label>
      <p>${escapeHtml(profile.preset.headline)}</p>
    </div>
    <div class="definition-card">
      <label>${escapeHtml(txt({ ko: '필터', en: 'Filters' }))}</label>
      <p>${escapeHtml(filterSummary)}</p>
    </div>
    <div class="definition-card">
      <label>${escapeHtml(txt({ ko: '방법', en: 'Method' }))}</label>
      <p>${escapeHtml(txt({ ko: '기본 SEPA 섹터/종목 후보를 이 트레이더 전용 가중치로 다시 정렬합니다. 핵심 엔진 위에 철학 레이어를 얹는 방식입니다.', en: 'The base SEPA sector and stock candidates are re-ranked through this trader-specific weight set. It is a philosophy overlay on top of the core engine.' }))}</p>
    </div>
  `;
  presetFormula.textContent = profile.preset.formula;

  const thPS = $('thPresetSectorScore');
  if (thPS) thPS.innerHTML = termTip('preset_score', 'Preset Score');
  const thBS = $('thBaseSectorScore');
  if (thBS) thBS.innerHTML = termTip('sector', 'Base Leader Score');
  const thPSt = $('thPresetStockScore');
  if (thPSt) thPSt.innerHTML = termTip('preset_score', 'Preset Score');
  const thBSt = $('thBaseStockScore');
  if (thBSt) thBSt.innerHTML = termTip('leader', 'Base Leader Score');

  // Render preset results as rich sector cards (same style as bottom view)
  const presetCardsEl = $('presetSectorCards');
  if (presetCardsEl) {
    presetCardsEl.innerHTML = ranking.sectors.map((sector) => {
      const stocks = ranking.stocksBySector.get(sector.sector) || [];
      const stockRows = stocks.map((item, i) => {
        const closes = item.sparkline || [];
        const price = item.price || (closes.length ? closes[closes.length - 1] : null);
        const ret = item.ret120_pct != null ? fmtPlainPct(item.ret120_pct) : (item.ret120 != null ? fmtPlainPct(item.ret120 * 100) : '-');
        return `
          <tr class="clickable-row" data-symbol="${escapeHtml(item.symbol)}">
            <td>${i + 1}</td>
            <td>${companyCell(item)}</td>
            <td class="sparkline-cell">${sparklineSvg(closes)}</td>
            <td class="price-cell">${escapeHtml(fmtPrice(price))}</td>
            <td><span class="score ${item.leader_stock_score >= 70 ? 'good' : item.leader_stock_score >= 40 ? 'mid' : 'bad'}">${fmtNum(item.leader_stock_score, 1)}</span></td>
            <td>${escapeHtml(ret)}</td>
            <td>${fmtNum(item.preset_score, 2)}</td>
            <td><small style="color:var(--muted)">${escapeHtml(item.reason_labels.slice(0,2).join(', '))}</small></td>
          </tr>`;
      }).join('');

      return `
        <article class="panel sector-grouped-card" style="margin-bottom:12px">
          <div class="sector-grouped-card__head">
            <div>
              <h3>${escapeHtml(sector.sector)}</h3>
              <div class="sector-grouped-card__badges">
                <span class="flag ${sector.leadership_ready ? 'good' : 'mid'}">${sector.leadership_ready ? 'Confirmed' : 'Watchlist'}</span>
              </div>
            </div>
            <div class="sector-grouped-card__stats">
              <span><strong>${fmtNum(sector.preset_score, 1)}</strong><small>Preset</small></span>
              <span><strong>${fmtNum(sector.leader_score, 1)}</strong><small>Leader</small></span>
              <span><strong>${sector.alpha_count || '-'}/${sector.universe_count || '-'}</strong><small>Alpha</small></span>
            </div>
          </div>
          <table class="sector-grouped-card__table">
            <thead><tr>
              <th>#</th><th>${txt({ ko: '종목', en: 'Stock' })}</th><th>${txt({ ko: '차트', en: 'Chart' })}</th>
              <th>${txt({ ko: '현재가', en: 'Price' })}</th><th>${txt({ ko: '점수', en: 'Score' })}</th>
              <th>120D</th><th>Preset</th><th>${txt({ ko: '핵심', en: 'Reason' })}</th>
            </tr></thead>
            <tbody>${stockRows || `<tr><td colspan="8">${escapeHtml(txt({ ko: '통과 종목 없음', en: 'No stocks passed' }))}</td></tr>`}</tbody>
          </table>
        </article>`;
    }).join('') || `<p style="color:var(--muted);padding:20px">${escapeHtml(txt({ ko: '프리셋 로직을 통과한 섹터가 없습니다.', en: 'No sectors passed.' }))}</p>`;

    // Click handler for stock profile
    presetCardsEl.querySelectorAll('.clickable-row[data-symbol]').forEach((row) => {
      row.addEventListener('click', () => openStockProfile(row.dataset.symbol));
    });
  }

  // Legacy table fallback (hidden if cards exist)
  if (presetSectorRows && !presetCardsEl) {
    presetSectorRows.innerHTML = ranking.sectors.map((item, index) => `
      <tr class="clickable-row${index === 0 ? ' is-active' : ''}" data-sector="${escapeHtml(item.sector)}">
        <td>${index + 1}</td><td>${escapeHtml(item.sector)}</td>
        <td>${item.preset_score.toFixed(2)}</td><td>${Number(item.leader_score || 0).toFixed(2)}</td>
        <td>${escapeHtml(item.reason_labels.join(' | '))}</td>
      </tr>
    `).join('');
  }
}

function renderDetail(profile) {
  const detail = $('wizardDetail');
  const meta = $('wizardMeta');
  const selector = $('wizardSelector');
  if (!detail || !meta || !selector) return;

  selector.innerHTML = traderProfiles.map((profileItem) => buttonMarkup(profileItem, profile.id)).join('');
  meta.innerHTML = `
    <span class="chip" style="background:#2563eb;color:#fff;font-weight:600">${escapeHtml(profile.style)}</span>
    <span class="chip" style="background:#7c3aed;color:#fff">${escapeHtml(profile.fit.focus)}</span>
    <span class="chip" style="background:#0d9488;color:#fff">${escapeHtml(profile.fit.timeframe)}</span>
    <span class="chip" style="background:#d97706;color:#fff">${escapeHtml(profile.fit.trigger)}</span>
  `;

  detail.innerHTML = `
    <section class="strategy-hero panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">${escapeHtml(txt({ ko: '국내 적용 연구실', en: 'KR Application Lab' }))}</p>
          <h2>${escapeHtml(profile.name)}</h2>
          <p class="panel-caption">${escapeHtml(profile.style)}</p>
        </div>
      </div>
      <div class="logic-copy">
        ${profile.philosophy.map((line) => `<p>${escapeHtml(line)}</p>`).join('')}
      </div>
    </section>
    <section class="strategy-grid">
      <article class="panel strategy-card">
        <h3>${escapeHtml(txt({ ko: '한국 증시 적용', en: 'Korea Market Translation' }))}</h3>
        <ul class="wizard-list">
          ${profile.koreaPlaybook.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </article>
      <article class="panel strategy-card">
        <h3>${escapeHtml(txt({ ko: 'SEPA에서 확인할 곳', en: 'Where To Check In SEPA' }))}</h3>
        <ul class="wizard-list">
          ${profile.projectHooks.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </article>
    </section>
    <section class="strategy-grid">
      <article class="panel strategy-card">
        <h3>${escapeHtml(txt({ ko: '체크리스트', en: 'Checklist' }))}</h3>
        <ul class="wizard-list">
          ${profile.checkpoints.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </article>
      <article class="panel strategy-card">
        <h3>${escapeHtml(txt({ ko: '실행 순서', en: 'Execution Order' }))}</h3>
        <ol class="wizard-list wizard-list--ordered">
          <li>${escapeHtml(txt({ ko: '상위 주도섹터부터 시작합니다.', en: 'Start from the top leader sectors.' }))}</li>
          <li>${escapeHtml(txt({ ko: '해당 섹터 안에서 RS와 구조가 가장 좋은 종목을 좁힙니다.', en: 'Within those sectors, isolate the stocks with the best RS and structure.' }))}</li>
          <li>${escapeHtml(txt({ ko: '이 트레이더 관점으로 가격, 거래량, EPS를 다시 확인합니다.', en: 'Re-check price, volume, and EPS through this trader\'s lens.' }))}</li>
          <li>${escapeHtml(txt({ ko: '손절 위치와 R 배수가 여전히 맞을 때만 진행합니다.', en: 'Only move forward if the stop placement and R multiple still make sense.' }))}</li>
          <li>${escapeHtml(txt({ ko: '과거 날짜와 백테스트 버킷으로 같은 패턴이 반복되는지 확인합니다.', en: 'Use past dates and backtest buckets to see whether the pattern repeats.' }))}</li>
        </ol>
      </article>
    </section>
  `;

  renderPreset(profile);
}

function activeProfile() {
  const raw = window.location.hash.replace(/^#/, '').trim();
  return getTraderProfile(raw);
}

function syncHash() {
  const profile = activeProfile();
  if (window.location.hash.replace(/^#/, '').trim() !== profile.id) {
    window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#${profile.id}`);
  }
  renderDetail(profile);
  renderWeeklyPerformance(profile);
}

/* ── Weekly 12-week preset performance ── */

function applyPresetToWeeklyBucket(profile, bucket) {
  const sectors = (bucket.sectors || []).map((item) => {
    const metrics = normalizedSectorMetrics(item);
    return { ...item, preset_score: weightedScore(profile.preset.sectorWeights, metrics) };
  }).sort((a, b) => b.preset_score - a.preset_score);

  const sectorScoreMap = new Map(sectors.map((s) => [s.sector, s.preset_score]));

  const stocks = (bucket.stocks || []).map((item) => {
    const metrics = normalizedStockMetrics(item, sectorScoreMap.get(item.sector) || 0, null);
    return { ...item, preset_score: weightedScore(profile.preset.stockWeights, metrics), _passes: passesFilters(profile, metrics) };
  }).filter((s) => s._passes).sort((a, b) => b.preset_score - a.preset_score);

  const avgScore = sectors.length
    ? sectors.slice(0, 3).reduce((s, item) => s + item.preset_score, 0) / Math.min(3, sectors.length)
    : 0;

  return { sectors: sectors.slice(0, 3), stocks: stocks.slice(0, 5), avgScore };
}

function renderWeeklyPerformance(profile) {
  const chartEl = $('weeklyChart');
  const rowsEl = $('weeklyRows');
  const metaEl = $('weeklyMeta');
  if (!chartEl || !rowsEl) return;

  const buckets = state.weeklyBuckets || [];
  if (!buckets.length) {
    if (metaEl) metaEl.textContent = txt({ ko: '주간 데이터 없음', en: 'No weekly data' });
    chartEl.innerHTML = '';
    rowsEl.innerHTML = `<tr><td colspan="4">${escapeHtml(txt({ ko: '주간 백테스트 데이터를 불러오지 못했습니다.', en: 'No weekly backtest data available.' }))}</td></tr>`;
    return;
  }

  const ranked = buckets.map((bucket) => ({ bucket, result: applyPresetToWeeklyBucket(profile, bucket) }));
  const maxScore = Math.max(...ranked.map((r) => r.result.avgScore), 1);
  const bestIdx = ranked.reduce((best, r, i) => r.result.avgScore > ranked[best].result.avgScore ? i : best, 0);

  if (metaEl) {
    metaEl.textContent = txt({ ko: `${profile.name} · ${ranked.length}주`, en: `${profile.name} · ${ranked.length}W` });
  }

  chartEl.innerHTML = ranked.map((r, i) => {
    const pct = Math.max(2, (r.result.avgScore / maxScore) * 100);
    const best = i === bestIdx ? ' is-best' : '';
    const weekLabel = r.bucket.bucket || '';
    return `
      <div class="weekly-bar${best}">
        <span class="weekly-bar__score">${r.result.avgScore.toFixed(0)}</span>
        <div class="weekly-bar__fill" style="height:${pct}%"></div>
        <span class="weekly-bar__label">${escapeHtml(weekLabel.replace(/^\d{4}-/, ''))}</span>
      </div>
    `;
  }).join('');

  rowsEl.innerHTML = ranked.map((r) => {
    const sectorChips = r.result.sectors.map((s) =>
      `<span class="chip">${escapeHtml(s.sector)} <small>${s.preset_score.toFixed(0)}</small></span>`
    ).join('') || '<span class="chip">-</span>';
    const stockChips = r.result.stocks.map((s) =>
      `<span class="chip">${escapeHtml(s.name || s.symbol)} <small>${s.preset_score.toFixed(0)}</small></span>`
    ).join('') || '<span class="chip">-</span>';
    return `
      <tr>
        <td>${escapeHtml(r.bucket.bucket || '-')}</td>
        <td>${r.bucket.snapshot_count || 0}</td>
        <td><div class="weekly-sector-chips">${sectorChips}</div></td>
        <td><div class="weekly-stock-chips">${stockChips}</div></td>
      </tr>
    `;
  }).join('');
}

/* ── Sector Grouped View + Company Profile ── */

function renderSectorGroupedView(items) {
  const root = $('koreaGroupedView');
  const meta = $('sectorOverviewMeta');
  if (!root) return;

  const MAX_SECTORS = 8;
  const MAX_STOCKS_PER_SECTOR = 3;

  if (!items || !items.length) {
    root.innerHTML = `<div class="empty-state">${escapeHtml(txt({ ko: '섹터 그룹 데이터가 없습니다.', en: 'No sector-grouped data available.' }))}</div>`;
    if (meta) meta.textContent = '-';
    return;
  }

  // Only show confirmed + watchlist sectors (exclude emerging)
  const filtered = items.filter((g) => {
    const bucket = (g.sector_meta || {}).sector_bucket || '';
    return bucket === 'confirmed_leader' || bucket === 'watchlist';
  });

  const trimmed = filtered.slice(0, MAX_SECTORS).map((g) => ({
    ...g,
    stocks: (g.stocks || []).slice(0, MAX_STOCKS_PER_SECTOR),
  }));
  const totalStocks = trimmed.reduce((s, g) => s + g.stocks.length, 0);
  if (meta) meta.textContent = `${trimmed.length} sectors · ${totalStocks} stocks`;

  root.innerHTML = trimmed.map((group) => {
    const m = group.sector_meta || {};
    const ready = m.leadership_ready;
    const tone = ready ? 'good' : (m.leader_score >= 35 ? 'mid' : 'bad');

    const stockRows = (group.stocks || []).map((stock, i) => {
      const closes = stock.sparkline || [];
      const ma20arr = movingAvg(closes, 20);
      const ma60arr = movingAvg(closes, 60);
      const ma20val = ma20arr.length ? ma20arr[ma20arr.length - 1] : null;
      const ma60val = ma60arr.length ? ma60arr[ma60arr.length - 1] : null;
      return `
      <tr class="clickable-row" data-symbol="${escapeHtml(stock.symbol)}">
        <td>${i + 1}</td>
        <td>
          <div class="company-cell">
            <strong>${escapeHtml(stock.name || stock.symbol)}</strong>
            <small>${escapeHtml(stock.symbol)}</small>
          </div>
        </td>
        <td class="sparkline-cell">${sparklineSvg(stock.sparkline)}</td>
        <td class="price-cell">${(stock.price || (stock.sparkline && stock.sparkline.length ? stock.sparkline[stock.sparkline.length - 1] : null)) ? fmtPrice(stock.price || stock.sparkline[stock.sparkline.length - 1]) : '-'}</td>
        <td class="ma-cell"><span style="color:#f0c040">${ma20val != null ? fmtPrice(ma20val) : '-'}</span><br><span style="color:#60a0ff">${ma60val != null ? fmtPrice(ma60val) : '-'}</span></td>
        <td><span class="score ${stock.leader_stock_score >= 70 ? 'good' : stock.leader_stock_score >= 40 ? 'mid' : 'bad'}">${fmtNum(stock.leader_stock_score, 1)}</span></td>
        <td>${fmtPlainPct(stock.ret120_pct)}</td>
        <td>${fmtNum(stock.beta_confidence, 2)}</td>
        <td><button type="button" class="profile-btn" data-symbol="${escapeHtml(stock.symbol)}" title="${txt({ ko: '기업개요', en: 'Company Profile' })}">&#x2139;</button></td>
      </tr>
    `}).join('');

    return `
      <article class="panel sector-grouped-card tone-border-${tone}">
        <div class="sector-grouped-card__head">
          <div>
            <h3>${escapeHtml(group.sector)}</h3>
            <div class="sector-grouped-card__badges">
              <span class="flag ${ready ? 'good' : 'mid'}">${ready ? termTip('confirmed', 'Confirmed') : termTip('watchlist', 'Watchlist')}</span>
              <span class="flag mid">${termTip('sector_breakout', breakoutLabel(m.breakout_state))}</span>
            </div>
          </div>
          <div class="sector-grouped-card__stats">
            <span><strong>${fmtNum(m.leader_score, 1)}</strong><small>${termTip('sector', 'Score')}</small></span>
            <span><strong>${m.alpha_count || 0}/${m.universe_count || 0}</strong><small>${termTip('alpha', 'Alpha')}</small></span>
            <span><strong>${fmtPct(m.avg_ret120)}</strong><small>${termTip('ret', '120D')}</small></span>
          </div>
        </div>
        <table class="sector-grouped-card__table">
          <thead><tr><th>#</th><th>${txt({ ko: '종목', en: 'Stock' })}</th><th>${termTip('sparkline', txt({ ko: '차트', en: 'Chart' }))}</th><th>${txt({ ko: '현재가', en: 'Price' })}</th><th>MA20/60</th><th>${termTip('leader', txt({ ko: '점수', en: 'Score' }))}</th><th>${termTip('ret', '120D')}</th><th>${termTip('beta', 'Beta')}</th><th></th></tr></thead>
          <tbody>${stockRows || '<tr><td colspan="9">-</td></tr>'}</tbody>
        </table>
      </article>
    `;
  }).join('');

  root.querySelectorAll('.profile-btn[data-symbol]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      openCompanyProfile(btn.dataset.symbol);
    });
  });

  root.querySelectorAll('.clickable-row[data-symbol]').forEach((row) => {
    row.addEventListener('click', (e) => {
      if (e.target.closest('.profile-btn')) return;
      openCompanyProfile(row.dataset.symbol);
    });
  });
}

async function openCompanyProfile(symbol) {
  const dialog = $('companyProfileDialog');
  if (!dialog || !symbol) return;
  $('profileName').textContent = symbol;
  $('profileContent').innerHTML = `<p>${escapeHtml(txt({ ko: '로딩 중...', en: 'Loading...' }))}</p>`;
  dialog.showModal();

  try {
    const encodedSym = encodeURIComponent(symbol);
    const data = await fetchJSON(`${DEFAULT_API_BASE}/api/stock/${encodedSym}/overview`);
    const p = data.profile || data;

    $('profileName').textContent = `${p.name || symbol} (${symbol})`;
    renderCompanyProfile(data);

    // Phase 2: load heavy detail in background
    fetchJSON(`${DEFAULT_API_BASE}/api/stock/${encodedSym}/overview?detail=true`).then((full) => {
      if ($('companyProfileDialog')?.open) renderCompanyProfile(full);
    }).catch(() => {});
  } catch (err) {
    $('profileContent').innerHTML = `<p style="color:var(--bad)">${escapeHtml(String(err))}</p>`;
  }
}

/* ── Data loading ── */

async function loadSectorGrouped() {
  try {
    const data = await fetchJSON(`${DEFAULT_API_BASE}/api/leaders/sectors-grouped`);
    renderSectorGroupedView(data.items || []);
  } catch (error) {
    console.warn('Sector grouped load failed:', error);
    renderSectorGroupedView([]);
  }
}

async function loadWeeklyBuckets() {
  try {
    const data = await fetchJSON(`${DEFAULT_API_BASE}/api/backtest/leaders?period=weekly&buckets=12&sector_limit=10&stock_limit=20`);
    state.weeklyBuckets = data.items || [];
  } catch (error) {
    console.warn('Weekly backtest load failed:', error);
    state.weeklyBuckets = [];
  }
}

async function loadPresetContext(dateDir = '') {
  const token = toDateToken(dateDir);
  const query = token ? `?date_dir=${encodeURIComponent(token)}` : '';

  const [catalog, summary, sectors, stocks, recommendations] = await Promise.all([
    fetchJSON(`${DEFAULT_API_BASE}/api/catalog`),
    fetchJSON(`${DEFAULT_API_BASE}/api/summary${query}`),
    fetchJSON(`${DEFAULT_API_BASE}/api/leaders/sectors${query}`),
    fetchJSON(`${DEFAULT_API_BASE}/api/leaders/stocks${query}`),
    fetchJSON(token ? `${DEFAULT_API_BASE}/api/recommendations${query}` : `${DEFAULT_API_BASE}/api/recommendations/latest`),
  ]);

  state.catalog = catalog;
  state.requestedDateDir = token;
  state.dateDir = summary.date_dir || sectors.date_dir || stocks.date_dir || '';
  state.sectors = sectors.items || [];
  state.stocks = stocks.items || [];
  state.recMap = new Map((recommendations.items || []).map((item) => [item.symbol, item]));

  const picker = $('presetDatePicker');
  if (picker && catalog) {
    picker.min = fmtDate(catalog.available_date_min);
    picker.max = fmtDate(catalog.available_date_max);
  }
  setDateInputValue(state.dateDir);
  if (picker && state.dateDir) {
    picker.value = fmtDate(state.dateDir);
  }

  const url = new URL(window.location.href);
  if (token) {
    url.searchParams.set('date', token);
  } else {
    url.searchParams.delete('date');
  }
  window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);

  renderPreset(activeProfile());
}

/* ── Init ── */

function bindEvents() {
  $('btnPresetLoadDate')?.addEventListener('click', async () => {
    await loadPresetContext($('presetDatePicker')?.value || '');
  });
  $('btnPresetLatest')?.addEventListener('click', async () => {
    await loadPresetContext('');
  });
  window.addEventListener('hashchange', () => syncHash());
}

async function init() {
  bindEvents();
  setupTermTips();
  setupProfileDialogClose();
  setupPageI18n('market-wizards-korea', () => {
    renderDetail(activeProfile());
    renderWeeklyPerformance(activeProfile());
  });

  const todayToken = new Date().toISOString().slice(0, 10);
  const picker = $('presetDatePicker');
  if (picker) picker.value = todayToken;

  syncHash();
  const initialDate = new URL(window.location.href).searchParams.get('date') || '';
  try {
    await Promise.all([
      loadPresetContext(initialDate),
      loadWeeklyBuckets(),
      loadSectorGrouped(),
    ]);
    renderWeeklyPerformance(activeProfile());
  } catch (error) {
    console.error('Korea preset init error:', error);
    const msg = String(error);
    const stack = error?.stack ? `\n${error.stack}` : '';
    $('presetDateMeta').textContent = `${txt({ ko: '프리셋 로딩 실패', en: 'Preset load failed' })}: ${msg} (API: ${DEFAULT_API_BASE})`;
    $('presetExplain').innerHTML = `<div class="definition-card" style="border:2px solid #e44;padding:12px"><label>Error</label><p>${escapeHtml(msg)}</p><p style="color:#aaa;font-size:12px">API base: ${escapeHtml(DEFAULT_API_BASE)}<br>Origin: ${escapeHtml(window.location.origin)}<br>Sectors loaded: ${state.sectors.length}<br>Stocks loaded: ${state.stocks.length}</p><pre style="color:#e88;font-size:11px;white-space:pre-wrap">${escapeHtml(stack)}</pre></div>`;
    $('presetSectorRows').innerHTML = `<tr><td colspan="5">Failed to load sector data.</td></tr>`;
    $('presetStockRows').innerHTML = `<tr><td colspan="6">Failed to load stock data.</td></tr>`;
  }
}

// ── Trader Screening (today's picks) ──
async function runTraderScreen() {
  const preset = $('traderScreenPreset')?.value || 'minervini';
  const rows = $('traderScreenRows');
  const meta = $('traderScreenMeta');
  rows.innerHTML = `<tr><td colspan="8" class="empty-state">${txt({ ko: '스크리닝 중...', en: 'Screening...' })}</td></tr>`;
  meta.textContent = '';

  try {
    const data = await fetchJSON(`${DEFAULT_API_BASE}/api/screen/trader?preset=${preset}&limit=10`);
    const items = data.items || [];
    meta.innerHTML = `<strong>${escapeHtml(data.trader || preset)}</strong> — ${escapeHtml(data.description || '')} | ${txt({ ko: '대상', en: 'Universe' })}: ${fmtNum(data.screened_symbols || 0)} | ${txt({ ko: '통과', en: 'Passed' })}: ${fmtNum(data.passed || 0)} | ${txt({ ko: '기준일', en: 'Date' })}: ${data.date || 'latest'}`;

    if (!items.length) {
      rows.innerHTML = `<tr><td colspan="8" class="empty-state">${txt({ ko: '조건에 맞는 종목이 없습니다.', en: 'No stocks match the conditions.' })}</td></tr>`;
      return;
    }

    rows.innerHTML = items.map((s, i) => `
      <tr>
        <td>${i + 1}</td>
        <td><strong>${escapeHtml(s.name || s.symbol)}</strong><br><small style="color:var(--muted)">${escapeHtml(s.symbol)}</small></td>
        <td>${escapeHtml(s.sector || '-')}</td>
        <td><span class="score ${s.tt_passed >= 7 ? 'good' : s.tt_passed >= 5 ? 'mid' : 'bad'}">${s.tt_passed}/8</span></td>
        <td>${s.rs_percentile?.toFixed(0) || '-'}%</td>
        <td style="text-align:right">${fmtPrice(s.close)}</td>
        <td style="text-align:right">${fmtPrice(s.high52)}</td>
        <td style="text-align:right"><strong>${s.score?.toFixed(1) || '-'}</strong></td>
      </tr>
    `).join('');
  } catch (e) {
    rows.innerHTML = `<tr><td colspan="8" class="empty-state">${txt({ ko: '스크리닝 실패', en: 'Screening failed' })}: ${escapeHtml(String(e))}</td></tr>`;
  }
}

$('btnTraderScreen')?.addEventListener('click', runTraderScreen);

// ── Trader Consensus (multi-preset scan) ──
const PRESET_COLORS = {
  minervini: '#6ee7a8', oneil: '#4db8ff', dennis: '#ffb84d', seykota: '#ff9966',
  hite: '#c4b5fd', jones: '#ffd700', driehaus: '#ff8f8f', schwartz: '#7fd4ff',
  raschke: '#e0a0ff', weinstein: '#90caf9',
};
const PRESET_LABELS = {
  minervini: 'Minervini', oneil: "O'Neil", dennis: 'Dennis', seykota: 'Seykota',
  hite: 'Hite', jones: 'Jones', driehaus: 'Driehaus', schwartz: 'Schwartz',
  raschke: 'Raschke', weinstein: 'Weinstein',
};

async function runConsensus() {
  const rows = $('consensusRows');
  rows.innerHTML = `<tr><td colspan="7" class="empty-state">${txt({ ko: '스캔 중... (10개 프리셋, 약 30초)', en: 'Scanning... (10 presets, ~30s)' })}</td></tr>`;

  try {
    const data = await fetchJSON(`${DEFAULT_API_BASE}/api/screen/multi?limit=20`);
    const items = data.items || [];

    if (!items.length) {
      rows.innerHTML = `<tr><td colspan="7" class="empty-state">${txt({ ko: '매칭 종목 없음', en: 'No matches' })}</td></tr>`;
      return;
    }

    rows.innerHTML = items.map((s, i) => `
      <tr>
        <td>${i + 1}</td>
        <td><strong>${escapeHtml(s.name || s.symbol)}</strong><br><small style="color:var(--muted)">${escapeHtml(s.symbol)}</small></td>
        <td>${escapeHtml(s.sector || '-')}</td>
        <td>${s.tt_passed}/8</td>
        <td>${s.rs_percentile?.toFixed(0) || '-'}%</td>
        <td><strong>${s.score?.toFixed(1) || '-'}</strong></td>
        <td>
          <div style="display:flex;flex-wrap:wrap;gap:3px">
            ${(s.presets || []).map(p => `<span style="font-size:10px;padding:2px 6px;border-radius:8px;background:${PRESET_COLORS[p] || '#666'}20;color:${PRESET_COLORS[p] || '#aaa'};border:1px solid ${PRESET_COLORS[p] || '#666'}40">${PRESET_LABELS[p] || p}</span>`).join('')}
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    rows.innerHTML = `<tr><td colspan="7" class="empty-state">${txt({ ko: '스캔 실패', en: 'Scan failed' })}: ${escapeHtml(String(e))}</td></tr>`;
  }
}

$('btnConsensus')?.addEventListener('click', runConsensus);

// Load preset dropdown from API
async function loadTraderPresets() {
  try {
    const data = await fetchJSON(`${DEFAULT_API_BASE}/api/backtest/presets`);
    const items = data.items || [];
    const sel = $('traderScreenPreset');
    if (!sel) return;
    items.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.name} (${p.family})`;
      sel.appendChild(opt);
    });
    if (items.length) sel.value = items[0].id;
  } catch (e) {
    console.warn('Failed to load presets:', e);
  }
}
loadTraderPresets();

init();
