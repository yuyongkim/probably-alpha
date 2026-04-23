// ChartPane — real OHLCV polyline with SMA50 / SMA200 overlay.
// Pulls /api/v1/chartist/ohlcv/{symbol} client-side so the modal stays
// snappy. The SVG is presentation only; data math happens server-side.
"use client";

import { useEffect, useState } from "react";
import type { OHLCVResponse } from "@/types/chartist";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";

interface Props {
  symbol: string;
}

type Status = "loading" | "ready" | "error" | "empty";

export function ChartPane({ symbol }: Props) {
  const [data, setData] = useState<OHLCVResponse | null>(null);
  const [status, setStatus] = useState<Status>("loading");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setErr(null);
    fetch(`${API_BASE}/api/v1/chartist/ohlcv/${symbol}?days=250`)
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
  }, [symbol]);

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

  const closes = data.candles.map((c) => c.close);
  const last = closes[closes.length - 1];
  const first = closes[0];
  const changePct = first > 0 ? (last / first - 1) * 100 : 0;

  // Y-axis spans the envelope of price + both SMAs (where defined).
  const allYs: number[] = [...closes];
  for (const c of data.candles) {
    if (c.sma50 != null) allYs.push(c.sma50);
    if (c.sma200 != null) allYs.push(c.sma200);
    if (c.high != null) allYs.push(c.high);
    if (c.low != null) allYs.push(c.low);
  }
  const yMin = Math.min(...allYs);
  const yMax = Math.max(...allYs);
  const span = yMax - yMin || 1;

  const W = 960;
  const H = 320;
  const PADY = 12;
  const x = (i: number) => (i / Math.max(1, data.candles.length - 1)) * W;
  const y = (v: number) =>
    H - PADY - ((v - yMin) / span) * (H - 2 * PADY);

  const pricePath = data.candles
    .map(
      (c, i) =>
        `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(c.close).toFixed(1)}`,
    )
    .join(" ");

  const seriesPath = (
    getter: (c: OHLCVResponse["candles"][number]) => number | null,
  ) => {
    const pts: string[] = [];
    data.candles.forEach((c, i) => {
      const v = getter(c);
      if (v == null) return;
      pts.push(`${pts.length === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    });
    return pts.join(" ");
  };

  const sma50Path = seriesPath((c) => c.sma50);
  const sma200Path = seriesPath((c) => c.sma200);

  // Ensure asOf is rendered even if the last candle has no date (shouldn't happen).
  const asOf = data.as_of ?? data.candles[data.candles.length - 1]?.date;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-2 flex-wrap gap-2">
        <span className="text-[11px] text-[color:var(--fg-muted)]">
          일봉 · {data.candles.length}d · SMA50 · SMA200 · ky.db
        </span>
        <div className="flex items-baseline gap-3">
          <span className="mono text-[11px]">
            last {last.toLocaleString()}
          </span>
          <span
            className="mono text-[11px]"
            style={{
              color: changePct >= 0 ? "var(--pos)" : "var(--neg)",
            }}
          >
            {changePct >= 0 ? "+" : ""}
            {changePct.toFixed(2)}% ({data.candles.length}d)
          </span>
          {asOf && (
            <span
              className="mono text-[10px] px-1.5 py-[1px] rounded border"
              style={{
                borderColor: "var(--border)",
                color: "var(--fg-muted)",
                background: "var(--bg)",
              }}
            >
              as-of {asOf}
            </span>
          )}
        </div>
      </div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
        {sma200Path && (
          <path d={sma200Path} fill="none" stroke="#8b6a4f" strokeWidth={1.25} />
        )}
        {sma50Path && (
          <path d={sma50Path} fill="none" stroke="#6aa9ff" strokeWidth={1.25} />
        )}
        <path
          d={pricePath}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={1.5}
        />
      </svg>
      <div className="flex gap-4 mt-2 text-[10.5px] text-[color:var(--fg-muted)]">
        <span>
          <span style={{ color: "var(--accent)" }}>▬</span> close
        </span>
        <span>
          <span style={{ color: "#6aa9ff" }}>▬</span> SMA50
        </span>
        <span>
          <span style={{ color: "#8b6a4f" }}>▬</span> SMA200
        </span>
      </div>
    </div>
  );
}
