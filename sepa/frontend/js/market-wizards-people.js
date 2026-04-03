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

// Preset mapping: person id -> backtest preset id
const PERSON_PRESET = {
  'mark-minervini': 'minervini',
  'william-oneil': 'oneil',
  'david-ryan': 'oneil',
  'richard-dennis': 'dennis',
  'ed-seykota': 'seykota',
  'larry-hite': 'hite',
  'paul-tudor-jones': 'jones',
  'richard-driehaus': 'driehaus',
  'marty-schwartz': 'schwartz',
  'linda-raschke': 'raschke',
  'mark-weinstein': 'weinstein',
};

function personCard(person) {
  const presetId = PERSON_PRESET[person.id] || '';
  const hasPreset = !!presetId;
  return `
    <article class="person-card" data-person-id="${escapeHtml(person.id)}">
      <div class="person-card__head">
        <div>
          <p class="eyebrow">${escapeHtml(person.bucket)}</p>
          <h3>${escapeHtml(person.name)}</h3>
        </div>
        ${hasPreset ? `<span style="font-size:10px;background:var(--accent);color:#fff;padding:2px 8px;border-radius:10px">전략 프리셋</span>` : ''}
      </div>
      <p class="person-card__brief">${escapeHtml(person.brief)}</p>
      <div class="person-meta">
        ${person.keywords.map((keyword) => `<span class="wizard-chip">${escapeHtml(keyword)}</span>`).join('')}
      </div>
      <div class="person-card__actions" style="display:flex;gap:8px;flex-wrap:wrap">
        ${person.relatedProfileId
          ? `<a class="ghost-link" href="./market-wizards-korea.html#${escapeHtml(person.relatedProfileId)}">${escapeHtml(txt({ ko: '프리셋 매핑', en: 'Preset mapping' }))}</a>`
          : ''}
        ${hasPreset
          ? `<button class="ghost-link btn-screen-trader" data-preset="${escapeHtml(presetId)}" style="cursor:pointer;border:1px solid var(--accent);background:none;color:var(--accent);padding:4px 10px;border-radius:4px;font-size:12px">${escapeHtml(txt({ ko: '오늘의 매수 후보', en: "Today's picks" }))}</button>`
          : ''}
        ${hasPreset
          ? `<a class="ghost-link" href="./backtest.html" style="font-size:12px">${escapeHtml(txt({ ko: '백테스트', en: 'Backtest' }))}</a>`
          : ''}
      </div>
      <div class="person-card__screen-result" id="screen-${escapeHtml(person.id)}" style="display:none;margin-top:10px;padding:10px;background:rgba(255,255,255,.03);border-radius:6px;font-size:13px"></div>
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

function getApiBase() {
  const el = document.getElementById('apiBase');
  return el ? el.value.replace(/\/+$/, '') : 'http://127.0.0.1:8000';
}

async function screenTrader(presetId, personId) {
  const el = document.getElementById(`screen-${personId}`);
  if (!el) return;
  el.style.display = '';
  el.innerHTML = `<p style="color:var(--accent)">${txt({ ko: '스크리닝 중...', en: 'Screening...' })}</p>`;

  try {
    const resp = await fetch(`${getApiBase()}/api/screen/trader?preset=${presetId}&limit=5`);
    const data = await resp.json();
    const items = data.items || [];

    if (!items.length) {
      el.innerHTML = `<p style="color:var(--muted)">${txt({ ko: '조건에 맞는 종목 없음', en: 'No stocks match' })}</p>`;
      return;
    }

    el.innerHTML = `
      <p style="margin-bottom:6px"><strong>${escapeHtml(data.trader || presetId)}</strong> — ${data.passed || 0}/${data.screened_symbols || 0} ${txt({ ko: '통과', en: 'passed' })}</p>
      <table style="width:100%;font-size:12px">
        <tr style="color:var(--muted)"><th>#</th><th>${txt({ ko: '종목', en: 'Stock' })}</th><th>TT</th><th>RS</th><th>${txt({ ko: '점수', en: 'Score' })}</th></tr>
        ${items.map((s, i) => `
          <tr>
            <td>${i + 1}</td>
            <td>${escapeHtml(s.name || s.symbol)}</td>
            <td>${s.tt_passed}/8</td>
            <td>${s.rs_percentile?.toFixed(0) || '-'}%</td>
            <td><strong>${s.score?.toFixed(1) || '-'}</strong></td>
          </tr>
        `).join('')}
      </table>
    `;
  } catch (e) {
    el.innerHTML = `<p style="color:#ff6b6b">${txt({ ko: '스크리닝 실패', en: 'Failed' })}: ${escapeHtml(String(e))}</p>`;
  }
}

function bindScreenButtons() {
  document.querySelectorAll('.btn-screen-trader').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const presetId = btn.dataset.preset;
      const card = btn.closest('.person-card');
      const personId = card?.dataset.personId;
      if (presetId && personId) screenTrader(presetId, personId);
    });
  });
}

setupPageI18n('market-wizards-people', () => {
  renderSummary();
  renderSections();
  bindScreenButtons();
});
renderSummary();
renderSections();
bindScreenButtons();
