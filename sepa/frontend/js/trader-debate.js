import { traderProfiles } from './market-wizards-data.js?v=1775484394';
import { setupPageI18n, txt } from './i18n.js?v=1775484394';
import { $, escapeHtml, fetchJSON, fmtDate, fmtNum, fmtPct, cls } from './core.js?v=1775484394';

const DEFAULT_API_BASE = `${window.location.protocol}//${window.location.hostname || '127.0.0.1'}:8000`;

/* ── Scoring helpers (same logic as market-wizards-korea.js) ── */

function clamp(value, min = 0, max = 100) {
  const num = Number(value);
  if (!Number.isFinite(num)) return min;
  return Math.max(min, Math.min(max, num));
}

function epsScore(status) {
  return ({ strong_growth: 100, positive_growth: 82, stable_growth: 68, stable: 52, mixed: 38, negative_growth: 10 })[String(status || '').trim()] ?? 0;
}

function leastResistanceScore(status) {
  return ({ up_least_resistance: 100, breakout_ready: 92, pullback_in_uptrend: 78, range: 52, downtrend: 10 })[String(status || '').trim()] ?? 0;
}

function rrScore(rrRatio) {
  return clamp((Number(rrRatio || 0) / 2.0) * 100);
}

function normalizedSectorMetrics(item) {
  return {
    rs: clamp(item?.sector_rs_percentile),
    alpha: clamp(Number(item?.alpha_ratio || 0) * 100),
    beta: clamp(Number(item?.beta_ratio || 0) * 100),
    leader: clamp(item?.leader_score),
    ret: clamp(Number(item?.avg_ret120 || 0) * 100),
  };
}

function normalizedStockMetrics(item, sectorScore, rec) {
  const retPct = item?.ret120_pct != null ? item.ret120_pct : (item?.ret120 != null ? Number(item.ret120) * 100 : 0);
  const leaderScore = item?.leader_stock_score ?? item?.avg_leader_stock_score ?? 0;
  return {
    alpha: clamp(item?.alpha_score),
    beta: clamp(Number(item?.beta_confidence || 0) * 10),
    gamma: clamp(Number(item?.gamma_score || 0) * 10),
    ret: clamp(retPct),
    leader: clamp((Number(leaderScore) / 120) * 100),
    recommendation: clamp(rec?.recommendation_score),
    sector: clamp(sectorScore),
    rr: rrScore(rec?.risk_plan?.rr_ratio),
    eps: epsScore(rec?.why?.eps_status),
    leastResistance: leastResistanceScore(rec?.why?.least_resistance),
  };
}

function weightedScore(weights, metrics) {
  return Object.entries(weights || {}).reduce(
    (total, [key, weight]) => total + (Number(weight || 0) * Number(metrics[key] || 0)),
    0,
  );
}

function passesFilters(profile, metrics) {
  const filters = profile?.preset?.filters || {};
  if (filters.minAlpha && metrics.alpha < filters.minAlpha) return false;
  if (filters.minBeta && metrics.beta < filters.minBeta) return false;
  if (filters.minGamma && metrics.gamma < filters.minGamma) return false;
  if (filters.minRecommendation && metrics.recommendation < filters.minRecommendation) return false;
  if (filters.requirePositiveEps && metrics.eps < 68) return false;
  return true;
}

/* ── Trader-specific risk concerns ── */

