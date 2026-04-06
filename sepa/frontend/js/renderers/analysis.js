import {
  $,
  escapeHtml,
  fmtCompact,
  fmtDate,
  fmtKrwCompact,
  fmtNum,
  fmtPlainPct,
  fmtPrice,
  state,
} from '../core.js?v=1775472534';
import { txt } from '../i18n.js?v=1775472534';
import {
  companyFactMarkup,
  companyMarkup,
  defaultRowMarkup,
  metricNote,
  scoreMarkup,
  setDynamicText,
  stockContext,
} from './shared.js?v=1775472534';

function sourceLabel(context = {}) {
  const labels = {
    'leader-stocks-confirmed': { ko: 'Confirmed leaders', en: 'Confirmed leaders' },
    'leader-stocks-setup': { ko: 'Setup candidates', en: 'Setup candidates' },
    'sector-members': { ko: 'Sector drill-down', en: 'Sector drill-down' },
    recommendations: { ko: 'Recommendations', en: 'Recommendations' },
    omega: { ko: 'Omega plan', en: 'Omega plan' },
    backtest: { ko: 'Backtest bucket', en: 'Backtest bucket' },
    'recommendation-history': { ko: 'Recommendation history', en: 'Recommendation history' },
  };
  return txt(labels[String(context?.source || '').trim()] || { ko: 'Dashboard', en: 'Dashboard' });
}

function summaryCard(label, value, note = '') {
  return `
    <article class="summary-card">
      <label>${escapeHtml(label)}</label>
      <strong>${escapeHtml(value)}</strong>
      ${note ? `<small>${escapeHtml(note)}</small>` : ''}
    </article>
  `;
}

function renderSectorPeerRows(actions, analysis) {
  const peers = ((state.activeSectorPayload?.members || []).length
    ? state.activeSectorPayload.members
    : state.latestStocks.filter((item) => item?.sector === analysis?.sector))
    .slice()
    .sort((a, b) => Number(b?.leader_stock_score || 0) - Number(a?.leader_stock_score || 0));

  const target = $('sectorPeerRows');
  if (!target) return;

  if (!peers.length) {
    target.innerHTML = defaultRowMarkup(5, txt({ ko: 'No sector peers available', en: 'No sector peers available' }));
    return;
  }

  target.innerHTML = peers.map((item, index) => {
    const active = item?.symbol === state.activeSymbol ? ' is-active' : '';
    return `
      <tr class="clickable-row${active}" data-peer-symbol="${escapeHtml(item?.symbol || '')}">
        <td>${index + 1}</td>
        <td>${companyMarkup(item)}</td>
        <td>${scoreMarkup(item?.leader_stock_score)}</td>
        <td>${escapeHtml(fmtNum(item?.beta_confidence, 2))}</td>
        <td>${escapeHtml(fmtPlainPct(item?.ret120_pct))}</td>
      </tr>
    `;
  }).join('');

  document.querySelectorAll('#sectorPeerRows [data-peer-symbol]').forEach((row) => {
    row.addEventListener('click', () => {
      const peer = peers.find((item) => item?.symbol === row.dataset.peerSymbol);
      if (!peer) return;
      void actions.loadAnalysis(peer.symbol, state.activeAsOfDate || state.latestDateDir, stockContext(peer, 'sector-members'));
    });
  });
}

