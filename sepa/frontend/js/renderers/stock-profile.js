/**
 * stock-profile.js — Shared stock-profile dialog rendering helpers.
 *
 * Extracted from sector-grouped.js and market-wizards-korea.js to eliminate
 * duplicated sparkline / EPS / financial / profile markup code.
 */
import {
  escapeHtml,
  fetchJSON,
  fmtNum,
  fmtPrice,
  fmtKrwCompact,
  fmtCompact,
  fmtPlainPct,
  fmtPct,
  $,
} from '../core.js?v=1775488167';
import { txt } from '../i18n.js?v=1775488167';

/* ── Moving Average helper ── */

export function movingAvg(data, period) {
  const out = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) { out.push(null); continue; }
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += data[j];
    out.push(sum / period);
  }
  return out;
}

/* ── Sparkline SVG with MA20/MA60 and overlap-prevention labels ── */

export function sparklineSvg(closes, width = 240, height = 80, endDate = '') {
  if (!closes || closes.length < 2) return '';
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const padL = 2;
  const padR = 42;
  const padY = 2;
  const padBot = endDate ? 14 : 0;
  const w = width - padL - padR;
  const h = height - padY * 2 - padBot;

  const toX = (i) => padL + (i / (closes.length - 1)) * w;
  const toY = (v) => padY + h - ((v - min) / range) * h;

  const points = closes.map((v, i) => `${toX(i).toFixed(1)},${toY(v).toFixed(1)}`);
  const last = closes[closes.length - 1];
  const first = closes[0];
  const color = last >= first ? '#8af0b8' : '#ff9e9e';
  const fillColor = last >= first ? 'rgba(138,240,184,0.08)' : 'rgba(255,158,158,0.08)';

  const linePath = `M${points.join('L')}`;
  const fillPath = `${linePath}L${toX(closes.length - 1).toFixed(1)},${(padY + h).toFixed(1)}L${padL.toFixed(1)},${(padY + h).toFixed(1)}Z`;

  // MA lines
  const ma20 = movingAvg(closes, 20);
  const ma60 = movingAvg(closes, 60);

  const maPath = (arr, clr) => {
    const pts = [];
    arr.forEach((v, i) => { if (v !== null) pts.push(`${toX(i).toFixed(1)},${toY(v).toFixed(1)}`); });
    if (pts.length < 2) return '';
    return `<path d="M${pts.join('L')}" fill="none" stroke="${clr}" stroke-width="1" opacity="0.7"/>`;
  };

  // High / Low / Last price labels — with overlap prevention
  const hiY = toY(max);
  const loY = toY(min);
  let lastLabelY = toY(last);
  const minGap = 12;
  // Nudge lastY away from hiY and loY if too close
  if (Math.abs(hiY - lastLabelY) < minGap && Math.abs(loY - lastLabelY) < minGap) {
    // Sandwiched between both — place in the middle
    lastLabelY = (hiY + loY) / 2;
  } else if (Math.abs(hiY - lastLabelY) < minGap) {
    lastLabelY = hiY + minGap;
  } else if (Math.abs(loY - lastLabelY) < minGap) {
    lastLabelY = loY - minGap;
  }
  const fmtK = (v) => v >= 10000 ? `${(v / 1000).toFixed(0)}K` : v >= 1000 ? `${(v / 1000).toFixed(1)}K` : `${Math.round(v)}`;

  const labels = `
    <line x1="${padL}" y1="${hiY.toFixed(1)}" x2="${(padL + w).toFixed(1)}" y2="${hiY.toFixed(1)}" stroke="rgba(138,240,184,0.2)" stroke-dasharray="2,3"/>
    <line x1="${padL}" y1="${loY.toFixed(1)}" x2="${(padL + w).toFixed(1)}" y2="${loY.toFixed(1)}" stroke="rgba(255,158,158,0.2)" stroke-dasharray="2,3"/>
    <text x="${width - 2}" y="${(hiY + 3).toFixed(1)}" text-anchor="end" fill="#8af0b8" font-size="9">${fmtK(max)}</text>
    <text x="${width - 2}" y="${(loY + 3).toFixed(1)}" text-anchor="end" fill="#ff9e9e" font-size="9">${fmtK(min)}</text>
    <text x="${width - 2}" y="${(lastLabelY + 3).toFixed(1)}" text-anchor="end" fill="${color}" font-size="9" font-weight="bold">${fmtK(last)}</text>
  `;

  // MA legend
  const legend = `
    <text x="${padL + 1}" y="${padY + 8}" fill="#f0c040" font-size="8" opacity="0.7">MA20</text>
    <text x="${padL + 30}" y="${padY + 8}" fill="#60a0ff" font-size="8" opacity="0.7">MA60</text>
  `;

  // X-axis date labels (estimated from endDate and ~120 trading days)
  let dateLabels = '';
  if (endDate) {
    const raw = String(endDate).replace(/-/g, '');
    if (raw.length === 8) {
      const endY = raw.slice(2, 4);
      const endM = raw.slice(4, 6);
      // Estimate start: ~6 months before end
      let startM = parseInt(endM) - 6;
      let startY = parseInt(endY);
      if (startM <= 0) { startM += 12; startY -= 1; }
      let midM = parseInt(endM) - 3;
      let midY = parseInt(endY);
      if (midM <= 0) { midM += 12; midY -= 1; }
      const fmt = (y, m) => `${String(y).padStart(2, '0')}/${String(m).padStart(2, '0')}`;
      const dateY = padY + h + padBot - 2;
      dateLabels = `
        <text x="${padL}" y="${dateY}" fill="var(--muted,#666)" font-size="8">${fmt(startY, startM)}</text>
        <text x="${padL + w / 2}" y="${dateY}" text-anchor="middle" fill="var(--muted,#666)" font-size="8">${fmt(midY, midM)}</text>
        <text x="${padL + w}" y="${dateY}" text-anchor="end" fill="var(--muted,#666)" font-size="8">${endY}/${endM}</text>
      `;
    }
  }

  return `<svg width="${width}" height="${height + padBot}" viewBox="0 0 ${width} ${height + padBot}" class="sparkline-svg">
    ${labels}
    <path d="${fillPath}" fill="${fillColor}"/>
    <path d="${linePath}" fill="none" stroke="${color}" stroke-width="1.5"/>
    ${maPath(ma20, '#f0c040')}
    ${maPath(ma60, '#60a0ff')}
    ${legend}
    ${dateLabels}
  </svg>`;
}

/* ── EPS Trend — SVG bar chart (annual + quarterly) ── */

export function epsBarChart(epsData) {
  if (!epsData || epsData.length < 1) return '';

  const annual = epsData.filter((e) => e.period_type === 'annual' || (!e.period_type && /^\d{4}$/.test(e.period)));
  const quarterly = epsData.filter((e) => e.period_type === 'quarterly' || (!e.period_type && /Q/.test(e.period)));

  // If no split available, treat all as quarterly
  const sections = [];
  if (annual.length) sections.push({ rows: annual.slice(-10), title: txt({ ko: '연간 EPS', en: 'Annual EPS' }) });
  if (quarterly.length) sections.push({ rows: quarterly.slice(-20), title: txt({ ko: '분기 EPS', en: 'Quarterly EPS' }) });
  if (!sections.length) sections.push({ rows: epsData.slice(-12), title: 'EPS' });

  return sections.map(({ rows, title }) => _epsBarSvg(rows, title)).join('');
}

