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
} from '../core.js';
import { txt } from '../i18n.js';

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

export function sparklineSvg(closes, width = 240, height = 80) {
  if (!closes || closes.length < 2) return '';
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const padL = 2;
  const padR = 42;
  const padY = 2;
  const w = width - padL - padR;
  const h = height - padY * 2;

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

  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" class="sparkline-svg">
    ${labels}
    <path d="${fillPath}" fill="${fillColor}"/>
    <path d="${linePath}" fill="none" stroke="${color}" stroke-width="1.5"/>
    ${maPath(ma20, '#f0c040')}
    ${maPath(ma60, '#60a0ff')}
    ${legend}
  </svg>`;
}

/* ── EPS Bar Chart SVG ── */

export function epsBarChart(epsData, width = 360, height = 90) {
  if (!epsData || epsData.length < 2) return '';
  const padL = 40, padR = 8, padT = 8, padB = 22;
  const w = width - padL - padR;
  const h = height - padT - padB;
  const vals = epsData.map((e) => e.eps || 0);
  const max = Math.max(...vals, 1);
  const min = Math.min(...vals, 0);
  const range = max - min || 1;
  const barW = Math.max(6, Math.min(20, w / epsData.length - 2));
  const gap = (w - barW * epsData.length) / Math.max(1, epsData.length);

  const bars = epsData.map((e, i) => {
    const v = e.eps || 0;
    const barH = Math.max(1, ((v - min) / range) * h);
    const x = padL + i * (barW + gap);
    const y = padT + h - barH;
    const color = (e.eps_yoy || 0) > 0 ? '#8af0b8' : (e.eps_yoy || 0) < 0 ? '#ff9e9e' : '#7a8fa6';
    const label = (e.period || '').replace(/^20/, '');
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barW}" height="${barH.toFixed(1)}" rx="2" fill="${color}" opacity="0.85"/>
      <text x="${(x + barW / 2).toFixed(1)}" y="${(height - 4).toFixed(1)}" text-anchor="middle" fill="var(--muted)" font-size="8">${label}</text>`;
  }).join('');

  // Y-axis labels
  const yLabels = [max, (max + min) / 2, min].map((v) => {
    const y = padT + h - ((v - min) / range) * h;
    return `<text x="${padL - 4}" y="${(y + 3).toFixed(1)}" text-anchor="end" fill="var(--muted)" font-size="8">${v >= 1000 ? (v / 1000).toFixed(0) + 'K' : Math.round(v)}</text>`;
  }).join('');

  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" class="eps-bar-chart">${yLabels}${bars}</svg>`;
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
  return `<p class="profile-biz-summary" style="font-size:12px;color:var(--muted);margin:6px 0 0;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;line-height:1.5">${escapeHtml(summary)}</p>`;
}

/* ── Financial Summary DL with grid ── */

export function financialTableMarkup(data) {
  const p = data.profile || {};
  const f = p.financials || {};

  const infoRows = [
    [txt({ ko: '시장', en: 'Market' }), escapeHtml(p.market || '-')],
    [txt({ ko: '업종', en: 'Sector' }), escapeHtml(p.sector_small || p.sector_large || '-')],
    [txt({ ko: '시가총액', en: 'Mkt Cap' }), escapeHtml(fmtKrwCompact(p.mkt_cap))],
  ];
  const finRows = [
    ['PER', f.per != null ? fmtNum(f.per, 2) : '-'],
    ['PBR', f.pbr != null ? fmtNum(f.pbr, 2) : '-'],
    ['ROE', f.roe != null ? `<span class="${f.roe >= 15 ? 'good' : f.roe >= 8 ? '' : 'bad'}">${fmtNum(f.roe, 1)}%</span>` : '-'],
    ['ROA', f.roa != null ? `${fmtNum(f.roa, 1)}%` : '-'],
    [txt({ ko: '영업이익률', en: 'OPM' }), f.opm != null ? `${fmtNum(f.opm, 1)}%` : '-'],
    [txt({ ko: '배당률', en: 'Div' }), f.dividend_yield != null ? `${fmtNum(f.dividend_yield, 1)}%` : '-'],
    [txt({ ko: '부채비율', en: 'Debt' }), f.debt_ratio != null ? `${fmtNum(f.debt_ratio, 0)}%` : '-'],
    ['EV/EBITDA', f.ev_ebitda != null ? fmtNum(f.ev_ebitda, 2) : '-'],
    [txt({ ko: '외인 1M', en: 'For. 1M' }), f.foreign_1m != null ? `<span class="${f.foreign_1m >= 0 ? 'good' : 'bad'}">${f.foreign_1m >= 0 ? '+' : ''}${fmtNum(f.foreign_1m, 1)}%</span>` : '-'],
  ];
  const infoDl = `<dl class="profile-dl">${infoRows.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('')}</dl>`;
  const finGrid = `<div class="profile-fin-grid">${finRows.map(([k, v]) => `<div class="fin-cell"><span class="fin-label">${k}</span><span class="fin-value">${v}</span></div>`).join('')}</div>`;
  return `${infoDl}${finGrid}${businessSummaryMarkup(p.business_summary)}`;
}

/* ── Session change display ── */

