import { txt } from './i18n.js';

export const $ = (id) => document.getElementById(id);

export const state = {
  glossary: [],
  catalog: null,
  latestSectors: [],
  latestStocks: [],
  latestRecommendations: [],
  latestOmega: {},
  history: [],
  backtestBuckets: [],
  pagination: {},
  latestDateDir: '',
  requestedDateDir: '',
  activeSymbol: '',
  activeAsOfDate: '',
  activeContext: null,
  activeAnalysis: null,
  activeSector: '',
  activeSectorPayload: null,
  logicPayload: null,
  sectorPersistence: null,
  stockPersistence: null,
  analysisWindowDays: 120,
  analysisPanOffset: 0,
  analysisHoverIndex: null,
  analysisHoverYRatio: null,
  epsWindowQuarters: 16,
  epsWindowStart: null,
};

export const backtestContext = new Map();

export async function fetchJSON(url) {
  const response = await fetch(url);
  if (!response.ok) {
    let detail = '';
    try {
      const payload = await response.clone().json();
      if (payload && typeof payload.detail === 'string' && payload.detail.trim()) {
        detail = ` - ${payload.detail.trim()}`;
      }
    } catch {}
    throw new Error(`${response.status} ${response.statusText}${detail}`);
  }
  return response.json();
}

export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function cls(score) {
  const value = Number(score || 0);
  if (value >= 70) return 'good';
  if (value >= 40) return 'mid';
  return 'bad';
}

export function fmtDate(value) {
  const raw = String(value || '').trim().replaceAll('-', '');
  if (/^\d{8}$/.test(raw)) return `${raw.slice(0, 4)}-${raw.slice(4, 6)}-${raw.slice(6, 8)}`;
  return String(value || '-');
}

export function toDateToken(value) {
  return String(value || '').trim().replaceAll('-', '');
}

export function fmtDateShort(value) {
  const raw = toDateToken(value);
  if (/^\d{8}$/.test(raw)) return `${raw.slice(4, 6)}/${raw.slice(6, 8)}`;
  return String(value || '');
}

export function fmtDateAxis(value, previousValue = '', forceYear = false) {
  const raw = toDateToken(value);
  const prev = toDateToken(previousValue);
  if (!/^\d{8}$/.test(raw)) return String(value || '');
  if (forceYear || !/^\d{8}$/.test(prev) || prev.slice(0, 4) !== raw.slice(0, 4)) {
    return `${raw.slice(0, 4)}/${raw.slice(4, 6)}`;
  }
  return `${raw.slice(4, 6)}/${raw.slice(6, 8)}`;
}

export function fmtQuarter(period) {
  const raw = String(period || '').trim();
  if (/^\d{4}Q[1-4]$/.test(raw)) return `${raw.slice(0, 4)} Q${raw.slice(-1)}`;
  return raw;
}

export function fmtNum(value, digits = 2) {
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(digits) : '-';
}

export function fmtPrice(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  const rounded = Math.round(num);
  const formatted = rounded.toLocaleString('ko-KR');
  return txt({ ko: `${formatted}원`, en: `KRW ${formatted}` });
}

export function fmtShares(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  const formatted = Math.round(num).toLocaleString('ko-KR');
  return txt({ ko: `${formatted}주`, en: `${formatted} shares` });
}

export function fmtRR(value) {
  const num = Number(value);
  return Number.isFinite(num) ? `${num.toFixed(2)}R` : '-';
}

export function fmtPct(value) {
  const num = Number(value);
  return Number.isFinite(num) ? `${(num * 100).toFixed(1)}%` : '-';
}

export function fmtPlainPct(value) {
  const num = Number(value);
  return Number.isFinite(num) ? `${num.toFixed(2)}%` : '-';
}

export function fmtSignedPct(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return `${num >= 0 ? '+' : ''}${num.toFixed(1)}%`;
}

export function fmtCompact(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  if (Math.abs(num) >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(num) >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (Math.abs(num) >= 1_000) return `${(num / 1_000).toFixed(0)}K`;
  return `${Math.round(num)}`;
}

export function fmtKrwCompact(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  if (Math.abs(num) >= 1_000_000_000_000) return `KRW ${(num / 1_000_000_000_000).toFixed(2)}T`;
  if (Math.abs(num) >= 1_000_000_000) return `KRW ${(num / 1_000_000_000).toFixed(1)}B`;
  if (Math.abs(num) >= 1_000_000) return `KRW ${(num / 1_000_000).toFixed(1)}M`;
  return fmtPrice(num);
}

export function setDateInputValue(value) {
  const input = $('asOfDatePicker');
  if (!input) return;
  const token = toDateToken(value);
  input.value = /^\d{8}$/.test(token) ? fmtDate(token) : '';
}

export function selectedPersistenceWindow() {
  const value = Number($('persistenceWindow')?.value || 126);
  return Number.isFinite(value) && value > 0 ? value : 126;
}

export function companyCell(item) {
  const name = escapeHtml(item?.name || item?.symbol || '-');
  const symbol = escapeHtml(item?.symbol || '-');
  return `<div class="company-cell"><strong>${name}</strong><small>${escapeHtml(txt({ ko: '종목코드', en: 'Code' }))} ${symbol}</small></div>`;
}

export function scoreBadge(value) {
  return `<span class="score ${cls(value)}">${fmtNum(value)}</span>`;
}

export function log(message) {
  $('statusLog').textContent = message;
}
