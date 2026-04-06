import {
  escapeHtml,
  fmtDate,
  fmtPrice,
  fmtRR,
  fmtShares,
  state,
} from '../core.js?v=1775481741';
import { txt } from '../i18n.js?v=1775481741';
import { renderPaginatedMarkup } from './pagination.js?v=1775481741';
import {
  companyMarkup,
  defaultRowMarkup,
  recommendationPlanMarkup,
  scoreMarkup,
  setDynamicText,
  stockContext,
} from './shared.js?v=1775481741';
import { openStockProfile } from './stock-profile.js?v=1775481741';

function recommendationRowMarkup(item, index) {
  const why = item?.why || {};
  const active = item?.symbol === state.activeSymbol ? ' is-active' : '';
  return `
    <tr class="clickable-row${active}" data-symbol="${escapeHtml(item?.symbol || '')}" data-sector="${escapeHtml(item?.sector || '')}">
      <td>${index + 1}</td>
      <td>${companyMarkup(item)}</td>
      <td>${escapeHtml(item?.sector || '-')}</td>
      <td><span class="chip ${item?.conviction === 'A' ? 'good' : 'mid'}">${escapeHtml(item?.conviction || '-')}</span></td>
      <td>${scoreMarkup(item?.recommendation_score)}</td>
      <td>${escapeHtml(why.eps_status || '-')}</td>
      <td>${escapeHtml(why.least_resistance || '-')}</td>
      <td><strong>${escapeHtml(fmtRR(item?.risk_plan?.rr_ratio))}</strong></td>
      <td>${recommendationPlanMarkup(item?.risk_plan, true)}</td>
    </tr>
  `;
}

function omegaRowMarkup(item) {
  const active = item?.symbol === state.activeSymbol ? ' is-active' : '';
  return `
    <tr class="clickable-row${active}" data-symbol="${escapeHtml(item?.symbol || '')}">
      <td>${companyMarkup(item)}</td>
      <td>${escapeHtml(fmtPrice(item?.entry))}</td>
      <td>${escapeHtml(fmtPrice(item?.stop))}</td>
      <td>${escapeHtml(fmtPrice(item?.target))}</td>
      <td>${escapeHtml(fmtShares(item?.qty))}</td>
      <td>${escapeHtml(fmtRR(item?.rr_ratio))}</td>
    </tr>
  `;
}

function historyTop3Markup(item = {}) {
  const top3 = item?.top3 || [];
  if (!top3.length) {
    return `<span class="empty-state">${escapeHtml(txt({ ko: 'No picks', en: 'No picks' }))}</span>`;
  }
  return `
    <div class="history-pick-stack">
      ${top3.map((pick, index) => `
        <button type="button" class="link-button history-pick" data-history-symbol="${escapeHtml(pick?.symbol || '')}" data-history-sector="${escapeHtml(pick?.sector || '')}">
          <span class="history-rank">${index + 1}</span>
          <span>
            <strong>${escapeHtml(pick?.name || pick?.symbol || '-')}</strong>
            <small>${escapeHtml(pick?.symbol || '-')} / ${escapeHtml(pick?.sector || '-')}</small>
          </span>
        </button>
      `).join('')}
    </div>
  `;
}

