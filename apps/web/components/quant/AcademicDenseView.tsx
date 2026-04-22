// AcademicDenseView — 4 strategy summary kv-cards + Top picks table per strategy.

import { Panel } from "@/components/shared/Panel";
import { ACADEMIC_SUMMARY } from "@/lib/quant/mockData";
import type { AcademicResponse } from "@/types/quant";

const num = (v: unknown, digits = 0) => {
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n.toLocaleString(undefined, { maximumFractionDigits: digits }) : "—";
};

interface Props {
  bundles: Array<AcademicResponse & { displayName: string }>;
}

export function AcademicDenseView({ bundles }: Props) {
  return (
    <>
      <div className="grid-2-equal" style={{ marginBottom: 16 }}>
        {ACADEMIC_SUMMARY.map((c) => (
          <div key={c.label} className="kv-card">
            <div className="kv-label">{c.label}</div>
            <div className="kv-value">{c.value}</div>
            <div style={{ marginTop: 8, fontSize: 11.5, color: "var(--text-muted)" }}>
              {c.sub}
            </div>
          </div>
        ))}
      </div>

      {bundles.map((b) => (
        <Panel
          key={b.strategy}
          title={`${b.displayName} — Top ${b.rows.length}`}
          muted={`as of ${b.as_of}`}
          bodyPadding="p0"
          className="mb-[10px]"
          style={{ marginBottom: 10 }}
        >
          <table className="mini">
            <thead>
              <tr>
                <th>#</th>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">Close</th>
                <th className="num">Score</th>
              </tr>
            </thead>
            <tbody>
              {b.rows.map((r, i) => (
                <tr key={r.symbol}>
                  <td className="mono">{String(i + 1).padStart(2, "0")}</td>
                  <td>
                    <span className="ticker-name">{r.name ?? r.symbol}</span>
                    <span className="mono" style={{ marginLeft: 6, color: "var(--text-muted)" }}>
                      {r.symbol}
                    </span>
                  </td>
                  <td>{r.sector ? <span className="chip accent">{r.sector}</span> : "—"}</td>
                  <td className="num">{num(r.close)}</td>
                  <td className="num" style={{ fontWeight: 600 }}>
                    {num(
                      r.magic_score ?? r.pb_proxy ?? r.score ?? r.super_score ?? null,
                      3,
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      ))}
    </>
  );
}
