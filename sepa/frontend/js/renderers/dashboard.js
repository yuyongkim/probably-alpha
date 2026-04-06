import {
  $,
  escapeHtml,
  fmtDate,
  fmtNum,
  fmtPct,
  fmtPlainPct,
  state,
} from '../core.js?v=1775480720';
import { txt } from '../i18n.js?v=1775480720';
import { renderPaginatedMarkup } from './pagination.js?v=1775480720';
import {
  activeSectorRecord,
  breakoutLabel,
  buildSectorContext,
  companyMarkup,
  defaultRowMarkup,
  heatTone,
  ret120Summary,
  scoreMarkup,
  sectorHeatValue,
  setDynamicText,
  stockContext,
  summaryReadyText,
} from './shared.js?v=1775480720';
import { openStockProfile } from './stock-profile.js?v=1775480720';

function bindSectorClick(selector, resolver, actions) {
  document.querySelectorAll(selector).forEach((node) => {
    node.addEventListener('click', () => {
      const sector = resolver(node);
      if (!sector) return;
      void actions.loadSectorMembers(sector, state.latestDateDir);
    });
  });
}

function sectorRowsMarkup(item, index) {
  const active = item?.sector === state.activeSector ? ' is-active' : '';
  return `
    <tr class="clickable-row${active}" data-sector="${escapeHtml(item?.sector || '')}">
      <td>${index + 1}</td>
      <td>
        <div class="company-cell">
          <strong>${escapeHtml(item?.sector || '-')}</strong>
          <small>${escapeHtml(breakoutLabel(item?.breakout_state))}</small>
        </div>
      </td>
      <td>${scoreMarkup(item?.leader_score)}</td>
      <td>${escapeHtml(`${Number(item?.alpha_count || 0)} / ${Number(item?.universe_count || 0)}`)}</td>
      <td>${escapeHtml(fmtNum(item?.beta_ratio ? Number(item.beta_ratio) * 100 : 0, 1))}%</td>
      <td>${escapeHtml(ret120Summary(item))}</td>
    </tr>
  `;
}

function stockRowMarkup(item, index) {
  const active = item?.symbol === state.activeSymbol ? ' is-active' : '';
  return `
    <tr class="clickable-row${active}" data-symbol="${escapeHtml(item?.symbol || '')}" data-sector="${escapeHtml(item?.sector || '')}">
      <td>${index + 1}</td>
      <td>${companyMarkup(item)}</td>
      <td>${escapeHtml(item?.sector || '-')}</td>
      <td>${scoreMarkup(item?.leader_stock_score)}</td>
      <td>${escapeHtml(fmtNum(item?.alpha_score, 1))}</td>
      <td>${escapeHtml(fmtNum(item?.beta_confidence, 2))}</td>
      <td>${escapeHtml(fmtNum(item?.gamma_score, 2))}</td>
      <td>${escapeHtml(fmtPlainPct(item?.ret120_pct))}</td>
    </tr>
  `;
}

function memberRowMarkup(item, index) {
  const active = item?.symbol === state.activeSymbol ? ' is-active' : '';
  return `
    <tr class="clickable-row${active}" data-symbol="${escapeHtml(item?.symbol || '')}">
      <td>${index + 1}</td>
      <td>
        ${companyMarkup(item)}
        <div class="member-flags">
          <span class="flag ${item?.recommended ? 'good' : 'mid'}">${escapeHtml(item?.recommended ? txt({ ko: 'Recommended', en: 'Recommended' }) : txt({ ko: 'Tracking', en: 'Tracking' }))}</span>
          <span class="flag ${item?.alpha_pass ? 'good' : 'mid'}">Alpha</span>
          <span class="flag ${item?.beta_pass ? 'good' : 'mid'}">Beta</span>
        </div>
      </td>
      <td>${scoreMarkup(item?.leader_stock_score)}</td>
      <td>${escapeHtml(fmtNum(item?.alpha_score, 1))}</td>
      <td>${escapeHtml(fmtNum(item?.beta_confidence, 2))}</td>
      <td>${escapeHtml(fmtNum(item?.gamma_score, 2))}</td>
      <td>${item?.recommendation_score != null ? scoreMarkup(item?.recommendation_score) : '-'}</td>
    </tr>
  `;
}

