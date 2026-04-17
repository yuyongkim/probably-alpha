    const $ = (id) => document.getElementById(id);

    function apiBase() {
      return $('apiBase').value.trim() || window.location.origin;
    }

    async function fetchJSON(url) {
      const response = await fetch(url);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || payload.message || `HTTP ${response.status}`);
      return payload;
    }

    function flag(value, goodLabel, badLabel) {
      return `<span class="pill ${value ? 'good' : 'warn'}">${value ? goodLabel : badLabel}</span>`;
    }

    function renderHealth(payload) {
      const box = $('healthBox');
      box.innerHTML = `
        <small class="note">${payload.env || '-'}</small>
        <strong class="${payload.auth_ok ? 'good' : 'warn'}">${payload.auth_ok ? '인증 가능' : '인증 미확인'}</strong>
        <div class="note">order_enabled: ${payload.order_enabled ? 'Y' : 'N'}</div>
      `;
    }

    function renderCatalog(payload) {
      $('catalogSummary').innerHTML = `
        <div class="stat"><small class="note">상품군 수</small><strong>${payload.count}</strong></div>
        <div class="stat"><small class="note">KIS 주문 가능</small><strong>${payload.summary.kis_orderable_count}</strong></div>
        <div class="stat"><small class="note">현재 정보 조회 지원</small><strong>${payload.summary.project_info_count}</strong></div>
        <div class="stat"><small class="note">현재 백테스트 지원</small><strong>${payload.summary.project_backtestable_count}</strong></div>
      `;

      $('catalogList').innerHTML = (payload.items || []).map((item) => `
        <article class="card">
          <div class="card-top">
            <div>
              <strong>${item.label_ko}</strong>
              <div class="note">${item.label_en} / ${item.market} / ${item.asset_class}</div>
            </div>
          </div>
          <div class="pill-row">
            ${flag(item.kis_quote_support, 'KIS 시세', 'KIS 시세 없음')}
            ${flag(item.kis_realtime_support, '실시간', '실시간 미확인')}
            ${flag(item.kis_order_support, 'KIS 주문', '주문 미확인')}
            ${flag(item.project_info_support, '프로젝트 정보 조회', '프로젝트 미연결')}
            ${flag(item.project_backtest_support, '프로젝트 백테스트', '백테스트 미연결')}
            ${flag(item.recommended_now, '지금 확장 추천', '후순위')}
          </div>
          <div class="note">예시 폴더: ${(item.examples_folders || []).join(', ')}</div>
          <div class="note">${item.notes || ''}</div>
        </article>
      `).join('');
    }

    async function loadHealth() {
      $('healthBox').innerHTML = '<small class="note">조회 중</small><strong>...</strong>';
      try {
        renderHealth(await fetchJSON(`${apiBase()}/api/kis/health`));
      } catch (error) {
        $('healthBox').innerHTML = `<small class="note">오류</small><strong>${String(error.message || error)}</strong>`;
      }
    }

    async function loadCatalog() {
      $('catalogList').innerHTML = '<div class="note">카탈로그 조회 중...</div>';
      try {
        renderCatalog(await fetchJSON(`${apiBase()}/api/kis/catalog`));
      } catch (error) {
        $('catalogList').innerHTML = `<div class="note">카탈로그 조회 실패: ${String(error.message || error)}</div>`;
      }
    }

    $('btnHealth').addEventListener('click', loadHealth);
    $('btnCatalog').addEventListener('click', loadCatalog);
    loadHealth();
    loadCatalog();