const RISK_CONCERNS = {
  'ed-seykota': {
    key: 'trend_break',
    ko: '추세 이탈 — 주도주가 주요 이동평균선 아래로 하락하면 추세추종 기반이 무너집니다.',
    en: 'Trend break — If leaders fall below key moving averages, the trend-following thesis collapses.',
  },
  'stan-druckenmiller': {
    key: 'theme_rotation',
    ko: '테마 순환 — 집중 투자한 테마가 갑자기 자금 유출을 겪으면 집중 리스크가 현실화됩니다.',
    en: 'Theme rotation — If the concentrated theme suddenly sees outflows, concentration risk materializes.',
  },
  'paul-tudor-jones': {
    key: 'failed_breakout',
    ko: '실패한 돌파 — 거래량 없는 돌파가 반복되면 위험 대비 보상이 급격히 악화됩니다.',
    en: 'Failed breakouts — Repeated breakouts without volume deteriorate the risk-reward rapidly.',
  },
  'william-oneil': {
    key: 'eps_miss',
    ko: 'EPS 미달 — 실적 가속이 둔화되면 성장주 프리미엄이 빠르게 소멸합니다.',
    en: 'EPS miss — If earnings acceleration stalls, the growth premium evaporates quickly.',
  },
  'nicolas-darvas': {
    key: 'box_failure',
    ko: '박스 실패 — 신고가 돌파가 즉시 되돌려지면 구조적 패턴이 무효화됩니다.',
    en: 'Box failure — If new-high breakouts reverse immediately, the structural pattern is invalidated.',
  },
  'jesse-livermore': {
    key: 'leader_exhaustion',
    ko: '주도주 소진 — 현재 사이클 리더가 지쳐 새 리더로 교체되는 전환기 리스크입니다.',
    en: 'Leader exhaustion — The risk of the current cycle leaders tiring and being replaced.',
  },
};

/* ── Analysis generation ── */

function generateAnalysis(profile, sectors, stocks, confirmedSectors) {
  const lines = [];
  const topSectors = sectors.slice(0, 3);
  const topStocks = stocks.slice(0, 5);

  // Check for euphoria: top stock with extreme returns
  const topStock = topStocks[0];
  if (topStock && topStock.ret120_pct > 300) {
    lines.push(txt({
      ko: `${escapeHtml(topStock.name || topStock.symbol)}의 120일 수익률이 ${fmtNum(topStock.ret120_pct, 0)}%로 과열 경고 수준입니다.`,
      en: `${escapeHtml(topStock.name || topStock.symbol)} has a 120-day return of ${fmtNum(topStock.ret120_pct, 0)}%, reaching euphoria warning levels.`,
    }));
  }

  // Narrow leadership check
  if (confirmedSectors.length <= 1) {
    lines.push(txt({
      ko: `확정 섹터가 ${confirmedSectors.length}개뿐이므로 시장 주도력이 매우 좁습니다.`,
      en: `Only ${confirmedSectors.length} confirmed sector(s) — market leadership is very narrow.`,
    }));
  } else if (confirmedSectors.length <= 3) {
    lines.push(txt({
      ko: `확정 섹터 ${confirmedSectors.length}개 — 주도력은 선택적입니다.`,
      en: `${confirmedSectors.length} confirmed sectors — leadership is selective.`,
    }));
  }

  // Watchlist sector with high alpha_ratio (upgrade candidate)
  for (const s of sectors) {
    if (s.breakout_status === 'sector_breakout_setup' && Number(s.alpha_ratio || 0) * 100 > 50) {
      lines.push(txt({
        ko: `${escapeHtml(s.sector)} 섹터는 감시 목록이지만 alpha_ratio ${fmtNum(Number(s.alpha_ratio || 0) * 100, 0)}%로 승격 후보입니다.`,
        en: `${escapeHtml(s.sector)} is on the watchlist but with alpha_ratio ${fmtNum(Number(s.alpha_ratio || 0) * 100, 0)}%, it is an upgrade candidate.`,
      }));
      break;
    }
  }

  // Use the trader's philosophy for flavor
  if (profile.philosophy && profile.philosophy.length > 0) {
    const philosophyLine = profile.philosophy[0];
    if (philosophyLine.length < 120) {
      lines.push(txt({
        ko: `"${escapeHtml(philosophyLine)}"`,
        en: `"${escapeHtml(philosophyLine)}"`,
      }));
    }
  }

  // Sector summary
  if (topSectors.length > 0) {
    const sectorNames = topSectors.map((s) => escapeHtml(s.sector)).join(', ');
    lines.push(txt({
      ko: `관심 섹터: ${sectorNames}`,
      en: `Focus sectors: ${sectorNames}`,
    }));
  }

  return lines;
}