function _epsBarSvg(rows, title) {
  if (!rows.length) return '';

  const fmtK = (v) => {
    if (Math.abs(v) >= 10000) return `${(v / 1000).toFixed(0)}K`;
    return v.toLocaleString('ko-KR', { maximumFractionDigits: 0 });
  };
  const fmtYoy = (v) => {
    const n = Number(v);
    if (!Number.isFinite(n) || n === 0) return '';
    return `${n >= 0 ? '+' : ''}${n.toFixed(0)}%`;
  };
  const label = (p) => (p || '').replace(/^20/, "'").replace(/Q/, 'Q');

  const vals = rows.map((e) => Number(e.eps) || 0);
  const maxAbs = Math.max(...vals.map(Math.abs), 1);

  const W = Math.max(rows.length * 48, 280);
  const H = 140;
  const padL = 4;
  const padR = 4;
  const padTop = 16;
  const padBot = 36;
  const chartH = H - padTop - padBot;
  const chartW = W - padL - padR;
  const barW = Math.min(28, (chartW / rows.length) * 0.65);
  const gap = chartW / rows.length;

  // zero line
  const zeroY = padTop + (maxAbs / (maxAbs * 2)) * chartH;
  const scale = (v) => (v / maxAbs) * (chartH / 2);

  let bars = '';
  let labels = '';
  let yoyLabels = '';

  rows.forEach((e, i) => {
    const v = Number(e.eps) || 0;
    const x = padL + i * gap + (gap - barW) / 2;
    const h = Math.abs(scale(v));
    const y = v >= 0 ? zeroY - h : zeroY;
    const color = v >= 0 ? 'var(--good, #4caf50)' : 'var(--bad, #f44336)';

    bars += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW.toFixed(1)}" height="${Math.max(h, 1).toFixed(1)}" fill="${color}" opacity="0.8" rx="2"/>`;

    // Value on top of bar
    const valY = v >= 0 ? y - 3 : y + h + 11;
    bars += `<text x="${(x + barW / 2).toFixed(1)}" y="${valY.toFixed(1)}" text-anchor="middle" fill="var(--text, #ccc)" font-size="9" font-weight="600">${fmtK(v)}</text>`;

    // Period label at bottom
    labels += `<text x="${(x + barW / 2).toFixed(1)}" y="${(H - padBot + 13).toFixed(1)}" text-anchor="middle" fill="var(--muted, #888)" font-size="9">${escapeHtml(label(e.period))}</text>`;

    // YoY below period
    const yoy = fmtYoy(e.eps_yoy);
    if (yoy) {
      const yoyColor = Number(e.eps_yoy) > 0 ? 'var(--good, #4caf50)' : 'var(--bad, #f44336)';
      yoyLabels += `<text x="${(x + barW / 2).toFixed(1)}" y="${(H - padBot + 25).toFixed(1)}" text-anchor="middle" fill="${yoyColor}" font-size="8">${yoy}</text>`;
    }
  });

  // Zero line
  const zeroLine = `<line x1="${padL}" y1="${zeroY.toFixed(1)}" x2="${(W - padR)}" y2="${zeroY.toFixed(1)}" stroke="var(--muted, #555)" stroke-width="0.5" stroke-dasharray="3,3"/>`;

  return `
    <div style="margin:8px 0">
      <strong style="font-size:11px;color:var(--muted)">${escapeHtml(title)}</strong>
      <div style="overflow-x:auto;margin-top:4px">
        <svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="display:block">
          ${zeroLine}${bars}${labels}${yoyLabels}
        </svg>
      </div>
    </div>`;
}

/* ── Naver-style Financial Performance Table ── */

export function financialAnalysisTable(data) {
  const fs = data.financial_summary;
  if (!fs || (!fs.annual?.length && !fs.quarterly?.length)) return '';

  const metricLabels = {
    revenue:    { ko: '매출액',     en: 'Revenue' },
    op_profit:  { ko: '영업이익',   en: 'Op. Profit' },
    net_income: { ko: '당기순이익', en: 'Net Income' },
    equity:     { ko: '자본총계',   en: 'Equity' },
    total_debt: { ko: '부채총계',   en: 'Total Debt' },
    opm:        { ko: '영업이익률', en: 'OPM' },
    npm:        { ko: '순이익률',   en: 'NPM' },
    roe:        { ko: 'ROE',       en: 'ROE' },
    debt_ratio: { ko: '부채비율',   en: 'Debt Ratio' },
    eps:        { ko: 'EPS',       en: 'EPS' },
    per:        { ko: 'PER',       en: 'PER' },
    bps:        { ko: 'BPS',       en: 'BPS' },
    pbr:        { ko: 'PBR',       en: 'PBR' },
    dps:        { ko: '주당배당금', en: 'DPS' },
    dividend_yield: { ko: '배당수익률', en: 'Div Yield' },
  };
  const pctMetrics = new Set(['opm', 'npm', 'roe', 'debt_ratio', 'dividend_yield']);
  const bigMetrics = new Set(['revenue', 'op_profit', 'net_income', 'equity', 'total_debt']);

  const metrics = fs.metrics || Object.keys(metricLabels);
  const annual = fs.annual || [];
  const quarterly = fs.quarterly || [];
  const allPeriods = [...annual, ...quarterly];

  const fmtCell = (val, key) => {
    if (val == null) return '<td class="fin-td">-</td>';
    const num = Number(val);
    const neg = num < 0;
    const cls = neg ? ' class="fin-td fin-neg"' : ' class="fin-td"';
    let display;
    if (bigMetrics.has(key)) {
      // Show in 억원 (values are already in 억원 from QuantDB)
      display = num >= 10000 || num <= -10000
        ? `${(num / 10000).toFixed(1)}조`
        : `${Math.round(num).toLocaleString()}`;
    } else if (pctMetrics.has(key)) {
      display = `${num.toFixed(1)}%`;
    } else {
      display = num >= 100000 || num <= -100000
        ? `${(num / 10000).toFixed(0)}만`
        : Number.isInteger(num) ? num.toLocaleString() : num.toFixed(1);
    }
    return `<td${cls}>${display}</td>`;
  };

  const headerCells = allPeriods.map((p) => {
    const label = p.period.length === 4 ? p.period : p.period.replace(/(\d{4})Q/, "'$1 Q");
    const isQ = p.period.length > 4;
    return `<th class="fin-th${isQ ? ' fin-th--q' : ''}">${label}</th>`;
  }).join('');

  const bodyRows = metrics.map((key) => {
    // Skip row if ALL periods have null values
    const hasAnyValue = allPeriods.some((p) => p[key] != null);
    if (!hasAnyValue) return '';
    const label = txt(metricLabels[key] || { ko: key, en: key });
    const cells = allPeriods.map((p) => fmtCell(p[key], key)).join('');
    return `<tr><td class="fin-td fin-td--label">${escapeHtml(label)}</td>${cells}</tr>`;
  }).join('');

  return `
    <div class="profile-fin-table-wrap" style="margin-top:14px">
      <h4>${txt({ ko: '기업실적분석', en: 'Financial Performance' })}</h4>
      <div class="profile-fin-table-scroll">
        <table class="profile-fin-table">
          <thead><tr><th class="fin-th fin-th--label"></th>${headerCells}</tr></thead>
          <tbody>${bodyRows}</tbody>
        </table>
      </div>
    </div>`;
}

/* ── Business Summary ── */

export function businessSummaryMarkup(summary) {
  if (!summary) return '';
  return `
    <div style="margin:12px 0 0;padding:10px;background:rgba(255,255,255,.03);border-radius:6px;border-left:3px solid var(--accent)">
      <h4 style="font-size:12px;color:var(--accent);margin:0 0 6px">${txt({ ko: '기업 개요', en: 'Business Summary' })}</h4>
      <p style="font-size:13px;color:var(--muted);margin:0;line-height:1.7">${escapeHtml(summary)}</p>
    </div>`;
}

/* ── Financial Summary DL with grid ── */

