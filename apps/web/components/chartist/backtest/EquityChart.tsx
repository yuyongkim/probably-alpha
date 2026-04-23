// Equity curve with benchmark overlay — pure SVG, no chart lib.
"use client";

import { useMemo } from "react";
import type { BacktestEquityPoint, BacktestBenchmarkPoint } from "@/types/chartist";

interface Props {
  equity: BacktestEquityPoint[];
  benchmark: BacktestBenchmarkPoint[];
  initialCash: number;
  height?: number;
}

export function EquityChart({ equity, benchmark, initialCash, height = 280 }: Props) {
  const { width, pathPort, pathBench, yMin, yMax, xLabels } = useMemo(
    () => layout(equity, benchmark, initialCash),
    [equity, benchmark, initialCash],
  );

  if (!equity.length) {
    return (
      <div
        className="rounded-md border p-4 text-[11px] text-[color:var(--fg-muted)]"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        No equity curve available.
      </div>
    );
  }

  return (
    <div
      className="rounded-md border"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}>
        <h2 className="display text-base">Equity vs Benchmark</h2>
        <div className="flex gap-3 text-[10px] text-[color:var(--fg-muted)]">
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-[2px]" style={{ background: "var(--accent)" }} />
            Portfolio
          </span>
          <span className="flex items-center gap-1">
            <span className="inline-block w-3 h-[2px]" style={{ background: "var(--fg-muted)" }} />
            KR Equal-Weight
          </span>
        </div>
      </div>
      <div className="p-3">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="none"
          style={{ width: "100%", height }}
        >
          <line x1={0} y1={height * 0.5} x2={width} y2={height * 0.5}
                stroke="var(--border-soft)" strokeWidth={0.5} strokeDasharray="2 4" />
          <path d={pathBench} fill="none" stroke="var(--fg-muted)" strokeWidth={1.25} />
          <path d={pathPort} fill="none" stroke="var(--accent)" strokeWidth={1.75} />
          {xLabels.map((lbl, i) => (
            <text
              key={i}
              x={lbl.x}
              y={height - 4}
              textAnchor="middle"
              fontSize={9}
              fill="var(--fg-muted)"
            >
              {lbl.text}
            </text>
          ))}
        </svg>
        <div className="flex justify-between text-[10px] text-[color:var(--fg-muted)] mt-1 px-1">
          <span>min {yMin.toFixed(0)}</span>
          <span>max {yMax.toFixed(0)}</span>
        </div>
      </div>
    </div>
  );
}

function layout(
  equity: BacktestEquityPoint[],
  benchmark: BacktestBenchmarkPoint[],
  initialCash: number,
) {
  const width = 1000;
  const height = 280;
  const padTop = 10;
  const padBot = 22;

  // Normalise to index base 100 so portfolio and benchmark share the y-axis.
  const portVals = equity.map((p) => (p.equity / initialCash) * 100);
  const benchByDate = new Map(benchmark.map((b) => [b.date, b.value]));
  // Re-base benchmark to 100 on the first matched date.
  const benchSeries: number[] = [];
  let benchBase: number | null = null;
  for (const p of equity) {
    const v = benchByDate.get(p.date);
    if (v == null) {
      benchSeries.push(benchSeries.length ? benchSeries[benchSeries.length - 1] : 100);
      continue;
    }
    if (benchBase == null) benchBase = v;
    benchSeries.push((v / (benchBase || 1)) * 100);
  }

  const all = [...portVals, ...benchSeries];
  const rawMin = Math.min(...all);
  const rawMax = Math.max(...all);
  const pad = (rawMax - rawMin) * 0.05 || 1;
  const yMin = rawMin - pad;
  const yMax = rawMax + pad;

  const n = equity.length;
  const xStep = (width - 10) / Math.max(1, n - 1);

  const toY = (v: number) => {
    const pct = (v - yMin) / (yMax - yMin);
    return padTop + (1 - pct) * (height - padTop - padBot);
  };

  const pathPort = portVals
    .map((v, i) => `${i === 0 ? "M" : "L"}${(i * xStep + 5).toFixed(1)},${toY(v).toFixed(1)}`)
    .join(" ");
  const pathBench = benchSeries
    .map((v, i) => `${i === 0 ? "M" : "L"}${(i * xStep + 5).toFixed(1)},${toY(v).toFixed(1)}`)
    .join(" ");

  // X-axis year labels
  const xLabels: { x: number; text: string }[] = [];
  let lastYear = "";
  equity.forEach((p, i) => {
    const y = p.date.slice(0, 4);
    if (y !== lastYear) {
      lastYear = y;
      xLabels.push({ x: i * xStep + 5, text: y });
    }
  });

  return { width, height, pathPort, pathBench, yMin, yMax, xLabels };
}
