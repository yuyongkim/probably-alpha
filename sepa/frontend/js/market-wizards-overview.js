import { compareAxis } from './market-wizards-data.js?v=1775488167';
import { getFullProfile } from './trader-tabs.js?v=1775488167';
import { setupPageI18n, txt } from './i18n.js?v=1775488167';

const state = {
  presetCatalog: new Map(),
};

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


function getPresetMeta(profile) {
  const presetId = profile?.presetBinding?.presetId || '';
  return presetId ? state.presetCatalog.get(presetId) || null : null;
}

function runtimeConditionsSection(profile) {
  const presetMeta = getPresetMeta(profile);
  const formula = profile?.preset?.formula || '';
  const runtimeConditions = presetMeta?.runtime_conditions || [];
  if (!formula && !runtimeConditions.length) return '';
  return `
    <div class="wizard-card__section">
      <h3>${escapeHtml(txt({ ko: 'Condition Formula', en: 'Condition Formula' }))}</h3>
      ${formula ? `<div class="logic-formula" style="margin-bottom:10px">${escapeHtml(formula)}</div>` : ''}
      ${runtimeConditions.length ? `
        <ul class="wizard-list">
          ${runtimeConditions.map((condition) => `<li><code>${escapeHtml(condition)}</code></li>`).join('')}
        </ul>
      ` : ''}
    </div>
  `;
}

async function loadPresetCatalog() {
  try {
    const resp = await fetch('/api/backtest/presets');
    const data = await resp.json();
    state.presetCatalog = new Map((data.items || []).map((item) => [item.id, item]));
  } catch (error) {
    console.warn('Failed to load preset catalog:', error);
    state.presetCatalog = new Map();
  }
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

  const profiles = [
    'ed-seykota',
    'stanley-druckenmiller',
    'paul-tudor-jones',
    'william-oneil',
    'nicolas-darvas',
    'mark-minervini',
  ].map((id) => getFullProfile(id)).filter(Boolean);

  cards.innerHTML = profiles.map((profile) => `
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
      ${runtimeConditionsSection(profile)}
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
        ${profiles.map((profile) => `
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
loadPresetCatalog().finally(() => {
  renderOverview();
});
