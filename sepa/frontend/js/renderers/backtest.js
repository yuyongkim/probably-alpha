import { escapeHtml, fmtDate, fmtNum, state } from '../core.js?v=1775488167';
import { txt } from '../i18n.js?v=1775488167';
import { renderPaginatedMarkup } from './pagination.js?v=1775488167';
import {
  backtestSessionMarkup,
  bucketWindowLabel,
  buildSectorContext,
  companyMarkup,
} from './shared.js?v=1775488167';

function sectorMetric(item = {}) {
  if (item?.weekly_leader_score != null) {
    return {
      label: txt({ ko: 'Weekly', en: 'Weekly' }),
      value: fmtNum(Math.min(item.weekly_leader_score || 0, 100), 2),
      note: txt({
        ko: `${item.appearance_count || 0}x / best #${item.best_rank || '-'}`,
        en: `${item.appearance_count || 0}x / best #${item.best_rank || '-'}`,
      }),
    };
  }
  return {
    label: txt({ ko: 'Score', en: 'Score' }),
    value: fmtNum(Math.min(item.leader_score || 0, 100), 2),
    note: txt({
      ko: `${item.alpha_count || 0} alpha / ${item.universe_count || 0} universe`,
      en: `${item.alpha_count || 0} alpha / ${item.universe_count || 0} universe`,
    }),
  };
}

function stockMetric(item = {}) {
  if (item?.weekly_leader_score != null) {
    return {
      label: txt({ ko: 'Weekly', en: 'Weekly' }),
      value: fmtNum(Math.min(item.weekly_leader_score || 0, 100), 2),
      note: txt({
        ko: `${item.appearance_count || 0}x / best #${item.best_rank || '-'}`,
        en: `${item.appearance_count || 0}x / best #${item.best_rank || '-'}`,
      }),
    };
  }
  return {
    label: txt({ ko: 'Score', en: 'Score' }),
    value: fmtNum(Math.min(item.leader_stock_score || 0, 100), 2),
    note: escapeHtml(item?.sector || '-'),
  };
}

function sectorEntryMarkup(item, index) {
  const metric = sectorMetric(item);
  return `
    <button type="button" class="link-button bucket-entry" data-bucket-sector="${escapeHtml(item?.sector || '')}">
      <span class="bucket-rank">#${index + 1}</span>
      <span class="bucket-entry__body">
        <strong>${escapeHtml(item?.sector || '-')}</strong>
        <small>${escapeHtml(metric.note)}</small>
      </span>
      <span class="bucket-entry__metric">
        <label>${escapeHtml(metric.label)}</label>
        <strong>${escapeHtml(metric.value)}</strong>
      </span>
    </button>
  `;
}

function stockEntryMarkup(item, index) {
  const metric = stockMetric(item);
  return `
    <button
      type="button"
      class="link-button bucket-entry"
      data-bucket-symbol="${escapeHtml(item?.symbol || '')}"
      data-bucket-sector="${escapeHtml(item?.sector || '')}"
    >
      <span class="bucket-rank">#${index + 1}</span>
      <span class="bucket-entry__body">
        <strong>${escapeHtml(item?.name || item?.symbol || '-')}</strong>
        <small>${escapeHtml(item?.symbol || '-')} / ${escapeHtml(item?.sector || '-')}</small>
        ${backtestSessionMarkup(item?.session)}
      </span>
      <span class="bucket-entry__metric">
        <label>${escapeHtml(metric.label)}</label>
        <strong>${escapeHtml(metric.value)}</strong>
      </span>
    </button>
  `;
}

