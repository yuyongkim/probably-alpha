// FundamentalsPane — 8Q placeholder (DART pending) + live FnGuide snapshot.
"use client";

import { useEffect, useState } from "react";
import type { FnguideSnapshot } from "@/types/chartist";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8300";

interface Props {
  symbol: string;
}

interface Q {
  quarter: string;
  rev: string;
  op: string;
  np: string;
  eps: string;
  yoy: number;
}

// Placeholder while DART connector is wired — same shape as before.
const SAMPLE: Q[] = [
  { quarter: "25Q2E", rev: "4.18조", op: "8,420억", np: "6,140억", eps: "1,842", yoy: 38 },
  { quarter: "25Q1",  rev: "3.92조", op: "7,610억", np: "5,580억", eps: "1,674", yoy: 32 },
  { quarter: "24Q4",  rev: "3.74조", op: "6,940억", np: "5,120억", eps: "1,534", yoy: 28 },
  { quarter: "24Q3",  rev: "3.52조", op: "6,210억", np: "4,540억", eps: "1,362", yoy: 22 },
  { quarter: "24Q2",  rev: "3.28조", op: "5,480억", np: "3,980억", eps: "1,194", yoy: 18 },
  { quarter: "24Q1",  rev: "3.04조", op: "4,820억", np: "3,510억", eps: "1,052", yoy: 12 },
  { quarter: "23Q4",  rev: "2.84조", op: "4,210억", np: "3,080억", eps: "924", yoy: 4 },
  { quarter: "23Q3",  rev: "2.72조", op: "3,940억", np: "2,850억", eps: "854", yoy: -2 },
];

export function FundamentalsPane({ symbol }: Props) {
  const [fn, setFn] = useState<FnguideSnapshot | null>(null);
  const [fnStatus, setFnStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );
  const [fnErr, setFnErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setFnStatus("loading");
    setFnErr(null);
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
        setFnStatus("ready");
      })
      .catch((e) => {
        if (cancelled) return;
        setFnErr(String(e?.message ?? e));
        setFnStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [symbol]);

  return (
    <div className="flex flex-col gap-4">
      {/* 8Q trailing placeholder — unchanged. */}
      <div>
        <div className="text-[11px] text-[color:var(--fg-muted)] mb-2">
          Trailing 8Q · KRW · placeholder (DART connector pending · {symbol})
        </div>
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
            {SAMPLE.map((q) => (
              <tr key={q.quarter} style={{ borderTop: "1px solid var(--border-soft)" }}>
                <td className="py-1.5 px-2 mono">{q.quarter}</td>
                <td className="py-1.5 px-2 mono text-right">{q.rev}</td>
                <td className="py-1.5 px-2 mono text-right">{q.op}</td>
                <td className="py-1.5 px-2 mono text-right">{q.np}</td>
                <td className="py-1.5 px-2 mono text-right font-medium">{q.eps}</td>
                <td
                  className="py-1.5 px-2 mono text-right"
                  style={{ color: q.yoy >= 0 ? "var(--pos)" : "var(--neg)" }}
                >
                  {q.yoy >= 0 ? `+${q.yoy}%` : `${q.yoy}%`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <FnguideBlock status={fnStatus} snapshot={fn} error={fnErr} />
    </div>
  );
}

function FnguideBlock({
  status,
  snapshot,
  error,
}: {
  status: "loading" | "ready" | "error";
  snapshot: FnguideSnapshot | null;
  error: string | null;
}) {
  if (status === "loading") {
    return (
      <Section title="FnGuide Snapshot" note="loading…" />
    );
  }
  if (status === "error" || !snapshot) {
    return (
      <Section
        title="FnGuide Snapshot"
        note="unavailable"
      >
        <div className="text-[11px] text-[color:var(--neg)]">
          {error ?? "no data"}
        </div>
      </Section>
    );
  }

  const {
    investment_opinion,
    target_price,
    per,
    pbr,
    eps,
    bps,
    roe,
    dividend_yield,
    foreign_ratio,
    major_shareholder_name,
    major_shareholder_pct,
    peers,
    source,
    cached,
    stale,
  } = snapshot;

  return (
    <Section
      title="FnGuide Snapshot"
      note={[
        `src=${source}`,
        cached ? "cached" : "fresh",
        stale ? "stale" : null,
      ]
        .filter(Boolean)
        .join(" · ")}
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <Stat label="목표주가" value={fmtNum(target_price, 0)} suffix="원" />
        <Stat label="투자의견" value={investment_opinion ?? "—"} />
        <Stat label="PER" value={fmtNum(per, 2)} suffix="배" />
        <Stat label="PBR" value={fmtNum(pbr, 2)} suffix="배" />
        <Stat label="EPS" value={fmtNum(eps, 0)} />
        <Stat label="BPS" value={fmtNum(bps, 0)} />
        <Stat label="ROE" value={fmtNum(roe, 2)} suffix="%" />
        <Stat label="배당수익률" value={fmtNum(dividend_yield, 2)} suffix="%" />
        <Stat label="외국인 비중" value={fmtNum(foreign_ratio, 2)} suffix="%" />
        <Stat
          label="최대주주"
          value={
            major_shareholder_name
              ? `${major_shareholder_name}${
                  major_shareholder_pct ? ` · ${fmtNum(major_shareholder_pct, 2)}%` : ""
                }`
              : "—"
          }
        />
      </div>

      {peers.length > 0 && <PeersTable peers={peers} />}
    </Section>
  );
}

function PeersTable({ peers }: { peers: FnguideSnapshot["peers"] }) {
  return (
    <div>
      <div className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)] mb-1">
        동종업계 Peers
      </div>
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

function Section({
  title,
  note,
  children,
}: {
  title: string;
  note?: string;
  children?: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-2">
        <span className="display text-[13px]">{title}</span>
        {note && (
          <span className="text-[10px] text-[color:var(--fg-muted)]">{note}</span>
        )}
      </div>
      {children}
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

function fmtNum(v: number | null | undefined, digits: number): string {
  if (v == null || Number.isNaN(v)) return "—";
  return v.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}