function renderSectorHeatmap(items, actions) {
  const root = $('sectorHeatmap');
  if (!root) return;

  const topItems = (items || []).slice(0, 6);
  root.innerHTML = topItems.map((item, index) => {
    const tone = heatTone(item?.leader_score, item?.leadership_ready);
    const active = item?.sector === state.activeSector ? ' is-active' : '';
    return `
      <button
        type="button"
        class="sector-tile tone-${tone}${active}"
        data-sector="${escapeHtml(item?.sector || '')}"
        style="--heat:${sectorHeatValue(item)}"
      >
        <div class="sector-tile__head">
          <span class="sector-tile__rank">#${index + 1}</span>
          <span class="sector-tile__state">${escapeHtml(item?.leadership_ready ? txt({ ko: 'Confirmed', en: 'Confirmed' }) : txt({ ko: 'Watch', en: 'Watch' }))}</span>
        </div>
        <strong>${escapeHtml(item?.sector || '-')}</strong>
        <span class="sector-tile__score">${escapeHtml(fmtNum(item?.leader_score, 2))}</span>
        <div class="sector-tile__meta">
          <small>${escapeHtml(summaryReadyText(item?.leadership_ready, item?.alpha_count || 0))}</small>
          <small>${escapeHtml(ret120Summary(item))}</small>
        </div>
      </button>
    `;
  }).join('') || `<div class="empty-state">${escapeHtml(txt({ ko: 'No sector heatmap data', en: 'No sector heatmap data' }))}</div>`;

  bindSectorClick('#sectorHeatmap [data-sector]', (node) => node.dataset.sector, actions);
}

function stockFilterValue() {
  return String($('stockFilter')?.value || '').trim().toLowerCase();
}

function filterStocks(items) {
  const keyword = stockFilterValue();
  if (!keyword) return items || [];
  return (items || []).filter((item) => {
    const haystack = `${item?.name || ''} ${item?.symbol || ''} ${item?.sector || ''}`.toLowerCase();
    return haystack.includes(keyword);
  });
}

