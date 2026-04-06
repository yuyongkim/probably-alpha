import { compareAxis, traderProfiles } from './market-wizards-data.js?v=1775482261';
import { setupPageI18n, txt } from './i18n.js?v=1775482261';

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function subtitle(profile) {
  if (!profile.englishName || profile.englishName === profile.name) return '';
  return `<p class="panel-caption">${escapeHtml(profile.englishName)}</p>`;
}

function axisLabel(axis) {
  const labels = {
    focus: { ko: '핵심 초점', en: 'Primary focus' },
    timeframe: { ko: '보는 기간', en: 'Typical holding period' },
    trigger: { ko: '진입 트리거', en: 'Entry trigger' },
    risk: { ko: '리스크 스타일', en: 'Risk style' },
  };
  return txt(labels[axis.key] || axis.label);
}

function renderOverview() {
  const cards = document.getElementById('wizardCards');
  const compare = document.getElementById('wizardCompare');
  if (!cards || !compare) return;

  cards.innerHTML = traderProfiles.map((profile) => `
    <article class="wizard-card">
      <div class="wizard-card__top">
        <div>
          <p class="eyebrow">${escapeHtml(profile.style)}</p>
          <h2>${escapeHtml(profile.name)}</h2>
          ${subtitle(profile)}
        </div>
      </div>
      <div class="wizard-card__section">
        <h3>${escapeHtml(txt({ ko: '핵심 철학', en: 'Core Philosophy' }))}</h3>
        <div class="definition-stack">
          ${profile.philosophy.map((line) => `<div class="definition-card"><p>${escapeHtml(line)}</p></div>`).join('')}
        </div>
      </div>
      <div class="wizard-card__section">
        <h3>${escapeHtml(txt({ ko: '체크리스트', en: 'Checklist' }))}</h3>
        <ul class="wizard-list">
          ${profile.checkpoints.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
      <div class="wizard-card__section">
        <h3>${escapeHtml(txt({ ko: 'SEPA 연결 지점', en: 'SEPA Mapping' }))}</h3>
        <ul class="wizard-list">
          ${profile.projectHooks.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}
        </ul>
      </div>
      <div class="wizard-card__actions">
        <a class="nav-link nav-link--button" href="./market-wizards-korea.html#${escapeHtml(profile.id)}">${escapeHtml(txt({ ko: '국내 적용 보기', en: 'Open Korea Lab' }))}</a>
      </div>
    </article>
  `).join('');

  compare.innerHTML = `
    <table class="compare-table">
      <thead>
        <tr>
          <th>${escapeHtml(txt({ ko: '트레이더', en: 'Trader' }))}</th>
          ${compareAxis.map((axis) => `<th>${escapeHtml(axisLabel(axis))}</th>`).join('')}
        </tr>
      </thead>
      <tbody>
        ${traderProfiles.map((profile) => `
          <tr>
            <td>
              <div class="company-cell">
                <strong>${escapeHtml(profile.name)}</strong>
                <small>${escapeHtml(profile.style)}</small>
              </div>
            </td>
            ${compareAxis.map((axis) => `<td>${escapeHtml(profile.fit[axis.key])}</td>`).join('')}
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

setupPageI18n('market-wizards-overview', renderOverview);
renderOverview();