function analyzeTrader(profile, allSectors, allStocks, recMap) {
  // Rank sectors
  const sectorScoreMap = new Map();
  const rankedSectors = allSectors
    .map((item) => {
      const metrics = normalizedSectorMetrics(item);
      const score = weightedScore(profile.preset.sectorWeights, metrics);
      sectorScoreMap.set(item.sector, score);
      return { ...item, preset_score: score };
    })
    .sort((a, b) => b.preset_score - a.preset_score);

  // Rank stocks
  const rankedStocks = allStocks
    .map((item) => {
      const rec = recMap.get(item.symbol) || null;
      const metrics = normalizedStockMetrics(item, sectorScoreMap.get(item.sector) || 0, rec);
      if (!passesFilters(profile, metrics)) return null;
      return { ...item, preset_score: weightedScore(profile.preset.stockWeights, metrics) };
    })
    .filter(Boolean)
    .sort((a, b) => b.preset_score - a.preset_score);

  const confirmedSectors = allSectors.filter((s) => s.breakout_status === 'sector_breakout_confirmed');
  const analysisLines = generateAnalysis(profile, rankedSectors, rankedStocks, confirmedSectors);
  const topPicks = rankedStocks.slice(0, 2);
  const riskConcern = RISK_CONCERNS[profile.id] || {
    ko: '일반적 시장 리스크',
    en: 'General market risk',
  };

  return {
    profile,
    sectors: rankedSectors.slice(0, 5),
    stocks: rankedStocks,
    topPicks,
    analysisLines,
    riskConcern,
  };
}

/* ── Consensus and Disagreements ── */

function buildConsensus(analyses) {
  const stockCounts = new Map();
  const sectorCounts = new Map();

  for (const a of analyses) {
    for (const pick of a.topPicks) {
      const key = pick.symbol;
      if (!stockCounts.has(key)) stockCounts.set(key, { item: pick, traders: [] });
      stockCounts.get(key).traders.push(a.profile.name);
    }
    for (const s of a.sectors.slice(0, 3)) {
      const key = s.sector;
      if (!sectorCounts.has(key)) sectorCounts.set(key, { name: s.sector, traders: [] });
      sectorCounts.get(key).traders.push(a.profile.name);
    }
  }

  const stockConsensus = [...stockCounts.values()]
    .filter((e) => e.traders.length >= 2)
    .sort((a, b) => b.traders.length - a.traders.length);

  const sectorConsensus = [...sectorCounts.values()]
    .filter((e) => e.traders.length >= 2)
    .sort((a, b) => b.traders.length - a.traders.length);

  return { stockConsensus, sectorConsensus };
}

function buildDisagreements(analyses) {
  // Find stocks where some traders rank high and others don't rank at all
  const allTopPicks = new Map();
  for (const a of analyses) {
    for (const pick of a.topPicks) {
      if (!allTopPicks.has(pick.symbol)) allTopPicks.set(pick.symbol, { item: pick, bullish: [], absent: [] });
      allTopPicks.get(pick.symbol).bullish.push(a.profile.name);
    }
  }

  // Check if other traders' top 10 stocks include this pick
  for (const [symbol, entry] of allTopPicks) {
    for (const a of analyses) {
      const inTop = a.stocks.slice(0, 10).some((s) => s.symbol === symbol);
      const isBullish = entry.bullish.includes(a.profile.name);
      if (!inTop && !isBullish) {
        entry.absent.push(a.profile.name);
      }
    }
  }

  return [...allTopPicks.values()]
    .filter((e) => e.bullish.length >= 1 && e.absent.length >= 2)
    .sort((a, b) => b.absent.length - a.absent.length)
    .slice(0, 5);
}