export function financialTableMarkup(data) {
  const p = data.profile || {};
  const f = p.financials || {};

  const infoRows = [
    [txt({ ko: '시장', en: 'Market' }), escapeHtml(p.market || '-')],
    [txt({ ko: '업종', en: 'Sector' }), escapeHtml(p.sector_small || p.sector_large || '-')],
    [txt({ ko: '시가총액', en: 'Mkt Cap' }), escapeHtml(p.market_cap_display || fmtKrwCompact(p.mkt_cap))],
  ];
  // Merge investment_metrics from new DB
  const im = data.investment_metrics || {};
  const roa = im.roa ?? f.roa;
  const opm = im.opm ?? f.opm;
  const ebitdaM = im.ebitda_margin ?? f.ev_ebitda;
  const roic = im.roic;
  const grossM = im.gross_margin;

  const finRows = [
    ['PER', f.per != null ? fmtNum(f.per, 2) : '-'],
    ['PBR', f.pbr != null ? fmtNum(f.pbr, 2) : '-'],
    ['ROE', f.roe != null ? `<span class="${f.roe >= 15 ? 'good' : f.roe >= 8 ? '' : 'bad'}">${fmtNum(f.roe, 1)}%</span>` : '-'],
    ['ROA', roa != null ? `${fmtNum(roa, 1)}%` : '-'],
    ['ROIC', roic != null ? `${fmtNum(roic, 1)}%` : '-'],
    [txt({ ko: '영업이익률', en: 'OPM' }), opm != null ? `${fmtNum(opm, 1)}%` : '-'],
    [txt({ ko: 'EBITDA마진', en: 'EBITDA Margin' }), ebitdaM != null ? `${fmtNum(ebitdaM, 1)}%` : '-'],
    [txt({ ko: '매출총이익률', en: 'Gross Margin' }), grossM != null ? `${fmtNum(grossM, 1)}%` : '-'],
    [txt({ ko: '배당률', en: 'Div' }), f.dividend_yield != null ? `${fmtNum(f.dividend_yield, 1)}%` : '-'],
    [txt({ ko: '부채비율', en: 'Debt' }), f.debt_ratio != null ? `${fmtNum(f.debt_ratio, 0)}%` : '-'],
    ['EV/EBITDA', f.ev_ebitda != null ? fmtNum(f.ev_ebitda, 2) : '-'],
    [txt({ ko: '외인비율', en: 'Foreign' }), p.foreign_ratio ? escapeHtml(p.foreign_ratio) : '-'],
  ];
  const infoDl = `<dl class="profile-dl">${infoRows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
  // Hide items with no data (value is '-')
  const visibleFinRows = finRows.filter(([, v]) => v !== '-');
  const finGrid = `<div class="profile-fin-grid">${visibleFinRows.map(([k, v]) => `<div class="fin-cell"><span class="fin-label">${k}</span><span class="fin-value">${v}</span></div>`).join('')}</div>`;

  // Consensus section
  const cns = data.consensus || {};
  const cnsHtml = cns.target_price ? `
    <div style="margin:10px 0;padding:8px 12px;background:rgba(96,160,255,.06);border-radius:6px;border-left:3px solid #60a0ff">
      <strong style="font-size:11px;color:#60a0ff">${txt({ ko: '컨센서스', en: 'Consensus' })}</strong>
      <div class="profile-fin-grid" style="margin-top:6px">
        <div class="fin-cell"><span class="fin-label">${txt({ ko: '목표주가', en: 'Target' })}</span><span class="fin-value">${fmtPrice(cns.target_price)}</span></div>
        <div class="fin-cell"><span class="fin-label">${txt({ ko: '추정EPS', en: 'Est EPS' })}</span><span class="fin-value">${cns.cns_eps != null ? fmtNum(cns.cns_eps, 0) : '-'}</span></div>
        <div class="fin-cell"><span class="fin-label">${txt({ ko: '추정PER', en: 'Est PER' })}</span><span class="fin-value">${cns.cns_per != null ? fmtNum(cns.cns_per, 2) : '-'}</span></div>
        <div class="fin-cell"><span class="fin-label">${txt({ ko: '투자의견', en: 'Opinion' })}</span><span class="fin-value">${cns.recommend_score != null ? fmtNum(cns.recommend_score, 1) + '/5' : '-'}</span></div>
      </div>
    </div>` : '';

  // Consensus and overview are now rendered separately in the profile layout
  return `${infoDl}${finGrid}`;
}

/* ── Session change display ── */

export function sessionMarkup(session) {
  if (!session || session.change_pct == null) return '';
  const up = session.change_pct >= 0;
  const sign = up ? '+' : '';
  const color = up ? 'var(--good)' : 'var(--bad)';
  return `<span class="profile-session" style="color:${color}">${sign}${fmtNum(session.change_abs, 0)} (${sign}${fmtNum(session.change_pct, 2)}%)</span>`;
}

/* ── Investor Trend (수급 — 외인/기관/개인) ── */

export function investorTrendMarkup(trend) {
  if (!trend || !trend.length) return '';
  const rows = trend.slice(0, 10).reverse(); // 오래된 순
  const fmtQ = (v) => {
    if (v == null) return '-';
    const n = Number(v);
    if (!Number.isFinite(n)) return '-';
    const abs = Math.abs(n);
    const display = abs >= 1000000 ? `${(n / 1000000).toFixed(1)}M` : abs >= 1000 ? `${(n / 1000).toFixed(0)}K` : `${n}`;
    return display;
  };
  const cls = (v) => {
    const n = Number(v);
    if (!Number.isFinite(n) || n === 0) return '';
    return n > 0 ? 'good' : 'bad';
  };
  const dateTds = rows.map((r) => `<th>${(r.trade_date || '').slice(4, 6)}/${(r.trade_date || '').slice(6)}</th>`).join('');
  const foreignTds = rows.map((r) => `<td class="${cls(r.foreign_net)}">${fmtQ(r.foreign_net)}</td>`).join('');
  const instTds = rows.map((r) => `<td class="${cls(r.institution_net)}">${fmtQ(r.institution_net)}</td>`).join('');
  const indivTds = rows.map((r) => `<td class="${cls(r.individual_net)}">${fmtQ(r.individual_net)}</td>`).join('');

  return `
    <div style="margin-top:14px">
      <h4>${txt({ ko: '수급 동향', en: 'Investor Flow' })}</h4>
      <div class="profile-fin-table-scroll">
        <table class="profile-fin-table">
          <thead><tr><th></th>${dateTds}</tr></thead>
          <tbody>
            <tr><td class="fin-td fin-td--label">${txt({ ko: '외국인', en: 'Foreign' })}</td>${foreignTds}</tr>
            <tr><td class="fin-td fin-td--label">${txt({ ko: '기관', en: 'Institution' })}</td>${instTds}</tr>
            <tr><td class="fin-td fin-td--label">${txt({ ko: '개인', en: 'Individual' })}</td>${indivTds}</tr>
          </tbody>
        </table>
      </div>
    </div>`;
}

/* ── Trend template check badges ── */

export function checksMarkup(checks) {
  if (!checks) return '';
  return Object.entries(checks).map(([k, v]) => `<span class="profile-check${v ? '' : ' off'}">${escapeHtml(k.replace(/_/g, ' '))}</span>`).join('');
}

/* ── Conviction badge class ── */

export function badgeCls(conviction) {
  const map = { 'A+': 'conviction-a-plus', A: 'conviction-a', B: 'conviction-b', C: 'conviction-c' };
  return map[conviction] || 'neutral';
}

/* ── Full company profile rendering (used by sector-grouped) ── */

export function renderCompanyProfile(data, targetEl) {
  const el = targetEl || $('profileContent');
  if (!el) return;

  const p = data.profile || data;
  const ts = data.technical_summary || {};
  const ps = data.pipeline_scores || {};
  const sc = data.sector_context || {};
  const ep = data.execution_plan;
  const rec = data.recommendation;
  const pers = data.persistence;
  const tt = ts.trend_template || {};
  const rs = ts.relative_strength || {};
  const vs = ts.volume_signal || {};
  const eq = ts.eps_quality || {};
  const lr = ts.least_resistance || {};
  const cwh = ts.cup_with_handle || {};

  const sparkline = sparklineSvg(data.sparkline || p.sparkline || [], 480, 150, (data.session || {}).date || data.date_dir || '');
  const epsData = data.eps_recent || p.eps_recent || [];

  const price = p.price || tt.close;

  // Build consensus + overview side by side
  const cns = data.consensus || {};
  const cnsBlock = cns.target_price ? `
    <div style="flex:1;min-width:200px;padding:10px;background:rgba(96,160,255,.04);border-radius:8px;border-left:3px solid #60a0ff">
      <h4 style="font-size:12px;color:#60a0ff;margin:0 0 8px">${txt({ ko: '컨센서스', en: 'Consensus' })}</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:13px">
        <div><span style="color:var(--muted)">목표주가</span><br><strong>${fmtPrice(cns.target_price)}</strong></div>
        <div><span style="color:var(--muted)">투자의견</span><br><strong>${cns.recommend_score ? cns.recommend_score.toFixed(1) + '/5' : '-'}</strong></div>
        <div><span style="color:var(--muted)">추정EPS</span><br><strong>${cns.cns_eps ? Math.round(cns.cns_eps).toLocaleString() : '-'}</strong></div>
        <div><span style="color:var(--muted)">추정PER</span><br><strong>${cns.cns_per ? cns.cns_per.toFixed(1) : '-'}</strong></div>
      </div>
    </div>` : '';

  const summaryText = p.business_summary || '';
  const overviewBlock = summaryText ? `
    <div style="flex:2;min-width:280px;padding:10px;background:rgba(255,255,255,.02);border-radius:8px;border-left:3px solid var(--accent)">
      <h4 style="font-size:12px;color:var(--accent);margin:0 0 6px">${txt({ ko: '기업 개요', en: 'Overview' })}</h4>
      <p style="font-size:12px;color:var(--muted);margin:0;line-height:1.7">${escapeHtml(summaryText)}</p>
    </div>` : '';

  el.innerHTML = `
    <div class="profile-grid">
      <div class="profile-chart">
        <h4>${txt({ ko: '최근 120일 주가', en: 'Price (120D)' })}</h4>
        ${sparkline}
        <p class="profile-price">${escapeHtml(fmtPrice(price))}</p>
        ${sessionMarkup(data.session)}
        <div style="margin-top:6px;display:flex;gap:8px">
          <a href="https://finance.naver.com/item/main.naver?code=${p.symbol || ''}" target="_blank" rel="noopener" style="font-size:11px;color:#60a0ff;text-decoration:none">네이버 증권 &rarr;</a>
          <a href="https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=${p.symbol || ''}" target="_blank" rel="noopener" style="font-size:11px;color:#60a0ff;text-decoration:none">상세 재무 &rarr;</a>
        </div>
      </div>
      <div class="profile-facts">
        ${financialTableMarkup(data)}
      </div>
    </div>
    ${(cnsBlock || overviewBlock) ? `<div style="display:flex;gap:12px;margin-top:12px;flex-wrap:wrap">${cnsBlock}${overviewBlock}</div>` : ''}
    ${epsData.length >= 2 ? `
    <div style="margin-top:14px">
      <h4>${txt({ ko: 'EPS 추이', en: 'EPS Trend' })}</h4>
      ${epsBarChart(epsData)}
    </div>` : ''}
    ${financialAnalysisTable(data)}
    ${investorTrendMarkup(data.investor_trend)}
    <div class="profile-sections">

      <div class="profile-section">
        <h4>Trend Template (${tt.passed_count || 0}/6)</h4>
        <dl class="profile-kv">
          <div><dt>52W High</dt><dd>${fmtPrice(tt.high52)} (${fmtNum(tt.distance_to_high52_pct, 1)}%)</dd></div>
          <div><dt>52W Low</dt><dd>${fmtPrice(tt.low52)} (+${fmtNum(tt.distance_from_low52_pct, 1)}%)</dd></div>
          <div><dt>MACD</dt><dd><span class="profile-badge ${tt.macd_state === 'bullish' ? 'pass' : tt.macd_state === 'bearish' ? 'fail' : 'neutral'}">${escapeHtml(tt.macd_state || '-')}</span></dd></div>
          <div><dt>Tightness</dt><dd>${fmtNum(tt.tightness_ratio_20_60, 3)}</dd></div>
        </dl>
        <div class="profile-checks">${checksMarkup(tt.checks)}</div>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '상대강도 & 볼륨', en: 'RS & Volume' })}</h4>
        <dl class="profile-kv">
          <div><dt>RS Percentile</dt><dd>${fmtNum(rs.rs_percentile_120, 1)}</dd></div>
          <div><dt>RS State</dt><dd><span class="profile-badge ${rs.state === 'rs_new_high' ? 'pass' : rs.state === 'rs_above_ma20' ? 'pass' : 'neutral'}">${escapeHtml((rs.state || '-').replace(/^rs_/, ''))}</span></dd></div>
          <div><dt>RS → High120</dt><dd>${fmtNum(rs.distance_to_high120_pct, 2)}%</dd></div>
          <div><dt>Vol State</dt><dd><span class="profile-badge ${vs.state === 'volume_dryup' ? 'pass' : vs.state === 'volume_expansion' ? 'neutral' : 'neutral'}">${escapeHtml((vs.state || '-').replace(/^volume_/, ''))}</span></dd></div>
          <div><dt>Vol Ratio</dt><dd>${fmtNum(vs.latest_ratio_20, 2)}x <small>(dry ${vs.dryup_days_20 || 0}d / exp ${vs.expansion_days_20 || 0}d)</small></dd></div>
        </dl>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '최소저항선 & EPS', en: 'Least Resistance & EPS' })}</h4>
        <dl class="profile-kv">
          <div><dt>Trend</dt><dd><span class="profile-badge ${lr.trend === 'up_least_resistance' ? 'pass' : lr.trend === 'pullback_in_uptrend' ? 'neutral' : 'fail'}">${escapeHtml((lr.trend || '-').replace(/_/g, ' '))}</span></dd></div>
          <div><dt>Distance</dt><dd>${fmtNum(lr.distance_pct, 2)}%</dd></div>
          <div><dt>EPS Status</dt><dd><span class="profile-badge ${eq.status === 'strong_growth' ? 'pass' : eq.status === 'positive_growth' ? 'neutral' : 'fail'}">${escapeHtml((eq.status || '-').replace(/_/g, ' '))}</span></dd></div>
          <div><dt>EPS YoY</dt><dd class="${eq.latest_yoy > 0 ? 'good' : 'bad'}">${fmtNum(eq.latest_yoy, 1)}%</dd></div>
          <div><dt>Acceleration</dt><dd>${fmtNum(eq.acceleration, 1)}</dd></div>
        </dl>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '컵위드핸들', en: 'Cup with Handle' })}</h4>
        <dl class="profile-kv">
          <div><dt>Detected</dt><dd><span class="profile-badge ${cwh.detected ? 'pass' : 'fail'}">${cwh.detected ? 'YES' : 'NO'}</span></dd></div>
          <div><dt>Stage</dt><dd><span class="profile-badge ${cwh.stage === 'breakout_ready' ? 'pass' : cwh.stage === 'handle_forming' ? 'neutral' : cwh.stage === 'cup_forming' ? 'neutral' : 'fail'}">${escapeHtml((cwh.stage || 'none').replace(/_/g, ' '))}</span></dd></div>
          <div><dt>Cup Depth</dt><dd>${fmtNum(cwh.cup_depth_pct, 1)}%</dd></div>
          <div><dt>Handle Depth</dt><dd>${fmtNum(cwh.handle_depth_pct, 1)}%</dd></div>
          <div><dt>Pivot (Buy)</dt><dd>${cwh.pivot_price ? fmtPrice(cwh.pivot_price) : '-'}</dd></div>
          <div><dt>Cup / Handle</dt><dd>${cwh.cup_days || 0}d / ${cwh.handle_days || 0}d</dd></div>
        </dl>
        ${cwh.detected && cwh.pivot_price ? (() => {
          const pivot = cwh.pivot_price;
          const depth = cwh.cup_depth_pct || 0;
          const cwhStop = Math.round(pivot * (1 - depth / 100));
          const cwhTarget = Math.round(pivot * (1 + (depth / 100) * 2));
          const cwhRisk = pivot - cwhStop;
          const cwhRR = cwhRisk > 0 ? ((cwhTarget - pivot) / cwhRisk).toFixed(1) : '-';
          return `
          <div class="profile-exec-grid" style="margin-top:8px;padding:8px;border:1px solid rgba(138,240,184,0.2);border-radius:6px;background:rgba(138,240,184,0.03)">
            <div style="grid-column:1/-1;font-size:11px;color:var(--muted);margin-bottom:4px">${txt({ ko: 'CWH 피벗 기반 실행 계획', en: 'CWH Pivot-Based Trade Plan' })}</div>
            <div class="exec-item"><div class="label">Entry</div><div class="value">${fmtPrice(pivot)}</div></div>
            <div class="exec-item"><div class="label">Stop</div><div class="value" style="color:var(--bad)">${fmtPrice(cwhStop)}</div></div>
            <div class="exec-item"><div class="label">Target (2R)</div><div class="value" style="color:var(--good)">${fmtPrice(cwhTarget)}</div></div>
            <div class="exec-item"><div class="label">R/R</div><div class="value">${cwhRR}</div></div>
          </div>`;
        })() : ''}
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '파이프라인', en: 'Pipeline' })}</h4>
        <dl class="profile-kv">
          <div><dt>Alpha</dt><dd><span class="profile-badge ${ps.alpha?.passed ? 'pass' : 'fail'}">${ps.alpha?.passed ? `PASS ${fmtNum(ps.alpha.score, 1)}` : 'FAIL'}</span></dd></div>
          <div><dt>Beta (VCP)</dt><dd><span class="profile-badge ${ps.beta?.passed ? 'pass' : 'fail'}">${ps.beta?.passed ? `PASS ${fmtNum(ps.beta.confidence, 2)}` : 'FAIL'}</span></dd></div>
          <div><dt>Gamma</dt><dd><span class="profile-badge ${ps.gamma?.passed ? 'pass' : 'fail'}">${ps.gamma?.passed ? `PASS ${fmtNum(ps.gamma.gamma_score, 1)}` : 'FAIL'}</span></dd></div>
          <div><dt>Leader</dt><dd>${ps.leader?.ranked ? `<span class="profile-badge pass">${escapeHtml(ps.leader.stock_bucket || '-')}</span> ${fmtNum(Math.min(ps.leader.leader_stock_score || 0, 100), 1)}` : '<span class="profile-badge fail">-</span>'}</dd></div>
        </dl>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '섹터', en: 'Sector' })}</h4>
        <dl class="profile-kv">
          <div><dt>Sector</dt><dd>${escapeHtml(sc.sector || p.sector || '-')}</dd></div>
          <div><dt>Breakout</dt><dd><span class="profile-badge ${sc.breakout_state === 'sector_breakout_confirmed' ? 'pass' : sc.breakout_state === 'sector_breakout_setup' ? 'neutral' : 'fail'}">${escapeHtml((sc.breakout_state || '-').replace(/^sector_/, '').replace(/_/g, ' '))}</span></dd></div>
          ${sc.leadership ? `
          <div><dt>Leader Score</dt><dd>${fmtNum(Math.min(sc.leadership.leader_score || 0, 100), 1)}</dd></div>
          <div><dt>Ready</dt><dd><span class="profile-badge ${sc.leadership.leadership_ready ? 'pass' : 'fail'}">${sc.leadership.leadership_ready ? 'YES' : 'NO'}</span></dd></div>
          <div><dt>Alpha/Beta</dt><dd>${fmtPlainPct((sc.leadership.alpha_ratio || 0) * 100)} / ${fmtPlainPct((sc.leadership.beta_ratio || 0) * 100)}</dd></div>
          ` : ''}
        </dl>
      </div>

      ${pers && pers.persistence_score != null ? `
      <div class="profile-section">
        <h4>${txt({ ko: '지속성', en: 'Persistence' })}</h4>
        <dl class="profile-kv">
          <div><dt>Score</dt><dd>${fmtNum(pers.persistence_score, 1)}</dd></div>
          <div><dt>Appearance</dt><dd>${fmtPlainPct((pers.appearance_ratio || 0) * 100)}</dd></div>
          <div><dt>Streak</dt><dd>${pers.current_streak || 0} (max ${pers.max_streak || 0})</dd></div>
          <div><dt>Avg Rank</dt><dd>${pers.avg_rank != null ? fmtNum(pers.avg_rank, 1) : '-'}</dd></div>
        </dl>
      </div>` : ''}

      ${ep && ep.entry ? `
      <div class="profile-section profile-section--full">
        <h4>${txt({ ko: '실행 계획', en: 'Execution Plan' })}</h4>
        <div class="profile-exec-grid">
          <div class="exec-item"><div class="label">Entry</div><div class="value">${fmtPrice(ep.entry)}</div></div>
          <div class="exec-item"><div class="label">Stop</div><div class="value" style="color:var(--bad)">${fmtPrice(ep.stop)}</div></div>
          <div class="exec-item"><div class="label">Target</div><div class="value" style="color:var(--good)">${fmtPrice(ep.target)}</div></div>
          <div class="exec-item"><div class="label">Qty</div><div class="value">${ep.qty || '-'}</div></div>
          <div class="exec-item"><div class="label">R/R</div><div class="value">${fmtNum(ep.rr_ratio, 2)}</div></div>
        </div>
      </div>` : ''}

      ${rec ? `
      <div class="profile-section profile-section--full">
        <h4>${txt({ ko: '추천', en: 'Recommendation' })}</h4>
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
          <span class="profile-badge ${badgeCls(rec.conviction)}" style="font-size:16px;padding:4px 14px">${escapeHtml(rec.conviction || '-')}</span>
          <span style="font-size:18px;font-weight:700">${fmtNum(rec.recommendation_score, 1)}</span>
        </div>
      </div>` : ''}

    </div>

    ${_verificationPrompt(data)}
  `;
}


/* ── AI 2차 검증 프롬프트 ── */

function _verificationPrompt(data) {
  if (!data) return '';
  const p = data.profile || data || {};
  const f = p.financials || {};
  const cns = data.consensus || {};
  const im = data.investment_metrics || {};
  const fs = data.financial_summary || {};
  const ep = data.execution_plan;

  const symbol = p.symbol || data.symbol || '?';
  const name = p.name || data.name || symbol;
  const price = p.price || 0;
  const sector = p.sector_small || p.sector_large || p.sector || '';

  // Build latest annual financials string
  const latestAnn = fs.annual && fs.annual.length ? fs.annual[fs.annual.length - 1] : {};
  const finStr = latestAnn.period ? `매출 ${latestAnn.revenue || '?'}억, 영업이익 ${latestAnn.op_profit || '?'}억, 순이익 ${latestAnn.net_income || '?'}억 (${latestAnn.period})` : '재무 데이터 없음';

  // EPS trend summary
  const epsData = data.eps_recent || [];
  const annEps = epsData.filter((e) => e.period_type === 'annual').slice(-3);
  const qtrEps = epsData.filter((e) => e.period_type === 'quarterly').slice(-4);
  const epsAnnStr = annEps.map((e) => `${e.period}: ${e.eps}`).join(', ') || '없음';
  const epsQtrStr = qtrEps.map((e) => `${e.period}: ${e.eps}`).join(', ') || '없음';
  const epsYoy = qtrEps.length ? qtrEps[qtrEps.length - 1].eps_yoy : null;

  // Investor trend summary
  const trend = data.investor_trend || [];
  const foreignSum = trend.reduce((s, t) => s + (t.foreign_net || 0), 0);
  const instSum = trend.reduce((s, t) => s + (t.institution_net || 0), 0);
  const trendStr = trend.length ? `최근 ${trend.length}일: 외국인 ${foreignSum > 0 ? '+' : ''}${Math.round(foreignSum).toLocaleString()}주, 기관 ${instSum > 0 ? '+' : ''}${Math.round(instSum).toLocaleString()}주` : '수급 데이터 없음';

  // Pipeline scores
  const pipeline = data.pipeline_scores || {};
  const alphaStr = pipeline.alpha?.passed ? `Alpha PASS (${pipeline.alpha.score})` : 'Alpha FAIL';
  const betaStr = pipeline.beta?.passed ? `Beta PASS` : 'Beta FAIL';
  const gammaStr = pipeline.gamma?.passed ? `Gamma PASS` : 'Gamma FAIL';

  const prompt = `## 한국 주식 2차 검증 요청

