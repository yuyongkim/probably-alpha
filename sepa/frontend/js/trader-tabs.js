import { traderProfiles, getTraderProfile } from './market-wizards-data.js?v=1775482261';
import { marketWizardPeople, peopleSeries } from './market-wizards-people-data.js?v=1775482261';
import { escapeHtml } from './core.js?v=1775482261';
import { txt } from './i18n.js?v=1775482261';

export { traderProfiles };

/* ── Bucket → Archetype mapping ── */

const ARCHETYPES = {
  trend:      { sW: { rs: 0.32, leader: 0.20, alpha: 0.20, beta: 0.16, ret: 0.12 }, kW: { alpha: 0.24, beta: 0.20, ret: 0.14, leader: 0.14, recommendation: 0.12, sector: 0.10, rr: 0.06 }, f: { minAlpha: 50 } },
  macro:      { sW: { leader: 0.28, rs: 0.24, alpha: 0.18, beta: 0.12, ret: 0.18 }, kW: { gamma: 0.20, recommendation: 0.18, sector: 0.18, alpha: 0.15, ret: 0.12, beta: 0.10, eps: 0.05, rr: 0.02 }, f: { minAlpha: 40 } },
  growth:     { sW: { alpha: 0.24, beta: 0.22, rs: 0.24, leader: 0.18, ret: 0.12 }, kW: { alpha: 0.22, beta: 0.20, gamma: 0.18, recommendation: 0.14, sector: 0.10, ret: 0.08, eps: 0.05, leastResistance: 0.03 }, f: { minAlpha: 50 } },
  risk:       { sW: { leader: 0.28, rs: 0.28, beta: 0.18, alpha: 0.14, ret: 0.12 }, kW: { rr: 0.20, recommendation: 0.18, beta: 0.16, leader: 0.14, alpha: 0.12, sector: 0.10, ret: 0.05, leastResistance: 0.05 }, f: { minAlpha: 40 } },
  systems:    { sW: { rs: 0.30, alpha: 0.22, beta: 0.18, leader: 0.16, ret: 0.14 }, kW: { alpha: 0.22, beta: 0.22, ret: 0.16, leader: 0.12, recommendation: 0.10, sector: 0.10, rr: 0.08 }, f: { minAlpha: 45 } },
  value:      { sW: { leader: 0.22, rs: 0.22, ret: 0.22, alpha: 0.18, beta: 0.16 }, kW: { gamma: 0.22, eps: 0.16, recommendation: 0.16, alpha: 0.14, sector: 0.12, ret: 0.10, beta: 0.10 }, f: { minAlpha: 40 } },
  breakout:   { sW: { beta: 0.30, rs: 0.24, alpha: 0.18, leader: 0.18, ret: 0.10 }, kW: { beta: 0.24, alpha: 0.18, leastResistance: 0.16, recommendation: 0.12, sector: 0.12, ret: 0.10, leader: 0.08 }, f: { minAlpha: 45 } },
  momentum:   { sW: { rs: 0.28, alpha: 0.24, beta: 0.20, ret: 0.16, leader: 0.12 }, kW: { alpha: 0.22, ret: 0.20, beta: 0.18, recommendation: 0.14, sector: 0.12, leader: 0.08, rr: 0.06 }, f: { minAlpha: 50 } },
  discretionary: { sW: { leader: 0.24, rs: 0.24, alpha: 0.20, beta: 0.16, ret: 0.16 }, kW: { alpha: 0.20, recommendation: 0.18, leader: 0.16, beta: 0.14, sector: 0.12, ret: 0.10, rr: 0.10 }, f: { minAlpha: 40 } },
  quant:      { sW: { rs: 0.26, alpha: 0.24, beta: 0.20, ret: 0.18, leader: 0.12 }, kW: { alpha: 0.20, beta: 0.20, ret: 0.16, recommendation: 0.14, gamma: 0.12, sector: 0.10, rr: 0.08 }, f: { minAlpha: 45 } },
  psychology: { sW: { leader: 0.24, rs: 0.24, alpha: 0.20, beta: 0.16, ret: 0.16 }, kW: { rr: 0.18, recommendation: 0.18, alpha: 0.16, beta: 0.14, leader: 0.14, sector: 0.10, ret: 0.10 }, f: { minAlpha: 35 } },
  options:    { sW: { rs: 0.26, beta: 0.24, alpha: 0.20, leader: 0.16, ret: 0.14 }, kW: { rr: 0.22, beta: 0.20, alpha: 0.16, recommendation: 0.14, sector: 0.12, ret: 0.08, leader: 0.08 }, f: { minAlpha: 35 } },
  event:      { sW: { leader: 0.26, rs: 0.24, beta: 0.20, alpha: 0.16, ret: 0.14 }, kW: { gamma: 0.18, recommendation: 0.18, sector: 0.16, beta: 0.14, alpha: 0.14, ret: 0.10, rr: 0.10 }, f: { minAlpha: 35 } },
  stocks:     { sW: { alpha: 0.24, rs: 0.24, beta: 0.20, leader: 0.18, ret: 0.14 }, kW: { alpha: 0.22, beta: 0.18, recommendation: 0.16, leader: 0.14, sector: 0.12, ret: 0.10, rr: 0.08 }, f: { minAlpha: 45 } },
};