function buildAllocation(analyses) {
  const endorsements = new Map();

  for (const a of analyses) {
    for (const pick of a.topPicks) {
      if (!endorsements.has(pick.symbol)) {
        endorsements.set(pick.symbol, {
          item: pick,
          count: 0,
          totalScore: 0,
          traders: [],
        });
      }
      const e = endorsements.get(pick.symbol);
      e.count += 1;
      e.totalScore += pick.preset_score;
      e.traders.push(a.profile.name);
    }
  }

  const entries = [...endorsements.values()].sort((a, b) => b.count - a.count || b.totalScore - a.totalScore);
  const totalWeight = entries.reduce((sum, e) => sum + e.count, 0) || 1;

  return entries.slice(0, 8).map((e) => ({
    ...e,
    weight: ((e.count / totalWeight) * 100),
  }));
}

/* ── Rendering ── */

function renderDebateCard(analysis) {
  const { profile, topPicks, analysisLines, riskConcern } = analysis;
  const riskText = txt(riskConcern);

  const picksHtml = topPicks.map((pick) => {
    const scoreClass = pick.preset_score >= 50 ? 'good' : pick.preset_score >= 30 ? 'mid' : 'bad';
    return `<div class="debate-pick">
      <strong>${escapeHtml(pick.name || pick.symbol)}</strong>
      <span class="debate-pick__score ${scoreClass}">${fmtNum(pick.preset_score, 1)}</span>
      <small style="color:var(--muted)">${escapeHtml(pick.sector || '')}</small>
    </div>`;
  }).join('');

  const analysisHtml = analysisLines.map((line) => `<p class="debate-card__body">${line}</p>`).join('');

  return `<article class="debate-card">
    <div class="debate-card__header">
      <h3 class="debate-card__name">${escapeHtml(profile.name)}</h3>
      <span class="debate-card__style">${escapeHtml(profile.style)}</span>
    </div>
    <div class="debate-card__section">
      <p class="debate-card__section-title">${escapeHtml(txt({ ko: '시장 진단', en: 'Market Diagnosis' }))}</p>
      ${analysisHtml || `<p class="debate-card__body" style="color:var(--muted)">${escapeHtml(txt({ ko: '데이터 부족', en: 'Insufficient data' }))}</p>`}
    </div>
    <div class="debate-card__section">
      <p class="debate-card__section-title">${escapeHtml(txt({ ko: 'Top 2 Picks', en: 'Top 2 Picks' }))}</p>
      ${picksHtml || `<p class="debate-card__body" style="color:var(--muted)">-</p>`}
    </div>
    <div class="debate-card__section">
      <p class="debate-card__section-title">${escapeHtml(txt({ ko: '주요 리스크', en: 'Key Risk' }))}</p>
      <div class="debate-risk">${escapeHtml(riskText)}</div>
    </div>
  </article>`;
}

function renderConsensus(consensus) {
  const body = $('consensusBody');
  if (!body) return;

  const items = [];

  for (const entry of consensus.sectorConsensus.slice(0, 5)) {
    items.push(`<div class="consensus-item">
      <strong>${escapeHtml(txt({ ko: '섹터', en: 'Sector' }))}: ${escapeHtml(entry.name)}</strong>
      &mdash; ${escapeHtml(txt({ ko: `${entry.traders.length}명 동의`, en: `${entry.traders.length} agree` }))}
      <small style="color:var(--muted);margin-left:8px">(${escapeHtml(entry.traders.join(', '))})</small>
    </div>`);
  }

  for (const entry of consensus.stockConsensus.slice(0, 5)) {
    items.push(`<div class="consensus-item">
      <strong>${escapeHtml(txt({ ko: '종목', en: 'Stock' }))}: ${escapeHtml(entry.item.name || entry.item.symbol)}</strong>
      &mdash; ${escapeHtml(txt({ ko: `${entry.traders.length}명 선택`, en: `${entry.traders.length} picked` }))}
      <small style="color:var(--muted);margin-left:8px">(${escapeHtml(entry.traders.join(', '))})</small>
    </div>`);
  }

  if (items.length === 0) {
    items.push(`<div class="consensus-item" style="color:var(--muted)">
      ${escapeHtml(txt({ ko: '2명 이상이 동의하는 항목이 없습니다.', en: 'No items with 2+ trader agreement.' }))}
    </div>`);
  }

  body.innerHTML = items.join('');
}

