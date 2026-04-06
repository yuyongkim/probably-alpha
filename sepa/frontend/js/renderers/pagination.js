import {
  $,
  escapeHtml,
  state,
} from '../core.js?v=1775488167';
import { txt } from '../i18n.js?v=1775488167';

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function paginationStore() {
  if (!state.pagination || typeof state.pagination !== 'object') {
    state.pagination = {};
  }
  return state.pagination;
}

function pagerMount(target, targetId) {
  const placeholder = $(`${targetId}Pager`);
  if (placeholder) {
    placeholder.classList.add('table-pager');
    placeholder.dataset.paginationFor = targetId;
    return placeholder;
  }

  const anchor = target.closest('table') || target;
  let mount = anchor.nextElementSibling;
  if (mount?.classList.contains('table-pager') && mount.dataset.paginationFor === targetId) {
    return mount;
  }

  mount = document.createElement('div');
  mount.className = 'table-pager';
  mount.dataset.paginationFor = targetId;
  anchor.insertAdjacentElement('afterend', mount);
  return mount;
}

export function resetPaginationPage(key) {
  delete paginationStore()[key];
}

function currentPage(key, totalPages) {
  const current = Number(paginationStore()[key] || 1);
  const safePages = Math.max(1, totalPages);
  return clamp(Math.round(current) || 1, 1, safePages);
}

function setCurrentPage(key, nextPage, totalPages) {
  paginationStore()[key] = currentPage(key, totalPages);
  paginationStore()[key] = clamp(Math.round(nextPage) || 1, 1, Math.max(1, totalPages));
}

function pageSlice(items, key, pageSize) {
  const safeSize = Math.max(1, Math.round(pageSize) || 1);
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / safeSize));
  const page = currentPage(key, totalPages);
  const start = (page - 1) * safeSize;
  const end = Math.min(totalItems, start + safeSize);
  return {
    totalItems,
    totalPages,
    page,
    pageSize: safeSize,
    start,
    end,
    items: items.slice(start, end),
  };
}

function renderPager({ target, targetId, stateKey, paging, rerender }) {
  const mount = pagerMount(target, targetId);
  if (paging.totalItems <= paging.pageSize) {
    mount.innerHTML = '';
    mount.hidden = true;
    return;
  }

  mount.hidden = false;
  mount.innerHTML = `
    <div class="table-pager__meta">
      ${escapeHtml(txt({
        ko: `${paging.start + 1}-${paging.end} / ${paging.totalItems} 표시`,
        en: `Showing ${paging.start + 1}-${paging.end} of ${paging.totalItems}`,
      }))}
    </div>
    <div class="table-pager__controls">
      <button class="table-pager__button" type="button" data-page-action="prev" ${paging.page <= 1 ? 'disabled' : ''}>
        ${escapeHtml(txt({ ko: '이전', en: 'Prev' }))}
      </button>
      <span class="table-pager__status">${paging.page} / ${paging.totalPages}</span>
      <button class="table-pager__button" type="button" data-page-action="next" ${paging.page >= paging.totalPages ? 'disabled' : ''}>
        ${escapeHtml(txt({ ko: '다음', en: 'Next' }))}
      </button>
    </div>
  `;

  mount.querySelectorAll('[data-page-action]').forEach((button) => {
    button.addEventListener('click', () => {
      const delta = button.dataset.pageAction === 'prev' ? -1 : 1;
      setCurrentPage(stateKey, paging.page + delta, paging.totalPages);
      rerender();
    });
  });
}

export function renderPaginatedMarkup({
  targetId,
  items,
  stateKey,
  pageSize,
  renderItem,
  emptyMarkup,
  onAfterRender,
}) {
  const target = $(targetId);
  if (!target) return null;

  const rerender = () => renderPaginatedMarkup({
    targetId,
    items,
    stateKey,
    pageSize,
    renderItem,
    emptyMarkup,
    onAfterRender,
  });

  const paging = pageSlice(items || [], stateKey, pageSize);
  target.innerHTML = paging.items.map((item, index) => renderItem(item, paging.start + index, paging)).join('') || emptyMarkup;
  renderPager({
    target,
    targetId,
    stateKey,
    paging,
    rerender,
  });

  if (onAfterRender) {
    onAfterRender(paging.items, paging);
  }
  return paging;
}