export function createRecommendationRenderers(actions) {
  function renderRecommendations(items) {
    renderPaginatedMarkup({
      targetId: 'recRows',
      items: items || [],
      stateKey: 'recommendations',
      pageSize: 6,
      renderItem: (item, index) => recommendationRowMarkup(item, index),
      emptyMarkup: defaultRowMarkup(9, txt({ ko: 'No recommendations available', en: 'No recommendations available' })),
      onAfterRender: (pageItems) => {
        document.querySelectorAll('#recRows [data-symbol]').forEach((row) => {
          row.addEventListener('click', () => {
            const item = pageItems.find((entry) => entry?.symbol === row.dataset.symbol);
            if (!item) return;
            if (item?.sector) {
              void actions.loadSectorMembers(item.sector, state.latestDateDir, { syncLogic: false });
            }
            void actions.loadAnalysis(item.symbol, state.latestDateDir, stockContext(item, 'recommendations'));
            openStockProfile(item.symbol);
          });
        });
      },
    });
  }

  function renderOmega(omega) {
    const finalPicks = Array.isArray(omega?.final_picks) ? omega.final_picks : [];
    const fallbackPicks = (state.latestRecommendations || [])
      .filter((item) => item?.risk_plan)
      .map((item) => ({
        symbol: item.symbol,
        name: item.name,
        sector: item.sector,
        entry: item.risk_plan.entry,
        stop: item.risk_plan.stop,
        target: item.risk_plan.target,
        qty: item.risk_plan.qty,
        rr_ratio: item.risk_plan.rr_ratio,
      }));
    const picks = finalPicks.length ? finalPicks : fallbackPicks;

    setDynamicText('omegaMeta', finalPicks.length
      ? txt({
        ko: `Omega note: ${omega?.note || 'rule-based final selection'}`,
        en: `Omega note: ${omega?.note || 'rule-based final selection'}`,
      })
      : txt({
        ko: 'Omega final picks are empty. Showing recommendation risk plans as the execution fallback.',
        en: 'Omega final picks are empty. Showing recommendation risk plans as the execution fallback.',
      }));

    renderPaginatedMarkup({
      targetId: 'omegaRows',
      items: picks,
      stateKey: 'omegaPlan',
      pageSize: 6,
      renderItem: (item) => omegaRowMarkup(item),
      emptyMarkup: defaultRowMarkup(6, txt({ ko: 'No Omega execution plan available', en: 'No Omega execution plan available' })),
      onAfterRender: (pageItems) => {
        document.querySelectorAll('#omegaRows [data-symbol]').forEach((row) => {
          row.addEventListener('click', () => {
            const item = pageItems.find((entry) => entry?.symbol === row.dataset.symbol);
            if (!item) return;
            if (item?.sector) {
              void actions.loadSectorMembers(item.sector, state.latestDateDir, { syncLogic: false });
            }
            void actions.loadAnalysis(item.symbol, state.latestDateDir, stockContext(item, 'omega'));
            openStockProfile(item.symbol);
          });
        });
      },
    });
  }

  function renderHistory(items) {
    renderPaginatedMarkup({
      targetId: 'historyRows',
      items: items || [],
      stateKey: 'recommendationHistory',
      pageSize: 8,
      renderItem: (item) => `
        <tr>
          <td>${escapeHtml(fmtDate(item?.date_dir))}</td>
          <td>${escapeHtml(String(item?.count ?? 0))}</td>
          <td>${historyTop3Markup(item)}</td>
          <td>${item?.top3?.[0]?.recommendation_score != null ? scoreMarkup(item.top3[0].recommendation_score) : '-'}</td>
        </tr>
      `,
      emptyMarkup: defaultRowMarkup(4, txt({ ko: 'No recommendation history available', en: 'No recommendation history available' })),
      onAfterRender: (pageItems) => {
        document.querySelectorAll('#historyRows [data-history-symbol]').forEach((button) => {
          button.addEventListener('click', () => {
            const historyItem = pageItems.find((entry) => (entry?.top3 || []).some((pick) => pick?.symbol === button.dataset.historySymbol));
            const stock = (historyItem?.top3 || []).find((pick) => pick?.symbol === button.dataset.historySymbol);
            if (!stock) return;
            if (stock?.sector) {
              void actions.loadSectorMembers(stock.sector, historyItem?.date_dir || state.latestDateDir, { syncLogic: false });
            }
            void actions.loadAnalysis(stock.symbol, historyItem?.date_dir || '', stockContext(stock, 'recommendation-history'));
            openStockProfile(stock.symbol);
          });
        });
      },
    });
  }

  return {
    renderRecommendations,
    renderOmega,
    renderHistory,
  };
}