function renderDisagreements(disagreements) {
  const body = $('disagreementBody');
  if (!body) return;

  if (disagreements.length === 0) {
    body.innerHTML = `<div class="disagreement-item" style="color:var(--muted)">
      ${escapeHtml(txt({ ko: '뚜렷한 의견 분쟁이 없습니다.', en: 'No clear disagreements found.' }))}
    </div>`;
    return;
  }

  body.innerHTML = disagreements.map((d) => `<div class="disagreement-item">
    <strong>${escapeHtml(d.item.name || d.item.symbol)}</strong>
    <span style="color:#4ade80;margin:0 6px">${escapeHtml(txt({ ko: '강세', en: 'Bullish' }))}: ${escapeHtml(d.bullish.join(', '))}</span>
    <span style="color:#f87171">${escapeHtml(txt({ ko: '미포함', en: 'Absent' }))}: ${escapeHtml(d.absent.join(', '))}</span>
  </div>`).join('');
}

function renderAllocation(allocation) {
  const body = $('conclusionBody');
  if (!body) return;

  if (allocation.length === 0) {
    body.innerHTML = `<p style="color:var(--muted);padding:12px">${escapeHtml(txt({ ko: '배분 데이터가 없습니다.', en: 'No allocation data.' }))}</p>`;
    return;
  }

  const maxWeight = Math.max(...allocation.map((a) => a.weight), 1);

  body.innerHTML = `<table class="allocation-table">
    <thead>
      <tr>
        <th>#</th>
        <th>${escapeHtml(txt({ ko: '종목', en: 'Stock' }))}</th>
        <th>${escapeHtml(txt({ ko: '섹터', en: 'Sector' }))}</th>
        <th>${escapeHtml(txt({ ko: '지지 트레이더', en: 'Endorsing Traders' }))}</th>
        <th>${escapeHtml(txt({ ko: '배분 비중', en: 'Weight' }))}</th>
        <th style="width:20%"></th>
      </tr>
    </thead>
    <tbody>
      ${allocation.map((a, i) => `<tr>
        <td>${i + 1}</td>
        <td><strong>${escapeHtml(a.item.name || a.item.symbol)}</strong><br><small style="color:var(--muted)">${escapeHtml(a.item.symbol)}</small></td>
        <td>${escapeHtml(a.item.sector || '-')}</td>
        <td>${escapeHtml(a.traders.join(', '))}</td>
        <td>${fmtNum(a.weight, 1)}%</td>
        <td><div class="allocation-bar" style="width:${(a.weight / maxWeight * 100).toFixed(0)}%"></div></td>
      </tr>`).join('')}
    </tbody>
  </table>`;
}

/* ── Data loading and init ── */

