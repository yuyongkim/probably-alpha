    const $ = (id) => document.getElementById(id);

    function apiBase() {
      return $('apiBase').value.trim() || window.location.origin;
    }

    function fmtNumber(value) {
      if (value === null || value === undefined || value === '') return '-';
      const num = Number(value);
      return Number.isFinite(num) ? num.toLocaleString('en-US') : String(value);
    }

    async function fetchJSON(url) {
      const response = await fetch(url);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || payload.message || `HTTP ${response.status}`);
      return payload;
    }

    function renderAnalysis(payload) {
      const quote = payload.quote || {};
      const detail = payload.detail || {};
      const info = payload.info || {};
      const metrics = payload.metrics || {};
      const levels = payload.support_resistance || {};
      const trade = payload.trade_levels || {};
      $('analysisBox').innerHTML = `
        <div class="metrics">
          <div class="metric">
            <small class="note">종목</small>
            <strong>${payload.name || payload.symbol}</strong>
            <div class="note mono">${payload.symbol} / ${payload.exchange_code}</div>
          </div>
          <div class="metric">
            <small class="note">현재가</small>
            <strong>${fmtNumber(quote.last)}</strong>
            <div class="note">등락 ${fmtNumber(quote.change)} / ${fmtNumber(quote.change_pct)}%</div>
          </div>
          <div class="metric">
            <small class="note">통화 / 시장</small>
            <strong>${info.currency || detail.currency || '-'}</strong>
            <div class="note">${info.country_name || '-'} / ${info.market_name || '-'}</div>
          </div>
          <div class="metric">
            <small class="note">추세 상태</small>
            <strong>${metrics.trend_state || '-'}</strong>
            <div class="note">20D ${fmtNumber(metrics.return_20d_pct)}% / 60D ${fmtNumber(metrics.return_60d_pct)}%</div>
          </div>
        </div>
        <div class="card">
          <strong>${payload.name || payload.symbol}</strong>
          <div class="pill-row">
            <span class="pill">PER ${fmtNumber(detail.per)}</span>
            <span class="pill">PBR ${fmtNumber(detail.pbr)}</span>
            <span class="pill">EPS ${fmtNumber(detail.eps)}</span>
            <span class="pill">52W High ${fmtNumber(detail.high_52w)}</span>
            <span class="pill">52W Low ${fmtNumber(detail.low_52w)}</span>
            <span class="pill">차트 ${fmtNumber((payload.chart || []).length)}일</span>
          </div>
          <div class="note">가장 가까운 지지선 ${fmtNumber(levels.nearest_support?.price)} / 저항선 ${fmtNumber(levels.nearest_resistance?.price)}</div>
          <div class="note">돌파 진입 ${fmtNumber(trade.breakout_entry)} / 눌림 진입 ${fmtNumber(trade.pullback_entry)} / 손절 ${fmtNumber(trade.stop_price)}</div>
          <div class="note">${payload.disclaimer || ''}</div>
        </div>
      `;
    }

    async function analyze() {
      $('analysisBox').innerHTML = '<div class="note">해외주식 분석 조회 중...</div>';
      try {
        const symbol = encodeURIComponent($('symbolInput').value.trim());
        const exchange = encodeURIComponent($('exchangeInput').value.trim() || 'NAS');
        const productType = encodeURIComponent($('productTypeInput').value.trim() || '512');
        const payload = await fetchJSON(`${apiBase()}/api/overseas/stock/${symbol}/analysis?exchange_code=${exchange}&product_type_code=${productType}`);
        renderAnalysis(payload);
      } catch (error) {
        $('analysisBox').innerHTML = `<div class="note">조회 실패: ${String(error.message || error)}</div>`;
      }
    }

    $('btnAnalyze').addEventListener('click', analyze);
    $('btnSample').addEventListener('click', () => {
      $('symbolInput').value = 'AAPL';
      $('exchangeInput').value = 'NAS';
      $('productTypeInput').value = '512';
    });
