// FlowPane — 외인/기관/개인 일별 순매수, fed by the FnGuide full snapshot.
"use client";

import { useEffect, useMemo, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type { FnguideInvestorTrendRow, FnguideSnapshot } from "@/types/chartist";

interface Props {
  symbol: string;
}

export function FlowPane({ symbol }: Props) {
  const [fn, setFn] = useState<FnguideSnapshot | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setErr(null);
    fetch(`${apiBase()}/api/v1/value/fnguide/${symbol}`)
      .then(async (r) => {
        const body = await r.json();
        if (!body.ok || !body.data) {
          throw new Error(body.error?.message ?? `HTTP ${r.status}`);
        }
        return body.data as FnguideSnapshot;
      })
      .then((d) => {
        if (cancelled) return;
        setFn(d);
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

  const rows = useMemo(() => fn?.investor_trend ?? [], [fn]);
  const totals = useMemo(() => aggregate5d(rows), [rows]);

  if (status === "loading") {
    return (
      <div className="text-[11px] text-[color:var(--fg-muted)]">
        Loading investor trend…
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="text-[11px] text-[color:var(--neg)]">
        FnGuide unavailable · {err ?? "no data"}
      </div>
    );
  }
  if (!rows.length) {
    return (
      <div className="text-[11px] text-[color:var(--fg-muted)]">
        no investor flow data · {symbol}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-3 gap-2">
        <TotalCard label="외인 · 5d" value={totals.foreign} />
        <TotalCard label="기관 · 5d" value={totals.inst} />
        <TotalCard label="개인 · 5d" value={totals.retail} />
      </div>

      <div>
        <div className="flex items-baseline justify-between mb-2">
          <span className="display text-[13px]">투자자별 순매수 (주)</span>
          <span className="text-[10px] text-[color:var(--fg-muted)]">
            {symbol} · {rows.length}d
          </span>
        </div>
        <table className="w-full text-[11.5px] border-collapse">
          <thead>
            <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
              <th className="py-1.5 px-2 text-left font-medium">Date</th>
              <th className="py-1.5 px-2 text-right font-medium">외인</th>
              <th className="py-1.5 px-2 text-right font-medium">기관</th>
              <th className="py-1.5 px-2 text-right font-medium">개인</th>
              <th className="py-1.5 px-2 text-right font-medium">외인지분</th>
              <th className="py-1.5 px-2 text-right font-medium">종가</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.date} style={{ borderTop: "1px solid var(--border-soft)" }}>
                <td className="py-1.5 px-2 mono">{fmtDate(r.date)}</td>
                <td className="py-1.5 px-2 mono text-right" style={{ color: col(r.foreign_net) }}>
                  {signed(r.foreign_net)}
                </td>
                <td className="py-1.5 px-2 mono text-right" style={{ color: col(r.institution_net) }}>
                  {signed(r.institution_net)}
                </td>
                <td className="py-1.5 px-2 mono text-right" style={{ color: col(r.individual_net) }}>
                  {signed(r.individual_net)}
                </td>
                <td className="py-1.5 px-2 mono text-right">
                  {r.foreign_hold_ratio == null ? "—" : `${r.foreign_hold_ratio.toFixed(2)}%`}
                </td>
                <td className="py-1.5 px-2 mono text-right">
                  {r.close == null ? "—" : r.close.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TotalCard({ label, value }: { label: string; value: number | null }) {
  return (
    <div
      className="rounded border px-2.5 py-1.5"
      style={{ borderColor: "var(--border)", background: "var(--bg)" }}
    >
      <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
        {label}
      </div>
      <div className="mono text-[13px] mt-0.5" style={{ color: col(value) }}>
        {signed(value)}
      </div>
    </div>
  );
}

function aggregate5d(rows: FnguideInvestorTrendRow[]): {
  foreign: number | null;
  inst: number | null;
  retail: number | null;
} {
  if (!rows.length) return { foreign: null, inst: null, retail: null };
  const slice = rows.slice(0, 5);
  const sum = (f: (r: FnguideInvestorTrendRow) => number | null | undefined) =>
    slice.reduce((acc, r) => {
      const v = f(r);
      return v == null ? acc : acc + v;
    }, 0);
  return {
    foreign: sum((r) => r.foreign_net),
    inst: sum((r) => r.institution_net),
    retail: sum((r) => r.individual_net),
  };
}

function signed(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  const sign = v > 0 ? "+" : "";
  return `${sign}${Math.round(v).toLocaleString()}`;
}

function col(v: number | null | undefined): string {
  if (v == null) return "var(--fg-muted)";
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function fmtDate(s: string): string {
  // "20260422" → "04-22"
  if (!s) return "—";
  if (s.length === 8) return `${s.slice(4, 6)}-${s.slice(6, 8)}`;
  return s;
}