async function loadAndRender() {
  const meta = $('debateMeta');
  const dateEl = $('debateDate');
  const grid = $('debateGrid');

  try {
    // Try loading pre-generated debate JSON first (from LLM or generate_debate.py)
    let preGenerated = null;
    try {
      const debateResp = await fetchJSON(`${DEFAULT_API_BASE}/api/trader-debate`);
      if (debateResp.available && debateResp.items) {
        preGenerated = debateResp.items;
      }
    } catch (_) { /* fallback to live computation */ }

    if (preGenerated) {
      // Use pre-generated debate (LLM or rule-based from generate_debate.py)
      const d = preGenerated;
      const dateDir = d.date || '';
      const source = d.source === 'rule-based'
        ? txt({ ko: '규칙 기반', en: 'Rule-based' })
        : txt({ ko: 'LLM 생성', en: 'LLM-generated' });

      if (dateEl) dateEl.textContent = dateDir ? fmtDate(dateDir) : '';
      if (meta) meta.textContent = txt({
        ko: `기준일 ${fmtDate(dateDir)} | 트레이더 ${(d.traders || []).length}명 | ${source}`,
        en: `Base date ${fmtDate(dateDir)} | ${(d.traders || []).length} traders | ${source}`,
      });

      // Render from saved data
      if (grid) grid.innerHTML = (d.traders || []).map((t) => renderSavedDebateCard(t)).join('');
      renderSavedConsensus(d.consensus || []);
      renderSavedDisagreements(d.disagreements || []);
      renderSavedAllocation(d.allocation || [], d.risk_rules || [], d.moderator_comment || '');
      return;
    }

    // Fallback: compute live from API data
    const [sectors, stocks, recommendations] = await Promise.all([
      fetchJSON(`${DEFAULT_API_BASE}/api/leaders/sectors`),
      fetchJSON(`${DEFAULT_API_BASE}/api/leaders/stocks`),
      fetchJSON(`${DEFAULT_API_BASE}/api/recommendations/latest`),
    ]);

    const sectorItems = sectors.items || [];
    const stockItems = stocks.items || [];
    const recItems = recommendations.items || [];
    const recMap = new Map(recItems.map((item) => [item.symbol, item]));
    const dateDir = sectors.date_dir || stocks.date_dir || '';

    if (dateEl) dateEl.textContent = dateDir ? fmtDate(dateDir) : '';
    if (meta) meta.textContent = txt({
      ko: `기준일 ${fmtDate(dateDir)} | 섹터 ${sectorItems.length}개 | 종목 ${stockItems.length}개 | 트레이더 6명 | 실시간 계산`,
      en: `Base date ${fmtDate(dateDir)} | ${sectorItems.length} sectors | ${stockItems.length} stocks | 6 traders | Live`,
    });

    // Run analysis for each of the 6 anchor traders
    const analyses = traderProfiles.map((profile) =>
      analyzeTrader(profile, sectorItems, stockItems, recMap)
    );

    // Render debate cards
    if (grid) grid.innerHTML = analyses.map((a) => renderDebateCard(a)).join('');

    // Build and render consensus
    const consensus = buildConsensus(analyses);
    renderConsensus(consensus);

    // Build and render disagreements
    const disagreements = buildDisagreements(analyses);
    renderDisagreements(disagreements);

    // Build and render allocation
    const allocation = buildAllocation(analyses);
    renderAllocation(allocation);

  } catch (error) {
    console.error('Trader debate load error:', error);
    if (meta) meta.textContent = txt({
      ko: `데이터 로딩 실패: ${String(error)}`,
      en: `Data load failed: ${String(error)}`,
    });
    if (grid) grid.innerHTML = `<div class="debate-loading" style="color:#f87171">
      ${escapeHtml(txt({ ko: '데이터를 불러오지 못했습니다.', en: 'Failed to load data.' }))}
      <br><small style="color:var(--muted)">API: ${escapeHtml(DEFAULT_API_BASE)}</small>
      <br><small style="color:var(--muted)">${escapeHtml(String(error))}</small>
    </div>`;
  }
}

/* ── Renderers for pre-generated (saved) debate JSON ── */