const BUCKET_KEYWORD_MAP = {
  'trend': 'trend', 'macro': 'macro', 'growth': 'growth', 'earnings': 'growth',
  'risk': 'risk', 'systems': 'systems', 'systematic': 'systems', 'value': 'value',
  'breakout': 'breakout', 'chart': 'breakout', 'momentum': 'momentum', 'swing': 'momentum',
  'discretionary': 'discretionary', 'experience': 'discretionary', 'veteran': 'discretionary',
  'quant': 'quant', 'computing': 'quant', 'data': 'quant', 'probability': 'quant',
  'psychology': 'psychology', 'mindset': 'psychology', 'coaching': 'psychology',
  'performance': 'psychology', 'options': 'options', 'fx': 'macro', 'rates': 'macro',
  'event': 'event', 'contrarian': 'event', 'special situations': 'value',
  'asymmetry': 'event', 'credit': 'value', 'concentration': 'growth',
  'stocks': 'stocks', 'stock': 'stocks', 'long-short': 'stocks', 'short bias': 'risk',
  'recovery': 'risk', 'rebuild': 'discretionary', 'patience': 'trend',
  'pattern': 'breakout', 'structure': 'breakout', 'sepa': 'growth',
  'independent': 'stocks', 'pit trader': 'momentum', 'aggressive': 'momentum',
  'speed': 'momentum', 'leader': 'trend', 'pivotal': 'trend',
  'alternative data': 'quant', 'social signals': 'quant', 'compounding': 'systems',
  'team': 'systems', 'process': 'systems', 'portfolio': 'discretionary',
  'balance': 'discretionary', 'adaptive': 'discretionary', 'field work': 'growth',
  'theme': 'macro', 'narrative': 'macro', 'repetition': 'systems',
  'turning points': 'macro', 'interpretation': 'discretionary',
  'judgment': 'discretionary', 'instinct': 'discretionary',
  'short-term': 'momentum', 'timing': 'momentum',
  'opportunity': 'momentum', 'rotation': 'momentum',
  'multi-strategy': 'discretionary',
};

function resolveArchetype(person) {
  const bucket = String(person.bucket || '').toLowerCase();
  const parts = bucket.split(/\s*\/\s*/);

  for (const part of parts) {
    const trimmed = part.trim();
    if (BUCKET_KEYWORD_MAP[trimmed]) return BUCKET_KEYWORD_MAP[trimmed];
  }

  for (const kw of (person.keywords || [])) {
    const lower = kw.toLowerCase().trim();
    if (BUCKET_KEYWORD_MAP[lower]) return BUCKET_KEYWORD_MAP[lower];
  }

  return 'stocks';
}

function buildAutoPreset(person) {
  const archetypeKey = resolveArchetype(person);
  const arch = ARCHETYPES[archetypeKey] || ARCHETYPES.stocks;
  return {
    headline: `Auto-generated preset based on ${person.name}'s ${person.bucket} style.`,
    formula: `Archetype: ${archetypeKey}`,
    sectorWeights: { ...arch.sW },
    stockWeights: { ...arch.kW },
    filters: { ...arch.f },
  };
}

/**
 * Get a complete profile for any person by id.
 * Uses hand-crafted profiles for the 6 anchors, auto-generates for others.
 */
export function getFullProfile(personId) {
  const handCrafted = traderProfiles.find((p) => p.id === personId);
  if (handCrafted) return handCrafted;

  const person = marketWizardPeople.find((p) => p.id === personId);
  if (!person) return null;

  return {
    id: person.id,
    name: person.name,
    englishName: person.englishName || person.name,
    style: person.bucket,
    philosophy: [person.brief],
    checkpoints: [],
    koreaPlaybook: [],
    projectHooks: [],
    fit: { focus: person.bucket, timeframe: '-', trigger: '-', risk: '-' },
    preset: buildAutoPreset(person),
  };
}

/* ── Scoring utils (same as before) ── */

