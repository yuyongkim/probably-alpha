import {
  $,
  escapeHtml,
  fmtCompact,
  fmtDate,
  fmtDateAxis,
  fmtNum,
  fmtQuarter,
  state,
} from './core.js?v=1775488167';
import { txt } from './i18n.js?v=1775488167';

const MAIN_CHART_PAD = { top: 24, right: 128, bottom: 56, left: 60 };
const EPS_CHART_PAD = { top: 48, right: 24, bottom: 70, left: 60 };

function numericSeries(values = []) {
  return values.map((value) => {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
  });
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function chartBox(id, fallbackWidth = 640, fallbackHeight = 260, pad = { top: 18, right: 20, bottom: 34, left: 56 }) {
  const node = $(id);
  if (!node) return null;
  const width = Math.max(320, Math.floor(node.clientWidth || fallbackWidth));
  const height = Number(node.dataset.height || fallbackHeight);
  return {
    node,
    width,
    height,
    plotLeft: pad.left,
    plotTop: pad.top,
    plotWidth: width - pad.left - pad.right,
    plotHeight: height - pad.top - pad.bottom,
  };
}

function linePath(points) {
  if (!points.length) return '';
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ');
}

function areaPath(points, baseY) {
  if (!points.length) return '';
  return `${linePath(points)} L ${points.at(-1).x.toFixed(2)} ${baseY.toFixed(2)} L ${points[0].x.toFixed(2)} ${baseY.toFixed(2)} Z`;
}

function pointX(index, box, length) {
  return box.plotLeft + (index * box.plotWidth) / Math.max(1, length - 1);
}

function pickTickIndexes(length, maxTicks = 6) {
  if (length <= 0) return [];
  if (length === 1) return [0];
  const indexes = new Set([0, length - 1]);
  const step = (length - 1) / Math.max(1, maxTicks - 1);
  for (let index = 1; index < maxTicks - 1; index += 1) {
    indexes.add(Math.round(index * step));
  }
  return [...indexes].sort((a, b) => a - b);
}

function niceTicks(min, max, count = 5) {
  const safeMin = Number.isFinite(min) ? min : 0;
  const safeMax = Number.isFinite(max) ? max : 1;
  if (safeMin === safeMax) {
    const pad = Math.abs(safeMin || 1) * 0.1;
    return [safeMin - pad, safeMin, safeMin + pad];
  }
  const range = safeMax - safeMin;
  const rough = range / Math.max(1, count - 1);
  const magnitude = 10 ** Math.floor(Math.log10(Math.abs(rough)));
  const residual = rough / magnitude;
  let niceResidual = 1;
  if (residual >= 5) niceResidual = 5;
  else if (residual >= 2) niceResidual = 2;
  const step = niceResidual * magnitude;
  const niceMin = Math.floor(safeMin / step) * step;
  const niceMax = Math.ceil(safeMax / step) * step;
  const ticks = [];
  for (let value = niceMin; value <= niceMax + step * 0.5; value += step) {
    ticks.push(Number(value.toFixed(6)));
  }
  return ticks;
}

function seriesBounds(seriesList, includeZero = false) {
  const values = seriesList.flat().filter((value) => Number.isFinite(value));
  if (!values.length) return { min: 0, max: 1 };
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (includeZero) {
    min = Math.min(min, 0);
    max = Math.max(max, 0);
  }
  if (min === max) {
    const pad = Math.abs(min || 1) * 0.08;
    min -= pad;
    max += pad;
  }
  const pad = (max - min) * 0.08;
  return { min: min - pad, max: max + pad };
}

function buildLinePoints(values, box, min, max) {
  const safeValues = numericSeries(values);
  const span = max - min || 1;
  return safeValues
    .map((value, index) => {
      if (!Number.isFinite(value)) return null;
      const x = pointX(index, box, safeValues.length);
      const y = box.plotTop + ((max - value) / span) * box.plotHeight;
      return { x, y, value, index };
    })
    .filter(Boolean);
}

function valuePointAtIndex(values, index, box, min, max) {
  const safeValues = numericSeries(values);
  const value = safeValues[index];
  if (!Number.isFinite(value)) return null;
  const span = max - min || 1;
  const x = pointX(index, box, safeValues.length);
  const y = box.plotTop + ((max - value) / span) * box.plotHeight;
  return { x, y, value, index };
}

function alignSeries(targetDates, sourceValues = [], sourceDates = []) {
  const values = numericSeries(sourceValues);
  if (!targetDates.length) return [];
  if (!sourceDates.length) {
    if (values.length >= targetDates.length) return values.slice(values.length - targetDates.length);
    return Array(targetDates.length - values.length).fill(null).concat(values);
  }

  const map = new Map();
  sourceDates.forEach((date, index) => {
    const value = Number(sourceValues[index]);
    map.set(String(date), Number.isFinite(value) ? value : null);
  });
  return targetDates.map((date) => {
    const value = map.get(String(date));
    return Number.isFinite(value) ? value : null;
  });
}

function emptyChart(node, width, height, message) {
  node.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(message)}">
    <rect x="0" y="0" width="${width}" height="${height}" rx="20" fill="#061120" />
    <text x="${width / 2}" y="${height / 2}" text-anchor="middle" fill="#87a0bb" font-size="15">${escapeHtml(message)}</text>
  </svg>`;
}

function makePanel(box, top, height) {
  return {
    plotLeft: box.plotLeft,
    plotTop: top,
    plotWidth: box.plotWidth,
    plotHeight: height,
  };
}

function panelGuides(panel, ticks, min, max, formatter, options = {}) {
  const {
    axisSide = 'right',
    stroke = 'rgba(116, 147, 181, 0.12)',
    labelFill = '#7f96af',
  } = options;
  const span = max - min || 1;
  return ticks.map((tick) => {
    const y = panel.plotTop + ((max - tick) / span) * panel.plotHeight;
    const axisX = axisSide === 'right' ? panel.plotLeft + panel.plotWidth + 12 : panel.plotLeft - 10;
    const anchor = axisSide === 'right' ? 'start' : 'end';
    return `
      <line x1="${panel.plotLeft}" y1="${y.toFixed(2)}" x2="${(panel.plotLeft + panel.plotWidth).toFixed(2)}" y2="${y.toFixed(2)}" stroke="${stroke}" stroke-width="1" />
      <text x="${axisX.toFixed(2)}" y="${(y + 4).toFixed(2)}" text-anchor="${anchor}" fill="${labelFill}" font-size="11">${escapeHtml(formatter(tick))}</text>
    `;
  }).join('');
}

function sharedVerticalGuides(box, top, bottom, labels) {
  const indexes = pickTickIndexes(labels.length, 7);
  const lines = indexes.map((index) => {
    const x = pointX(index, box, labels.length);
    return `<line x1="${x.toFixed(2)}" y1="${top.toFixed(2)}" x2="${x.toFixed(2)}" y2="${bottom.toFixed(2)}" stroke="rgba(116, 147, 181, 0.1)" stroke-width="1" />`;
  }).join('');
  const axisLabels = indexes.map((index, position) => {
    const x = pointX(index, box, labels.length);
    const previous = position > 0 ? labels[indexes[position - 1]] : '';
    const forceYear = position === 0 || position === indexes.length - 1;
    return `<text x="${x.toFixed(2)}" y="${(box.height - 12).toFixed(2)}" text-anchor="middle" fill="#7f96af" font-size="11">${escapeHtml(fmtDateAxis(labels[index], previous, forceYear))}</text>`;
  }).join('');
  return { lines, axisLabels };
}

function pill(text, xRight, y, accent = '#80d0ff') {
  const width = Math.max(80, text.length * 7 + 18);
  const height = 24;
  const top = y - height / 2;
  return `
    <g>
      <rect x="${(xRight - width).toFixed(2)}" y="${top.toFixed(2)}" width="${width.toFixed(2)}" height="${height}" rx="12" fill="rgba(11, 23, 38, 0.92)" stroke="${accent}" stroke-width="1" />
      <text x="${(xRight - width / 2).toFixed(2)}" y="${(y + 4).toFixed(2)}" text-anchor="middle" fill="#eef6ff" font-size="11">${escapeHtml(text)}</text>
    </g>
  `;
}

function panelTitle(panel, title, subtitle) {
  return `
    <text x="${(panel.plotLeft + 10).toFixed(2)}" y="${(panel.plotTop + 16).toFixed(2)}" fill="#d7e6f8" font-size="12" font-weight="700">${escapeHtml(title)}</text>
    <text x="${(panel.plotLeft + 10).toFixed(2)}" y="${(panel.plotTop + 32).toFixed(2)}" fill="#7f96af" font-size="11">${escapeHtml(subtitle)}</text>
  `;
}

function fmtWhole(value, digits = 0) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return num.toLocaleString('ko-KR', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatSigned(value, digits = 1) {
  const num = Number(value);
  if (!Number.isFinite(num)) return '-';
  return `${num >= 0 ? '+' : ''}${num.toFixed(digits)}%`;
}

function tooltipBox(lines, x, y, bounds, accent = '#80d0ff') {
  const safeLines = lines.filter(Boolean);
  const width = Math.max(136, ...safeLines.map((line) => line.length * 7 + 24));
  const height = safeLines.length * 16 + 16;
  const left = clamp(x, bounds.left, bounds.right - width);
  const top = clamp(y, bounds.top, bounds.bottom - height);
  const text = safeLines.map((line, index) => `
    <text x="${(left + 12).toFixed(2)}" y="${(top + 18 + index * 16).toFixed(2)}" fill="#eef6ff" font-size="11">${escapeHtml(line)}</text>
  `).join('');
  return `
    <g>
      <rect x="${left.toFixed(2)}" y="${top.toFixed(2)}" width="${width.toFixed(2)}" height="${height.toFixed(2)}" rx="14" fill="rgba(7, 17, 29, 0.94)" stroke="${accent}" stroke-width="1" />
      ${text}
    </g>
  `;
}

function yearToken(value) {
  const raw = String(value || '').trim();
  return /^\d{4}Q[1-4]$/.test(raw) ? raw.slice(0, 4) : '';
}

function quarterToken(value) {
  const raw = String(value || '').trim();
  return /^\d{4}Q[1-4]$/.test(raw) ? `Q${raw.slice(-1)}` : raw;
}

export function getEpsViewport(analysis) {
  // Only show quarterly EPS (period like "2024Q1"), exclude annual (period like "2024")
  const allRows = (analysis?.eps_series || []).filter((r) => /Q\d$/.test(r.period || ''));
  const total = allRows.length;
  const requested = Math.max(8, Math.round(Number(state.epsWindowQuarters || 16)));
  if (!total) {
    return {
      rows: [],
      total: 0,
      windowSize: requested,
      start: 0,
      end: 0,
      maxStart: 0,
    };
  }

  const windowSize = Math.min(total, requested);
  const maxStart = Math.max(0, total - windowSize);
  const rawStart = state.epsWindowStart == null ? maxStart : Number(state.epsWindowStart);
  const start = Number.isFinite(rawStart) ? clamp(Math.round(rawStart), 0, maxStart) : maxStart;
  const end = start + windowSize;

  return {
    rows: allRows.slice(start, end),
    total,
    windowSize,
    start,
    end,
    maxStart,
  };
}

export function getAnalysisViewport(analysis) {
  const allRows = analysis?.close_series || [];
  const total = allRows.length;
  if (!total) {
    return {
      rows: [],
      total: 0,
      windowSize: 0,
      panOffset: 0,
      maxOffset: 0,
      start: 0,
      end: 0,
    };
  }

  const requested = Number(state.analysisWindowDays || 0);
  const windowSize = requested > 0 ? clamp(Math.round(requested), 20, total) : total;
  const maxOffset = Math.max(0, total - windowSize);
  const panOffset = clamp(Math.round(Number(state.analysisPanOffset || 0)), 0, maxOffset);
  const end = total - panOffset;
  const start = Math.max(0, end - windowSize);

  return {
    rows: allRows.slice(start, end),
    total,
    windowSize,
    panOffset,
    maxOffset,
    start,
    end,
  };
}

export function mainChartIndexFromClientX(node, clientX, pointCount) {
  if (!node || pointCount <= 0) return 0;
  const rect = node.getBoundingClientRect();
  const width = Math.max(320, Math.floor(node.clientWidth || rect.width || 1280));
  const plotWidth = width - MAIN_CHART_PAD.left - MAIN_CHART_PAD.right;
  const x = clamp(clientX - rect.left - MAIN_CHART_PAD.left, 0, plotWidth);
  return Math.round((x / Math.max(1, plotWidth)) * Math.max(1, pointCount - 1));
}

function syncEpsRangeControls(viewport) {
  const range = $('epsRangeBar');
  const windowLabel = $('epsRangeWindow');
  const boundsLabel = $('epsRangeBounds');
  const shell = range?.closest('.eps-range-shell');
  if (!range || !windowLabel || !boundsLabel || !shell) return;

  const disabled = viewport.total <= viewport.windowSize;
  const firstPeriod = viewport.rows[0]?.period || '';
  const lastPeriod = viewport.rows.at(-1)?.period || '';

  range.min = '0';
  range.max = String(viewport.maxStart);
  range.step = '1';
  range.value = String(viewport.start);
  range.disabled = disabled;
  shell.classList.toggle('is-disabled', disabled);

  if (!viewport.total) {
    windowLabel.textContent = txt({ ko: 'EPS 데이터 없음', en: 'No EPS data' });
    boundsLabel.textContent = '-';
    return;
  }

  windowLabel.textContent = disabled
    ? txt({
      ko: `전체 ${viewport.total}개 분기 표시`,
      en: `Showing all ${viewport.total} quarters`,
    })
    : txt({
      ko: `${viewport.windowSize}개 분기 창 / 전체 ${viewport.total}개`,
      en: `${viewport.windowSize}-quarter window / ${viewport.total} total`,
    });
  boundsLabel.textContent = firstPeriod && lastPeriod ? `${firstPeriod} - ${lastPeriod}` : '-';
}

function renderCompositeChart(analysis) {
  const box = chartBox('mainChart', 1280, 1160, MAIN_CHART_PAD);
  if (!box) return;

  const viewport = getAnalysisViewport(analysis);
  const rows = viewport.rows;
  const labels = rows.map((row) => String(row.date || ''));
  const close = numericSeries(rows.map((row) => row.close));
  const volume = numericSeries(rows.map((row) => row.volume));
  if (labels.length < 2 || !close.some((value) => Number.isFinite(value))) {
    emptyChart(box.node, box.width, box.height, txt({ ko: '통합 차트 데이터가 없습니다.', en: 'Integrated chart data is not available.' }));
    return;
  }

  const indicators = analysis?.indicators || {};
  const sma20 = alignSeries(labels, indicators.sma20 || []);
  const sma50 = alignSeries(labels, indicators.sma50 || []);
  const sma150 = alignSeries(labels, indicators.sma150 || []);
  const sma200 = alignSeries(labels, indicators.sma200 || []);
  const lrLine = alignSeries(labels, indicators.least_resistance_line || []);
  const volumeMa20 = alignSeries(labels, indicators.volume_ma20 || []);
  const rs = analysis?.relative_strength || {};
  const sectorStrength = analysis?.sector_strength || {};
  const rsLine = alignSeries(labels, rs.line || []);
  const rsMa20 = alignSeries(labels, rs.ma20_line || []);
  const sectorRs = alignSeries(labels, sectorStrength.rs_line || [], sectorStrength.dates || []);
  const macd = analysis?.indicators?.macd_20_60 || {};
  const macdLine = alignSeries(labels, macd.line || []);
  const signalLine = alignSeries(labels, macd.signal || []);
  const histogram = alignSeries(labels, macd.histogram || []);

  const gap = 18;
  const availableHeight = box.plotHeight - gap * 3;
  const priceHeight = availableHeight * 0.60;
  const volumeHeight = availableHeight * 0.14;
  const rsHeight = availableHeight * 0.13;
  const macdHeight = availableHeight * 0.13;

  const pricePanel = makePanel(box, box.plotTop, priceHeight);
  const volumePanel = makePanel(box, pricePanel.plotTop + pricePanel.plotHeight + gap, volumeHeight);
  const rsPanel = makePanel(box, volumePanel.plotTop + volumePanel.plotHeight + gap, rsHeight);
  const macdPanel = makePanel(box, rsPanel.plotTop + rsPanel.plotHeight + gap, macdHeight);

  const priceBounds = seriesBounds([close, sma20, sma50, sma150, sma200, lrLine], false);
  const priceTicks = niceTicks(priceBounds.min, priceBounds.max, 6);
  const priceMin = priceTicks[0];
  const priceMax = priceTicks.at(-1);
  const pricePoints = buildLinePoints(close, pricePanel, priceMin, priceMax);
  const sma20Points = buildLinePoints(sma20, pricePanel, priceMin, priceMax);
  const sma50Points = buildLinePoints(sma50, pricePanel, priceMin, priceMax);
  const sma150Points = buildLinePoints(sma150, pricePanel, priceMin, priceMax);
  const sma200Points = buildLinePoints(sma200, pricePanel, priceMin, priceMax);
  const lrPoints = buildLinePoints(lrLine, pricePanel, priceMin, priceMax);

  const volumeBounds = seriesBounds([volume, volumeMa20], true);
  volumeBounds.min = 0;
  const volumeTicks = niceTicks(volumeBounds.min, volumeBounds.max, 4);
  const volumeMin = 0;
  const volumeMax = volumeTicks.at(-1);
  const volumeSpan = volumeMax - volumeMin || 1;
  const volumeMaPoints = buildLinePoints(volumeMa20, volumePanel, volumeMin, volumeMax);
  const volumeBarWidth = Math.max(2, (volumePanel.plotWidth / Math.max(1, volume.length)) * 0.66);

  const high120 = Number.isFinite(Number(rs.high120)) ? Number(rs.high120) : null;
  const rsBounds = seriesBounds([rsLine, rsMa20, sectorRs, high120 == null ? [] : [high120]], false);
  const rsTicks = niceTicks(rsBounds.min, rsBounds.max, 5);
  const rsMin = rsTicks[0];
  const rsMax = rsTicks.at(-1);
  const rsSpan = rsMax - rsMin || 1;
  const rsPoints = buildLinePoints(rsLine, rsPanel, rsMin, rsMax);
  const rsMaPoints = buildLinePoints(rsMa20, rsPanel, rsMin, rsMax);
  const sectorPoints = buildLinePoints(sectorRs, rsPanel, rsMin, rsMax);
  const rsHighY = high120 == null ? null : rsPanel.plotTop + ((rsMax - high120) / rsSpan) * rsPanel.plotHeight;

  const macdBounds = seriesBounds([macdLine, signalLine, histogram], true);
  const macdTicks = niceTicks(macdBounds.min, macdBounds.max, 5);
  const macdMin = macdTicks[0];
  const macdMax = macdTicks.at(-1);
  const macdSpan = macdMax - macdMin || 1;
  const macdZeroY = macdPanel.plotTop + ((macdMax - 0) / macdSpan) * macdPanel.plotHeight;
  const macdLinePoints = buildLinePoints(macdLine, macdPanel, macdMin, macdMax);
  const signalPoints = buildLinePoints(signalLine, macdPanel, macdMin, macdMax);
  const histogramBarWidth = Math.max(2, (macdPanel.plotWidth / Math.max(1, histogram.length)) * 0.54);

  const hoverIndex = clamp(
    Number.isInteger(state.analysisHoverIndex) ? state.analysisHoverIndex : labels.length - 1,
    0,
    labels.length - 1,
  );
  const hoverDate = labels[hoverIndex];
  const hoverX = pointX(hoverIndex, pricePanel, labels.length);
  const hoverPricePoint = valuePointAtIndex(close, hoverIndex, pricePanel, priceMin, priceMax);
  const hoverVolumePoint = valuePointAtIndex(volume, hoverIndex, volumePanel, volumeMin, volumeMax);
  const hoverRsPoint = valuePointAtIndex(rsLine, hoverIndex, rsPanel, rsMin, rsMax);
  const hoverMacdPoint = valuePointAtIndex(macdLine, hoverIndex, macdPanel, macdMin, macdMax);
  const hoverVolumeValue = Number(volume[hoverIndex]);
  const hoverVolumeMa = Number(volumeMa20[hoverIndex]);
  const hoverVolumeRatio = hoverVolumeMa > 0 ? hoverVolumeValue / hoverVolumeMa : null;
  const hoverRsValue = Number(rsLine[hoverIndex]);
  const hoverRsMa = Number(rsMa20[hoverIndex]);
  const hoverSectorRsValue = Number(sectorRs[hoverIndex]);
  const hoverSectorRs = Number.NaN;
  const hoverMacdValue = Number(macdLine[hoverIndex]);
  const hoverSignalValue = Number(signalLine[hoverIndex]);
  const hoverHistValue = Number(histogram[hoverIndex]);
  const rightRailX = box.plotLeft + box.plotWidth + 8;
  const rightRailWidth = Math.max(74, box.width - rightRailX - 10);

  const sharedGuides = sharedVerticalGuides(box, pricePanel.plotTop, macdPanel.plotTop + macdPanel.plotHeight, labels);
  const gradientId = `main-price-gradient-${(analysis?.symbol || 'chart').replaceAll('.', '-')}`;
  const tooltipLines = [
      fmtDate(hoverDate),
      hoverPricePoint ? `${txt({ ko: '종가', en: 'Close' })} KRW ${fmtWhole(hoverPricePoint.value)}` : '',
      Number.isFinite(hoverVolumeValue)
        ? `${txt({ ko: '거래량', en: 'Volume' })} ${fmtCompact(hoverVolumeValue)}${Number.isFinite(hoverVolumeRatio) ? ` / ${fmtNum(hoverVolumeRatio, 2)}x` : ''}`
        : '',
      Number.isFinite(hoverRsValue)
        ? `${txt({ ko: 'R/S', en: 'R/S' })} ${fmtNum(hoverRsValue, 1)}${Number.isFinite(hoverRsMa) ? ` / MA20 ${fmtNum(hoverRsMa, 1)}` : ''}`
        : '',
      Number.isFinite(hoverSectorRsValue)
        ? `${txt({ ko: '섹터 R/S', en: 'Sector R/S' })} ${fmtNum(hoverSectorRsValue, 1)}`
        : '',
      Number.isFinite(hoverMacdValue)
        ? `MACD ${fmtNum(hoverMacdValue, 2)}${Number.isFinite(hoverSignalValue) ? ` / Sig ${fmtNum(hoverSignalValue, 2)}` : ''}${Number.isFinite(hoverHistValue) ? ` / Hist ${fmtNum(hoverHistValue, 2)}` : ''}`
        : '',
  ];
  const hoverTooltipY = Number.isFinite(Number(state.analysisHoverYRatio))
    ? Number(state.analysisHoverYRatio) * box.height
    : (hoverPricePoint?.y || pricePanel.plotTop + 32);
  const tooltip = tooltipBox(
    tooltipLines,
    hoverX < box.plotLeft + box.plotWidth * 0.55 ? hoverX + 20 : hoverX - 196,
    hoverTooltipY - 34,
    {
      left: pricePanel.plotLeft + 8,
      right: pricePanel.plotLeft + pricePanel.plotWidth - 8,
      top: pricePanel.plotTop + 8,
      bottom: macdPanel.plotTop + macdPanel.plotHeight - 8,
    },
  );

  const volumeBars = volume.map((value, index) => {
    if (!Number.isFinite(value)) return '';
    const x = pointX(index, volumePanel, volume.length) - volumeBarWidth / 2;
    const y = volumePanel.plotTop + ((volumeMax - value) / volumeSpan) * volumePanel.plotHeight;
    const previous = index > 0 ? Number(close[index - 1]) : Number(close[index]);
    const current = Number(close[index]);
    const ratio = Number(volumeMa20[index]) > 0 ? value / Number(volumeMa20[index]) : null;
    let fill = current >= previous ? 'rgba(138, 240, 184, 0.44)' : 'rgba(255, 158, 158, 0.34)';
    if (Number.isFinite(ratio) && ratio >= 1.5) fill = 'rgba(87, 180, 255, 0.62)';
    return `<rect x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${volumeBarWidth.toFixed(2)}" height="${Math.max(1, volumePanel.plotTop + volumePanel.plotHeight - y).toFixed(2)}" rx="2" fill="${fill}" />`;
  }).join('');

  const macdBars = histogram.map((value, index) => {
    if (!Number.isFinite(value)) return '';
    const x = pointX(index, macdPanel, histogram.length) - histogramBarWidth / 2;
    const y = macdPanel.plotTop + ((macdMax - value) / macdSpan) * macdPanel.plotHeight;
    const fill = value >= 0 ? 'rgba(138, 240, 184, 0.52)' : 'rgba(255, 158, 158, 0.48)';
    return `<rect x="${x.toFixed(2)}" y="${Math.min(y, macdZeroY).toFixed(2)}" width="${histogramBarWidth.toFixed(2)}" height="${Math.max(1, Math.abs(macdZeroY - y)).toFixed(2)}" rx="2" fill="${fill}" />`;
  }).join('');

  const separatorLines = [
    volumePanel.plotTop - gap / 2,
    rsPanel.plotTop - gap / 2,
    macdPanel.plotTop - gap / 2,
  ].map((y) => `<line x1="${box.plotLeft}" y1="${y.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${y.toFixed(2)}" stroke="rgba(116, 147, 181, 0.16)" stroke-width="1" />`).join('');

  const panelFrames = [pricePanel, volumePanel, rsPanel, macdPanel].map((panel, index) => `
    <rect x="${panel.plotLeft}" y="${panel.plotTop}" width="${panel.plotWidth}" height="${panel.plotHeight}" rx="${index === 0 ? 18 : 12}" fill="rgba(5, 13, 24, ${index === 0 ? '0.58' : '0.40'})" />
  `).join('');
  const railFrames = [pricePanel, volumePanel, rsPanel, macdPanel].map((panel, index) => `
    <rect x="${rightRailX.toFixed(2)}" y="${panel.plotTop.toFixed(2)}" width="${rightRailWidth.toFixed(2)}" height="${panel.plotHeight.toFixed(2)}" rx="${index === 0 ? 16 : 10}" fill="rgba(7, 17, 29, 0.94)" stroke="rgba(92,133,171,0.14)" stroke-width="1" />
  `).join('');

  const priceRail = hoverPricePoint
    ? `<line x1="${hoverPricePoint.x.toFixed(2)}" y1="${hoverPricePoint.y.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${hoverPricePoint.y.toFixed(2)}" stroke="rgba(128,208,255,0.42)" stroke-width="1" stroke-dasharray="4 4" />`
    : '';
  const volumeRail = hoverVolumePoint
    ? `<line x1="${hoverVolumePoint.x.toFixed(2)}" y1="${hoverVolumePoint.y.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${hoverVolumePoint.y.toFixed(2)}" stroke="rgba(255,210,116,0.28)" stroke-width="1" stroke-dasharray="4 4" />`
    : '';
  const rsRail = hoverRsPoint
    ? `<line x1="${hoverRsPoint.x.toFixed(2)}" y1="${hoverRsPoint.y.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${hoverRsPoint.y.toFixed(2)}" stroke="rgba(87,180,255,0.34)" stroke-width="1" stroke-dasharray="4 4" />`
    : '';
  const macdRail = hoverMacdPoint
    ? `<line x1="${hoverMacdPoint.x.toFixed(2)}" y1="${hoverMacdPoint.y.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${hoverMacdPoint.y.toFixed(2)}" stroke="rgba(255,189,99,0.34)" stroke-width="1" stroke-dasharray="4 4" />`
    : '';

  box.node.innerHTML = `
    <svg viewBox="0 0 ${box.width} ${box.height}" role="img" aria-label="Integrated market chart">
      <defs>
        <linearGradient id="${gradientId}" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#57b4ff" stop-opacity="0.28" />
          <stop offset="100%" stop-color="#57b4ff" stop-opacity="0.02" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="${box.width}" height="${box.height}" rx="22" fill="#061120" />
      ${panelFrames}
      ${railFrames}
      ${sharedGuides.lines}
      ${separatorLines}
      <line x1="${hoverX.toFixed(2)}" y1="${pricePanel.plotTop.toFixed(2)}" x2="${hoverX.toFixed(2)}" y2="${(macdPanel.plotTop + macdPanel.plotHeight).toFixed(2)}" stroke="rgba(220,235,255,0.18)" stroke-width="1" stroke-dasharray="3 6" />

      ${panelGuides(pricePanel, priceTicks, priceMin, priceMax, (tick) => fmtWhole(tick))}
      ${panelGuides(volumePanel, volumeTicks, volumeMin, volumeMax, (tick) => fmtCompact(tick))}
      ${panelGuides(rsPanel, rsTicks, rsMin, rsMax, (tick) => fmtNum(tick, 1))}
      ${panelGuides(macdPanel, macdTicks, macdMin, macdMax, (tick) => fmtNum(tick, 2))}

      ${panelTitle(pricePanel, txt({ ko: '가격', en: 'PRICE' }), txt({ ko: '종가 / SMA20 / SMA50 / SMA150 / SMA200 / 저항선', en: 'Close / SMA20 / SMA50 / SMA150 / SMA200 / Resistance' }))}
      ${panelTitle(volumePanel, txt({ ko: '거래량', en: 'VOLUME' }), txt({ ko: '일봉 막대 / 20일 평균', en: 'Daily bars / 20D average' }))}
      ${panelTitle(rsPanel, txt({ ko: `${rs.benchmark_label || '-'} 대비 R/S`, en: `R/S vs ${rs.benchmark_label || '-'}` }), txt({ ko: '종목 / MA20 / 섹터 / 120일 고점', en: 'Stock / MA20 / Sector / 120D high' }))}
      ${panelTitle(macdPanel, txt({ ko: 'MACD 20,60', en: 'MACD 20,60' }), txt({ ko: '라인 / 시그널 / 히스토그램', en: 'Line / Signal / Histogram' }))}

      <path d="${areaPath(pricePoints, pricePanel.plotTop + pricePanel.plotHeight)}" fill="url(#${gradientId})" />
      ${lrPoints.length ? `<path d="${linePath(lrPoints)}" fill="none" stroke="#dbe7ff" stroke-width="1.4" stroke-dasharray="7 6" />` : ''}
      ${sma200Points.length ? `<path d="${linePath(sma200Points)}" fill="none" stroke="#ff9b92" stroke-width="1.5" />` : ''}
      ${sma150Points.length ? `<path d="${linePath(sma150Points)}" fill="none" stroke="#ffbf63" stroke-width="1.5" />` : ''}
      ${sma50Points.length ? `<path d="${linePath(sma50Points)}" fill="none" stroke="#98f1b7" stroke-width="1.6" />` : ''}
      ${sma20Points.length ? `<path d="${linePath(sma20Points)}" fill="none" stroke="#9fd3ff" stroke-width="1.2" stroke-dasharray="4 4" />` : ''}
      <path d="${linePath(pricePoints)}" fill="none" stroke="#80d0ff" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round" />
      ${hoverPricePoint ? `<circle cx="${hoverPricePoint.x.toFixed(2)}" cy="${hoverPricePoint.y.toFixed(2)}" r="4.5" fill="#80d0ff" stroke="#061120" stroke-width="2" />` : ''}
      ${priceRail}
      ${tooltip}

      ${volumeBars}
      ${volumeMaPoints.length ? `<path d="${linePath(volumeMaPoints)}" fill="none" stroke="#ffd274" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round" />` : ''}
      ${volumeRail}

      ${rsHighY == null ? '' : `<line x1="${rsPanel.plotLeft}" y1="${rsHighY.toFixed(2)}" x2="${(rsPanel.plotLeft + rsPanel.plotWidth).toFixed(2)}" y2="${rsHighY.toFixed(2)}" stroke="rgba(255, 210, 116, 0.64)" stroke-width="1.1" stroke-dasharray="6 6" />`}
      ${sectorPoints.length ? `<path d="${linePath(sectorPoints)}" fill="none" stroke="#8af0b8" stroke-width="1.5" stroke-dasharray="7 5" stroke-linejoin="round" stroke-linecap="round" />` : ''}
      ${rsMaPoints.length ? `<path d="${linePath(rsMaPoints)}" fill="none" stroke="#ffd274" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" />` : ''}
      ${rsPoints.length ? `<path d="${linePath(rsPoints)}" fill="none" stroke="#57b4ff" stroke-width="2.0" stroke-linejoin="round" stroke-linecap="round" />` : ''}
      ${hoverRsPoint ? `<circle cx="${hoverRsPoint.x.toFixed(2)}" cy="${hoverRsPoint.y.toFixed(2)}" r="3.6" fill="#57b4ff" stroke="#061120" stroke-width="2" />` : ''}
      ${rsRail}

      <line x1="${macdPanel.plotLeft}" y1="${macdZeroY.toFixed(2)}" x2="${(macdPanel.plotLeft + macdPanel.plotWidth).toFixed(2)}" y2="${macdZeroY.toFixed(2)}" stroke="rgba(255,255,255,0.16)" stroke-width="1" />
      ${macdBars}
      ${signalPoints.length ? `<path d="${linePath(signalPoints)}" fill="none" stroke="#ffbd63" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" />` : ''}
      ${macdLinePoints.length ? `<path d="${linePath(macdLinePoints)}" fill="none" stroke="#57b4ff" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round" />` : ''}
      ${hoverMacdPoint ? `<circle cx="${hoverMacdPoint.x.toFixed(2)}" cy="${hoverMacdPoint.y.toFixed(2)}" r="3.6" fill="#ffbd63" stroke="#061120" stroke-width="2" />` : ''}
      ${macdRail}

      ${sharedGuides.axisLabels}

      ${pill(fmtDateAxis(hoverDate, '', true), clamp(hoverX + 70, 110, box.width - 96), box.height - 15, '#7f96af')}
      ${Number.isFinite(hoverSectorRs) && hoverRsPoint ? pill(`${txt({ ko: '섹터', en: 'Sector' })} ${fmtNum(hoverSectorRs, 1)}`, rightRailX + rightRailWidth - 8, clamp(hoverRsPoint.y + 26, rsPanel.plotTop + 20, rsPanel.plotTop + rsPanel.plotHeight - 18), '#8af0b8') : ''}
      ${viewport.total > viewport.windowSize ? `<text x="${(box.plotLeft + box.plotWidth - 8).toFixed(2)}" y="${(box.plotTop + 16).toFixed(2)}" text-anchor="end" fill="#7f96af" font-size="11">${escapeHtml(txt({ ko: '아래 바를 끌어 과거 분기 보기', en: 'Drag the bar below for older quarters' }))}</text>` : ''}
    </svg>
  `;
}

function renderEpsChart(analysis) {
  const box = chartBox('epsChart', 720, 420, EPS_CHART_PAD);
  if (!box) return;

  const viewport = getEpsViewport(analysis);
  const epsSeries = viewport.rows;
  syncEpsRangeControls(viewport);
  const epsValues = epsSeries.map((row) => Number(row.eps));
  const valid = epsValues.filter((value) => Number.isFinite(value));
  if (!valid.length) {
    emptyChart(box.node, box.width, box.height, txt({ ko: '분기 EPS 데이터가 없습니다.', en: 'Quarterly EPS data is not available.' }));
    return;
  }

  const bounds = seriesBounds([epsValues], true);
  const ticks = niceTicks(bounds.min, bounds.max, 5);
  const min = ticks[0];
  const max = ticks.at(-1);
  const span = max - min || 1;
  const zeroY = box.plotTop + ((max - 0) / span) * box.plotHeight;
  const count = epsValues.length;
  const barWidth = Math.max(10, Math.min(18, (box.plotWidth / Math.max(1, count)) * 0.34));

  const yGuides = ticks.map((tick) => {
    const y = box.plotTop + ((max - tick) / span) * box.plotHeight;
    return `
      <line x1="${box.plotLeft}" y1="${y.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${y.toFixed(2)}" stroke="rgba(116, 147, 181, 0.14)" stroke-width="1" />
      <text x="${box.plotLeft - 10}" y="${(y + 4).toFixed(2)}" text-anchor="end" fill="#7f96af" font-size="11">${escapeHtml(fmtWhole(tick))}</text>
    `;
  }).join('');

  const yearMarkers = epsSeries.map((row, index) => {
    const year = yearToken(row.period);
    const previousYear = index > 0 ? yearToken(epsSeries[index - 1].period) : '';
    if (!year || year === previousYear) return '';
    const x = pointX(index, box, count);
    return `
      <line x1="${x.toFixed(2)}" y1="${box.plotTop.toFixed(2)}" x2="${x.toFixed(2)}" y2="${(box.plotTop + box.plotHeight).toFixed(2)}" stroke="rgba(116, 147, 181, 0.12)" stroke-width="1" stroke-dasharray="3 5" />
      <text x="${x.toFixed(2)}" y="${(box.plotTop + box.plotHeight + 38).toFixed(2)}" text-anchor="middle" fill="#7f96af" font-size="11">${escapeHtml(year)}</text>
    `;
  }).join('');

  const bars = epsSeries.map((row, index) => {
    const value = Number(row.eps);
    if (!Number.isFinite(value)) return '';
    const xCenter = pointX(index, box, count);
    const y = box.plotTop + ((max - value) / span) * box.plotHeight;
    const barTop = Math.min(y, zeroY);
    const barBot = Math.max(y, zeroY);
    const barX = xCenter - barWidth / 2;
    const isUp = value >= 0;
    const isLatest = index === epsSeries.length - 1;
    const yoyVal = Number(row.eps_yoy) || 0;
    const yoyGrow = yoyVal > 0;
    const yoyShrink = yoyVal < 0;
    // Bar color by YoY growth direction (consistent with mini-chart)
    const fill = yoyGrow ? 'rgba(138, 240, 184, 0.82)' : yoyShrink ? 'rgba(255, 158, 158, 0.76)' : 'rgba(122, 143, 166, 0.7)';
    const stroke = isLatest ? 'rgba(255,255,255,0.82)' : 'rgba(255,255,255,0.08)';
    // YoY label above bar top; EPS value just above bar top (below YoY)
    const yoyY = barTop - 16;
    const valueY = barTop - 3;
    const yoyColor = yoyGrow ? '#8af0b8' : yoyShrink ? '#ff9e9e' : '#7a8fa6';
    return `
      <rect x="${barX.toFixed(2)}" y="${barTop.toFixed(2)}" width="${barWidth.toFixed(2)}" height="${Math.max(1, barBot - barTop).toFixed(2)}" rx="5" fill="${fill}" stroke="${stroke}" stroke-width="${isLatest ? 1.5 : 1}" />
      <text x="${xCenter.toFixed(2)}" y="${yoyY.toFixed(2)}" text-anchor="middle" fill="${yoyColor}" font-size="10" font-weight="600">${escapeHtml(formatSigned(row.eps_yoy, 1))}</text>
      <text x="${xCenter.toFixed(2)}" y="${valueY.toFixed(2)}" text-anchor="middle" fill="#9ec5ea" font-size="10">${escapeHtml(fmtWhole(value))}</text>
      <text x="${xCenter.toFixed(2)}" y="${(box.plotTop + box.plotHeight + 20).toFixed(2)}" text-anchor="middle" fill="#9ec5ea" font-size="10">${escapeHtml(quarterToken(row.period) || fmtQuarter(row.period))}</text>
    `;
  }).join('');

  box.node.innerHTML = `
    <svg viewBox="0 0 ${box.width} ${box.height}" role="img" aria-label="${escapeHtml(txt({ ko: '분기 EPS 차트', en: 'Quarterly EPS chart' }))}">
      <rect x="0" y="0" width="${box.width}" height="${box.height}" rx="18" fill="#061120" />
      ${yGuides}
      ${yearMarkers}
      <line x1="${box.plotLeft}" y1="${zeroY.toFixed(2)}" x2="${(box.plotLeft + box.plotWidth).toFixed(2)}" y2="${zeroY.toFixed(2)}" stroke="rgba(255,255,255,0.18)" stroke-width="1.1" />
      ${bars}
      <text x="${(box.plotLeft + 8).toFixed(2)}" y="${(box.plotTop + 16).toFixed(2)}" fill="#d7e6f8" font-size="12" font-weight="700">${escapeHtml(txt({ ko: '분기 EPS', en: 'QUARTERLY EPS' }))}</text>
      <text x="${(box.plotLeft + 8).toFixed(2)}" y="${(box.plotTop + 32).toFixed(2)}" fill="#7f96af" font-size="11">${escapeHtml(txt({ ko: '막대 = EPS / 라벨 = YoY / 하단 = 분기와 연도', en: 'Bar = EPS / Label = YoY / Bottom = quarter and year' }))}</text>
    </svg>
  `;
}

export function renderAnalysisCharts(analysis) {
  renderCompositeChart(analysis);
  renderEpsChart(analysis);
}
