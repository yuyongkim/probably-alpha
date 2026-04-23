// FundamentalsPane — live FnGuide bundle: consensus + 8Q + annual + peers + governance.
"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  FnguideFinRow,
  FnguideSnapshot,
} from "@/types/chartist";
import { EPSBlock } from "./EPSBlock";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";

interface Props {
  symbol: string;
}

export function FundamentalsPane({ symbol }: Props) {
  const [fn, setFn] = useState<FnguideSnapshot | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setStatus("loading");
    setErr(null);
    fetch(`${API_BASE}/api/v1/value/fnguide/${symbol}`)
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

  if (status === "loading") {
    return (
      <div className="text-[11px] text-[color:var(--fg-muted)]">
        Loading FnGuide snapshot…
      </div>
    );
  }
  if (status === "error" || !fn) {
    return (
      <div className="text-[11px] text-[color:var(--neg)]">
        FnGuide unavailable · {err ?? "no data"}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <EPSBlock symbol={symbol} period="Q" years={5} />
      <QuarterlyBlock rows={fn.financials_quarterly} symbol={symbol} />
      <AnnualBlock rows={fn.financials_annual} />
      <SnapshotStats snap={fn} />
      <GovernanceBlock snap={fn} />
      {fn.peers.length > 0 && <PeersTable peers={fn.peers} />}
      <SourceFootnote snap={fn} />
    </div>
  );
}

// --------------------------------------------------------------------------- #
// Quarterly (trailing 8Q)                                                      #
// --------------------------------------------------------------------------- #

function QuarterlyBlock({ rows, symbol }: { rows: FnguideFinRow[]; symbol: string }) {
  const ordered = useMemo(() => rows.slice(0, 8), [rows]);
  const withYoY = useMemo(() => attachYoY(ordered), [ordered]);

  const anyRevenue = withYoY.some((r) => r.revenue != null);
  if (!anyRevenue) {
    return (
      <div>
        <SectionHeader title="Trailing 8Q" note={`KRW · ${symbol}`} />
        <div className="text-[11px] text-[color:var(--fg-muted)]">no quarterly data</div>
      </div>
    );
  }

  return (
    <div>
      <SectionHeader title="Trailing 8Q" note={`KRW · ${symbol}`} />
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            <th className="py-1.5 px-2 text-left font-medium">Q</th>
            <th className="py-1.5 px-2 text-right font-medium">매출</th>
            <th className="py-1.5 px-2 text-right font-medium">영업이익</th>
            <th className="py-1.5 px-2 text-right font-medium">당기순이익</th>
            <th className="py-1.5 px-2 text-right font-medium">EPS</th>
            <th className="py-1.5 px-2 text-right font-medium">YoY</th>
          </tr>
        </thead>
        <tbody>
          {withYoY.map((r) => {
            const period = String(r.period ?? "—");
            const label = r.is_estimate ? `${period}E` : period;
            return (
              <tr key={period} style={{ borderTop: "1px solid var(--border-soft)" }}>
                <td className="py-1.5 px-2 mono">{label}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtKRW(r.revenue)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtKRW(r.operating_income)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtKRW(r.net_income)}</td>
                <td className="py-1.5 px-2 mono text-right font-medium">{fmtNum(r.eps, 0)}</td>
                <td
                  className="py-1.5 px-2 mono text-right"
                  style={{
                    color:
                      r.yoy == null
                        ? "var(--fg-muted)"
                        : r.yoy >= 0
                          ? "var(--pos)"
                          : "var(--neg)",
                  }}
                >
                  {r.yoy == null ? "—" : fmtPct(r.yoy)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function attachYoY(
  rows: FnguideFinRow[],
): (FnguideFinRow & { yoy: number | null })[] {
  // rows are newest-first. YoY = (t / t-4 - 1) * 100.
  return rows.map((r, i) => {
    const prev = rows[i + 4];
    const cur = r.revenue ?? r.net_income ?? null;
    const base = prev?.revenue ?? prev?.net_income ?? null;
    if (cur == null || base == null || base === 0) {
      return { ...r, yoy: null };
    }
    return { ...r, yoy: ((cur - base) / Math.abs(base)) * 100 };
  });
}

// --------------------------------------------------------------------------- #
// Annual (3+ years)                                                            #
// --------------------------------------------------------------------------- #

function AnnualBlock({ rows }: { rows: FnguideFinRow[] }) {
  const ordered = useMemo(() => rows.slice(0, 4), [rows]);
  if (!ordered.length) return null;

  const anyRevenue = ordered.some((r) => r.revenue != null || r.operating_income != null);
  if (!anyRevenue) return null;

  return (
    <div>
      <SectionHeader title="Annual" note="KRW · 억원 단위 원본" />
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            <th className="py-1.5 px-2 text-left font-medium">Y</th>
            <th className="py-1.5 px-2 text-right font-medium">매출</th>
            <th className="py-1.5 px-2 text-right font-medium">영업이익</th>
            <th className="py-1.5 px-2 text-right font-medium">당기순이익</th>
            <th className="py-1.5 px-2 text-right font-medium">EPS</th>
            <th className="py-1.5 px-2 text-right font-medium">ROE</th>
            <th className="py-1.5 px-2 text-right font-medium">부채비율</th>
          </tr>
        </thead>
        <tbody>
          {ordered.map((r) => {
            const period = String(r.period ?? "—");
            const label = r.is_estimate ? `${period}E` : period;
            return (
              <tr key={period} style={{ borderTop: "1px solid var(--border-soft)" }}>
                <td className="py-1.5 px-2 mono">{label}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtKRW(r.revenue)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtKRW(r.operating_income)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtKRW(r.net_income)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtNum(r.eps, 0)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtNum(r.roe, 2)}</td>
                <td className="py-1.5 px-2 mono text-right">{fmtNum(r.debt_ratio, 1)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// --------------------------------------------------------------------------- #
// Consensus / valuation stat grid                                              #
// --------------------------------------------------------------------------- #

function SnapshotStats({ snap }: { snap: FnguideSnapshot }) {
  return (
    <div>
      <SectionHeader title="Consensus & Valuation" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <Stat label="목표주가" value={fmtNum(snap.target_price, 0)} suffix="원" />
        <Stat label="투자의견" value={snap.investment_opinion ?? "—"} />
        <Stat label="추정 EPS" value={fmtNum(snap.consensus_eps, 0)} />
        <Stat label="추정 PER" value={fmtNum(snap.consensus_per, 2)} suffix="배" />
        <Stat label="PER" value={fmtNum(snap.per, 2)} suffix="배" />
        <Stat label="PBR" value={fmtNum(snap.pbr, 2)} suffix="배" />
        <Stat label="EPS" value={fmtNum(snap.eps, 0)} />
        <Stat label="BPS" value={fmtNum(snap.bps, 0)} />
        <Stat label="ROE" value={fmtNum(snap.roe, 2)} suffix="%" />
        <Stat label="ROA" value={fmtNum(snap.roa, 2)} suffix="%" />
        <Stat label="부채비율" value={fmtNum(snap.debt_ratio, 1)} suffix="%" />
        <Stat label="배당수익률" value={fmtNum(snap.dividend_yield, 2)} suffix="%" />
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- #
// Corporate governance                                                         #
// --------------------------------------------------------------------------- #

function GovernanceBlock({ snap }: { snap: FnguideSnapshot }) {
  const anyField =
    snap.major_shareholder_name != null ||
    snap.major_shareholder_pct != null ||
    snap.foreign_ratio != null ||
    snap.float_ratio != null ||
    snap.shares_outstanding != null ||
    snap.beta_52w != null;
  if (!anyField) return null;

  return (
    <div>
      <SectionHeader title="지배구조 & 수급" />
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <Stat
          label="최대주주"
          value={
            snap.major_shareholder_name
              ? `${snap.major_shareholder_name}${
                  snap.major_shareholder_pct != null
                    ? ` · ${fmtNum(snap.major_shareholder_pct, 2)}%`
                    : ""
                }`
              : "—"
          }
        />
        <Stat label="외국인 비중" value={fmtNum(snap.foreign_ratio, 2)} suffix="%" />
        <Stat label="유동비율" value={fmtNum(snap.float_ratio, 2)} suffix="%" />
        <Stat label="52주 β" value={fmtNum(snap.beta_52w, 2)} />
        <Stat label="시가총액" value={snap.market_cap_raw ?? fmtMarketCap(snap.market_cap)} />
        <Stat label="발행주식수" value={fmtShares(snap.shares_outstanding)} suffix="주" />
        <Stat label="52주 최고" value={fmtNum(snap.high_52w, 0)} />
        <Stat label="52주 최저" value={fmtNum(snap.low_52w, 0)} />
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- #
// Peers                                                                        #
// --------------------------------------------------------------------------- #

function PeersTable({ peers }: { peers: FnguideSnapshot["peers"] }) {
  return (
    <div>
      <SectionHeader title="동종업계 Peers" note={`${peers.length}사`} />
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            <th className="py-1 px-2 text-left font-medium">종목</th>
            <th className="py-1 px-2 text-right font-medium">Close</th>
            <th className="py-1 px-2 text-right font-medium">1D%</th>
            <th className="py-1 px-2 text-right font-medium">PER</th>
            <th className="py-1 px-2 text-right font-medium">PBR</th>
            <th className="py-1 px-2 text-right font-medium">ROE</th>
          </tr>
        </thead>
        <tbody>
          {peers.map((p, i) => (
            <tr
              key={p.symbol ?? `${p.name}-${i}`}
              style={{ borderTop: "1px solid var(--border-soft)" }}
            >
              <td className="py-1 px-2">
                <span>{p.name ?? "—"}</span>
                <span className="mono ml-2 text-[10px] text-[color:var(--fg-muted)]">
                  {p.symbol ?? ""}
                </span>
              </td>
              <td className="py-1 px-2 mono text-right">{fmtNum(p.close, 0)}</td>
              <td
                className="py-1 px-2 mono text-right"
                style={{
                  color:
                    p.change_pct == null
                      ? "var(--fg-muted)"
                      : p.change_pct >= 0
                        ? "var(--pos)"
                        : "var(--neg)",
                }}
              >
                {p.change_pct == null
                  ? "—"
                  : `${p.change_pct >= 0 ? "+" : ""}${p.change_pct.toFixed(2)}%`}
              </td>
              <td className="py-1 px-2 mono text-right">{fmtNum(p.per, 2)}</td>
              <td className="py-1 px-2 mono text-right">{fmtNum(p.pbr, 2)}</td>
              <td className="py-1 px-2 mono text-right">{fmtNum(p.roe, 2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SourceFootnote({ snap }: { snap: FnguideSnapshot }) {
  const bits = [
    `src=${snap.source}`,
    snap.cached ? "cached" : "fresh",
    snap.stale ? "stale" : null,
    snap.degraded ? "degraded" : null,
    snap.sources_used && snap.sources_used.length
      ? `[${snap.sources_used.join(" · ")}]`
      : null,
  ].filter(Boolean);
  return (
    <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
      {bits.join(" · ")}
    </div>
  );
}

// --------------------------------------------------------------------------- #
// Layout primitives                                                            #
// --------------------------------------------------------------------------- #

function SectionHeader({ title, note }: { title: string; note?: string }) {
  return (
    <div className="flex items-baseline justify-between mb-2">
      <span className="display text-[13px]">{title}</span>
      {note && (
        <span className="text-[10px] text-[color:var(--fg-muted)]">{note}</span>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  suffix,
}: {
  label: string;
  value: string;
  suffix?: string;
}) {
  return (
    <div
      className="rounded border px-2.5 py-1.5"
      style={{ borderColor: "var(--border)", background: "var(--bg)" }}
    >
      <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
        {label}
      </div>
      <div className="mono text-[13px] mt-0.5">
        {value}
        {suffix && value !== "—" && (
          <span className="ml-1 text-[10.5px] text-[color:var(--fg-muted)]">
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- #
// Formatters                                                                   #
// --------------------------------------------------------------------------- #

function fmtNum(v: number | null | undefined, digits: number): string {
  if (v == null || Number.isNaN(v)) return "—";
  return v.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function fmtPct(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function fmtKRW(v: number | null | undefined): string {
  // Values from cF3002 / finance APIs come in 억원 units ("hundreds of millions").
  // So a raw value of 300000 = 30조. We render in 조 / 억 depending on magnitude.
  if (v == null || Number.isNaN(v)) return "—";
  const abs = Math.abs(v);
  if (abs >= 10_000) {
    const jo = v / 10_000;
    return `${jo.toLocaleString(undefined, { maximumFractionDigits: 2 })}조`;
  }
  return `${v.toLocaleString(undefined, { maximumFractionDigits: 0 })}억`;
}

function fmtMarketCap(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  const abs = Math.abs(v);
  if (abs >= 1e12) return `${(v / 1e12).toLocaleString(undefined, { maximumFractionDigits: 2 })}조`;
  if (abs >= 1e8) return `${(v / 1e8).toLocaleString(undefined, { maximumFractionDigits: 0 })}억`;
  return v.toLocaleString();
}

function fmtShares(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  const abs = Math.abs(v);
  if (abs >= 1e8) return `${(v / 1e8).toLocaleString(undefined, { maximumFractionDigits: 1 })}억`;
  if (abs >= 1e4) return `${(v / 1e4).toLocaleString(undefined, { maximumFractionDigits: 1 })}만`;
  return v.toLocaleString();
}
