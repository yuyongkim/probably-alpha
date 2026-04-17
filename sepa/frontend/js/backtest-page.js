    const $ = id => document.getElementById(id);
    const api = () => ($('apiBase')?.value || '').replace(/\/+$/, '');
    function esc(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    // ── Trader Presets ──
    const PRESETS = [
      {
        id: 'minervini', trader: 'Mark Minervini', style: 'SEPA 성장 모멘텀',
        color: '#6ee7a8',
        desc: 'Trend Template 8조건 + VCP + RS 상위. 핵심 SEPA 전략.',
        rules: { alphaTT: true, minTT: 5, alphaRS: true, rsVal: 70, ma50: true, sma200: true, sectorFilter: true, topSectors: 5, sectorLimit: 2, stopLoss: true, stopPct: 7.5, sectorExit: true, leaderExit: true, maxPos: 5, rebalance: 'weekly', near52w: true, near52wThreshold: 0.75 },
      },
      {
        id: 'oneil', trader: "William O'Neil", style: 'CAN SLIM 성장주',
        color: '#4db8ff',
        desc: 'RS 상위 + 실적 가속 + 신고가 돌파. 엄격한 손절.',
        rules: { alphaTT: true, minTT: 6, alphaRS: true, rsVal: 80, ma50: true, sma200: true, sectorFilter: true, topSectors: 3, sectorLimit: 2, stopLoss: true, stopPct: 7.0, sectorExit: true, leaderExit: true, maxPos: 4, rebalance: 'weekly', volExpansion: true, volRatio: 1.5, near52w: true, near52wThreshold: 0.85 },
      },
      {
        id: 'dennis', trader: 'Richard Dennis', style: '터틀 추세추종',
        color: '#ffb84d',
        desc: '20일 채널 돌파 + 거래량 확인. 추세추종의 원조.',
        rules: { alphaTT: true, minTT: 4, alphaRS: true, rsVal: 50, ma50: true, sma200: false, sectorFilter: false, topSectors: 10, sectorLimit: 5, stopLoss: true, stopPct: 8.0, sectorExit: false, leaderExit: true, maxPos: 5, rebalance: 'weekly', breakout20d: true, volExpansion: true, volRatio: 1.3 },
      },
      {
        id: 'seykota', trader: 'Ed Seykota', style: '시스템 추세추종',
        color: '#ff9966',
        desc: '추세 정배열만 따라가고, 규칙을 절대 어기지 않는다.',
        rules: { alphaTT: true, minTT: 7, alphaRS: true, rsVal: 60, ma50: true, sma200: true, sectorFilter: false, topSectors: 10, sectorLimit: 5, stopLoss: true, stopPct: 8.0, sectorExit: false, leaderExit: true, maxPos: 4, rebalance: 'weekly' },
      },
      {
        id: 'hite', trader: 'Larry Hite', style: '1% 리스크 룰',
        color: '#c4b5fd',
        desc: '한 종목당 최대 손실 1%. 작게 잃고, 크게 벌기.',
        rules: { alphaTT: true, minTT: 5, alphaRS: true, rsVal: 50, ma50: true, sma200: false, sectorFilter: true, topSectors: 10, sectorLimit: 2, stopLoss: true, stopPct: 5.0, sectorExit: true, leaderExit: true, maxPos: 5, rebalance: 'weekly' },
      },
      {
        id: 'driehaus', trader: 'Richard Driehaus', style: '실적 서프라이즈',
        color: '#ff8f8f',
        desc: 'RS 최상위 + 공격적 집중투자. 적은 종목, 큰 베팅.',
        rules: { alphaTT: true, minTT: 5, alphaRS: true, rsVal: 85, ma50: true, sma200: true, sectorFilter: true, topSectors: 3, sectorLimit: 2, stopLoss: true, stopPct: 10.0, sectorExit: true, leaderExit: true, maxPos: 3, rebalance: 'weekly', volExpansion: true, volRatio: 1.5, near52w: true, near52wThreshold: 0.90 },
      },
      {
        id: 'schwartz', trader: 'Marty Schwartz', style: '단기 스윙',
        color: '#7fd4ff',
        desc: 'MA 위에서만 진입, 빠른 손절, 일간 리밸런싱.',
        rules: { alphaTT: true, minTT: 4, alphaRS: true, rsVal: 40, ma50: true, sma200: false, sectorFilter: false, topSectors: 10, sectorLimit: 5, stopLoss: true, stopPct: 5.0, sectorExit: false, leaderExit: true, maxPos: 5, rebalance: 'daily', vcp: true },
      },
      {
        id: 'jones', trader: 'Paul Tudor Jones', style: '200MA 필터 매크로',
        color: '#ffd700',
        desc: '200일선 위에서만 투자. 방어적 포지션 관리.',
        rules: { alphaTT: true, minTT: 6, alphaRS: true, rsVal: 60, ma50: true, sma200: true, sectorFilter: true, topSectors: 5, sectorLimit: 3, stopLoss: true, stopPct: 6.0, sectorExit: true, leaderExit: true, maxPos: 4, rebalance: 'weekly' },
      },
      {
        id: 'custom', trader: '커스텀', style: '직접 설정',
        color: 'var(--muted)',
        desc: '모든 규칙을 직접 설정합니다.',
        rules: null,
      },
    ];

    function renderPresets() {
      const el = $('presetCards');
      el.innerHTML = PRESETS.map(p => `
        <div class="preset-card" data-preset="${p.id}" style="border-color:${p.color};padding:14px;background:var(--panel);border-radius:var(--radius-xs);cursor:pointer;transition:opacity .15s;border:1px solid">
          <div style="display:flex;justify-content:space-between;align-items:start">
            <div>
              <strong style="font-size:15px">${p.trader}</strong>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">${p.style}</div>
            </div>
            ${p.rules ? `<span style="font-size:11px;background:rgba(255,255,255,.06);padding:2px 8px;border-radius:10px">${p.rules.maxPos}종목</span>` : ''}
          </div>
          <p style="font-size:13px;color:var(--muted);margin-top:8px;line-height:1.5">${p.desc}</p>
        </div>
      `).join('');

      el.querySelectorAll('.preset-card').forEach(card => {
        card.addEventListener('click', () => {
          el.querySelectorAll('.preset-card').forEach(c => c.style.opacity = '0.5');
          card.style.opacity = '1';
          applyPreset(card.dataset.preset);
        });
      });
    }

    let activePresetId = null;

    function applyPreset(presetId) {
      activePresetId = presetId;
      const preset = PRESETS.find(p => p.id === presetId);
      if (!preset || !preset.rules) { activePresetId = null; return; }
      const r = preset.rules;
      $('rAlphaTT').checked = r.alphaTT;
      $('rAlphaMinTT').value = r.minTT;
      $('rAlphaRS').checked = r.alphaRS;
      $('rAlphaRSVal').value = r.rsVal;
      $('rAlphaMA50').checked = r.ma50;
      $('rSectorFilter').checked = r.sectorFilter;
      $('rSectorTopN').value = r.topSectors;
      $('btSectorLimit').value = r.sectorLimit;
      $('rStopLoss').checked = r.stopLoss;
      $('rStopPct').value = r.stopPct;
      $('rSectorExit').checked = r.sectorExit;
      $('rLeaderExit').checked = r.leaderExit;
      $('btMaxPos').value = r.maxPos;
      $('btRebalance').value = r.rebalance;
      // Extra conditions
      $('rVolExpansion').checked = r.volExpansion || false;
      $('rVolRatio').value = r.volRatio || 1.5;
      $('rNear52W').checked = r.near52w || false;
      $('rNear52WVal').value = (r.near52wThreshold || 0.85) * 100;
      $('rVCP').checked = r.vcp || false;
      $('r20dBreak').checked = r.breakout20d || false;
      $('rSMA200').checked = r.sma200 !== false;
    }

    renderPresets();

    function pct(v) { return v != null ? (v * 100).toFixed(1) + '%' : '-'; }
    function num(v) { return v != null ? Number(v).toLocaleString('ko-KR') : '-'; }
    function fixed(v, d=2) { return v != null ? Number(v).toFixed(d) : '-'; }

    $('btnRunBacktest').addEventListener('click', async () => {
      const status = $('btStatus');
      status.textContent = '백테스트 실행 중... (수 분 소요될 수 있습니다)';
      status.style.color = 'var(--accent)';
      $('btnRunBacktest').disabled = true;
      $('resultSection').style.display = 'none';

      try {
        const params = new URLSearchParams({
          start: $('btStart').value,
          end: $('btEnd').value,
          initial_cash: $('btCash').value,
          max_positions: $('btMaxPos').value,
          sector_limit: $('btSectorLimit').value,
          top_sectors: $('rSectorTopN').value,
          rebalance: $('btRebalance').value,
          stop_loss_pct: ($('rStopLoss').checked ? parseFloat($('rStopPct').value) / 100 : 0).toString(),
          commission: (parseFloat($('rCommission').value) / 100).toString(),
          slippage: (parseFloat($('rSlippage').value) / 100).toString(),
          tax: (parseFloat($('rTax').value) / 100).toString(),
          alpha_min_tt: $('rAlphaTT').checked ? $('rAlphaMinTT').value : '0',
          alpha_rs_threshold: $('rAlphaRS').checked ? $('rAlphaRSVal').value : '0',
          require_ma50: $('rAlphaMA50').checked ? '1' : '0',
          require_sma200: $('rSMA200').checked ? '1' : '0',
          sector_filter: $('rSectorFilter').checked ? '1' : '0',
          sector_exit: $('rSectorExit').checked ? '1' : '0',
          leader_exit: $('rLeaderExit').checked ? '1' : '0',
          require_volume_expansion: $('rVolExpansion').checked ? '1' : '0',
          min_volume_ratio: $('rVolRatio').value,
          require_near_52w_high: $('rNear52W').checked ? '1' : '0',
          near_52w_threshold: (parseFloat($('rNear52WVal').value) / 100).toString(),
          require_volatility_contraction: $('rVCP').checked ? '1' : '0',
          require_20d_breakout: $('r20dBreak').checked ? '1' : '0',
        });
        // If using a preset, send preset name for server-side config
        if (activePresetId && activePresetId !== 'custom') {
          params.set('preset', activePresetId);
        }
        const adminToken = window.prompt('Admin token required. Paste SEPA_ADMIN_TOKEN to run this backtest.');
        if (!adminToken) {
          status.textContent = 'Admin token required.';
          status.style.color = '#ffb84d';
          return;
        }
        const resp = await fetch(`${api()}/api/admin/backtest/run?${params}`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${adminToken}` },
        });
        const result = await resp.json();

        if (!resp.ok || result.error) {
          status.textContent = `Error: ${result.detail || result.error || resp.statusText}`;
          status.style.color = '#ff6b6b';
          return;
        }

        renderResult(result);
        status.textContent = `완료: ${result.run_id} (${result.trading_days || 0}거래일)`;
        status.style.color = '#6ee7a8';
      } catch (e) {
        status.textContent = `실행 실패: ${e.message}`;
        status.style.color = '#ff6b6b';
      } finally {
        $('btnRunBacktest').disabled = false;
      }
    });

    function renderResult(r) {
      const m = r.metrics || {};
      const p = r.params || {};
      const period = r.period || {};
      const bench = m.benchmark || {};

      $('resultSection').style.display = '';
      $('resultTitle').textContent = `${r.strategy || '?'} — ${period.start || '?'} ~ ${period.end || '?'}`;

      const curve = r.equity_curve || [];
      const startCash = p.initial_cash || (curve[0]?.equity) || 0;
      const endEquity = curve.length ? curve[curve.length - 1].equity : startCash;
      $('kStartCash').textContent = num(startCash) + '원';
      $('kEndEquity').textContent = num(endEquity) + '원';
      $('kCagr').textContent = pct(m.cagr);
      $('kTotal').textContent = pct(m.total_return);
      $('kMDD').textContent = pct(m.max_drawdown);
      $('kSharpe').textContent = fixed(m.sharpe);
      $('kWinRate').textContent = pct(m.trade_win_rate ?? m.win_rate);
      $('kTrades').textContent = num(m.total_trades);

      const metrics = [
        ['CAGR', pct(m.cagr), '연환산 복리 수익률'],
        ['총 수익률', pct(m.total_return), '전체 기간 수익률'],
        ['샤프 비율', fixed(m.sharpe), '(수익률-무위험)/변동성'],
        ['소르티노', fixed(m.sortino), '하방 변동성만 사용'],
        ['최대 낙폭(MDD)', pct(m.max_drawdown), '최대 고점 대비 하락'],
        ['MDD 지속일', num(m.mdd_duration_days) + '일', '최대 낙폭 지속 기간'],
        ['변동성', pct(m.volatility), '연환산 변동성'],
        ['승률(일간)', pct(m.win_rate), '일간 수익일 비율'],
        ['승률(거래)', pct(m.trade_win_rate), '수익 거래 비율'],
        ['평균 수익', fixed(m.avg_win_pct) + '%', '수익 거래 평균 수익률'],
        ['평균 손실', fixed(m.avg_loss_pct) + '%', '손실 거래 평균 손실률'],
        ['손절 횟수', num(m.stop_loss_exits), '스탑로스 발동 횟수'],
        ['총 거래 수', num(m.total_trades), '매수+매도 쌍'],
        ['거래일 수', num(r.trading_days), '백테스트 기간 거래일'],
      ];
      if (bench.cagr != null) {
        metrics.push(['벤치마크 CAGR', pct(bench.cagr), 'KOSPI 연환산 수익률']);
        metrics.push(['알파', pct(bench.alpha), '벤치마크 대비 초과 수익']);
        metrics.push(['베타', fixed(bench.beta), '시장 민감도']);
      }
      $('metricsRows').innerHTML = metrics.map(([k, v, d]) =>
        `<tr><td>${k}</td><td><strong>${v}</strong></td><td style="color:var(--muted)">${d}</td></tr>`
      ).join('');

      const rules = r.rules || {};
      const paramsList = [
        ['초기 자금', num(p.initial_cash) + '원'],
        ['최대 종목 수', num(p.max_positions)],
        ['섹터당 최대', num(p.sector_limit)],
        ['리밸런싱', p.rebalance === 'weekly' ? '주간 (금요일)' : '일간'],
        ['체결 방식', p.execution],
        ['수수료', pct(p.commission)],
        ['슬리피지', pct(p.slippage)],
        ['거래세', pct(p.tax)],
      ];
      const rulesList = [
        ['Alpha TT 최소 통과', rules.alpha_min_tt != null ? `${rules.alpha_min_tt}/8` : '-'],
        ['Alpha RS 임계값', rules.alpha_rs_threshold != null ? `${rules.alpha_rs_threshold}%` : '-'],
        ['close > MA50 필수', rules.require_ma50 ? 'ON' : 'OFF'],
        ['주도섹터 필터', rules.sector_filter ? `ON (상위 ${rules.top_sectors}개)` : 'OFF'],
        ['손절 규칙', rules.stop_loss_pct ? `ON (${(rules.stop_loss_pct * 100).toFixed(1)}%)` : 'OFF'],
        ['섹터 이탈 청산', rules.sector_exit ? 'ON' : 'OFF'],
        ['리더 이탈 청산', rules.leader_exit ? 'ON' : 'OFF'],
      ];
      $('paramsRows').innerHTML = [
        '<tr><td colspan="2" style="font-weight:700;color:var(--accent);padding-top:12px">포트폴리오 설정</td></tr>',
        ...paramsList.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`),
        '<tr><td colspan="2" style="font-weight:700;color:var(--accent);padding-top:12px">적용된 규칙</td></tr>',
        ...rulesList.map(([k, v]) => `<tr><td>${k}</td><td><strong>${v}</strong></td></tr>`),
      ].join('');

      // Equity curve chart
      renderEquityChart(r.equity_curve || []);

      // Trade log
      renderTradeLog(r.trades || []);

      $('resultSection').scrollIntoView({ behavior: 'smooth' });
    }

    function renderEquityChart(curve) {
      const canvas = $('equityChart');
      if (!canvas || !curve.length) return;
      const ctx = canvas.getContext('2d');
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = 300 * dpr;
      ctx.scale(dpr, dpr);
      const W = rect.width, H = 300;
      ctx.clearRect(0, 0, W, H);

      const equities = curve.map(p => p.equity);
      const maxE = Math.max(...equities);
      const minE = Math.min(...equities);
      const range = maxE - minE || 1;
      const pad = { t: 20, b: 30, l: 60, r: 20 };

      // Grid
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i++) {
        const y = pad.t + (H - pad.t - pad.b) * i / 4;
        ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
        const val = maxE - range * i / 4;
        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.font = '11px monospace';
        ctx.textAlign = 'right';
        ctx.fillText((val / 1e6).toFixed(0) + 'M', pad.l - 6, y + 4);
      }

      // Equity line
      ctx.strokeStyle = '#4db8ff';
      ctx.lineWidth = 2;
      ctx.beginPath();
      curve.forEach((p, i) => {
        const x = pad.l + (W - pad.l - pad.r) * i / (curve.length - 1);
        const y = pad.t + (H - pad.t - pad.b) * (1 - (p.equity - minE) / range);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();

      // Initial capital line
      const initY = pad.t + (H - pad.t - pad.b) * (1 - (curve[0].equity - minE) / range);
      ctx.strokeStyle = 'rgba(255,255,255,0.2)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath(); ctx.moveTo(pad.l, initY); ctx.lineTo(W - pad.r, initY); ctx.stroke();
      ctx.setLineDash([]);

      // Date labels
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      [0, Math.floor(curve.length / 2), curve.length - 1].forEach(i => {
        const x = pad.l + (W - pad.l - pad.r) * i / (curve.length - 1);
        const d = curve[i]?.date || '';
        ctx.fillText(d.slice(0, 4) + '-' + d.slice(4, 6) + '-' + d.slice(6, 8), x, H - 8);
      });
    }

    function renderTradeLog(trades) {
      const el = $('tradeRows');
      if (!trades.length) {
        el.innerHTML = '<tr><td colspan="10" class="empty-state">거래 내역이 없습니다.</td></tr>';
        $('tradeLogCaption').textContent = '거래 0건';
        return;
      }
      const wins = trades.filter(t => t.pnl > 0).length;
      $('tradeLogCaption').textContent = `총 ${trades.length}건 (수익 ${wins}건, 손실 ${trades.length - wins}건)`;

      const reasonMap = { stop_loss: '손절', rebalance_exit: '리밸런싱', backtest_end: '기간종료', signal: '시그널' };
      el.innerHTML = trades.map((t, i) => {
        const pnlClass = t.pnl > 0 ? 'color:#6ee7a8' : t.pnl < 0 ? 'color:#ff6b6b' : '';
        return `<tr>
          <td>${i + 1}</td>
          <td>${esc(t.name || t.symbol)}<br><small style="color:var(--muted)">${esc(t.symbol)}</small></td>
          <td>${esc(t.entry_date)}</td>
          <td>${esc(t.exit_date)}</td>
          <td style="text-align:right">${num(t.entry_price)}</td>
          <td style="text-align:right">${num(t.exit_price)}</td>
          <td style="text-align:right">${num(t.qty)}</td>
          <td style="text-align:right;${pnlClass}"><strong>${num(t.pnl)}</strong></td>
          <td style="text-align:right;${pnlClass}">${t.pnl_pct > 0 ? '+' : ''}${t.pnl_pct}%</td>
          <td>${esc(reasonMap[t.reason_exit] || t.reason_exit)}</td>
        </tr>`;
      }).join('');
    }

    // History loader
    $('btnLoadHistory')?.addEventListener('click', async () => {
      try {
        const resp = await fetch(`${api()}/api/backtest/results`);
        const data = await resp.json();
        const items = data.items || [];
        if (!items.length) {
          $('historyRows').innerHTML = '<tr><td colspan="7" class="empty-state">저장된 백테스트 결과가 없습니다.</td></tr>';
          return;
        }
        $('historyRows').innerHTML = items.map(r => {
          const m = r.metrics || {};
          const p = r.period || {};
          return `<tr>
            <td><small>${r.run_id || '-'}</small></td>
            <td>${r.strategy || '-'}</td>
            <td>${p.start || '?'}~${p.end || '?'}</td>
            <td>${pct(m.cagr)}</td>
            <td>${pct(m.max_drawdown)}</td>
            <td>${fixed(m.sharpe)}</td>
            <td>${num(m.total_trades)}</td>
          </tr>`;
        }).join('');
      } catch (e) {
        $('historyRows').innerHTML = `<tr><td colspan="7" class="empty-state">불러오기 실패: ${esc(e.message)}</td></tr>`;
      }
    });