function bucketCardMarkup(bucket) {
  return `
    <article class="bucket-card">
      <div class="bucket-head">
        <div>
          <span class="bucket-kicker">${escapeHtml(bucket?.bucket || '-')}</span>
          <h3>${escapeHtml(fmtDate(bucket?.date_to || bucket?.bucket || '-'))}</h3>
          <p>${escapeHtml(bucketWindowLabel(bucket))}</p>
        </div>
        <div class="bucket-head__meta">
          <span class="bucket-meta-pill">${escapeHtml(txt({ ko: `${bucket?.snapshot_count || 0} snapshots`, en: `${bucket?.snapshot_count || 0} snapshots` }))}</span>
          <span class="bucket-meta-pill">${escapeHtml(txt({ ko: `${(bucket?.sectors || []).length} sectors`, en: `${(bucket?.sectors || []).length} sectors` }))}</span>
          <span class="bucket-meta-pill">${escapeHtml(txt({ ko: `${(bucket?.stocks || []).length} stocks`, en: `${(bucket?.stocks || []).length} stocks` }))}</span>
        </div>
      </div>
      <div class="bucket-columns">
        <section class="bucket-column">
          <div class="bucket-column__head">
            <strong>${escapeHtml(txt({ ko: 'Top sectors', en: 'Top sectors' }))}</strong>
            <small>${escapeHtml(txt({ ko: 'Use sector strength to reopen the same-date drill-down.', en: 'Use sector strength to reopen the same-date drill-down.' }))}</small>
          </div>
          <div class="mini-list">
            ${(bucket?.sectors || []).map((item, index) => sectorEntryMarkup(item, index)).join('') || `<div class="empty-state">${escapeHtml(txt({ ko: 'No sectors', en: 'No sectors' }))}</div>`}
          </div>
        </section>
        <section class="bucket-column">
          <div class="bucket-column__head">
            <strong>${escapeHtml(txt({ ko: 'Top stocks', en: 'Top stocks' }))}</strong>
            <small>${escapeHtml(txt({ ko: 'Session move is measured versus the previous close for that bucket date.', en: 'Session move is measured versus the previous close for that bucket date.' }))}</small>
          </div>
          <div class="mini-list">
            ${(bucket?.stocks || []).map((item, index) => stockEntryMarkup(item, index)).join('') || `<div class="empty-state">${escapeHtml(txt({ ko: 'No stocks', en: 'No stocks' }))}</div>`}
          </div>
        </section>
      </div>
    </article>
  `;
}

export function createBacktestRenderers(actions) {
  function renderBacktest(items) {
    state.backtestBuckets = items || [];

    renderPaginatedMarkup({
      targetId: 'backtestBuckets',
      items: state.backtestBuckets,
      stateKey: 'backtestBuckets',
      pageSize: 4,
      renderItem: (bucket) => bucketCardMarkup(bucket),
      emptyMarkup: `<div class="empty-state">${escapeHtml(txt({ ko: 'No backtest buckets available', en: 'No backtest buckets available' }))}</div>`,
      onAfterRender: (pageItems) => {
        document.querySelectorAll('#backtestBuckets [data-bucket-sector]').forEach((button) => {
          button.addEventListener('click', () => {
            const bucket = pageItems.find((entry) => (entry?.sectors || []).some((sector) => sector?.sector === button.dataset.bucketSector));
            if (!bucket) return;
            void actions.loadSectorMembers(button.dataset.bucketSector, bucket?.date_to || state.latestDateDir);
          });
        });

        document.querySelectorAll('#backtestBuckets [data-bucket-symbol]').forEach((button) => {
          button.addEventListener('click', () => {
            const bucket = pageItems.find((entry) => (entry?.stocks || []).some((stock) => stock?.symbol === button.dataset.bucketSymbol));
            const stock = (bucket?.stocks || []).find((item) => item?.symbol === button.dataset.bucketSymbol);
            if (!stock) return;
            if (stock?.sector) {
              void actions.loadSectorMembers(stock.sector, bucket?.date_to || state.latestDateDir, { syncLogic: false });
            }
            void actions.loadAnalysis(stock.symbol, bucket?.date_to || '', buildSectorContext(stock, {
              source: 'backtest',
              sector: stock?.sector,
              sectorBucket: stock?.sector_bucket,
              sectorLeadershipReady: stock?.sector_leadership_ready,
              sectorLeaderScore: stock?.sector_leader_score || stock?.avg_leader_stock_score,
              dateDir: bucket?.date_to || '',
            }));
          });
        });
      },
    });
  }

  return {
    renderBacktest,
  };
}