function renderSavedDebateCard(t) {
  const picks = (t.picks || []).map((p) => `
    <div class="debate-pick">
      <strong>${escapeHtml(p.name || p.symbol)}</strong>
      <small>${escapeHtml(p.symbol || '')}</small>
      <span class="debate-pick-reason">${escapeHtml(p.reason || '')}</span>
    </div>
  `).join('');

  return `
    <article class="debate-card panel">
      <div class="debate-card-head">
        <h3>${escapeHtml(t.name || t.name_en)}</h3>
        <span class="debate-style-tag">${escapeHtml(t.style || '')}</span>
      </div>
      <div class="debate-diagnosis">
        <label>${escapeHtml(txt({ ko: '시장 진단', en: 'Diagnosis' }))}</label>
        <p>${escapeHtml(t.diagnosis || '')}</p>
      </div>
      <div class="debate-picks">
        <label>${escapeHtml(txt({ ko: '종목 선택', en: 'Picks' }))}</label>
        ${picks || '<p class="muted">-</p>'}
      </div>
      <div class="debate-risk">
        <label>${escapeHtml(txt({ ko: '주요 리스크', en: 'Key Risk' }))}</label>
        <p>${escapeHtml(t.risk || '')}</p>
      </div>
    </article>
  `;
}

function renderSavedConsensus(items) {
  const el = $('consensusBody');
  if (!el) return;
  el.innerHTML = items.map((c) => `
    <div class="consensus-item">
      <strong>${escapeHtml(c.topic)}</strong>
      <span>${escapeHtml(c.detail)}</span>
      <small>${c.supporters || 0}${escapeHtml(txt({ ko: '인 동의', en: ' agree' }))}</small>
    </div>
  `).join('') || `<p class="muted">${escapeHtml(txt({ ko: '합의 없음', en: 'No consensus' }))}</p>`;
}

function renderSavedDisagreements(items) {
  const el = $('disagreementBody');
  if (!el) return;
  el.innerHTML = items.map((d) => `
    <div class="disagreement-item">
      <strong>${escapeHtml(d.topic)}</strong>
      <div class="disagreement-sides">
        <span class="bull">${escapeHtml(txt({ ko: '찬성', en: 'Bull' }))}: ${escapeHtml((d.bull || []).join(', '))}</span>
        <span class="bear">${escapeHtml(txt({ ko: '반대', en: 'Bear' }))}: ${escapeHtml((d.bear || []).join(', '))}</span>
      </div>
      <small>${escapeHtml(d.detail || '')}</small>
    </div>
  `).join('') || `<p class="muted">${escapeHtml(txt({ ko: '분쟁 없음', en: 'No disagreements' }))}</p>`;
}

function renderSavedAllocation(items, riskRules, comment) {
  const el = $('conclusionBody');
  if (!el) return;

  const rows = items.map((a) => `
    <tr>
      <td>${a.priority || ''}</td>
      <td><strong>${escapeHtml(a.name || a.symbol)}</strong><br><small>${escapeHtml(a.symbol || '')}</small></td>
      <td>${escapeHtml(a.weight || '')}</td>
      <td>${escapeHtml(a.reason || '')}</td>
    </tr>
  `).join('');

  const rulesHtml = riskRules.length ? `<ul style="margin-top:12px;padding-left:20px">${riskRules.map((r) => `<li style="margin:4px 0;color:var(--text)">${escapeHtml(r)}</li>`).join('')}</ul>` : '';
  const commentHtml = comment ? `<p style="margin-top:16px;padding:12px;border-left:3px solid var(--accent);color:var(--muted);font-style:italic">${escapeHtml(comment)}</p>` : '';

  el.innerHTML = `
    <table class="allocation-table">
      <thead><tr><th>#</th><th>${escapeHtml(txt({ ko: '종목', en: 'Stock' }))}</th><th>${escapeHtml(txt({ ko: '비중', en: 'Weight' }))}</th><th>${escapeHtml(txt({ ko: '근거', en: 'Reason' }))}</th></tr></thead>
      <tbody>${rows || `<tr><td colspan="4">${escapeHtml(txt({ ko: '배분 데이터 없음', en: 'No allocation' }))}</td></tr>`}</tbody>
    </table>
    <h3 style="margin-top:20px">${escapeHtml(txt({ ko: '리스크 규칙', en: 'Risk Rules' }))}</h3>
    ${rulesHtml}
    ${commentHtml}
  `;
}

function init() {
  setupPageI18n('trader-debate', () => loadAndRender());
  loadAndRender();
}

init();