종목: ${name} (${symbol})
업종: ${sector}
검증일: ${new Date().toISOString().slice(0, 10)}

### 1. 시스템 산출 데이터 (교차 검증 필요)
- 현재가: ${price ? Math.round(price).toLocaleString() + '원' : '?'}
- PER: ${f.per ?? '?'} | PBR: ${f.pbr ?? '?'} | ROE: ${f.roe ?? '?'}%
- ${finStr}
- 연간 EPS: ${epsAnnStr}
- 분기 EPS: ${epsQtrStr}
${epsYoy != null ? `- 최근 분기 EPS YoY: ${epsYoy > 0 ? '+' : ''}${epsYoy}%` : ''}
${cns.target_price ? `- 컨센서스: 목표주가 ${Math.round(cns.target_price).toLocaleString()}원, 추정EPS ${cns.cns_eps || '?'}, 투자의견 ${cns.recommend_score || '?'}/5` : ''}
${im.roa ? `- ROA: ${im.roa}% | ROIC: ${im.roic || '?'}% | EBITDA마진: ${im.ebitda_margin || '?'}%` : ''}
- ${trendStr}
- 파이프라인: ${alphaStr}, ${betaStr}, ${gammaStr}
${ep ? `- 실행계획: 매수 ${ep.entry}원 → 손절 ${ep.stop}원 → 목표 ${ep.target}원 (R:R ${ep.rr_ratio || '?'})` : ''}