export function createAnalysisRenderers(actions) {
  function renderLogicExplain(payload) {
    const root = $('logicExplain');
    if (!root) return;

    if (!payload) {
      root.innerHTML = `<div class="empty-state">${escapeHtml(txt({ ko: 'No logic payload available', en: 'No logic payload available' }))}</div>`;
      return;
    }

    const philosophy = payload?.philosophy || [];
    const usage = payload?.usage || [];
    const formulas = payload?.formulas || [];
    const examples = payload?.examples || [];

    root.innerHTML = `
      <article class="logic-card">
        <div class="logic-headline">
          <div>
            <h3>${escapeHtml(txt({ ko: 'Scoring philosophy', en: 'Scoring philosophy' }))}</h3>
            <small>${escapeHtml(txt({ ko: `Resolved ${fmtDate(payload?.date_dir)}`, en: `Resolved ${fmtDate(payload?.date_dir)}` }))}</small>
          </div>
        </div>
        <ul class="logic-list">
          ${philosophy.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </article>

      <article class="logic-card">
        <div class="logic-headline">
          <div>
            <h3>${escapeHtml(txt({ ko: 'How to use it', en: 'How to use it' }))}</h3>
            <small>${escapeHtml(txt({ ko: 'Workflow order', en: 'Workflow order' }))}</small>
          </div>
        </div>
        <ul class="logic-list">
          ${usage.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </article>

      <details class="logic-card logic-card--wide logic-disclosure">
        <summary class="logic-summary">
          <div>
            <div class="logic-headline">
              <div>
                <h3>${escapeHtml(txt({ ko: 'Example calculations', en: 'Example calculations' }))}</h3>
                <small>${escapeHtml(txt({ ko: 'Collapsed by default to keep the panel readable.', en: 'Collapsed by default to keep the panel readable.' }))}</small>
              </div>
            </div>
          </div>
          <span class="logic-summary__meta">${escapeHtml(txt({ ko: `${examples.length} examples`, en: `${examples.length} examples` }))}</span>
        </summary>
        <div class="logic-disclosure__body">
          <div class="logic-examples">
            ${examples.map((example) => `
              <article class="logic-example">
                <strong>${escapeHtml(example?.title || '-')}</strong>
                <div class="logic-formula">${escapeHtml(example?.expression || '-')}</div>
                <p>${escapeHtml(example?.meaning || '-')}</p>
              </article>
            `).join('')}
          </div>
        </div>
      </details>

      <details class="logic-card logic-card--wide logic-disclosure">
        <summary class="logic-summary">
          <div>
            <div class="logic-headline">
              <div>
                <h3>${escapeHtml(txt({ ko: 'Formula library', en: 'Formula library' }))}</h3>
                <small>${escapeHtml(txt({ ko: 'Reference definitions and Minervini linkages.', en: 'Reference definitions and Minervini linkages.' }))}</small>
              </div>
            </div>
          </div>
          <span class="logic-summary__meta">${escapeHtml(txt({ ko: `${formulas.length} formulas`, en: `${formulas.length} formulas` }))}</span>
        </summary>
        <div class="logic-disclosure__body">
          <div class="logic-formula-grid">
            ${formulas.map((formula) => `
              <article class="logic-example">
                <strong>${escapeHtml(formula?.title || '-')}</strong>
                <div class="logic-formula">${escapeHtml(formula?.expression || '-')}</div>
                <ul class="logic-list">
                  ${(formula?.terms || []).map((term) => `<li>${escapeHtml(term)}</li>`).join('')}
                </ul>
                <p class="logic-copy">${escapeHtml(formula?.meaning || '-')}</p>
                <p class="logic-copy">${escapeHtml(formula?.minervini_link || '-')}</p>
              </article>
            `).join('')}
          </div>
        </div>
      </details>
    `;
  }

  function renderPersistenceCards(targetId, payload, kindLabel) {
    const root = $(targetId);
    if (!root) return;

    if (!payload) {
      root.innerHTML = `<div class="mini-stat-note">${escapeHtml(txt({
        ko: `${kindLabel} persistence appears here after selection.`,
        en: `${kindLabel} persistence appears here after selection.`,
      }))}</div>`;
      return;
    }

    root.innerHTML = [
      metricNote(txt({ ko: 'Persistence score', en: 'Persistence score' }), fmtNum(payload?.persistence_score, 2), `${payload?.top_n || '-'} top-N`),
      metricNote(txt({ ko: 'Appearances', en: 'Appearances' }), `${payload?.appearance_count ?? 0} / ${payload?.lookback_days ?? 0}`, `${fmtNum(Number(payload?.appearance_ratio || 0) * 100, 1)}%`),
      metricNote(txt({ ko: 'Current streak', en: 'Current streak' }), String(payload?.current_streak ?? 0), `${txt({ ko: 'Forward', en: 'Forward' })} ${payload?.forward_streak ?? 0}`),
      metricNote(txt({ ko: 'Max streak', en: 'Max streak' }), String(payload?.max_streak ?? 0), `${txt({ ko: 'Top1', en: 'Top1' })} ${payload?.top1_count ?? 0}`),
      metricNote(txt({ ko: 'Average rank', en: 'Average rank' }), payload?.avg_rank != null ? fmtNum(payload.avg_rank, 2) : '-', `${txt({ ko: 'Avg score', en: 'Avg score' })} ${fmtNum(payload?.avg_score_when_present, 2)}`),
      metricNote(txt({ ko: 'Seen window', en: 'Seen window' }), `${fmtDate(payload?.first_seen)} -> ${fmtDate(payload?.last_seen)}`, `${txt({ ko: 'Resolved', en: 'Resolved' })} ${fmtDate(payload?.resolved_date)}`),
      `<div class="mini-stat-note">${escapeHtml(payload?.logic?.expression || '')} ${payload?.logic?.meaning ? `| ${escapeHtml(payload.logic.meaning)}` : ''}</div>`,
    ].join('');
  }

  function renderAnalysisSummary(analysis, context) {
    setDynamicText('analysisName', analysis?.name || analysis?.symbol || txt({ ko: 'Unknown stock', en: 'Unknown stock' }));
    setDynamicText('pickedSymbol', `${txt({ ko: 'Code', en: 'Code' })} ${analysis?.symbol || '-'}`);
    setDynamicText('analysisSector', `${txt({ ko: 'Sector', en: 'Sector' })} ${analysis?.sector || context?.sector || '-'}`);
    setDynamicText('analysisDate', `${txt({ ko: 'Date', en: 'Date' })} ${fmtDate(analysis?.as_of_date || state.latestDateDir)}`);

    const trend = analysis?.trend_template || {};
    const rs = analysis?.relative_strength || {};
    const eps = analysis?.eps_quality || {};
    const lr = analysis?.least_resistance || {};
    const volume = analysis?.volume_signal || {};
    const summaryRoot = $('analysisSummary');

    if (summaryRoot) {
      summaryRoot.innerHTML = [
        summaryCard(txt({ ko: 'Close', en: 'Close' }), fmtPrice(trend?.close), `${txt({ ko: '52W high gap', en: '52W high gap' })} ${fmtPlainPct(trend?.distance_to_high52_pct)}`),
        summaryCard(txt({ ko: 'RS percentile', en: 'RS percentile' }), fmtNum(rs?.rs_percentile_120, 1), `${txt({ ko: 'State', en: 'State' })} ${rs?.state || '-'}`),
        summaryCard(txt({ ko: 'Least resistance', en: 'Least resistance' }), lr?.trend || '-', `${txt({ ko: 'Distance', en: 'Distance' })} ${fmtPlainPct(lr?.distance_pct)}`),
        summaryCard(txt({ ko: 'EPS quality', en: 'EPS quality' }), eps?.status || '-', `${txt({ ko: 'YoY', en: 'YoY' })} ${fmtPlainPct(eps?.latest_yoy)}`),
        summaryCard(txt({ ko: 'Volume 20D', en: 'Volume 20D' }), fmtNum(volume?.latest_ratio_20, 2), `${txt({ ko: 'State', en: 'State' })} ${volume?.state || '-'}`),
        companyFactMarkup(analysis),
      ].join('');
    }

    renderSectorPeerRows(actions, analysis);

    setDynamicText('analysisMeta', [
      `${txt({ ko: 'Source', en: 'Source' })} ${sourceLabel(context)}`,
      `${txt({ ko: 'Alpha checks', en: 'Alpha checks' })} ${trend?.passed_count ?? 0}/6`,
      `${txt({ ko: 'Sector RS', en: 'Sector RS' })} ${fmtNum(analysis?.sector_strength?.latest_rs, 1)}`,
      `${txt({ ko: 'Volume dry-up days', en: 'Volume dry-up days' })} ${volume?.dryup_days_20 ?? 0}`,
      `${txt({ ko: 'MACD', en: 'MACD' })} ${trend?.macd_state || '-'}`,
      `${txt({ ko: 'Market cap', en: 'Market cap' })} ${fmtKrwCompact(analysis?.company_facts?.market_cap_estimated || analysis?.company_facts?.market_cap_latest)}`,
    ].join(' | '));
  }

  return {
    renderLogicExplain,
    renderPersistenceCards,
    renderAnalysisSummary,
  };
}
