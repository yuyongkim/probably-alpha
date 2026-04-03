import { marketWizardPeople, peopleSeries } from './market-wizards-people-data.js';
import { setupPageI18n, txt } from './i18n.js';

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function peopleInSeries(seriesId) {
  return marketWizardPeople.filter((item) => item.series === seriesId);
}

function seriesLabel(series) {
  const labels = {
    'market-wizards': { ko: 'Market Wizards', en: 'Market Wizards' },
    'new-market-wizards': { ko: 'The New Market Wizards', en: 'The New Market Wizards' },
    'stock-market-wizards': { ko: 'Stock Market Wizards', en: 'Stock Market Wizards' },
    'hedge-fund-market-wizards': { ko: 'Hedge Fund Market Wizards', en: 'Hedge Fund Market Wizards' },
    'unknown-market-wizards': { ko: 'Unknown Market Wizards', en: 'Unknown Market Wizards' },
  };
  return txt(labels[series.id] || series.label);
}

function seriesCountLabel(series) {
  const labels = {
    'market-wizards': { ko: '선물과 매크로 중심의 고전 인터뷰', en: 'Classic futures and macro interviews' },
    'new-market-wizards': { ko: '매크로, 시스템, 주식으로 확장된 2세대 인터뷰', en: 'Second-wave interviews across macro, systems, and stock trading' },
    'stock-market-wizards': { ko: '주식 중심의 전용 권', en: 'Stock-focused volume with discretionary and systematic managers' },
    'hedge-fund-market-wizards': { ko: '펀드매니저 중심의 다중 전략 인터뷰', en: 'Fund-manager volume with multi-strategy and event-driven traders' },
    'unknown-market-wizards': { ko: '개인 트레이더와 잘 알려지지 않은 고성과자', en: 'Independent traders and lesser-known standout performers' },
  };
  return txt(labels[series.id] || series.countLabel);
}

function renderSummary() {
  const root = document.getElementById('peopleSummary');
  const count = document.getElementById('peopleCount');
  if (!root || !count) return;

  count.textContent = txt({ ko: `${marketWizardPeople.length}명`, en: `${marketWizardPeople.length} people` });
  root.innerHTML = peopleSeries.map((series) => {
    const seriesCount = peopleInSeries(series.id).length;
    return `
      <article class="definition-card">
        <label>${escapeHtml(seriesLabel(series))}</label>
        <strong>${escapeHtml(txt({ ko: `${seriesCount}명`, en: `${seriesCount} people` }))}</strong>
        <p>${escapeHtml(seriesCountLabel(series))}</p>
      </article>
    `;
  }).join('');
}

function personCard(person) {
  return `
    <article class="person-card">
      <div class="person-card__head">
        <div>
          <p class="eyebrow">${escapeHtml(person.bucket)}</p>
          <h3>${escapeHtml(person.name)}</h3>
        </div>
      </div>
      <p class="person-card__brief">${escapeHtml(person.brief)}</p>
      <div class="person-meta">
        ${person.keywords.map((keyword) => `<span class="wizard-chip">${escapeHtml(keyword)}</span>`).join('')}
      </div>
      ${person.relatedProfileId
        ? `<div class="person-card__actions"><a class="ghost-link" href="./market-wizards-korea.html#${escapeHtml(person.relatedProfileId)}">${escapeHtml(txt({ ko: '프리셋 매핑 보기', en: 'Open preset mapping' }))}</a></div>`
        : ''}
    </article>
  `;
}

function renderSections() {
  const root = document.getElementById('peopleSections');
  if (!root) return;

  root.innerHTML = peopleSeries.map((series) => {
    const items = peopleInSeries(series.id);
    return `
      <section class="panel people-section">
        <div class="panel-head">
          <div>
            <h2>${escapeHtml(seriesLabel(series))}</h2>
            <p class="panel-caption">${escapeHtml(seriesCountLabel(series))} | ${escapeHtml(txt({ ko: `${items.length}명`, en: `${items.length} people` }))}</p>
          </div>
        </div>
        <div class="people-grid">
          ${items.map(personCard).join('')}
        </div>
      </section>
    `;
  }).join('');
}

setupPageI18n('market-wizards-people', () => {
  renderSummary();
  renderSections();
});
renderSummary();
renderSections();