### 2. 기술적 분석 (Technical Analysis)

**[추세 구조]**
1. Weinstein Stage 분석: Stage 1(바닥) / 2(상승) / 3(천장) / 4(하락) 중 현재 위치
2. 이동평균 배열: 20MA > 50MA > 150MA > 200MA 정배열 여부, 200MA 기울기
3. 52주 고점 대비 위치(%), 52주 저점 대비 위치(%)
4. 상대강도(RS): KOSPI 대비 20일/60일/120일 RS 순위

**[패턴/시그널]**
5. VCP 형성 여부: 수축 횟수, 마지막 수축폭(%), 거래량 건조 확인
6. Cup with Handle: 컵 깊이(%), 핸들 진행도, 피봇 포인트(원)
7. 채널/박스: 상단/하단 가격, 돌파 여부
8. MACD(20,60): 골든크로스/데드크로스, 히스토그램 방향
9. 거래량: 5일평균 / 50일평균 비율, 돌파 시 거래량 동반 여부

**[지지/저항]**
10. 지지선 3개 (가격 + 근거: MA/전저점/피보나치/갭)
11. 저항선 3개 (가격 + 근거)
12. 최소저항경로: 상방 vs 하방 + 근거

**[재무/리스크]**
13. PER/EPS/ROE 최신 공시 일치 여부, 실적 컨센서스
14. ${sector} 업황 변화 방향, 경쟁사 PER/PBR 비교
15. 최근 뉴스/공시/대주주 변동/공매도/CB전환 이슈

