    const $ = (id) => document.getElementById(id);

    function apiBase() {
      return $('apiBase').value.trim() || window.location.origin;
    }

    function fmtNumber(value) {
      if (value === null || value === undefined || value === '') return '-';
      const num = Number(value);
      return Number.isFinite(num) ? num.toLocaleString('ko-KR') : String(value);
    }

    function toneClass(value) {
      const num = Number(value);
      if (!Number.isFinite(num)) return 'muted';
      if (num >= 80) return 'good';
      if (num >= 55) return 'warn';
      return 'bad';
    }

    async function fetchJSON(url, options = {}) {
      const response = await fetch(url, options);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || `HTTP ${response.status}`);
      }
      return payload;
    }

    function renderHealth(payload) {
      const box = $('healthBox');
      if (!payload) {
        box.innerHTML = '<small>대기 중</small><strong>-</strong>';
        return;
      }
      const status = payload.auth_ok ? '인증 가능' : '인증 미확인';
      box.innerHTML = `
        <small>${payload.env || '-'}</small>
        <strong class="${payload.auth_ok ? 'good' : 'warn'}">${status}</strong>
        <div class="note">order_enabled: ${payload.order_enabled ? 'Y' : 'N'}</div>
      `;
    }

    function renderAnalysis(payload) {
      const levels = payload.support_resistance || {};
      const metrics = payload.metrics || {};
      const trade = payload.trade_levels || {};
      const quote = payload.quote || {};
      $('analysisBox').innerHTML = `
        <div class="metrics">
          <div class="metric">
            <small>ETF</small>
            <strong>${payload.name || payload.symbol || '-'}</strong>
            <div class="note mono">${payload.symbol || '-'}</div>
          </div>
          <div class="metric">
            <small>현재가</small>
            <strong>${fmtNumber(quote.current_price)}</strong>
            <div class="note">등락률 ${fmtNumber(quote.change_pct)}%</div>
          </div>
          <div class="metric">
            <small>추세 상태</small>
            <strong>${metrics.trend_state || '-'}</strong>
            <div class="note">20D ${fmtNumber(metrics.return_20d_pct)}% / 60D ${fmtNumber(metrics.return_60d_pct)}%</div>
          </div>
          <div class="metric">
            <small>20일 변동성</small>
            <strong>${fmtNumber(metrics.volatility_20d_pct)}%</strong>
            <div class="note">SMA20 ${fmtNumber(metrics.sma20)} / SMA60 ${fmtNumber(metrics.sma60)}</div>
          </div>
        </div>
        <div class="grid-2">
          <div class="card">
            <div class="card-top">
              <div>
                <strong>가장 가까운 지지선</strong>
                <div class="note">${levels.nearest_support ? `${fmtNumber(levels.nearest_support.price)}원` : '없음'}</div>
              </div>
            </div>
            <div class="note">거리 ${fmtNumber(levels.nearest_support?.distance_pct)}% / 터치 ${fmtNumber(levels.nearest_support?.touches)}회</div>
            <div class="pill-row">${(levels.supports || []).map((item) => `<span class="pill">${fmtNumber(item.price)}원</span>`).join('')}</div>
          </div>
          <div class="card">
            <div class="card-top">
              <div>
                <strong>가장 가까운 저항선</strong>
                <div class="note">${levels.nearest_resistance ? `${fmtNumber(levels.nearest_resistance.price)}원` : '없음'}</div>
              </div>
            </div>
            <div class="note">거리 ${fmtNumber(levels.nearest_resistance?.distance_pct)}% / 터치 ${fmtNumber(levels.nearest_resistance?.touches)}회</div>
            <div class="pill-row">${(levels.resistances || []).map((item) => `<span class="pill">${fmtNumber(item.price)}원</span>`).join('')}</div>
          </div>
        </div>
        <div class="card">
          <strong>휴리스틱 트레이드 레벨</strong>
          <div class="metrics">
            <div class="metric"><small>돌파 진입</small><strong>${fmtNumber(trade.breakout_entry)}</strong></div>
            <div class="metric"><small>눌림 진입</small><strong>${fmtNumber(trade.pullback_entry)}</strong></div>
            <div class="metric"><small>손절</small><strong>${fmtNumber(trade.stop_price)}</strong></div>
            <div class="metric"><small>목표</small><strong>${fmtNumber(trade.target_price)}</strong></div>
          </div>
          <div class="note">예상 R/R ${fmtNumber(trade.rr_ratio)} / 차트 데이터 ${fmtNumber(payload.chart?.length)}일</div>
          <div class="note">${payload.disclaimer || ''}</div>
        </div>
      `;
    }

    function renderRecommendations(payload) {
      const items = payload.items || [];
      const failures = payload.failures || [];
      $('recommendationBox').innerHTML = `
        ${items.map((item) => `
          <div class="card">
            <div class="card-top">
              <div>
                <strong>${item.name || item.symbol}</strong>
                <div class="note mono">${item.symbol}</div>
              </div>
              <div class="score">
                <small>${item.risk_profile}</small>
                <strong class="${toneClass(item.score)}">${fmtNumber(item.score)}</strong>
              </div>
            </div>
            <div class="pill-row">
              <span class="pill">현재가 ${fmtNumber(item.quote?.current_price)}</span>
              <span class="pill">20D ${fmtNumber(item.metrics?.return_20d_pct)}%</span>
              <span class="pill">60D ${fmtNumber(item.metrics?.return_60d_pct)}%</span>
              <span class="pill">변동성 ${fmtNumber(item.metrics?.volatility_20d_pct)}%</span>
            </div>
            <div class="note">${(item.reasons || []).join(' / ')}</div>
          </div>
        `).join('')}
        ${failures.length ? `<div class="card"><strong>조회 실패</strong><div class="note">${failures.map((item) => `${item.symbol}: ${item.message || item.error}`).join('<br/>')}</div></div>` : ''}
        <div class="note">${payload.disclaimer || ''}</div>
      `;
    }

    async function loadHealth() {
      $('healthBox').innerHTML = '<small>조회 중</small><strong>...</strong>';
      try {
        const payload = await fetchJSON(`${apiBase()}/api/kis/health`);
        renderHealth(payload);
      } catch (error) {
        $('healthBox').innerHTML = `<small>오류</small><strong class="bad">${String(error.message || error)}</strong>`;
      }
    }

    async function analyzeSymbol() {
      const symbol = $('symbolInput').value.trim();
      if (!symbol) return;
      $('analysisBox').innerHTML = '<div class="note">분석 조회 중...</div>';
      try {
        const payload = await fetchJSON(`${apiBase()}/api/etf/${encodeURIComponent(symbol)}/analysis`);
        renderAnalysis(payload);
      } catch (error) {
        $('analysisBox').innerHTML = `<div class="card"><strong>분석 실패</strong><div class="note">${String(error.message || error)}</div></div>`;
      }
    }

    async function recommendSymbols() {
      const symbols = $('symbolsTextarea').value
        .split(/[\n, ]+/)
        .map((item) => item.trim())
        .filter(Boolean);
      if (!symbols.length) return;
      $('recommendationBox').innerHTML = '<div class="note">추천 계산 중...</div>';
      try {
        const payload = await fetchJSON(`${apiBase()}/api/etf/recommendations/profile`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            symbols,
            risk_profile: $('riskProfile').value,
          }),
        });
        renderRecommendations(payload);
      } catch (error) {
        $('recommendationBox').innerHTML = `<div class="card"><strong>추천 실패</strong><div class="note">${String(error.message || error)}</div></div>`;
      }
    }

    $('btnHealth').addEventListener('click', loadHealth);
    $('btnAnalyze').addEventListener('click', analyzeSymbol);
    $('btnRecommend').addEventListener('click', recommendSymbols);
    $('btnSample').addEventListener('click', () => {
      $('symbolsTextarea').value = '069500\\n360750\\n114800\\n102110';
      $('symbolInput').value = '069500';
    });

    loadHealth();
