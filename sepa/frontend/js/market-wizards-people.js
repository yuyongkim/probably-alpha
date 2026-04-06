import { marketWizardPeople, peopleSeries } from './market-wizards-people-data.js?v=1775482261';
import { traderProfiles } from './market-wizards-data.js?v=1775482261';
import { setupPageI18n, txt } from './i18n.js?v=1775482261';

function _getProfile(personId) {
  return traderProfiles.find((p) => p.id === personId) || null;
}

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
  'linda-bradford-raschke': 'raschke',
  'mark-weinstein': 'weinstein',
  'joel-greenblatt': 'greenblatt',
  'ray-dalio': 'dalio',
  'stanley-druckenmiller': 'druckenmiller',
  'bruce-kovner': 'kovner',
  'jesse-livermore': 'livermore',
  'nicolas-darvas': 'darvas',
  'steve-cohen': 'cohen',
  'michael-steinhardt': 'steinhardt',
  'edward-thorp': 'thorp',
  'peter-brandt': 'brandt',
  'ahmet-okumus': 'okumus',
  'dana-galante': 'galante',
  'jason-shapiro': 'shapiro',
  'gary-bielfeldt': 'bielfeldt',
  'gil-blake': 'blake',
  // Cluster mappings (similar style → nearest preset)
  'michael-marcus': 'livermore',
  'tom-basso': 'seykota',
  'william-eckhardt': 'dennis',
  'al-weiss': 'brandt',
  'victor-sperandeo': 'kovner',
  'jim-rogers': 'kovner',
  'randy-mckay': 'schwartz',
  'bill-lipschutz': 'kovner',
  'stuart-walton': 'darvas',
  'michael-masters': 'cohen',
  'mark-d-cook': 'schwartz',
  'buddy-fletcher': 'greenblatt',
  'steve-watson': 'cohen',
  'colm-oshea': 'kovner',
  'larry-benedict': 'schwartz',
  'scott-ramsey': 'brandt',
  'jaffray-woodriff': 'thorp',
  'jamie-mai': 'shapiro',
  'michael-platt': 'hite',
  'steve-clark': 'weinstein',
  'martin-taylor': 'kovner',
  'tom-claugus': 'greenblatt',
  'joe-vidich': 'greenblatt',
  'kevin-daly': 'greenblatt',
  'jimmy-balodimas': 'shapiro',
  'john-netto': 'schwartz',
  'chris-camillo': 'darvas',
  'marsten-parker': 'seykota',
  'michael-kean': 'dalio',
  'pavel-krejci': 'hite',
};

function personCard(person) {
  const presetId = PERSON_PRESET[person.id] || '';
  const hasPreset = !!presetId;
  // Try to get detailed profile from market-wizards-data
  const profile = _getProfile(person.id);
  const hasProfile = profile && profile.philosophy && profile.philosophy.length > 0;

  return `
    <article class="person-card" data-person-id="${escapeHtml(person.id)}" style="cursor:pointer">
      <div class="person-card__head">
        <div>
          <p class="eyebrow">${escapeHtml(person.bucket)}</p>
          <h3>${escapeHtml(person.name)}</h3>
        </div>
        <div style="display:flex;gap:4px">
          ${hasPreset ? '<span style="font-size:10px;background:var(--accent);color:#fff;padding:2px 8px;border-radius:10px">전략</span>' : ''}
          ${hasProfile ? '<span style="font-size:10px;background:#7c3aed;color:#fff;padding:2px 8px;border-radius:10px">프로필</span>' : ''}
        </div>
      </div>
      <p class="person-card__brief">${escapeHtml(person.brief)}</p>
      <div class="person-meta">
        ${person.keywords.map((keyword) => `<span class="wizard-chip">${escapeHtml(keyword)}</span>`).join('')}
      </div>

      <!-- Expandable detail section -->
      <div class="person-card__detail" id="detail-${escapeHtml(person.id)}" style="display:none;margin-top:12px;padding-top:12px;border-top:1px solid var(--border)">
        ${hasProfile ? `
          <div style="margin-bottom:10px">
            ${profile.fit ? `
              <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">
                <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#2563eb;color:#fff">${escapeHtml(profile.style || '')}</span>
                <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#7c3aed;color:#fff">${escapeHtml(profile.fit.focus || '')}</span>
                <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#0d9488;color:#fff">${escapeHtml(profile.fit.timeframe || '')}</span>
                <span style="font-size:11px;padding:3px 8px;border-radius:4px;background:#d97706;color:#fff">${escapeHtml(profile.fit.trigger || '')}</span>
              </div>` : ''}
            <h4 style="color:var(--accent);font-size:13px;margin:8px 0 4px">${txt({ ko: '투자 철학', en: 'Philosophy' })}</h4>
            ${profile.philosophy.map((p) => `<p style="font-size:13px;color:var(--muted);margin:2px 0;line-height:1.6">${escapeHtml(p)}</p>`).join('')}
          </div>
          ${profile.checkpoints && profile.checkpoints.length ? `
            <h4 style="color:var(--accent);font-size:13px;margin:10px 0 4px">${txt({ ko: '체크포인트', en: 'Checkpoints' })}</h4>
            <ul style="font-size:13px;color:var(--muted);padding-left:18px;line-height:1.8;margin:0">
              ${profile.checkpoints.map((c) => `<li>${escapeHtml(c)}</li>`).join('')}
            </ul>` : ''}
          ${profile.koreaPlaybook && profile.koreaPlaybook.length ? `
            <h4 style="color:var(--accent);font-size:13px;margin:10px 0 4px">${txt({ ko: '한국 시장 적용', en: 'Korea Playbook' })}</h4>
            <ul style="font-size:13px;color:var(--muted);padding-left:18px;line-height:1.8;margin:0">
              ${profile.koreaPlaybook.map((c) => `<li>${escapeHtml(c)}</li>`).join('')}
            </ul>` : ''}
        ` : `<p style="font-size:13px;color:var(--muted)">${escapeHtml(person.brief)}</p>`}
      </div>

      <div class="person-card__actions" style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
        <button class="ghost-link btn-toggle-detail" data-person="${escapeHtml(person.id)}" style="cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);padding:4px 10px;border-radius:4px;font-size:12px">${txt({ ko: '상세보기', en: 'Details' })}</button>
        ${hasPreset
          ? `<button class="ghost-link btn-screen-trader" data-preset="${escapeHtml(presetId)}" style="cursor:pointer;border:1px solid var(--accent);background:none;color:var(--accent);padding:4px 10px;border-radius:4px;font-size:12px">${escapeHtml(txt({ ko: '매수 후보', en: 'Picks' }))}</button>`
          : ''}
        ${hasPreset
          ? `<a class="ghost-link" href="./strategy-follow.html" style="font-size:12px;padding:4px 10px">${escapeHtml(txt({ ko: '전략 따라하기', en: 'Follow' }))}</a>`
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

function bindDetailToggle() {
  document.querySelectorAll('.btn-toggle-detail').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const personId = btn.dataset.person;
      const detail = document.getElementById(`detail-${personId}`);
      if (!detail) return;
      const showing = detail.style.display !== 'none';
      detail.style.display = showing ? 'none' : '';
      btn.textContent = showing ? txt({ ko: '상세보기', en: 'Details' }) : txt({ ko: '접기', en: 'Collapse' });
    });
  });
}

setupPageI18n('market-wizards-people', () => {
  renderSummary();
  renderSections();
  bindScreenButtons();
  bindDetailToggle();
});
renderSummary();
renderSections();
bindScreenButtons();
bindDetailToggle();
