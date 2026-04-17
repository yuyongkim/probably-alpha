    import { openStockProfile, setupProfileDialogClose } from './js/renderers/stock-profile.js?v=1775488167';

    const API = () => document.getElementById('apiBase').value.trim();
    const capital = () => Number(document.getElementById('userCapital').value.replace(/,/g, '')) || 100_000_000;
    function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    const fmtPct = (v) => v != null ? `${(v * 100).toFixed(1)}%` : '-';
    const fmtPrice = (v) => v != null ? `${Math.round(v).toLocaleString('ko-KR')}원` : '-';
    const fmtNum = (v) => v != null ? Number(v).toFixed(2) : '-';

    let allPresets = [];
    let dailyPicks = {};  // cached preset-picks from pipeline

    async function load() {
      try {
        const [summaryResp, picksResp] = await Promise.all([
          fetch(`${API()}/api/presets/summary`),
          fetch(`${API()}/api/presets/daily-picks`).catch(() => null),
        ]);
        const summaryData = await summaryResp.json();
        allPresets = summaryData.items || [];

        if (picksResp && picksResp.ok) {
          const picksData = await picksResp.json();
          dailyPicks = picksData.items || picksData || {};
        }

        // Enrich presets with pick counts
        for (const p of allPresets) {
          const dp = dailyPicks[p.id];
          if (dp) p._daily_picks_count = (dp.items || []).length;
        }

        render(allPresets);
      } catch (e) {
        document.getElementById('strategyGrid').innerHTML = `<p style="color:var(--bad)">로드 실패: ${esc(e.message)}</p>`;
      }
    }

    function render(presets) {
      const grid = document.getElementById('strategyGrid');
      if (!presets.length) {
        grid.innerHTML = '<p style="color:var(--muted)">프리셋이 없습니다.</p>';
        return;
      }

      grid.innerHTML = presets.map((p) => {
        const bt = p.backtest || {};
        const ret = bt.total_return;
        const retStr = ret != null ? `${(ret * 100).toFixed(1)}%` : '-';
        const retCls = ret != null ? (ret >= 0 ? 'pos' : 'neg') : '';
        return `
          <div class="strategy-card risk-${p.risk_level}" data-preset="${p.id}">
            <div class="strategy-card__head">
              <div>
                <h3 class="strategy-card__name">${p.name}</h3>
                <div class="strategy-card__family">${p.family_ko || p.family}</div>
              </div>
              <div class="strategy-card__return ${retCls}">${ret != null ? (ret >= 0 ? '+' : '') : ''}${retStr}</div>
            </div>
            <p style="font-size:13px;color:var(--muted);margin:0 0 8px">${p.description}</p>
            <div class="strategy-card__metrics">
              <dl><dt>MDD</dt><dd>${bt.max_drawdown != null ? (bt.max_drawdown * 100).toFixed(0) + '%' : '-'}</dd></dl>
              <dl><dt>Sharpe</dt><dd>${bt.sharpe != null ? bt.sharpe.toFixed(2) : '-'}</dd></dl>
              <dl><dt>승률</dt><dd>${bt.win_rate != null ? (bt.win_rate * 100).toFixed(0) + '%' : '-'}</dd></dl>
              <dl><dt>거래</dt><dd>${bt.total_trades || '-'}</dd></dl>
            </div>
            <div class="strategy-card__tags">
              <span class="strategy-card__tag">${p.holding_period}</span>
              <span class="strategy-card__tag">${p.stop_desc}</span>
              <span class="strategy-card__tag">${p.params?.sizing_method === 'atr_risk' ? 'ATR 사이징' : '균등 배분'}</span>
              <span class="strategy-card__tag">최대 ${p.params?.max_positions || '?'}종목</span>
              ${p._daily_picks_count ? `<span class="strategy-card__tag" style="background:var(--accent);color:#fff">오늘 ${p._daily_picks_count}종목</span>` : ''}
            </div>
          </div>`;
      }).join('');

      // Click handlers
      grid.querySelectorAll('.strategy-card').forEach((card) => {
        card.addEventListener('click', () => openDetail(card.dataset.preset));
      });
    }

    async function openDetail(presetId) {
      const p = allPresets.find((x) => x.id === presetId);
      if (!p) return;

      const modal = document.getElementById('detailModal');
      const body = document.getElementById('detailBody');
      modal.classList.add('open');

      body.innerHTML = `<h2>${p.name}</h2><p style="color:var(--muted)">${p.description}</p><p>매수 후보 로딩 중...</p>`;

      try {
        // Use cached daily picks if available, else fetch live
        let data;
        const cached = dailyPicks[presetId];
        if (cached && cached.items && cached.items.length) {
          data = cached;
        } else {
          const resp = await fetch(`${API()}/api/presets/${presetId}/picks?limit=10&initial_cash=${capital()}`);
          data = await resp.json();
        }
        const picks = data.items || [];
        const bt = p.backtest || {};

        body.innerHTML = `
          <h2 style="margin-bottom:4px">${p.name}</h2>
          <div style="display:flex;gap:8px;margin-bottom:16px">
            <span class="strategy-card__tag" style="background:#2563eb;color:#fff">${p.family_ko}</span>
            <span class="strategy-card__tag">${p.holding_period}</span>
            <span class="strategy-card__tag">${p.stop_desc}</span>
          </div>
          <p style="color:var(--muted);margin-bottom:20px">${p.description}</p>

          <div class="tab-bar">
            <button class="tab-btn active" data-tab="picks">오늘의 매수 후보</button>
            <button class="tab-btn" data-tab="rules">매매 규칙</button>
            <button class="tab-btn" data-tab="backtest">백테스트 성과</button>
            <button class="tab-btn" data-tab="howto">따라하기 가이드</button>
          </div>

          <div id="tabPicks" class="tab-panel active">
            <h3 style="margin-bottom:8px">스크리닝 결과: ${data.screened?.toLocaleString() || '?'}개 중 ${picks.length}개 통과</h3>
            ${picks.length ? picks.map((s) => {
              const ex = s.execution || {};
              return `
                <div class="exec-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                    <div>
                      <strong style="font-size:16px;cursor:pointer" class="pick-symbol" data-sym="${esc(s.symbol)}">${esc(s.name || s.symbol)}</strong>
                      <span style="color:var(--muted);margin-left:8px">${esc(s.symbol)} · ${esc(s.sector || '')}</span>
                    </div>
                    <span class="score ${(s.score || 0) >= 70 ? 'good' : (s.score || 0) >= 40 ? 'mid' : 'bad'}">${Math.min(s.score || 0, 100).toFixed(1)}</span>
                  </div>
                  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px">
                    <div class="exec-row"><span class="exec-label">매수가</span><span class="exec-value">${fmtPrice(ex.entry_price)}</span></div>
                    <div class="exec-row"><span class="exec-label">손절가</span><span class="exec-value exec-stop">${fmtPrice(ex.stop_price)}</span></div>
                    <div class="exec-row"><span class="exec-label">목표가</span><span class="exec-value exec-target">${fmtPrice(ex.target_price)}</span></div>
                    <div class="exec-row"><span class="exec-label">R:R</span><span class="exec-value">${ex.rr_ratio || '-'}</span></div>
                    <div class="exec-row"><span class="exec-label">매수 수량</span><span class="exec-value">${ex.shares?.toLocaleString() || '-'}주</span></div>
                    <div class="exec-row"><span class="exec-label">투자금액</span><span class="exec-value">${ex.position_value ? Math.round(ex.position_value).toLocaleString() + '원' : '-'}</span></div>
                    <div class="exec-row"><span class="exec-label">최대 손실</span><span class="exec-value exec-stop">${ex.max_loss_krw ? Math.round(ex.max_loss_krw).toLocaleString() + '원' : '-'} (종목의 ${ex.max_loss_pct || '-'}%, 전체의 ${ex.max_loss_pct_equity || '-'}%)</span></div>
                  </div>
                  ${s.rs_percentile ? `<div style="margin-top:6px;font-size:12px;color:var(--muted)">RS ${s.rs_percentile?.toFixed(0)}% · TT ${s.tt_passed || '-'}/8 · ${ex.stop_type} · ${ex.sizing_method}</div>` : ''}
                </div>`;
            }).join('') : '<p style="color:var(--muted)">오늘 이 전략에 맞는 종목이 없습니다.</p>'}
          </div>

          <div id="tabRules" class="tab-panel">
            <h3>매매 규칙</h3>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:12px">
              <div>
                <h4 style="color:var(--accent);margin-bottom:8px">진입 조건</h4>
                <ul style="color:var(--muted);line-height:2;padding-left:18px;font-size:14px">
                  <li>시그널: <strong>${p.params?.signal_type || 'trend_template'}</strong></li>
                  <li>TT 최소 통과: <strong>${p.params?.min_tt_pass || 5}/8</strong></li>
                  <li>RS 임계값: <strong>${p.params?.rs_threshold || 70}%</strong></li>
                  ${p.params?.use_earnings_filter ? '<li>실적 필터: <strong>EPS YoY 25%+</strong></li>' : ''}
                  ${p.params?.use_market_filter ? '<li>시장 필터: <strong>KOSPI > 200MA일 때만</strong></li>' : ''}
                </ul>
              </div>
              <div>
                <h4 style="color:var(--accent);margin-bottom:8px">청산 조건</h4>
                <ul style="color:var(--muted);line-height:2;padding-left:18px;font-size:14px">
                  <li>손절: <strong>${p.stop_desc}</strong></li>
                  <li>포지션 사이징: <strong>${p.params?.sizing_method === 'atr_risk' ? 'ATR 기반 (1% 리스크)' : '균등 배분'}</strong></li>
                  <li>리밸런싱: <strong>${p.params?.rebalance === 'daily' ? '매일' : p.params?.rebalance === 'monthly' ? '매월' : '매주 금요일'}</strong></li>
                  <li>최대 보유: <strong>${p.params?.max_positions || '?'}종목</strong></li>
                </ul>
              </div>
            </div>
          </div>

          <div id="tabBacktest" class="tab-panel">
            <h3>백테스트 성과</h3>
            ${bt.total_return != null ? `
            <div style="display:flex;gap:24px;margin:16px 0;flex-wrap:wrap">
              <dl><dt style="color:var(--muted);font-size:12px">총 수익률</dt><dd style="font-size:24px;font-weight:800;color:${bt.total_return >= 0 ? 'var(--good)' : 'var(--bad)'}">${(bt.total_return * 100).toFixed(1)}%</dd></dl>
              <dl><dt style="color:var(--muted);font-size:12px">CAGR</dt><dd style="font-size:18px;font-weight:600">${bt.cagr != null ? (bt.cagr * 100).toFixed(1) + '%' : '-'}</dd></dl>
              <dl><dt style="color:var(--muted);font-size:12px">Sharpe</dt><dd style="font-size:18px;font-weight:600">${bt.sharpe != null ? bt.sharpe.toFixed(2) : '-'}</dd></dl>
              <dl><dt style="color:var(--muted);font-size:12px">MDD</dt><dd style="font-size:18px;font-weight:600;color:var(--bad)">${bt.max_drawdown != null ? (bt.max_drawdown * 100).toFixed(0) + '%' : '-'}</dd></dl>
              <dl><dt style="color:var(--muted);font-size:12px">승률</dt><dd style="font-size:18px;font-weight:600">${bt.win_rate != null ? (bt.win_rate * 100).toFixed(0) + '%' : '-'}</dd></dl>
              <dl><dt style="color:var(--muted);font-size:12px">거래 수</dt><dd style="font-size:18px;font-weight:600">${bt.total_trades || '-'}</dd></dl>
            </div>
            <p style="color:var(--muted);font-size:13px">기간: ${bt.period?.start || '?'} ~ ${bt.period?.end || '?'}</p>
            ` : '<p style="color:var(--muted)">백테스트 결과가 없습니다. 백테스트 페이지에서 실행해주세요.</p>'}
          </div>

          <div id="tabHowto" class="tab-panel">
            <h3>따라하기 가이드</h3>
            <div style="margin-top:12px;line-height:2;color:var(--muted);font-size:14px">
              <h4 style="color:var(--accent)">매주 실행 체크리스트</h4>
              <ol style="padding-left:20px">
                <li><strong>금요일 장 마감 후</strong>: 이 페이지에서 매수 후보 확인</li>
                <li><strong>월요일 장 시작</strong>: 매수 후보 중 시가에 매수 주문</li>
                <li><strong>매일</strong>: 보유 종목의 손절가 확인 (${p.stop_desc})</li>
                <li><strong>손절 발동 시</strong>: 즉시 매도, 감정 개입 금지</li>
                <li><strong>다음 금요일</strong>: 리밸런싱 — 탈락 종목 매도, 신규 매수</li>
              </ol>
              <h4 style="color:var(--accent);margin-top:16px">투자금 ${capital().toLocaleString()}원 기준</h4>
              <ul style="padding-left:20px">
                <li>종목당 투자: ~${Math.round(capital() / (p.params?.max_positions || 5)).toLocaleString()}원</li>
                <li>종목당 최대 손실: ~${Math.round(capital() * (p.params?.stop_loss_pct || 0.075) / (p.params?.max_positions || 5)).toLocaleString()}원</li>
                <li>전체 최대 손실 (전 종목 동시 손절): ~${Math.round(capital() * (p.params?.stop_loss_pct || 0.075)).toLocaleString()}원</li>
              </ul>
              <div style="margin-top:16px;padding:12px;background:rgba(239,68,68,.1);border-radius:8px;border:1px solid var(--bad)">
                <strong style="color:var(--bad)">주의사항</strong>
                <p style="margin:4px 0 0">과거 성과가 미래 수익을 보장하지 않습니다. 반드시 자신의 리스크 허용 범위 내에서 투자하세요.</p>
              </div>
            </div>
          </div>
        `;

        // Tab switching
        body.querySelectorAll('.tab-btn').forEach((btn) => {
          btn.addEventListener('click', () => {
            body.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
            body.querySelectorAll('.tab-panel').forEach((p) => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(`tab${btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1)}`).classList.add('active');
          });
        });

        // Stock click → profile dialog
        body.querySelectorAll('.pick-symbol').forEach((el) => {
          el.addEventListener('click', (e) => {
            e.stopPropagation();
            openStockProfile(el.dataset.sym);
          });
        });

      } catch (e) {
        body.innerHTML = `<h2>${esc(p.name)}</h2><p style="color:var(--bad)">로드 실패: ${esc(e.message)}</p>`;
      }
    }

    // Filter chips
    document.getElementById('filterBar').addEventListener('click', (e) => {
      if (!e.target.classList.contains('filter-chip')) return;
      document.querySelectorAll('.filter-chip').forEach((c) => c.classList.remove('active'));
      e.target.classList.add('active');
      const family = e.target.dataset.family;
      const filtered = family === 'all' ? allPresets : allPresets.filter((p) => p.family === family);
      render(filtered);
    });

    // Modal close
    document.getElementById('detailClose').addEventListener('click', () => {
      document.getElementById('detailModal').classList.remove('open');
    });
    document.getElementById('detailModal').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
    });

    // Init
    setupProfileDialogClose();
    load();