### 3. 매매 계획 검증
${ep ? '시스템 제안: 매수 ' + ep.entry + '원, 손절 ' + ep.stop + '원, 목표 ' + ep.target + '원' : ''}
- 진입가/손절가/목표가가 지지/저항선 기준으로 합리적인가?
- R:R이 2.0 이상인가?
- 더 나은 진입 타이밍(풀백, 피봇 돌파)이 있는가?

### 4. 최종 결론
- **기술적 의견**: 매수 적기 / 풀백 대기 / 관망 / 매도
- **진입가**: 지지선 기반 매수 구간
- **손절가**: 기술적 근거 (어떤 지지선 이탈 시)
- **목표가**: 1차(저항선) / 2차(확장 목표)
- **핵심 근거 3가지**
- **주요 리스크 2가지**`;

  return `
    <div style="margin-top:20px;padding:16px;background:rgba(96,160,255,.04);border:1px solid rgba(96,160,255,.15);border-radius:8px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <h4 style="margin:0;color:#60a0ff;font-size:14px">AI 2차 검증 프롬프트</h4>
        <button onclick="navigator.clipboard.writeText(this.closest('div').querySelector('pre').textContent).then(()=>{this.textContent='복사됨!';setTimeout(()=>this.textContent='복사',1500)})" style="padding:4px 12px;background:#60a0ff;color:#fff;border:none;border-radius:4px;cursor:pointer;font-size:12px">복사</button>
      </div>
      <p style="font-size:12px;color:var(--muted);margin:0 0 8px">Perplexity, ChatGPT, Claude 등에 붙여넣기하여 2차 검증하세요.</p>
      <pre style="font-size:12px;line-height:1.6;color:var(--text);white-space:pre-wrap;word-break:break-all;max-height:300px;overflow-y:auto;background:rgba(0,0,0,.3);padding:12px;border-radius:6px;margin:0">${escapeHtml(prompt)}</pre>
    </div>`;
}

/* ── Phase 2 detail update (progressive rendering for market-wizards-korea) ── */

export function renderOverviewFull(data) {
  const ts = data.technical_summary || {};
  const pers = data.persistence;
  const tt = ts.trend_template || {};
  const rs = ts.relative_strength || {};
  const vs = ts.volume_signal || {};
  const eq = ts.eps_quality || {};
  const lr = ts.least_resistance || {};
  const cwh = ts.cup_with_handle || {};
  const sc = data.sector_context || {};

  // Update Trend Template section
  const ttEl = document.querySelector('.profile-section[data-section="trend-template"]');
  if (ttEl && tt.checks) {
    ttEl.querySelector('h4').textContent = `Trend Template (${tt.passed_count || 0}/6)`;
    ttEl.querySelector('.profile-kv').innerHTML = `
      <div><dt>52W High</dt><dd>${fmtPrice(tt.high52)} (${fmtNum(tt.distance_to_high52_pct, 1)}%)</dd></div>
      <div><dt>52W Low</dt><dd>${fmtPrice(tt.low52)} (+${fmtNum(tt.distance_from_low52_pct, 1)}%)</dd></div>
      <div><dt>MACD</dt><dd><span class="profile-badge ${tt.macd_state === 'bullish' ? 'pass' : tt.macd_state === 'bearish' ? 'fail' : 'neutral'}">${escapeHtml(tt.macd_state || '-')}</span></dd></div>
      <div><dt>Tightness</dt><dd>${fmtNum(tt.tightness_ratio_20_60, 3)}</dd></div>
    `;
    const checksEl = ttEl.querySelector('.profile-checks');
    if (checksEl) checksEl.innerHTML = checksMarkup(tt.checks);
  }

  // Update RS & Volume section
  const rsEl = document.querySelector('.profile-section[data-section="rs-volume"]');
  if (rsEl && rs.rs_percentile_120 != null) {
    rsEl.querySelector('.profile-kv').innerHTML = `
      <div><dt>RS Percentile</dt><dd>${fmtNum(rs.rs_percentile_120, 1)}</dd></div>
      <div><dt>RS State</dt><dd><span class="profile-badge ${rs.state === 'rs_new_high' || rs.state === 'rs_above_ma20' ? 'pass' : 'neutral'}">${escapeHtml((rs.state || '-').replace(/^rs_/, ''))}</span></dd></div>
      <div><dt>RS → High120</dt><dd>${fmtNum(rs.distance_to_high120_pct, 2)}%</dd></div>
      <div><dt>Vol State</dt><dd><span class="profile-badge neutral">${escapeHtml((vs.state || '-').replace(/^volume_/, ''))}</span></dd></div>
      <div><dt>Vol Ratio</dt><dd>${fmtNum(vs.latest_ratio_20, 2)}x <small>(dry ${vs.dryup_days_20 || 0}d / exp ${vs.expansion_days_20 || 0}d)</small></dd></div>
    `;
  }

  // Update LR & EPS section
  const lrEl = document.querySelector('.profile-section[data-section="lr-eps"]');
  if (lrEl && lr.trend) {
    lrEl.querySelector('.profile-kv').innerHTML = `
      <div><dt>Trend</dt><dd><span class="profile-badge ${lr.trend === 'up_least_resistance' ? 'pass' : lr.trend === 'pullback_in_uptrend' ? 'neutral' : 'fail'}">${escapeHtml((lr.trend || '-').replace(/_/g, ' '))}</span></dd></div>
      <div><dt>Distance</dt><dd>${fmtNum(lr.distance_pct, 2)}%</dd></div>
      <div><dt>EPS Status</dt><dd><span class="profile-badge ${eq.status === 'strong_growth' ? 'pass' : eq.status === 'positive_growth' ? 'neutral' : 'fail'}">${escapeHtml((eq.status || '-').replace(/_/g, ' '))}</span></dd></div>
      <div><dt>EPS YoY</dt><dd class="${eq.latest_yoy > 0 ? 'good' : 'bad'}">${fmtNum(eq.latest_yoy, 1)}%</dd></div>
      <div><dt>Acceleration</dt><dd>${fmtNum(eq.acceleration, 1)}</dd></div>
    `;
  }

  // Update Cup with Handle section
  const cwhEl = document.querySelector('.profile-section[data-section="cup-with-handle"]');
  if (cwhEl) {
    // Compute pivot-based execution plan when CWH is detected
    let cwhPlanHtml = '';
    if (cwh.detected && cwh.pivot_price) {
      const pivot = cwh.pivot_price;
      const depth = cwh.cup_depth_pct || 0;
      const cwhStop = Math.round(pivot * (1 - depth / 100));
      const cwhTarget = Math.round(pivot * (1 + (depth / 100) * 2));
      const cwhRisk = pivot - cwhStop;
      const cwhRR = cwhRisk > 0 ? ((cwhTarget - pivot) / cwhRisk).toFixed(1) : '-';
      cwhPlanHtml = `
        <div class="profile-exec-grid" style="margin-top:8px;padding:8px;border:1px solid rgba(138,240,184,0.2);border-radius:6px;background:rgba(138,240,184,0.03)">
          <div style="grid-column:1/-1;font-size:11px;color:var(--muted);margin-bottom:4px">${txt({ ko: 'CWH 피벗 기반 실행 계획', en: 'CWH Pivot-Based Trade Plan' })}</div>
          <div class="exec-item"><div class="label">Entry</div><div class="value">${fmtPrice(pivot)}</div></div>
          <div class="exec-item"><div class="label">Stop</div><div class="value" style="color:var(--bad)">${fmtPrice(cwhStop)}</div></div>
          <div class="exec-item"><div class="label">Target (2R)</div><div class="value" style="color:var(--good)">${fmtPrice(cwhTarget)}</div></div>
          <div class="exec-item"><div class="label">R/R</div><div class="value">${cwhRR}</div></div>
        </div>`;
    }
    cwhEl.querySelector('.profile-kv').innerHTML = `
      <div><dt>Detected</dt><dd><span class="profile-badge ${cwh.detected ? 'pass' : 'fail'}">${cwh.detected ? 'YES' : 'NO'}</span></dd></div>
      <div><dt>Stage</dt><dd><span class="profile-badge ${cwh.stage === 'breakout_ready' ? 'pass' : cwh.stage === 'handle_forming' ? 'neutral' : cwh.stage === 'cup_forming' ? 'neutral' : 'fail'}">${escapeHtml((cwh.stage || 'none').replace(/_/g, ' '))}</span></dd></div>
      <div><dt>Cup Depth</dt><dd>${fmtNum(cwh.cup_depth_pct, 1)}%</dd></div>
      <div><dt>Handle Depth</dt><dd>${fmtNum(cwh.handle_depth_pct, 1)}%</dd></div>
      <div><dt>Pivot (Buy)</dt><dd>${cwh.pivot_price ? fmtPrice(cwh.pivot_price) : '-'}</dd></div>
      <div><dt>Cup / Handle</dt><dd>${cwh.cup_days || 0}d / ${cwh.handle_days || 0}d</dd></div>
    `;
    if (cwhPlanHtml) {
      cwhEl.insertAdjacentHTML('beforeend', cwhPlanHtml);
    }
  }

  // Update Sector with breakout data
  const scEl = document.querySelector('.profile-section[data-section="sector"]');
  if (scEl && sc.breakout_state) {
    const kvEl = scEl.querySelector('.profile-kv');
    const breakoutDiv = kvEl?.querySelector('[data-key="breakout"]');
    if (breakoutDiv) {
      breakoutDiv.querySelector('dd').innerHTML = `<span class="profile-badge ${sc.breakout_state === 'sector_breakout_confirmed' ? 'pass' : sc.breakout_state === 'sector_breakout_setup' ? 'neutral' : 'fail'}">${escapeHtml((sc.breakout_state || '-').replace(/^sector_/, '').replace(/_/g, ' '))}</span>`;
    }
  }

  // Update Persistence section
  const persEl = document.querySelector('.profile-section[data-section="persistence"]');
  if (persEl) {
    if (pers) {
      persEl.innerHTML = `
        <h4>${txt({ ko: '지속성', en: 'Persistence' })}</h4>
        <dl class="profile-kv">
          <div><dt>Score</dt><dd>${fmtNum(pers.persistence_score, 1)}</dd></div>
          <div><dt>Appearance</dt><dd>${fmtPlainPct((pers.appearance_ratio || 0) * 100)}</dd></div>
          <div><dt>Streak</dt><dd>${pers.current_streak || 0} (max ${pers.max_streak || 0})</dd></div>
          <div><dt>Avg Rank</dt><dd>${pers.avg_rank != null ? fmtNum(pers.avg_rank, 1) : '-'}</dd></div>
        </dl>
      `;
    } else {
      persEl.innerHTML = `
        <h4>${txt({ ko: '지속성', en: 'Persistence' })}</h4>
        <p style="color:var(--muted);font-size:12px">N/A</p>
      `;
    }
  }
}

/* ── Initial profile markup (skeleton with data-section placeholders) ── */

export function renderProfileSkeleton(data) {
  const p = data.profile || data;
  const ts = data.technical_summary || {};
  const ps = data.pipeline_scores || {};
  const sc = data.sector_context || {};
  const ep = data.execution_plan;
  const rec = data.recommendation;
  const tt = ts.trend_template || {};

  const spark = sparklineSvg(data.sparkline || [], 480, 150, (data.session || {}).date || data.date_dir || '');
  const price = p.price || tt.close;
  const epsData = data.eps_recent || [];

  // Consensus + Overview (same as renderCompanyProfile)
  const cns = data.consensus || {};
  const cnsBlock = cns.target_price ? `
    <div style="flex:1;min-width:200px;padding:10px;background:rgba(96,160,255,.04);border-radius:8px;border-left:3px solid #60a0ff">
      <h4 style="font-size:12px;color:#60a0ff;margin:0 0 8px">${txt({ ko: '컨센서스', en: 'Consensus' })}</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:13px">
        <div><span style="color:var(--muted)">목표주가</span><br><strong>${fmtPrice(cns.target_price)}</strong></div>
        <div><span style="color:var(--muted)">투자의견</span><br><strong>${cns.recommend_score ? cns.recommend_score.toFixed(1) + '/5' : '-'}</strong></div>
        <div><span style="color:var(--muted)">추정EPS</span><br><strong>${cns.cns_eps ? Math.round(cns.cns_eps).toLocaleString() : '-'}</strong></div>
        <div><span style="color:var(--muted)">추정PER</span><br><strong>${cns.cns_per ? cns.cns_per.toFixed(1) : '-'}</strong></div>
      </div>
    </div>` : '';
  const summaryText = p.business_summary || '';
  const overviewBlock = summaryText ? `
    <div style="flex:2;min-width:280px;padding:10px;background:rgba(255,255,255,.02);border-radius:8px;border-left:3px solid var(--accent)">
      <h4 style="font-size:12px;color:var(--accent);margin:0 0 6px">${txt({ ko: '기업 개요', en: 'Overview' })}</h4>
      <p style="font-size:12px;color:var(--muted);margin:0;line-height:1.7">${escapeHtml(summaryText)}</p>
    </div>` : '';

  return `
    <div class="profile-grid">
      <div class="profile-chart">
        <h4>${txt({ ko: '최근 120일 주가', en: 'Price (120D)' })}</h4>
        ${spark}
        <p class="profile-price">${escapeHtml(fmtPrice(price))}</p>
        ${sessionMarkup(data.session)}
        <div style="margin-top:6px;display:flex;gap:8px">
          <a href="https://finance.naver.com/item/main.naver?code=${p.symbol || ''}" target="_blank" rel="noopener" style="font-size:11px;color:#60a0ff;text-decoration:none">네이버 증권 &rarr;</a>
          <a href="https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=${p.symbol || ''}" target="_blank" rel="noopener" style="font-size:11px;color:#60a0ff;text-decoration:none">상세 재무 &rarr;</a>
        </div>
      </div>
      <div class="profile-facts">
        ${financialTableMarkup(data)}
      </div>
    </div>
    ${(cnsBlock || overviewBlock) ? `<div style="display:flex;gap:12px;margin-top:12px;flex-wrap:wrap">${cnsBlock}${overviewBlock}</div>` : ''}
    ${epsData.length >= 2 ? `
    <div style="margin-top:14px">
      <h4>${txt({ ko: 'EPS 추이', en: 'EPS Trend' })}</h4>
      ${epsBarChart(epsData)}
    </div>` : ''}
    ${financialAnalysisTable(data)}
    ${investorTrendMarkup(data.investor_trend)}
    <div class="profile-sections">

      <div class="profile-section" data-section="trend-template">
        <h4>Trend Template</h4>
        <dl class="profile-kv"><div><dt colspan="2" style="color:var(--muted);font-size:11px">${txt({ ko: '분석 대기', en: 'Awaiting analysis' })}</dt><dd></dd></div></dl>
        <div class="profile-checks"></div>
      </div>

      <div class="profile-section" data-section="rs-volume">
        <h4>${txt({ ko: '상대강도 & 볼륨', en: 'RS & Volume' })}</h4>
        <dl class="profile-kv"><div><dt style="color:var(--muted);font-size:11px">${txt({ ko: '분석 대기', en: 'Awaiting analysis' })}</dt><dd></dd></div></dl>
      </div>

      <div class="profile-section" data-section="lr-eps">
        <h4>${txt({ ko: '최소저항선 & EPS', en: 'Least Resistance & EPS' })}</h4>
        <dl class="profile-kv"><div><dt style="color:var(--muted);font-size:11px">${txt({ ko: '분석 대기', en: 'Awaiting analysis' })}</dt><dd></dd></div></dl>
      </div>

      <div class="profile-section" data-section="cup-with-handle">
        <h4>${txt({ ko: '컵위드핸들', en: 'Cup with Handle' })}</h4>
        <dl class="profile-kv"><div><dt style="color:var(--muted);font-size:11px">${txt({ ko: '분석 대기', en: 'Awaiting analysis' })}</dt><dd></dd></div></dl>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '파이프라인', en: 'Pipeline' })}</h4>
        <dl class="profile-kv">
          <div><dt>Alpha</dt><dd><span class="profile-badge ${ps.alpha?.passed ? 'pass' : 'fail'}">${ps.alpha?.passed ? `PASS ${fmtNum(ps.alpha.score, 1)}` : 'FAIL'}</span></dd></div>
          <div><dt>Beta (VCP)</dt><dd><span class="profile-badge ${ps.beta?.passed ? 'pass' : 'fail'}">${ps.beta?.passed ? `PASS ${fmtNum(ps.beta.confidence, 2)}` : 'FAIL'}</span></dd></div>
          <div><dt>Gamma</dt><dd><span class="profile-badge ${ps.gamma?.passed ? 'pass' : 'fail'}">${ps.gamma?.passed ? `PASS ${fmtNum(ps.gamma.gamma_score, 1)}` : 'FAIL'}</span></dd></div>
          <div><dt>Leader</dt><dd>${ps.leader?.ranked ? `<span class="profile-badge pass">${escapeHtml(ps.leader.stock_bucket || '-')}</span> ${fmtNum(Math.min(ps.leader.leader_stock_score || 0, 100), 1)}` : '<span class="profile-badge fail">-</span>'}</dd></div>
        </dl>
      </div>

      <div class="profile-section" data-section="sector">
        <h4>${txt({ ko: '섹터', en: 'Sector' })}</h4>
        <dl class="profile-kv">
          <div><dt>Sector</dt><dd>${escapeHtml(sc.sector || p.sector || '-')}</dd></div>
          <div data-key="breakout"><dt>Breakout</dt><dd><span class="profile-badge neutral">${escapeHtml(sc.leadership?.breakout_state ? (sc.leadership.breakout_state).replace(/^sector_/, '').replace(/_/g, ' ') : '-')}</span></dd></div>
          ${sc.leadership ? `
          <div><dt>Leader Score</dt><dd>${fmtNum(Math.min(sc.leadership.leader_score || 0, 100), 1)}</dd></div>
          <div><dt>Ready</dt><dd><span class="profile-badge ${sc.leadership.leadership_ready ? 'pass' : 'fail'}">${sc.leadership.leadership_ready ? 'YES' : 'NO'}</span></dd></div>
          ` : ''}
        </dl>
      </div>

      <div class="profile-section" data-section="persistence">
        <h4>${txt({ ko: '지속성', en: 'Persistence' })}</h4>
        <p style="color:var(--muted);font-size:11px">${txt({ ko: '별도 조회', en: 'N/A' })}</p>
      </div>

      ${ep && ep.entry ? `
      <div class="profile-section profile-section--full">
        <h4>${txt({ ko: '실행 계획', en: 'Execution Plan' })}</h4>
        <div class="profile-exec-grid">
          <div class="exec-item"><div class="label">Entry</div><div class="value">${fmtPrice(ep.entry)}</div></div>
          <div class="exec-item"><div class="label">Stop</div><div class="value" style="color:var(--bad)">${fmtPrice(ep.stop)}</div></div>
          <div class="exec-item"><div class="label">Target</div><div class="value" style="color:var(--good)">${fmtPrice(ep.target)}</div></div>
          <div class="exec-item"><div class="label">Qty</div><div class="value">${ep.qty || '-'}</div></div>
          <div class="exec-item"><div class="label">R/R</div><div class="value">${fmtNum(ep.rr_ratio, 2)}</div></div>
        </div>
      </div>` : ''}

      ${rec ? `
      <div class="profile-section profile-section--full">
        <h4>${txt({ ko: '추천', en: 'Recommendation' })}</h4>
        <div style="display:flex;align-items:center;gap:12px">
          <span class="profile-badge ${badgeCls(rec.conviction)}" style="font-size:16px;padding:4px 14px">${escapeHtml(rec.conviction || '-')}</span>
          <span style="font-size:18px;font-weight:700">${fmtNum(rec.recommendation_score, 1)}</span>
        </div>
      </div>` : ''}

    </div>

    ${_verificationPrompt(data)}
  `;
}

/* ── Open stock profile dialog (shared across all sections) ── */

let _activeProfileSymbol = null;

export function openStockProfile(symbol, apiBase) {
  if (!symbol) return;
  const dialog = $('companyProfileDialog');
  if (!dialog) return;
  _activeProfileSymbol = symbol;
  $('profileName').textContent = symbol;
  $('profileContent').innerHTML = `<p>${escapeHtml(txt({ ko: '로딩 중...', en: 'Loading...' }))}</p>`;
  if (!dialog.open) dialog.showModal();

  const base = apiBase || $('apiBase')?.value?.trim() || '';
  const encodedSym = encodeURIComponent(symbol);
  fetchJSON(`${base}/api/stock/${encodedSym}/overview`).then((overview) => {
    if (_activeProfileSymbol !== symbol) return;
    const displayName = (overview.profile || {}).name || symbol;
    $('profileName').textContent = `${displayName} (${symbol})`;
    renderCompanyProfile(overview);
    fetchJSON(`${base}/api/stock/${encodedSym}/overview?detail=true`).then((full) => {
      if (_activeProfileSymbol === symbol && dialog.open) renderCompanyProfile(full);
    }).catch(() => {});
  }).catch(() => {
    if (_activeProfileSymbol !== symbol) return;
    $('profileContent').innerHTML = `<p class="bad">${escapeHtml(txt({ ko: '로딩 실패. 새로고침 해주세요.', en: 'Failed to load. Please refresh.' }))}</p>`;
  });
}

/* ── Setup dialog close button ── */

export function setupProfileDialogClose() {
  const closeBtn = $('profileClose');
  const dialog = $('companyProfileDialog');
  if (closeBtn && dialog) {
    closeBtn.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (e) => {
      if (e.target === dialog) dialog.close();
    });
  }
}