function clamp(value, min = 0, max = 100) {
  const num = Number(value);
  if (!Number.isFinite(num)) return min;
  return Math.max(min, Math.min(max, num));
}

function epsScore(status) {
  return ({ strong_growth: 100, positive_growth: 82, stable_growth: 68, stable: 52, mixed: 38, negative_growth: 10 })[String(status || '').trim()] ?? 0;
}

function leastResistanceScore(status) {
  return ({ up_least_resistance: 100, breakout_ready: 92, pullback_in_uptrend: 78, range: 52, downtrend: 10 })[String(status || '').trim()] ?? 0;
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
  return {
    alpha: clamp(item?.alpha_score),
    beta: clamp(Number(item?.beta_confidence || 0) * 10),
    gamma: clamp(Number(item?.gamma_score || 0) * 10),
    ret: clamp(item?.ret120_pct),
    leader: clamp((Number(item?.leader_stock_score || 0) / 120) * 100),
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

function passesFilters(profile, metrics) {
  const filters = profile?.preset?.filters || {};
  if (filters.minAlpha && metrics.alpha < filters.minAlpha) return false;
  if (filters.minBeta && metrics.beta < filters.minBeta) return false;
  if (filters.minGamma && metrics.gamma < filters.minGamma) return false;
  if (filters.minRecommendation && metrics.recommendation < filters.minRecommendation) return false;
  if (filters.requirePositiveEps && metrics.eps < 68) return false;
  return true;
}

/* ── Public API ── */

export function applyTraderPreset(traderId, sectors, stocks, recommendations) {
  if (!traderId || traderId === 'default') return null;

  const profile = getFullProfile(traderId);
  if (!profile || !profile.preset) return null;

  const recMap = new Map((recommendations || []).map((item) => [item.symbol, item]));

  const rankedSectors = sectors
    .map((item) => {
      const metrics = normalizedSectorMetrics(item);
      const presetScore = weightedScore(profile.preset.sectorWeights, metrics);
      return { ...item, preset_score: presetScore, original_leader_score: item.leader_score };
    })
    .sort((a, b) => b.preset_score - a.preset_score);

  const sectorScoreMap = new Map(rankedSectors.map((item) => [item.sector, item.preset_score]));

  const rankedStocks = stocks
    .map((item) => {
      const rec = recMap.get(item.symbol) || null;
      const metrics = normalizedStockMetrics(item, sectorScoreMap.get(item.sector) || 0, rec);
      return {
        ...item,
        preset_score: weightedScore(profile.preset.stockWeights, metrics),
        original_leader_stock_score: item.leader_stock_score,
        _passes_filter: passesFilters(profile, metrics),
      };
    })
    .filter((item) => item._passes_filter)
    .sort((a, b) => b.preset_score - a.preset_score);

  return { profile, sectors: rankedSectors, stocks: rankedStocks };
}

/**
 * Render the trader tabs UI: "Default" button + all wizards grouped by series.
 */
export function renderTraderTabs(containerId, activeId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const defaultLabel = txt({ ko: 'SEPA 기본', en: 'Default SEPA' });
  const defaultActive = (!activeId || activeId === 'default') ? 'is-active' : '';
  const anchorIds = new Set(traderProfiles.map((p) => p.id));

  const seriesGroups = peopleSeries.map((series) => {
    const people = marketWizardPeople.filter((p) => p.series === series.id);
    if (!people.length) return '';
    const chips = people.map((p) => {
      const active = p.id === activeId ? 'is-active' : '';
      const anchor = anchorIds.has(p.id) ? ' anchor' : '';
      const displayName = p.name.split(' ').pop();
      return `<button type="button" class="selector-chip${anchor ? ' selector-chip--anchor' : ''} ${active}" data-trader-id="${escapeHtml(p.id)}" title="${escapeHtml(p.name)} — ${escapeHtml(p.bucket)}">${escapeHtml(displayName)}</button>`;
    }).join('');
    const labelMap = {
      'Market Wizards': '마법사 1편',
      'The New Market Wizards': '마법사 2편',
      'Stock Market Wizards': '주식 마법사',
      'Hedge Fund Market Wizards': '헤지펀드 마법사',
      'Unknown Market Wizards': '마법사 최신편',
    };
    const displayLabel = labelMap[series.label] || series.label;
    return `<div class="trader-series-group"><span class="trader-series-label">${escapeHtml(displayLabel)}</span>${chips}</div>`;
  }).join('');

  container.innerHTML = `
    <div class="trader-tabs-all">
      <button type="button" class="selector-chip selector-chip--default ${defaultActive}" data-trader-id="default">${escapeHtml(defaultLabel)}</button>
      ${seriesGroups}
    </div>
  `;
}
