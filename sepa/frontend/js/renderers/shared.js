import {
  $,
  companyCell,
  escapeHtml,
  fmtCompact,
  fmtDate,
  fmtKrwCompact,
  fmtNum,
  fmtPct,
  fmtPlainPct,
  fmtPrice,
  fmtRR,
  fmtShares,
  fmtSignedPct,
  scoreBadge,
  state,
} from '../core.js?v=1775472534';
import { txt } from '../i18n.js?v=1775472534';

export function activeStockRecord(items = state.latestStocks) {
  return (items || []).find((item) => item?.symbol === state.activeSymbol) || null;
}

export function activeSectorRecord(items = state.latestSectors) {
  return (items || []).find((item) => item?.sector === state.activeSector) || null;
}

export function buildSectorContext(item = {}, extra = {}) {
  return {
    sector: item?.sector || extra?.sector || '',
    sectorBucket: item?.sector_bucket || extra?.sectorBucket || '',
    sectorLeadershipReady: Boolean(item?.sector_leadership_ready ?? item?.leadership_ready ?? extra?.sectorLeadershipReady),
    sectorLeaderScore: Number(item?.sector_leader_score ?? item?.leader_score ?? extra?.sectorLeaderScore ?? 0),
    source: extra?.source || '',
    dateDir: extra?.dateDir || state.latestDateDir || '',
  };
}

export function labelCheck(flag) {
  return `<span class="flag ${flag ? 'good' : 'mid'}">${escapeHtml(flag ? txt({ ko: 'Pass', en: 'Pass' }) : txt({ ko: 'Watch', en: 'Watch' }))}</span>`;
}

export function breakoutLabel(value) {
  const labels = {
    sector_breakout_confirmed: { ko: 'Confirmed breakout', en: 'Confirmed breakout' },
    sector_breakout_setup: { ko: 'Breakout setup', en: 'Breakout setup' },
    sector_not_ready: { ko: 'Not ready', en: 'Not ready' },
  };
  return txt(labels[String(value || '').trim()] || { ko: String(value || '-'), en: String(value || '-') });
}

export function sectorStateText(item = {}) {
  if (item?.leadership_ready || item?.sector_leadership_ready) {
    return txt({ ko: 'Confirmed leader', en: 'Confirmed leader' });
  }
  if (String(item?.sector_bucket || item?.stock_bucket || '').includes('setup')) {
    return txt({ ko: 'Setup candidate', en: 'Setup candidate' });
  }
  if (String(item?.sector_bucket || '').includes('watch')) {
    return txt({ ko: 'Watchlist', en: 'Watchlist' });
  }
  return txt({ ko: 'Monitoring', en: 'Monitoring' });
}

export function heatTone(score, ready = false) {
  if (ready || Number(score || 0) >= 65) return 'good';
  if (Number(score || 0) >= 35) return 'mid';
  return 'bad';
}

export function metricNote(label, value, note = '') {
  return `
    <article class="mini-stat-card">
      <label>${escapeHtml(label)}</label>
      <strong>${escapeHtml(value)}</strong>
      ${note ? `<small>${escapeHtml(note)}</small>` : ''}
    </article>
  `;
}

export function fmtSignedPctPrecise(value, digits = 2) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return `${num >= 0 ? '+' : ''}${num.toFixed(digits)}%`;
}

export function recommendationPlanMarkup(plan = {}, compact = false) {
  if (!plan || typeof plan !== 'object') {
    return `<span class="omega-plan omega-plan--empty">${escapeHtml(txt({ ko: 'Plan n/a', en: 'Plan n/a' }))}</span>`;
  }

  const tone = compact ? ' omega-plan--tight' : '';
  return `
    <div class="omega-plan${tone}">
      <span class="omega-plan__item">
        <span class="omega-plan__label">E</span>
        <strong>${escapeHtml(fmtPrice(plan.entry))}</strong>
      </span>
      <span class="omega-plan__item">
        <span class="omega-plan__label">S</span>
        <strong>${escapeHtml(fmtPrice(plan.stop))}</strong>
      </span>
      <span class="omega-plan__item">
        <span class="omega-plan__label">T</span>
        <strong>${escapeHtml(fmtPrice(plan.target))}</strong>
      </span>
      <span class="omega-plan__item">
        <span class="omega-plan__label">Qty</span>
        <strong>${escapeHtml(fmtShares(plan.qty))}</strong>
      </span>
    </div>
  `;
}

