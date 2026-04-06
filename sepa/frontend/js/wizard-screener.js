/**
 * Wizard Screener — Multi-strategy screening dashboard.
 * Fetches wizard-screen.json + strategies metadata from API
 * and renders a comprehensive screener view.
 */

import { txt, setupPageI18n } from './i18n.js?v=1775488167';

const DEFAULT_API = '';
const CATEGORIES = [
  { id: 'all', label: { ko: '전체', en: 'All' } },
  { id: 'trend_following', label: { ko: '추세추종', en: 'Trend Following' } },
  { id: 'growth_momentum', label: { ko: '성장 모멘텀', en: 'Growth Momentum' } },
  { id: 'swing', label: { ko: '단기 스윙', en: 'Swing Trading' } },
  { id: 'contrarian_value', label: { ko: '역발상/가치', en: 'Contrarian/Value' } },
  { id: 'volatility_contraction', label: { ko: '변동성 수축', en: 'Volatility Contraction' } },
  { id: 'macro_liquidity', label: { ko: '매크로/유동성', en: 'Macro/Liquidity' } },
];

const CAT_COLORS = {
  trend_following: '#4db8ff',
  growth_momentum: '#6ee7a8',
  swing: '#ffb84d',
  contrarian_value: '#ff8f8f',
  volatility_contraction: '#c4b5fd',
  macro_liquidity: '#7fd4ff',
};

let state = {
  strategies: [],
  screenData: null,
  activeCategory: 'all',
  activeStrategy: null,
};

function apiBase() {
  const el = document.getElementById('apiBase');
  return el ? el.value.replace(/\/+$/, '') : DEFAULT_API;
}

async function fetchJSON(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

// ── Render Category Filters ──
function renderCategoryFilters() {
  const el = document.getElementById('categoryFilters');
  el.innerHTML = CATEGORIES.map(c =>
    `<button class="selector-chip${state.activeCategory === c.id ? ' is-active' : ''}" data-cat="${c.id}">${txt(c.label)}</button>`
  ).join('');
  el.querySelectorAll('.selector-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      state.activeCategory = btn.dataset.cat;
      renderCategoryFilters();
      renderStrategyGrid();
    });
  });
}

// ── Render Strategy Cards ──
function renderStrategyGrid() {
  const el = document.getElementById('strategyGrid');
  const hitRates = state.screenData?.strategy_hit_rates || {};
  const filtered = state.activeCategory === 'all'
    ? state.strategies
    : state.strategies.filter(s => s.category === state.activeCategory);

  el.innerHTML = filtered.map(s => {
    const hits = hitRates[s.name] || 0;
    const color = CAT_COLORS[s.category] || '#4db8ff';
    return `
      <article class="wizard-card wizard-strat-card" data-strategy="${esc(s.name)}" style="cursor:pointer;border-left:3px solid ${color}">
        <div class="wizard-card__top">
          <div>
            <h3>${esc(s.name)}</h3>
            <small style="color:var(--muted)">${esc(s.trader)} &middot; ${esc(s.category_display || s.category)}</small>
          </div>
          <span class="score ${hits > 3 ? 'good' : hits > 0 ? 'mid' : 'zero-hits'}">${hits} ${txt({ ko: '매칭', en: 'hits' })}</span>
        </div>
        <p style="color:var(--muted);font-size:13px;line-height:1.6;margin-bottom:10px">${esc(s.description || '')}</p>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
          ${(s.kiwoom_conditions || []).slice(0, 3).map(c =>
            `<span class="chip" style="font-size:10px;padding:2px 6px">${esc(c)}</span>`
          ).join('')}
          ${(s.kiwoom_conditions || []).length > 3 ? `<span class="chip" style="font-size:10px;padding:2px 6px;opacity:.6">+${s.kiwoom_conditions.length - 3}</span>` : ''}
        </div>
      </article>`;
  }).join('');

  el.querySelectorAll('.wizard-strat-card').forEach(card => {
    card.addEventListener('click', () => showStrategyDetail(card.dataset.strategy));
  });
}

