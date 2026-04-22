// ChartPane — placeholder SVG candles + MA50/MA200 overlay.
// Mock series seeded from the symbol so each ticker looks distinct.
"use client";

interface Props {
  symbol: string;
}

function seededSeries(symbol: string, n = 120): number[] {
  // deterministic xorshift-ish hash per symbol
  let seed = 0;
  for (let i = 0; i < symbol.length; i++) seed = (seed * 31 + symbol.charCodeAt(i)) | 0;
  const out: number[] = [];
  let v = 100 + (Math.abs(seed) % 50);
  for (let i = 0; i < n; i++) {
    seed ^= seed << 13; seed ^= seed >>> 17; seed ^= seed << 5;
    const drift = ((seed & 0xffff) / 0xffff - 0.48) * 4;
    v = Math.max(10, v + drift);
    out.push(v);
  }
  return out;
}

function sma(arr: number[], window: number): (number | null)[] {
  const out: (number | null)[] = [];
  let sum = 0;
  for (let i = 0; i < arr.length; i++) {
    sum += arr[i];
    if (i >= window) sum -= arr[i - window];
    out.push(i >= window - 1 ? sum / window : null);
  }
  return out;
}

export function ChartPane({ symbol }: Props) {
  const series = seededSeries(symbol);
  const ma50 = sma(series, 50);
  const ma200 = sma(series, Math.min(80, series.length - 1));

  const W = 960;
  const H = 320;
  const min = Math.min(...series);
  const max = Math.max(...series);
  const span = max - min || 1;
  const x = (i: number) => (i / (series.length - 1)) * W;
  const y = (v: number) => H - ((v - min) / span) * H;

  const pathFor = (vs: (number | null)[], color: string) => {
    const pts: string[] = [];
    vs.forEach((v, i) => {
      if (v == null) return;
      pts.push(`${pts.length === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    });
    return (
      <path d={pts.join(" ")} fill="none" stroke={color} strokeWidth={1.25} />
    );
  };

  const pricePath = series
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
    .join(" ");

  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="text-[11px] text-[color:var(--fg-muted)]">
          일봉 · 120d · MA50 · MA200 (mock)
        </span>
        <span className="mono text-[11px]">
          last {series[series.length - 1].toFixed(2)}
        </span>
      </div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ display: "block" }}>
        <path
          d={pricePath}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={1.5}
        />
        {pathFor(ma50, "#6aa9ff")}
        {pathFor(ma200, "#8b6a4f")}
      </svg>
      <div className="flex gap-4 mt-2 text-[10.5px] text-[color:var(--fg-muted)]">
        <span>
          <span style={{ color: "var(--accent)" }}>▬</span> price
        </span>
        <span>
          <span style={{ color: "#6aa9ff" }}>▬</span> MA50
        </span>
        <span>
          <span style={{ color: "#8b6a4f" }}>▬</span> MA200
        </span>
      </div>
    </div>
  );
}