export function backtestSessionMarkup(session = {}) {
  if (!session || !session.date) {
    return `<div class="bucket-session bucket-session--muted">${escapeHtml(txt({ ko: 'Session move unavailable', en: 'Session move unavailable' }))}</div>`;
  }

  const changePct = Number(session.change_pct);
  const changeAbs = Number(session.change_abs);
  let tone = 'bucket-session--flat';
  if (Number.isFinite(changePct) && changePct > 0) tone = 'bucket-session--up';
  if (Number.isFinite(changePct) && changePct < 0) tone = 'bucket-session--down';

  return `
    <div class="bucket-session ${tone}">
      <strong>${escapeHtml(Number.isFinite(changePct) ? fmtSignedPct(changePct) : '-')}</strong>
      <span>${escapeHtml(Number.isFinite(changeAbs) ? fmtPrice(changeAbs) : '-')}</span>
      <small>${escapeHtml(fmtDate(session.date))}</small>
    </div>
  `;
}

export function bucketWindowLabel(bucket = {}) {
  const from = fmtDate(bucket?.date_from || '');
  const to = fmtDate(bucket?.date_to || '');
  if (!bucket?.date_from && !bucket?.date_to) return '-';
  if (bucket?.date_from === bucket?.date_to) return to;
  return `${from} - ${to}`;
}

export function summaryReadyText(ready, count) {
  if (ready) {
    return txt({
      ko: `${count} names aligned`,
      en: `${count} names aligned`,
    });
  }
  return txt({
    ko: `${count} names tracked`,
    en: `${count} names tracked`,
  });
}

export function companyMarkup(item) {
  return companyCell(item);
}

export function scoreMarkup(value) {
  return scoreBadge(value);
}

export function retMarkup(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return escapeHtml(fmtPlainPct(num));
}

export function rrMarkup(value) {
  return escapeHtml(fmtRR(value));
}

export function catalogMetaText(catalog = {}, summary = {}) {
  return txt({
    ko: `Dates ${fmtDate(catalog.available_date_min)} -> ${fmtDate(catalog.available_date_max)} | snapshots ${fmtCompact(catalog.snapshot_count)} | sectors ${summary.counts?.leader_sectors ?? 0}/${catalog.sector_count ?? 0}`,
    en: `Dates ${fmtDate(catalog.available_date_min)} -> ${fmtDate(catalog.available_date_max)} | snapshots ${fmtCompact(catalog.snapshot_count)} | sectors ${summary.counts?.leader_sectors ?? 0}/${catalog.sector_count ?? 0}`,
  });
}

export function setDynamicText(id, value) {
  const node = $(id);
  if (!node) return;
  node.dataset.dynamic = '1';
  node.textContent = value;
}

export function defaultRowMarkup(colspan, message) {
  return `<tr><td colspan="${colspan}">${escapeHtml(message)}</td></tr>`;
}

export function stockContext(item = {}, source = '') {
  return buildSectorContext(item, {
    source,
    sector: item?.sector,
    sectorBucket: item?.sector_bucket,
    sectorLeadershipReady: item?.sector_leadership_ready,
    sectorLeaderScore: item?.sector_leader_score,
    dateDir: state.latestDateDir,
  });
}

export function recommendationMeta(item = {}) {
  const why = item?.why || {};
  return `
    <div class="company-cell">
      <strong>${escapeHtml(item?.sector || '-')}</strong>
      <small>${escapeHtml(why.eps_status || '-')} / ${escapeHtml(why.least_resistance || '-')}</small>
    </div>
  `;
}

export function sectorHeatValue(item = {}) {
  const value = Number(item?.leader_score || 0);
  return `${Math.max(0.12, Math.min(0.42, value / 180)).toFixed(2)}`;
}

export function ret120Summary(item = {}) {
  return Number.isFinite(Number(item?.avg_ret120))
    ? fmtPct(item.avg_ret120)
    : Number.isFinite(Number(item?.ret120))
      ? fmtPct(item.ret120)
      : '-';
}

export function companyFactMarkup(analysis = {}) {
  const facts = analysis?.company_facts || {};
  return `
    <div class="summary-card">
      <label>${escapeHtml(txt({ ko: 'Market cap', en: 'Market cap' }))}</label>
      <strong>${escapeHtml(fmtKrwCompact(facts.market_cap_estimated || facts.market_cap_latest))}</strong>
      <small>${escapeHtml(txt({ ko: 'Shares', en: 'Shares' }))} ${escapeHtml(fmtCompact(facts.shares_outstanding))}</small>
    </div>
  `;
}
