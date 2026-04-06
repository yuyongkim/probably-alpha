import {
  $,
  escapeHtml,
  fmtKrwCompact,
  fmtNum,
  fmtPct,
  fmtPlainPct,
  fmtPrice,
  fmtCompact,
  state,
} from '../core.js?v=1775480720';
import { termTip } from '../term-tips.js?v=1775480720';
import { txt } from '../i18n.js?v=1775480720';
import { breakoutLabel, heatTone } from './shared.js?v=1775480720';
import {
  movingAvg,
  sparklineSvg,
  openStockProfile,
  setupProfileDialogClose,
} from './stock-profile.js?v=1775480720';

function sectorCardMarkup(group, actions) {
  const meta = group.sector_meta || {};
  const tone = heatTone(meta.leader_score, meta.leadership_ready);
  const bucketLabel = meta.leadership_ready
    ? txt({ ko: 'Confirmed', en: 'Confirmed' })
    : txt({ ko: 'Watchlist', en: 'Watchlist' });

  const stockRows = (group.stocks || []).map((stock, i) => {
    const sparkline = sparklineSvg(stock.sparkline);
    const closes = stock.sparkline || [];
    const ma20arr = movingAvg(closes, 20);
    const ma60arr = movingAvg(closes, 60);
    const ma20val = ma20arr.length ? ma20arr[ma20arr.length - 1] : null;
    const ma60val = ma60arr.length ? ma60arr[ma60arr.length - 1] : null;
    return `
      <tr class="clickable-row" data-symbol="${escapeHtml(stock.symbol)}" data-sector="${escapeHtml(group.sector)}">
        <td>${i + 1}</td>
        <td>
          <div class="company-cell">
            <strong>${escapeHtml(stock.name || stock.symbol)}</strong>
            <small>${escapeHtml(stock.symbol)}</small>
          </div>
        </td>
        <td class="sparkline-cell">${sparkline}</td>
        <td class="price-cell">${escapeHtml(fmtPrice(stock.price || (stock.sparkline && stock.sparkline.length ? stock.sparkline[stock.sparkline.length - 1] : null)))}</td>
        <td class="ma-cell"><span style="color:#f0c040">${ma20val != null ? fmtPrice(ma20val) : '-'}</span><br><span style="color:#60a0ff">${ma60val != null ? fmtPrice(ma60val) : '-'}</span></td>
        <td><span class="score ${stock.leader_stock_score >= 70 ? 'good' : stock.leader_stock_score >= 40 ? 'mid' : 'bad'}">${fmtNum(Math.min(stock.leader_stock_score || 0, 100), 1)}</span></td>
        <td>${escapeHtml(fmtPlainPct(stock.ret120_pct))}</td>
        <td>${fmtNum(stock.beta_confidence, 2)}</td>
        <td>
          <button type="button" class="profile-btn" data-symbol="${escapeHtml(stock.symbol)}" title="${txt({ ko: '기업개요', en: 'Company Profile' })}">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm.75 3.5v2.75H11.5v1.5H8.75V11.5h-1.5V8.75H4.5v-1.5h2.75V4.5h1.5z"/></svg>
          </button>
        </td>
      </tr>
    `;
  }).join('');

  return `
    <article class="panel sector-grouped-card tone-border-${tone}">
      <div class="sector-grouped-card__head">
        <div>
          <h3>${escapeHtml(group.sector)}</h3>
          <div class="sector-grouped-card__badges">
            <span class="flag ${meta.leadership_ready ? 'good' : 'mid'}">${escapeHtml(bucketLabel)}</span>
            <span class="flag mid">${escapeHtml(breakoutLabel(meta.breakout_state))}</span>
          </div>
        </div>
        <div class="sector-grouped-card__stats">
          <span><strong>${fmtNum(meta.leader_score, 1)}</strong><small>Score</small></span>
          <span><strong>${meta.alpha_count || 0}/${meta.universe_count || 0}</strong><small>Alpha</small></span>
          <span><strong>${fmtPct(meta.avg_ret120)}</strong><small>120D</small></span>
        </div>
      </div>
      <table class="sector-grouped-card__table">
        <thead>
          <tr>
            <th>#</th>
            <th>${txt({ ko: '종목', en: 'Stock' })}</th>
            <th>${termTip('sparkline', txt({ ko: '차트', en: 'Chart' }))}</th>
            <th>${txt({ ko: '현재가', en: 'Price' })}</th>
            <th>${txt({ ko: 'MA20/60', en: 'MA20/60' })}</th>
            <th>${termTip('leader', txt({ ko: '점수', en: 'Score' }))}</th>
            <th>${termTip('ret', '120D')}</th>
            <th>${termTip('beta', 'Beta')}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${stockRows || `<tr><td colspan="9">${escapeHtml(txt({ ko: '해당 섹터에 Alpha 통과 종목 없음', en: 'No Alpha pass stocks in this sector' }))}</td></tr>`}</tbody>
      </table>
    </article>
  `;
}

export function createSectorGroupedRenderers(actions) {
  function renderSectorGroupedView(groupedItems) {
    const root = $('sectorGroupedView');
    if (!root) return;

    const MAX_SECTORS = 8;
    const MAX_STOCKS_PER_SECTOR = 3;

    const items = groupedItems || [];
    if (!items.length) {
      root.innerHTML = `<div class="empty-state">${escapeHtml(txt({ ko: '섹터 그룹 데이터가 없습니다.', en: 'No sector-grouped data available.' }))}</div>`;
      return;
    }

    // Follow the exact order from the sector tables (state.latestSectors),
    // showing only confirmed + watchlist sectors (no emerging).
    const groupedMap = new Map(items.map((g) => [g.sector, g]));
    const sectorOrder = (state.latestSectors || [])
      .map((s) => s?.sector)
      .filter(Boolean);

    let ordered;
    if (sectorOrder.length) {
      ordered = sectorOrder
        .map((name) => groupedMap.get(name))
        .filter(Boolean);
    } else {
      // Fallback: use grouped items that are confirmed or watchlist, sorted by score
      ordered = items
        .filter((g) => {
          const bucket = g.sector_meta?.sector_bucket || '';
          return bucket === 'confirmed_leader' || bucket === 'watchlist';
        })
        .slice()
        .sort((a, b) => (b.sector_meta?.leader_score || 0) - (a.sector_meta?.leader_score || 0));
    }

    const trimmed = ordered.slice(0, MAX_SECTORS).map((group) => ({
      ...group,
      stocks: (group.stocks || []).slice(0, MAX_STOCKS_PER_SECTOR),
    }));

    root.innerHTML = trimmed.map((group) => sectorCardMarkup(group, actions)).join('');

    // Row click → open profile dialog + update Chart Desk
    root.querySelectorAll('.clickable-row[data-symbol]').forEach((row) => {
      row.addEventListener('click', (e) => {
        if (e.target.closest('.profile-btn')) return;
        const symbol = row.dataset.symbol;
        const sector = row.dataset.sector;
        if (sector) void actions.loadSectorMembers(sector, state.latestDateDir);
        void actions.loadAnalysis(symbol, state.latestDateDir, { source: 'sector-grouped', sector });
        openStockProfile(symbol);
      });
    });

    // Profile button → only open profile dialog
    root.querySelectorAll('.profile-btn[data-symbol]').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        openStockProfile(btn.dataset.symbol);
      });
    });
  }

  setupProfileDialogClose();

  return { renderSectorGroupedView };
}
