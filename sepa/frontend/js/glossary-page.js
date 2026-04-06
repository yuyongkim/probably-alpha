import { getLang, setupPageI18n, txt } from './i18n.js?v=1775484394';

const API_BASE = `${window.location.protocol}//${window.location.hostname || '127.0.0.1'}:8000`;

let glossaryItems = [];

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

async function fetchGlossary() {
  const response = await fetch(`${API_BASE}/api/glossary`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

async function initGlossaryPage() {
  const grid = document.getElementById('glossaryGrid');
  const count = document.getElementById('glossaryCount');
  if (!grid || !count) return;

  const render = () => {
    count.textContent = txt({ ko: `${glossaryItems.length}개`, en: `${glossaryItems.length} terms` });
    grid.innerHTML = glossaryItems.map((item) => `
      <article class="term-card">
        <strong>${escapeHtml(getLang() === 'ko' ? (item.term_ko || item.term) : item.term)}</strong>
        <small>${escapeHtml(getLang() === 'ko' ? (item.short_ko || item.short) : item.short)}</small>
        <p>${escapeHtml(getLang() === 'ko' ? (item.description_ko || item.description) : item.description)}</p>
      </article>
    `).join('') || `<div class="empty-state">${escapeHtml(txt({ ko: '표시할 용어가 없습니다.', en: 'No glossary terms available.' }))}</div>`;
  };

  setupPageI18n('glossary', render);

  try {
    const payload = await fetchGlossary();
    glossaryItems = payload.items || [];
    render();
  } catch (error) {
    count.textContent = txt({ ko: '오류', en: 'Error' });
    grid.innerHTML = `<div class="empty-state">${escapeHtml(txt({ ko: '용어를 불러오지 못했습니다.', en: 'Failed to load glossary terms.' }))} ${escapeHtml(String(error))}</div>`;
  }
}

initGlossaryPage();
