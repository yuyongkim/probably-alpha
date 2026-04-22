// LeadersTable — dense Bloomberg-style table used on
// /chartist/leaders. Supports up to 500 rows with column sorting
// kept inside the component (client-side only).
"use client";

import { useMemo, useState } from "react";
import type { LeaderRow } from "@/types/chartist";
import { TickerName } from "@/components/shared/TickerName";

interface Props {
  rows: LeaderRow[];
}

type SortKey =
  | "leader_score"
  | "tt_passes"
  | "rs"
  | "d1"
  | "d5"
  | "m1"
  | "vol_x";

const NUM = "py-1 px-2 mono text-[11px] text-right tabular-nums";
const TH =
  "py-1.5 px-2 text-[9.5px] uppercase tracking-widest font-medium text-[color:var(--muted)] border-b select-none cursor-pointer";

function signed(v: number, digits = 2): string {
  return v > 0 ? `+${v.toFixed(digits)}` : v.toFixed(digits);
}

function tone(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

function patternChipClass(p: string): string {
  if (p === "VCP")
    return "border border-[color:var(--accent)] text-[color:var(--accent)] bg-[color:var(--accent-soft)]";
  if (p === "B.out")
    return "border border-[color:var(--pos)] text-[color:var(--pos)] bg-[color:var(--pos-soft)]";
  return "border border-[color:var(--border-soft)] text-[color:var(--fg-muted)]";
}

export function LeadersTable({ rows }: Props) {
  const [sort, setSort] = useState<SortKey>("leader_score");
  const [desc, setDesc] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => {
      const va = a[sort] as number;
      const vb = b[sort] as number;
      return desc ? vb - va : va - vb;
    });
    return copy;
  }, [rows, sort, desc]);

  const handle = (key: SortKey) => () => {
    if (key === sort) setDesc((d) => !d);
    else {
      setSort(key);
      setDesc(true);
    }
  };

  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">Leaders</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          {rows.length} rows · click header to sort
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11.5px] border-collapse">
          <thead>
            <tr>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>#</th>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Ticker</th>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Sector</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("leader_score")}>LS{sort==="leader_score"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("tt_passes")}>TT{sort==="tt_passes"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("rs")}>RS{sort==="rs"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("d1")}>1D{sort==="d1"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("d5")}>5D{sort==="d5"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("m1")}>1M{sort==="m1"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-right`} style={{ borderColor: "var(--border)" }} onClick={handle("vol_x")}>Vol×{sort==="vol_x"?(desc?"↓":"↑"):""}</th>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>Pat.</th>
              <th className={`${TH} text-left`} style={{ borderColor: "var(--border)" }}>왜?</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((l, i) => (
              <tr
                key={l.symbol}
                style={{ borderBottom: "1px solid var(--border-soft)" }}
                className="hover:bg-[color:var(--surface-2)]"
              >
                <td className="py-1 px-2 mono text-[10px] text-[color:var(--fg-muted)]">{i + 1}</td>
                <td className="py-1 px-2">
                  <TickerName symbol={l.symbol} name={l.name} sector={l.sector} />
                  <span className="mono ml-2 text-[10px] text-[color:var(--fg-muted)]">{l.symbol}</span>
                </td>
                <td className="py-1 px-2 text-[color:var(--fg-muted)] text-[11px]">{l.sector}</td>
                <td className={NUM}>{l.leader_score.toFixed(3)}</td>
                <td className={NUM}>{l.trend_template}</td>
                <td className={NUM} style={{ color: tone(l.rs) }}>{signed(l.rs * 100, 0)}%</td>
                <td className={NUM} style={{ color: tone(l.d1) }}>{signed(l.d1)}</td>
                <td className={NUM} style={{ color: tone(l.d5) }}>{signed(l.d5)}</td>
                <td className={NUM} style={{ color: tone(l.m1) }}>{signed(l.m1)}</td>
                <td className={NUM}>{l.vol_x.toFixed(1)}×</td>
                <td className="py-1 px-2">
                  <span className={`inline-block px-1.5 py-[1px] text-[10px] rounded ${patternChipClass(l.pattern)}`}>
                    {l.pattern}
                  </span>
                </td>
                <td className="py-1 px-2 text-[10.5px] text-[color:var(--fg-muted)]">{l.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
