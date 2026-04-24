// ChartPane — OHLCV chart with axes, range/scale toggles, and indicator selector.
// Pure SVG (no new deps). Server ships SMA50/200 pre-computed; the rest (SMA20,
// SMA100, EMA20) are computed client-side from the close series.
"use client";

import { useEffect, useMemo, useState } from "react";
import type { OHLCVResponse } from "@/types/chartist";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:31300";

interface Props {
  symbol: string;
}

type Status = "loading" | "ready" | "error" | "empty";
type ScaleMode = "linear" | "log";

const RANGE_OPTIONS: Array<{ label: string; days: number }> = [
  { label: "1M", days: 22 },
  { label: "3M", days: 66 },
  { label: "6M", days: 132 },
  { label: "1Y", days: 250 },
  { label: "3Y", days: 750 },
  { label: "5Y", days: 1250 },
];

const MA_WINDOWS = [20, 50, 100, 200] as const;
type MaWindow = (typeof MA_WINDOWS)[number];
const MA_COLOR: Record<MaWindow, string> = {
  20: "#f4c55a",
  50: "#6aa9ff",
  100: "#9bd168",
  200: "#8b6a4f",
};

function sma(values: number[], window: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  let sum = 0;
  for (let i = 0; i < values.length; i++) {
    sum += values[i];
    if (i >= window) sum -= values[i - window];
    if (i >= window - 1) out[i] = sum / window;
  }
  return out;
}

function ema(values: number[], window: number): (number | null)[] {
  const out: (number | null)[] = new Array(values.length).fill(null);
  if (values.length < window) return out;
  const k = 2 / (window + 1);
  let prev = values.slice(0, window).reduce((a, b) => a + b, 0) / window;
  out[window - 1] = prev;
  for (let i = window; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k);
    out[i] = prev;
  }
  return out;
}