export function sessionMarkup(session) {
  if (!session || session.change_pct == null) return '';
  const up = session.change_pct >= 0;
  const sign = up ? '+' : '';
  const color = up ? 'var(--good)' : 'var(--bad)';
  return `<span class="profile-session" style="color:${color}">${sign}${fmtNum(session.change_abs, 0)} (${sign}${fmtNum(session.change_pct, 2)}%)</span>`;
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

  const sparkline = sparklineSvg(data.sparkline || p.sparkline || [], 340, 100);
  const epsData = data.eps_recent || p.eps_recent || [];

  const price = p.price || tt.close;

  el.innerHTML = `
    <div class="profile-grid">
      <div class="profile-chart">
        <h4>${txt({ ko: '최근 120일 주가', en: 'Price (120D)' })}</h4>
        ${sparkline}
        <p class="profile-price">${escapeHtml(fmtPrice(price))}</p>
        ${sessionMarkup(data.session)}
      </div>
      <div class="profile-facts">
        ${financialTableMarkup(data)}
      </div>
    </div>
    ${epsData.length >= 2 ? `
    <div class="profile-eps" style="margin-top:12px">
      <h4>${txt({ ko: 'EPS 추이', en: 'EPS Trend' })}</h4>
      ${epsBarChart(epsData, 380, 90)}
    </div>` : ''}
    ${financialAnalysisTable(data)}
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
          <div><dt>Leader</dt><dd>${ps.leader?.ranked ? `<span class="profile-badge pass">${escapeHtml(ps.leader.stock_bucket || '-')}</span> ${fmtNum(ps.leader.leader_stock_score, 1)}` : '<span class="profile-badge fail">-</span>'}</dd></div>
        </dl>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '섹터', en: 'Sector' })}</h4>
        <dl class="profile-kv">
          <div><dt>Sector</dt><dd>${escapeHtml(sc.sector || p.sector || '-')}</dd></div>
          <div><dt>Breakout</dt><dd><span class="profile-badge ${sc.breakout_state === 'sector_breakout_confirmed' ? 'pass' : sc.breakout_state === 'sector_breakout_setup' ? 'neutral' : 'fail'}">${escapeHtml((sc.breakout_state || '-').replace(/^sector_/, '').replace(/_/g, ' '))}</span></dd></div>
          ${sc.leadership ? `
          <div><dt>Leader Score</dt><dd>${fmtNum(sc.leadership.leader_score, 1)}</dd></div>
          <div><dt>Ready</dt><dd><span class="profile-badge ${sc.leadership.leadership_ready ? 'pass' : 'fail'}">${sc.leadership.leadership_ready ? 'YES' : 'NO'}</span></dd></div>
          <div><dt>Alpha/Beta</dt><dd>${fmtPlainPct((sc.leadership.alpha_ratio || 0) * 100)} / ${fmtPlainPct((sc.leadership.beta_ratio || 0) * 100)}</dd></div>
          ` : ''}
        </dl>
      </div>

      <div class="profile-section">
        <h4>${txt({ ko: '지속성', en: 'Persistence' })}</h4>
        ${pers && pers.persistence_score != null ? `
        <dl class="profile-kv">
          <div><dt>Score</dt><dd>${fmtNum(pers.persistence_score, 1)}</dd></div>
          <div><dt>Appearance</dt><dd>${fmtPlainPct((pers.appearance_ratio || 0) * 100)}</dd></div>
          <div><dt>Streak</dt><dd>${pers.current_streak || 0} (max ${pers.max_streak || 0})</dd></div>
          <div><dt>Avg Rank</dt><dd>${pers.avg_rank != null ? fmtNum(pers.avg_rank, 1) : '-'}</dd></div>
        </dl>
        ` : `<p style="color:var(--muted);font-size:12px">-</p>`}
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
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
          <span class="profile-badge ${badgeCls(rec.conviction)}" style="font-size:16px;padding:4px 14px">${escapeHtml(rec.conviction || '-')}</span>
          <span style="font-size:18px;font-weight:700">${fmtNum(rec.recommendation_score, 1)}</span>
        </div>
      </div>` : ''}

    </div>
  `;
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

  const spark = sparklineSvg(data.sparkline || [], 340, 100);
  const price = p.price || tt.close;
  const epsData = data.eps_recent || [];

  return `
    <div class="profile-grid">
      <div class="profile-chart">
        <h4>${txt({ ko: '최근 120일 주가', en: 'Price (120D)' })}</h4>
        ${spark}
        <p class="profile-price">${escapeHtml(fmtPrice(price))}</p>
        ${sessionMarkup(data.session)}
      </div>
      <div class="profile-facts">
        ${financialTableMarkup(data)}
      </div>
    </div>
    ${epsData.length >= 2 ? `
    <div class="profile-eps" style="margin-top:12px">
      <h4>${txt({ ko: 'EPS 추이', en: 'EPS Trend' })}</h4>
      ${epsBarChart(epsData, 380, 90)}
    </div>` : ''}
    ${financialAnalysisTable(data)}
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
          <div><dt>Leader</dt><dd>${ps.leader?.ranked ? `<span class="profile-badge pass">${escapeHtml(ps.leader.stock_bucket || '-')}</span> ${fmtNum(ps.leader.leader_stock_score, 1)}` : '<span class="profile-badge fail">-</span>'}</dd></div>
        </dl>
      </div>

      <div class="profile-section" data-section="sector">
        <h4>${txt({ ko: '섹터', en: 'Sector' })}</h4>
        <dl class="profile-kv">
          <div><dt>Sector</dt><dd>${escapeHtml(sc.sector || p.sector || '-')}</dd></div>
          <div data-key="breakout"><dt>Breakout</dt><dd><span class="profile-badge neutral">${escapeHtml(sc.leadership?.breakout_state ? (sc.leadership.breakout_state).replace(/^sector_/, '').replace(/_/g, ' ') : '-')}</span></dd></div>
          ${sc.leadership ? `
          <div><dt>Leader Score</dt><dd>${fmtNum(sc.leadership.leader_score, 1)}</dd></div>
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