export function createDashboardRenderers(actions) {
  function renderCatalog(catalog, summary) {
    state.catalog = catalog || null;
    const picker = $('asOfDatePicker');
    if (picker && catalog) {
      picker.min = fmtDate(catalog.available_date_min);
      picker.max = fmtDate(catalog.available_date_max);
      // Default to latest resolved date, not the old min
      if (!picker.value && state.latestDateDir) {
        picker.value = fmtDate(state.latestDateDir);
      }
    }

    $('kpiSectorCount').textContent = String(catalog?.sector_count ?? 0);
    $('kpiLeaderStocks').textContent = String(summary?.counts?.leader_stocks ?? state.latestStocks.filter((item) => item?.stock_bucket === 'confirmed_leader').length);
    setDynamicText('dateRangeMeta', txt({
      ko: `Supported ${fmtDate(catalog?.available_date_min)} -> ${fmtDate(catalog?.available_date_max)} | snapshots ${catalog?.snapshot_count ?? 0}`,
      en: `Supported ${fmtDate(catalog?.available_date_min)} -> ${fmtDate(catalog?.available_date_max)} | snapshots ${catalog?.snapshot_count ?? 0}`,
    }));
  }

  function renderSectorRows(items) {
    const all = items || [];
    const confirmed = all.filter((item) => item?.sector_bucket === 'confirmed_leader' || item?.leadership_ready);
    const watchlist = all.filter((item) => !confirmed.includes(item));

    $('confirmedSectorCount').textContent = txt({
      ko: `${confirmed.length} confirmed`,
      en: `${confirmed.length} confirmed`,
    });
    $('watchSectorCount').textContent = txt({
      ko: `${watchlist.length} watchlist`,
      en: `${watchlist.length} watchlist`,
    });

    renderSectorHeatmap(all, actions);

    renderPaginatedMarkup({
      targetId: 'sectorRows',
      items: confirmed,
      stateKey: 'confirmedSectors',
      pageSize: 5,
      renderItem: (item, index) => sectorRowsMarkup(item, index),
      emptyMarkup: defaultRowMarkup(6, txt({ ko: 'No confirmed leader sectors', en: 'No confirmed leader sectors' })),
      onAfterRender: () => bindSectorClick('#sectorRows [data-sector]', (node) => node.dataset.sector, actions),
    });

    renderPaginatedMarkup({
      targetId: 'watchSectorRows',
      items: watchlist,
      stateKey: 'watchSectors',
      pageSize: 5,
      renderItem: (item, index) => sectorRowsMarkup(item, index),
      emptyMarkup: defaultRowMarkup(6, txt({ ko: 'No watchlist sectors', en: 'No watchlist sectors' })),
      onAfterRender: () => bindSectorClick('#watchSectorRows [data-sector]', (node) => node.dataset.sector, actions),
    });
  }

  function renderStockRows(items) {
    const filtered = filterStocks(items);
    const confirmed = filtered.filter((item) => item?.stock_bucket === 'confirmed_leader');
    const setup = filtered.filter((item) => item?.stock_bucket !== 'confirmed_leader');

    $('confirmedStockCount').textContent = txt({
      ko: `${confirmed.length} confirmed`,
      en: `${confirmed.length} confirmed`,
    });
    $('setupStockCount').textContent = txt({
      ko: `${setup.length} setups`,
      en: `${setup.length} setups`,
    });

    const bindRows = (selector, pageItems, source) => {
      document.querySelectorAll(selector).forEach((row) => {
        row.addEventListener('click', () => {
          const item = pageItems.find((entry) => entry?.symbol === row.dataset.symbol);
          if (!item) return;
          if (item?.sector) {
            void actions.loadSectorMembers(item.sector, state.latestDateDir, { syncLogic: false });
          }
          void actions.loadAnalysis(item.symbol, state.latestDateDir, stockContext(item, source));
          openStockProfile(item.symbol);
        });
      });
    };

    renderPaginatedMarkup({
      targetId: 'stockRows',
      items: confirmed,
      stateKey: 'confirmedStocks',
      pageSize: 6,
      renderItem: (item, index) => stockRowMarkup(item, index),
      emptyMarkup: defaultRowMarkup(8, txt({ ko: 'No confirmed leader stocks', en: 'No confirmed leader stocks' })),
      onAfterRender: (pageItems) => bindRows('#stockRows [data-symbol]', pageItems, 'leader-stocks-confirmed'),
    });

    renderPaginatedMarkup({
      targetId: 'setupStockRows',
      items: setup,
      stateKey: 'setupStocks',
      pageSize: 6,
      renderItem: (item, index) => stockRowMarkup(item, index),
      emptyMarkup: defaultRowMarkup(8, txt({ ko: 'No setup candidates', en: 'No setup candidates' })),
      onAfterRender: (pageItems) => bindRows('#setupStockRows [data-symbol]', pageItems, 'leader-stocks-setup'),
    });
  }

  function renderSectorMembers(payload) {
    const target = $('sectorMembersRows');
    const pager = $('sectorMembersRowsPager');
    if (!target) return;

    if (!payload) {
      state.activeSector = '';
      state.activeSectorPayload = null;
      setDynamicText('sectorFocusMeta', txt({
        ko: 'Pick a sector to inspect members and ranking evidence.',
        en: 'Pick a sector to inspect members and ranking evidence.',
      }));
      target.innerHTML = defaultRowMarkup(7, txt({ ko: 'No sector selected', en: 'No sector selected' }));
      if (pager) {
        pager.innerHTML = '';
        pager.hidden = true;
      }
      return;
    }

    state.activeSector = payload.sector || '';
    state.activeSectorPayload = payload;

    const summary = payload?.sector_summary || activeSectorRecord() || {};
    setDynamicText('sectorFocusMeta', [
      payload?.sector || '-',
      `${txt({ ko: 'Score', en: 'Score' })} ${fmtNum(summary?.leader_score, 2)}`,
      breakoutLabel(summary?.breakout_state),
      `${txt({ ko: '120D', en: '120D' })} ${ret120Summary(summary)}`,
      `${txt({ ko: 'Date', en: 'Date' })} ${fmtDate(payload?.date_dir || state.latestDateDir)}`,
    ].join(' | '));

    renderPaginatedMarkup({
      targetId: 'sectorMembersRows',
      items: payload?.members || [],
      stateKey: 'sectorMembers',
      pageSize: 8,
      renderItem: (item, index) => memberRowMarkup(item, index),
      emptyMarkup: defaultRowMarkup(7, txt({ ko: 'No sector members available', en: 'No sector members available' })),
      onAfterRender: (pageItems) => {
        const context = buildSectorContext(summary, {
          source: 'sector-members',
          sector: payload?.sector,
          dateDir: payload?.date_dir || state.latestDateDir,
        });

        document.querySelectorAll('#sectorMembersRows [data-symbol]').forEach((row) => {
          row.addEventListener('click', () => {
            const item = pageItems.find((entry) => entry?.symbol === row.dataset.symbol);
            if (!item) return;
            void actions.loadAnalysis(item.symbol, payload?.date_dir || '', context);
            openStockProfile(item.symbol);
          });
        });
      },
    });
  }

  return {
    renderCatalog,
    renderSectorRows,
    renderStockRows,
    renderSectorMembers,
  };
}