function formatPrice(v: number): string {
  if (v >= 10000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
  if (v >= 100) return v.toFixed(0);
  if (v >= 10) return v.toFixed(1);
  return v.toFixed(2);
}

function formatDate(iso: string): string {
  // YYYY-MM-DD -> MM/DD
  if (iso.length >= 10) return `${iso.slice(5, 7)}/${iso.slice(8, 10)}`;
  return iso;
}

export function ChartPane({ symbol }: Props) {
  const [data, setData] = useState<OHLCVResponse | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [err, setErr] = useState<string | null>(null);
  const [rangeDays, setRangeDays] = useState<number>(250);
  const [scale, setScale] = useState<ScaleMode>("linear");
  const [maOn, setMaOn] = useState<Record<MaWindow, boolean>>({
    20: false,
    50: true,
    100: false,
    200: true,
  });
  const [emaOn, setEmaOn] = useState<boolean>(false);
  const [fetchedAt, setFetchedAt] = useState<Date | null>(null);
  const [refreshTick, setRefreshTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setErr(null);
    fetch(`${API_BASE}/api/v1/chartist/ohlcv/${symbol}?days=${rangeDays}`)
      .then(async (r) => {
        const body = await r.json();
        if (!body.ok || !body.data) {
          throw new Error(body.error?.message ?? `HTTP ${r.status}`);
        }
        return body.data as OHLCVResponse;
      })
      .then((d) => {
        if (cancelled) return;
        if (!d.candles || d.candles.length === 0) {
          setStatus("empty");
          return;
        }
        setData(d);
        setFetchedAt(new Date());
        setStatus("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        setErr(String(e?.message ?? e));
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, rangeDays, refreshTick]);

  // Derived series — always compute (Rules of Hooks: no conditional hook below).
  const closes = useMemo(
    () => (data?.candles ?? []).map((c) => c.close),
    [data],
  );
  const clientSma = useMemo(() => {
    return {
      20: sma(closes, 20),
      50: sma(closes, 50),
      100: sma(closes, 100),
      200: sma(closes, 200),
    } as Record<MaWindow, (number | null)[]>;
  }, [closes]);
  const clientEma20 = useMemo(() => ema(closes, 20), [closes]);

  if (status === "loading") {
    return (
      <div className="text-[11.5px] text-[color:var(--fg-muted)]">
        Loading chart…
      </div>
    );
  }
  if (status === "empty" || !data) {
    return (
      <div className="text-[11.5px] text-[color:var(--fg-muted)]">
        No OHLCV history in ky.db for {symbol} yet. (KIS ingest pending.)
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="text-[11.5px] text-[color:var(--neg)]">
        Failed to load chart: {err}
      </div>
    );
  }

  const last = closes[closes.length - 1];
  const first = closes[0];
  const changePct = first > 0 ? (last / first - 1) * 100 : 0;

  // Y domain — envelope of highs/lows + enabled indicators.
  const allYs: number[] = [];
  for (const c of data.candles) {
    allYs.push(c.close);
    if (c.high != null) allYs.push(c.high);
    if (c.low != null) allYs.push(c.low);
  }
  for (const w of MA_WINDOWS) {
    if (!maOn[w]) continue;
    for (const v of clientSma[w]) if (v != null) allYs.push(v);
  }
  if (emaOn) for (const v of clientEma20) if (v != null) allYs.push(v);
  const rawMin = Math.min(...allYs);
  const rawMax = Math.max(...allYs);

  const useLog = scale === "log" && rawMin > 0;
  const tx = (v: number) => (useLog ? Math.log(v) : v);
  const yMin = tx(rawMin);
  const yMax = tx(rawMax);
  const span = yMax - yMin || 1;

  // Viewport. Reserve margins for axes.
  const W = 960;
  const H = 320;
  const ML = 6;
  const MR = 56; // right gutter for y-axis labels
  const MT = 8;
  const MB = 22; // bottom gutter for x-axis labels
  const innerW = W - ML - MR;
  const innerH = H - MT - MB;

  const x = (i: number) =>
    ML + (i / Math.max(1, data.candles.length - 1)) * innerW;
  const y = (v: number) =>
    MT + innerH - ((tx(v) - yMin) / span) * innerH;

  // Build paths (price close line + enabled MAs).
  const buildPath = (getter: (i: number) => number | null): string => {
    const pts: string[] = [];
    data.candles.forEach((_, i) => {
      const v = getter(i);
      if (v == null || (useLog && v <= 0)) return;
      pts.push(`${pts.length === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    });
    return pts.join(" ");
  };
  const pricePath = buildPath((i) => data.candles[i].close);
  const maPaths: Array<{ window: MaWindow; d: string }> = MA_WINDOWS.filter(
    (w) => maOn[w],
  ).map((w) => ({ window: w, d: buildPath((i) => clientSma[w][i]) }));
  const emaPath = emaOn ? buildPath((i) => clientEma20[i]) : "";

  // Axis ticks.
  const yTickCount = 5;
  const yTicks: number[] = [];
  for (let k = 0; k <= yTickCount; k++) {
    const v = useLog
      ? Math.exp(yMin + (span * k) / yTickCount)
      : yMin + (span * k) / yTickCount;
    yTicks.push(v);
  }
  const xTickCount = Math.min(6, data.candles.length);
  const xTickIndices: number[] = [];
  for (let k = 0; k < xTickCount; k++) {
    xTickIndices.push(
      Math.round(((data.candles.length - 1) * k) / Math.max(1, xTickCount - 1)),
    );
  }

  const lastCandle = data.candles[data.candles.length - 1];
  const asOf = data.as_of ?? lastCandle?.date;
  const today = new Date();
  const asOfDate = asOf ? new Date(asOf) : null;
  const ageDays = asOfDate
    ? Math.floor((today.getTime() - asOfDate.getTime()) / 86400000)
    : null;
  const isStale = ageDays !== null && ageDays > 2;

  return (
    <div>
      {/* Header: range / scale / indicator controls */}
      <div className="flex items-baseline justify-between mb-2 flex-wrap gap-2">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-[11px] text-[color:var(--fg-muted)]">
            일봉 · {data.candles.length}d · ky.db
          </span>
          <div className="flex gap-1">
            {RANGE_OPTIONS.map((r) => (
              <button
                key={r.days}
                type="button"
                onClick={() => setRangeDays(r.days)}
                className="mono text-[10px] px-1.5 py-[1px] rounded border"
                style={{
                  borderColor:
                    r.days === rangeDays
                      ? "var(--accent)"
                      : "var(--border-soft)",
                  color:
                    r.days === rangeDays
                      ? "var(--accent)"
                      : "var(--fg-muted)",
                  background: "var(--bg)",
                }}
              >
                {r.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => setScale(scale === "linear" ? "log" : "linear")}
            className="mono text-[10px] px-1.5 py-[1px] rounded border"
            style={{
              borderColor: "var(--border-soft)",
              color: "var(--fg-muted)",
              background: "var(--bg)",
            }}
          >
            {scale === "linear" ? "Linear" : "Log"}
          </button>
        </div>
        <div className="flex items-baseline gap-3">
          <span className="mono text-[11px]">
            last {last.toLocaleString()}
          </span>
          <span
            className="mono text-[11px]"
            style={{ color: changePct >= 0 ? "var(--pos)" : "var(--neg)" }}
          >
            {changePct >= 0 ? "+" : ""}
            {changePct.toFixed(2)}% ({data.candles.length}d)
          </span>
          {asOf && (
            <span
              className="mono text-[10px] px-1.5 py-[1px] rounded border"
              style={{
                borderColor: isStale ? "var(--neg)" : "var(--border)",
                color: isStale ? "var(--neg)" : "var(--fg-muted)",
                background: "var(--bg)",
              }}
              title={
                ageDays !== null
                  ? `${ageDays}d old · today is ${today.toISOString().slice(0, 10)}`
                  : undefined
              }
            >
              as-of {asOf}
              {isStale && ` (${ageDays}d stale)`}
            </span>
          )}
          <button
            type="button"
            onClick={() => setRefreshTick((t) => t + 1)}
            className="mono text-[10px] px-1.5 py-[1px] rounded border"
            style={{
              borderColor: "var(--border-soft)",
              color: "var(--fg-muted)",
              background: "var(--bg)",
            }}
            title="reload from API (as-of today)"
          >
            ↻
          </button>
        </div>
      </div>

      {/* SVG chart with axes */}
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
        {/* y-axis grid + labels (right side) */}
        {yTicks.map((v, i) => {
          const yy = y(v);
          return (
            <g key={`y-${i}`}>
              <line
                x1={ML}
                y1={yy}
                x2={ML + innerW}
                y2={yy}
                stroke="var(--border-soft)"
                strokeWidth={0.5}
                strokeDasharray={i === 0 || i === yTickCount ? "0" : "2 3"}
              />
              <text
                x={ML + innerW + 4}
                y={yy + 3}
                fontSize="9"
                fill="var(--fg-muted)"
                className="mono"
              >
                {formatPrice(v)}
              </text>
            </g>
          );
        })}
        {/* x-axis ticks + labels (bottom) */}
        {xTickIndices.map((idx) => {
          const xx = x(idx);
          const dt = data.candles[idx]?.date ?? "";
          return (
            <g key={`x-${idx}`}>
              <line
                x1={xx}
                y1={MT + innerH}
                x2={xx}
                y2={MT + innerH + 3}
                stroke="var(--border-soft)"
                strokeWidth={0.5}
              />
              <text
                x={xx}
                y={MT + innerH + 14}
                textAnchor="middle"
                fontSize="9"
                fill="var(--fg-muted)"
                className="mono"
              >
                {formatDate(dt)}
              </text>
            </g>
          );
        })}
        {/* indicator paths */}
        {maPaths.map(({ window: w, d }) =>
          d ? (
            <path
              key={`ma-${w}`}
              d={d}
              fill="none"
              stroke={MA_COLOR[w]}
              strokeWidth={1.25}
            />
          ) : null,
        )}
        {emaPath && (
          <path
            d={emaPath}
            fill="none"
            stroke="#c97eff"
            strokeWidth={1.25}
            strokeDasharray="3 3"
          />
        )}
        {/* close line — drawn on top */}
        <path
          d={pricePath}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={1.5}
        />
      </svg>

      {/* Indicator toggles */}
      <div className="flex gap-2 mt-2 text-[10.5px] text-[color:var(--fg-muted)] flex-wrap">
        <span className="mr-1">
          <span style={{ color: "var(--accent)" }}>▬</span> close
        </span>
        {MA_WINDOWS.map((w) => (
          <button
            key={w}
            type="button"
            onClick={() => setMaOn((m) => ({ ...m, [w]: !m[w] }))}
            className="mono text-[10px] px-1.5 py-[1px] rounded border"
            style={{
              borderColor: maOn[w] ? MA_COLOR[w] : "var(--border-soft)",
              color: maOn[w] ? MA_COLOR[w] : "var(--fg-muted)",
              background: "var(--bg)",
            }}
          >
            SMA{w}
          </button>
        ))}
        <button
          type="button"
          onClick={() => setEmaOn((v) => !v)}
          className="mono text-[10px] px-1.5 py-[1px] rounded border"
          style={{
            borderColor: emaOn ? "#c97eff" : "var(--border-soft)",
            color: emaOn ? "#c97eff" : "var(--fg-muted)",
            background: "var(--bg)",
          }}
        >
          EMA20
        </button>
        {fetchedAt && (
          <span className="mono text-[10px] text-[color:var(--fg-muted)] ml-auto">
            fetched {fetchedAt.toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  );
}
