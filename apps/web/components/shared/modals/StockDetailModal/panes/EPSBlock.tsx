// EPSBlock — real EPS history ported from Company_Credit financial.db.
// Consumed by FundamentalsPane. Renders a compact SVG sparkline + table.
"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import { fmtNum, fmtPct } from "@/lib/format";

export interface EPSPoint {
  period: string;
  period_type: "annual" | "quarterly" | string;
  available_date: string;
  eps: number;
  eps_yoy: number | null;
  source: string;
  is_estimate: boolean;
}

export interface EPSPayload {
  symbol: string;
  period: string;
  years: number;
  n: number;
  rows: EPSPoint[];
}

interface Props {
  symbol: string;
  period?: "Q" | "A" | "ALL";
  years?: number;
}

export function EPSBlock({ symbol, period = "Q", years = 5 }: Props) {
  const [payload, setPayload] = useState<EPSPayload | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setPayload(null);
    setLoaded(false);
    fetch(`${apiBase()}/api/v1/value/eps/${symbol}?period=${period}&years=${years}`)
      .then((r) => r.json())
      .then((body) => {
        if (cancelled) return;
        if (body?.ok && body.data) setPayload(body.data as EPSPayload);
        setLoaded(true);
      })
      .catch(() => {
        if (cancelled) return;
        setLoaded(true);
      });
    return () => {
      cancelled = true;
    };
  }, [symbol, period, years]);

  // Hooks MUST run on every render in the same order — compute before any
  // early return. When payload is null we pass an empty array through.
  const points = useMemo(
    () => (payload?.rows?.length ? payload.rows.slice().reverse() : []),
    [payload?.rows],
  );

  // silent when no data — EPS section is secondary to FnGuide bundle
  if (!loaded || !payload || points.length === 0) return null;

  const values = points.map((p) => p.eps);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 280;
  const height = 72;
  const padL = 28;
  const padR = 6;
  const padY = 6;
  const w = width - padL - padR;
  const h = height - padY * 2;
  const toX = (i: number) =>
    points.length <= 1 ? padL + w / 2 : padL + (i / (points.length - 1)) * w;
  const toY = (v: number) => padY + h - ((v - min) / range) * h;
  const latest = points[points.length - 1];
  const color = latest.eps >= points[0].eps ? "var(--pos)" : "var(--neg)";

  const linePoints = points
    .map((p, i) => `${toX(i).toFixed(1)},${toY(p.eps).toFixed(1)}`)
    .join("L");

  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="display text-[13px]">
          EPS 추이 (실 EPS · financial.db port)
        </span>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {points.length}
          {period === "A" ? "Y" : period === "ALL" ? "pts" : "Q"} · source=
          {latest.source}
        </span>
      </div>
      <div
        className="rounded border px-2 py-2"
        style={{ borderColor: "var(--border)", background: "var(--bg)" }}
      >
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          xmlns="http://www.w3.org/2000/svg"
          className="block"
        >
          <line
            x1={padL}
            y1={padY + h}
            x2={padL + w}
            y2={padY + h}
            stroke="var(--border-soft)"
            strokeWidth="0.5"
          />
          <text
            x={padL - 4}
            y={padY + 8}
            textAnchor="end"
            fontSize="8"
            fill="var(--muted)"
          >
            {fmtEPS(max)}
          </text>
          <text
            x={padL - 4}
            y={padY + h}
            textAnchor="end"
            fontSize="8"
            fill="var(--muted)"
          >
            {fmtEPS(min)}
          </text>
          {points.length >= 2 && (
            <path
              d={`M${linePoints}`}
              fill="none"
              stroke={color}
              strokeWidth="1.4"
            />
          )}
          {points.map((p, i) => (
            <circle
              key={p.period}
              cx={toX(i)}
              cy={toY(p.eps)}
              r={2.2}
              fill={color}
            />
          ))}
        </svg>
        <table className="w-full text-[11.5px] border-collapse mt-2">
          <thead>
            <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
              <th className="py-1 px-2 text-left font-medium">기간</th>
              <th className="py-1 px-2 text-right font-medium">EPS</th>
              <th className="py-1 px-2 text-right font-medium">YoY</th>
            </tr>
          </thead>
          <tbody>
            {points
              .slice()
              .reverse()
              .map((p) => (
                <tr
                  key={p.period}
                  style={{ borderTop: "1px solid var(--border-soft)" }}
                >
                  <td className="py-1 px-2 mono">{p.period}</td>
                  <td className="py-1 px-2 mono text-right font-medium">
                    {fmtNum(p.eps, 0)}
                  </td>
                  <td
                    className="py-1 px-2 mono text-right"
                    style={{
                      color:
                        p.eps_yoy == null
                          ? "var(--fg-muted)"
                          : p.eps_yoy >= 0
                            ? "var(--pos)"
                            : "var(--neg)",
                    }}
                  >
                    {p.eps_yoy == null ? "—" : fmtPct(p.eps_yoy)}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function fmtEPS(v: number): string {
  if (Math.abs(v) >= 10000) return `${(v / 1000).toFixed(0)}K`;
  if (Math.abs(v) >= 1000) return `${(v / 1000).toFixed(1)}K`;
  return Math.round(v).toString();
}
