(function () {
  const byId = (id) => document.getElementById(id);

  function apiBase() {
    const input = byId('workspaceApiBase');
    return (input && input.value.trim()) || window.location.origin;
  }

  function fmtNumber(value, locale = 'ko-KR') {
    if (value === null || value === undefined || value === '') return '-';
    const num = Number(value);
    return Number.isFinite(num) ? num.toLocaleString(locale) : String(value);
  }

  async function fetchJSON(url, options) {
    const response = await fetch(url, options);
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(payload.detail || payload.message || ('HTTP ' + response.status));
    }
    return payload;
  }

  function chip(label, tone) {
    const toneClass = tone ? ` is-${tone}` : '';
    return `<span class="workspace-chip${toneClass}">${label}</span>`;
  }

  function renderWorkspaceStats(health, catalog) {
    const stats = byId('workspaceStats');
    if (!stats) return;
    const summary = catalog && catalog.summary ? catalog.summary : {};
    stats.innerHTML = `
      <div class="workspace-stat">
        <span class="workspace-inline-note">KIS 인증</span>
        <strong>${health && health.auth_ok ? 'OK' : 'CHECK'}</strong>
      </div>
      <div class="workspace-stat">
        <span class="workspace-inline-note">주문 가능 상품군</span>
        <strong>${fmtNumber(summary.kis_orderable_count)}</strong>
      </div>
      <div class="workspace-stat">
        <span class="workspace-inline-note">프로젝트 정보 조회 연결</span>
        <strong>${fmtNumber(summary.project_info_count)}</strong>
      </div>
      <div class="workspace-stat">
        <span class="workspace-inline-note">프로젝트 백테스트 연결</span>
        <strong>${fmtNumber(summary.project_backtestable_count)}</strong>
      </div>
    `;
  }

  function renderCatalog(payload) {
    const root = byId('workspaceCatalogList');
    if (!root) return;
    root.innerHTML = (payload.items || []).map((item) => `
      <article class="workspace-result-card">
        <strong>${item.label_ko}</strong>
        <p>${item.label_en} / ${item.market} / ${item.asset_class}</p>
        <div class="workspace-chip-row">
          ${chip(item.kis_quote_support ? 'KIS 시세' : '시세 미확인', item.kis_quote_support ? 'good' : 'warn')}
          ${chip(item.kis_order_support ? 'KIS 주문' : '주문 미확인', item.kis_order_support ? 'good' : 'warn')}
          ${chip(item.project_info_support ? '프로젝트 정보조회' : '프로젝트 미연결', item.project_info_support ? 'good' : 'warn')}
          ${chip(item.project_backtest_support ? '프로젝트 백테스트' : '백테스트 미연결', item.project_backtest_support ? 'good' : 'warn')}
        </div>
        <p>예시 폴더: ${(item.examples_folders || []).join(', ')}</p>
        <p>${item.notes || ''}</p>
      </article>
    `).join('');
  }

  function renderEtfAnalysis(payload) {
    const root = byId('workspaceEtfResult');
    if (!root) return;
    const quote = payload.quote || {};
    const metrics = payload.metrics || {};
    const levels = payload.support_resistance || {};
    const trade = payload.trade_levels || {};
    root.innerHTML = `
      <article class="workspace-result-card">
        <strong>${payload.name || payload.symbol}</strong>
        <p>${payload.symbol || '-'}</p>
        <div class="workspace-chip-row">
          ${chip('현재가 ' + fmtNumber(quote.current_price))}
          ${chip('20D ' + fmtNumber(metrics.return_20d_pct) + '%')}
          ${chip('60D ' + fmtNumber(metrics.return_60d_pct) + '%')}
          ${chip('추세 ' + (metrics.trend_state || '-'), metrics.trend_state === 'strong_uptrend' ? 'good' : 'warn')}
        </div>
        <p>가장 가까운 지지선 ${fmtNumber(levels.nearest_support && levels.nearest_support.price)} / 저항선 ${fmtNumber(levels.nearest_resistance && levels.nearest_resistance.price)}</p>
        <p>돌파 진입 ${fmtNumber(trade.breakout_entry)} / 눌림 진입 ${fmtNumber(trade.pullback_entry)} / 손절 ${fmtNumber(trade.stop_price)}</p>
      </article>
    `;
  }

  function renderEtfRecommendations(payload) {
    const root = byId('workspaceEtfRecommendation');
    if (!root) return;
    root.innerHTML = (payload.items || []).slice(0, 5).map((item) => `
      <article class="workspace-result-card">
        <strong>${item.name || item.symbol}</strong>
        <p>${item.symbol} / score ${fmtNumber(item.score)}</p>
        <div class="workspace-chip-row">
          ${chip(item.risk_profile || '-')}
          ${chip('20D ' + fmtNumber(item.metrics && item.metrics.return_20d_pct) + '%')}
          ${chip('변동성 ' + fmtNumber(item.metrics && item.metrics.volatility_20d_pct) + '%')}
        </div>
        <p>${(item.reasons || []).join(' / ')}</p>
      </article>
    `).join('') || '<div class="workspace-inline-note">추천 결과가 없습니다.</div>';
  }

  function renderOverseas(payload) {
    const root = byId('workspaceOverseasResult');
    if (!root) return;
    const quote = payload.quote || {};
    const info = payload.info || {};
    const detail = payload.detail || {};
    const metrics = payload.metrics || {};
    const levels = payload.support_resistance || {};
    root.innerHTML = `
      <article class="workspace-result-card">
        <strong>${payload.name || payload.symbol}</strong>
        <p>${payload.symbol} / ${payload.exchange_code || '-'} / ${info.country_name || '-'}</p>
        <div class="workspace-chip-row">
          ${chip('현재가 ' + fmtNumber(quote.last, 'en-US'))}
          ${chip('통화 ' + (info.currency || detail.currency || '-'))}
          ${chip('PER ' + fmtNumber(detail.per, 'en-US'))}
          ${chip('추세 ' + (metrics.trend_state || '-'), metrics.trend_state === 'strong_uptrend' || metrics.trend_state === 'uptrend' ? 'good' : 'warn')}
        </div>
        <p>시장 ${info.market_name || '-'} / 20D ${fmtNumber(metrics.return_20d_pct, 'en-US')}% / 60D ${fmtNumber(metrics.return_60d_pct, 'en-US')}%</p>
        <p>가장 가까운 지지선 ${fmtNumber(levels.nearest_support && levels.nearest_support.price, 'en-US')} / 저항선 ${fmtNumber(levels.nearest_resistance && levels.nearest_resistance.price, 'en-US')}</p>
      </article>
    `;
  }

  async function loadHealthAndCatalog() {
    renderWorkspaceStats(null, null);
    const [health, catalog] = await Promise.all([
      fetchJSON(`${apiBase()}/api/kis/health`),
      fetchJSON(`${apiBase()}/api/kis/catalog`),
    ]);
    renderWorkspaceStats(health, catalog);
    renderCatalog(catalog);
  }

  async function loadEtfAnalysis() {
    const symbol = (byId('workspaceEtfSymbol') && byId('workspaceEtfSymbol').value.trim()) || '069500';
    const payload = await fetchJSON(`${apiBase()}/api/etf/${encodeURIComponent(symbol)}/analysis`);
    renderEtfAnalysis(payload);
  }

  async function loadEtfRecommendations() {
    const riskProfile = (byId('workspaceEtfRisk') && byId('workspaceEtfRisk').value) || 'balanced';
    const symbolsRaw = (byId('workspaceEtfSymbols') && byId('workspaceEtfSymbols').value) || '';
    const symbols = symbolsRaw.split(/[\n, ]+/).map((item) => item.trim()).filter(Boolean);
    const payload = await fetchJSON(`${apiBase()}/api/etf/recommendations/profile`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({symbols, risk_profile: riskProfile}),
    });
    renderEtfRecommendations(payload);
  }

  async function loadOverseasAnalysis() {
    const symbol = (byId('workspaceOverseasSymbol') && byId('workspaceOverseasSymbol').value.trim()) || 'AAPL';
    const exchange = (byId('workspaceOverseasExchange') && byId('workspaceOverseasExchange').value.trim()) || 'NAS';
    const productType = (byId('workspaceOverseasProductType') && byId('workspaceOverseasProductType').value.trim()) || '512';
    const payload = await fetchJSON(`${apiBase()}/api/overseas/stock/${encodeURIComponent(symbol)}/analysis?exchange_code=${encodeURIComponent(exchange)}&product_type_code=${encodeURIComponent(productType)}`);
    renderOverseas(payload);
  }

  function bind() {
    const healthButton = byId('workspaceRefreshHealth');
    const catalogButton = byId('workspaceRefreshCatalog');
    const etfAnalyzeButton = byId('workspaceEtfAnalyze');
    const etfRecommendButton = byId('workspaceEtfRecommend');
    const overseasAnalyzeButton = byId('workspaceOverseasAnalyze');

    if (healthButton) {
      healthButton.addEventListener('click', function () {
        loadHealthAndCatalog().catch((error) => {
          const root = byId('workspaceCatalogList');
          if (root) root.innerHTML = `<div class="workspace-inline-note">KIS 카탈로그 조회 실패: ${String(error.message || error)}</div>`;
        });
      });
    }
    if (catalogButton) {
      catalogButton.addEventListener('click', function () {
        loadHealthAndCatalog().catch((error) => {
          const root = byId('workspaceCatalogList');
          if (root) root.innerHTML = `<div class="workspace-inline-note">KIS 카탈로그 조회 실패: ${String(error.message || error)}</div>`;
        });
      });
    }
    if (etfAnalyzeButton) {
      etfAnalyzeButton.addEventListener('click', function () {
        loadEtfAnalysis().catch((error) => {
          const root = byId('workspaceEtfResult');
          if (root) root.innerHTML = `<div class="workspace-inline-note">ETF 분석 실패: ${String(error.message || error)}</div>`;
        });
      });
    }
    if (etfRecommendButton) {
      etfRecommendButton.addEventListener('click', function () {
        loadEtfRecommendations().catch((error) => {
          const root = byId('workspaceEtfRecommendation');
          if (root) root.innerHTML = `<div class="workspace-inline-note">ETF 추천 실패: ${String(error.message || error)}</div>`;
        });
      });
    }
    if (overseasAnalyzeButton) {
      overseasAnalyzeButton.addEventListener('click', function () {
        loadOverseasAnalysis().catch((error) => {
          const root = byId('workspaceOverseasResult');
          if (root) root.innerHTML = `<div class="workspace-inline-note">해외주식 분석 실패: ${String(error.message || error)}</div>`;
        });
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      bind();
      loadHealthAndCatalog().catch(() => {});
      loadEtfAnalysis().catch(() => {});
      loadEtfRecommendations().catch(() => {});
      loadOverseasAnalysis().catch(() => {});
    });
  } else {
    bind();
    loadHealthAndCatalog().catch(() => {});
    loadEtfAnalysis().catch(() => {});
    loadEtfRecommendations().catch(() => {});
    loadOverseasAnalysis().catch(() => {});
  }
})();