// ── Render Top Stocks Table ──
function renderTopStocks() {
  const results = state.screenData?.results || [];
  const el = document.getElementById('topStockRows');
  if (!results.length) {
    el.innerHTML = `<tr><td colspan="6" class="empty-state">${txt({ ko: '스크리닝 데이터가 없습니다. 파이프라인을 먼저 실행하세요.', en: 'No screening data available. Run the pipeline first.' })}</td></tr>`;
    return;
  }

  el.innerHTML = results.slice(0, 30).map((r, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${esc(r.name || r.symbol)}</strong><br><small style="color:var(--muted)">${esc(r.symbol)}</small></td>
      <td><span class="score ${r.strategies_passed >= 5 ? 'good' : r.strategies_passed >= 2 ? 'mid' : 'bad'}">${r.strategies_passed} / ${r.strategies_total}</span></td>
      <td>${r.best_score.toFixed(1)}</td>
      <td>${r.avg_score.toFixed ? r.avg_score.toFixed(1) : r.avg_score}</td>
      <td>
        <div style="display:flex;flex-wrap:wrap;gap:4px">
          ${(r.passed_strategies || []).map(s => {
            const cat = (r.details || []).find(d => d.strategy === s)?.category || '';
            const c = CAT_COLORS[cat] || '#4db8ff';
            return `<span class="chip" style="font-size:10px;padding:2px 6px;border-left:2px solid ${c}">${esc(s)}</span>`;
          }).join('')}
        </div>
      </td>
    </tr>
  `).join('');
}

// ── Strategy Detail View ──
function showStrategyDetail(stratName) {
  state.activeStrategy = stratName;
  const section = document.getElementById('strategyDetail');
  section.style.display = '';

  const strat = state.strategies.find(s => s.name === stratName);
  if (!strat) return;

  document.getElementById('detailKicker').textContent = strat.category_display || strat.category;
  document.getElementById('detailTitle').textContent = `${strat.trader} — ${strat.name}`;
  document.getElementById('detailDesc').textContent = strat.description || '';
  document.getElementById('detailCondCount').textContent = `${(strat.kiwoom_conditions || []).length} ${txt({ ko: '조건', en: 'conditions' })}`;

  // Kiwoom conditions
  const condEl = document.getElementById('detailConditions');
  condEl.innerHTML = (strat.kiwoom_conditions || []).map((c, i) => `
    <div class="definition-card">
      <label>${txt({ ko: '조건', en: 'Condition' })} ${i + 1}</label>
      <strong style="font-size:14px;font-family:'IBM Plex Mono',monospace">${esc(c)}</strong>
    </div>
  `).join('');

  // Matching stocks
  const results = state.screenData?.results || [];
  const matches = [];
  for (const r of results) {
    const detail = (r.details || []).find(d => d.strategy === stratName);
    if (detail && detail.passed) {
      matches.push({ symbol: r.symbol, ...detail });
    }
  }

  const rowsEl = document.getElementById('detailStockRows');
  if (!matches.length) {
    rowsEl.innerHTML = `<tr><td colspan="5" class="empty-state">${txt({ ko: '현재 이 전략에 매칭되는 종목이 없습니다.', en: 'No stocks match this strategy currently.' })}</td></tr>`;
  } else {
    rowsEl.innerHTML = matches.map((m, i) => `
      <tr>
        <td>${i + 1}</td>
        <td><strong>${esc(m.name || m.symbol)}</strong><br><small style="color:var(--muted)">${esc(m.symbol)}</small></td>
        <td><span class="score ${m.score >= 80 ? 'good' : m.score >= 50 ? 'mid' : 'bad'}">${m.score.toFixed(1)}</span></td>
        <td>${m.conditions_met} / ${m.conditions_total}</td>
        <td>
          <div style="display:flex;flex-wrap:wrap;gap:4px">
            ${(m.conditions || []).map(c =>
              `<span class="chip ${c.passed ? 'good' : ''}" style="font-size:10px;padding:2px 6px">${c.passed ? '✓' : '✗'} ${esc(c.name)}</span>`
            ).join('')}
          </div>
        </td>
      </tr>
    `).join('');
  }

  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── KPI Update ──
function updateKPIs() {
  const d = state.screenData || {};
  document.getElementById('wsDate').textContent = d.date_dir || '-';
  document.getElementById('wsStocksTotal').textContent = d.total_stocks_screened || 0;
  document.getElementById('wsStocksPassing').textContent = d.stocks_passing_any || 0;
  document.getElementById('wsStrategies').textContent = d.total_strategies || state.strategies.length;

  const hits = d.strategy_hit_rates || {};
  const topEntry = Object.entries(hits).sort((a, b) => b[1] - a[1])[0];
  document.getElementById('wsTopHitRate').textContent = topEntry ? `${topEntry[1]}` : '-';
  document.getElementById('strategyCountBadge').textContent = `${state.strategies.length} strategies`;
}

// ── Load Data ──
async function loadData() {
  try {
    const [strats, screen] = await Promise.all([
      fetchJSON(`${apiBase()}/api/wizards/strategies`),
      fetchJSON(`${apiBase()}/api/wizards/screen`).catch(() => ({ items: [] })),
    ]);
    state.strategies = strats.items || strats;
    // Unwrap: API returns {date_dir, items: {results, ...}} or direct {results, ...}
    const raw = screen.items || screen;
    state.screenData = (raw && raw.results) ? raw : screen;
  } catch (e) {
    console.error('Wizard screener load error:', e);
    state.strategies = [];
    state.screenData = null;
  }
  render();
}

function render() {
  updateKPIs();
  renderCategoryFilters();
  renderStrategyGrid();
  renderTopStocks();
}

// ── Init ──
function init() {
  setupPageI18n('wizard-screener');
  document.getElementById('btnRefresh')?.addEventListener('click', loadData);
  document.getElementById('btnCloseDetail')?.addEventListener('click', () => {
    document.getElementById('strategyDetail').style.display = 'none';
  });

  loadData();
}

try { init(); } catch (e) { console.error('Wizard screener init error:', e); }
