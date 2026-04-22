// FactorsDenseView — full mockup port for Quant · Factors subsection.
// Uses real factor rows from API + mock regime/IC/heatmap panels.

import { DenseQuote } from "@/components/shared/DenseQuote";
import { MarketStripPanel } from "@/components/shared/MarketStripPanel";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { Heatmap } from "@/components/shared/Heatmap";
import { ActivityLog } from "@/components/shared/ActivityLog";
import type { FactorRow } from "@/types/quant";
import {
  FACTORS_MARKET,
  FACTORS_KPI,
  FACTORS_IC,
  FACTORS_QUINTILE,
  FACTORS_CORR,
  FACTORS_ACTIVITY,
} from "@/lib/quant/mockData";

const pct = (v: number | null | undefined) =>
  v == null ? "—" : v.toFixed(2);

interface Props {
  rows: FactorRow[];
}

export function FactorsDenseView({ rows }: Props) {
  const top = rows.slice(0, 20);
  return (
    <>
      <DenseQuote
        quote="“The premium to value is not a free lunch — it's compensation for bearing risk that others can't or won't bear.”"
        attribution="Cliff Asness · AQR · 2014"
      />
      <MarketStripPanel cells={FACTORS_MARKET} />
      <DenseSummary cells={FACTORS_KPI} />

      <div className="grid-2" style={{ marginBottom: 10 }}>
        <Panel
          title="Factor Composite — Top 20"
          muted="V · Q · M · LV · G · SIZE · COMP · RS · DECILE"
          bodyPadding="p0"
        >
          <table className="mini">
            <thead>
              <tr>
                <th>#</th>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">V</th>
                <th className="num">Q</th>
                <th className="num">M</th>
                <th className="num">LV</th>
                <th className="num">G</th>
                <th className="num">Comp</th>
              </tr>
            </thead>
            <tbody>
              {top.map((r, i) => (
                <tr key={r.symbol}>
                  <td className="mono">{String(i + 1).padStart(2, "0")}</td>
                  <td>
                    <span className="ticker-name">{r.name ?? r.symbol}</span>
                    <span className="mono" style={{ marginLeft: 6, color: "var(--text-muted)" }}>
                      {r.symbol}
                    </span>
                  </td>
                  <td>
                    <span className="chip accent">{r.sector ?? "—"}</span>
                  </td>
                  <td className="num">{pct(r.value)}</td>
                  <td className="num">{pct(r.quality)}</td>
                  <td className="num">{pct(r.momentum)}</td>
                  <td className="num">{pct(r.low_vol)}</td>
                  <td className="num">{pct(r.growth)}</td>
                  <td className="num" style={{ fontWeight: 600 }}>
                    {pct(r.composite)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Factor IC · 6M" muted="Spearman rank">
          <div style={{ display: "flex", flexDirection: "column", gap: 9 }}>
            {FACTORS_IC.map((f) => {
              const width = Math.min(Math.abs(f.value) * 250, 48);
              return (
                <div key={f.name} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11.5 }}>
                  <span style={{ width: 90, color: "var(--text-secondary)" }}>{f.name}</span>
                  <div style={{ flex: 1, height: 14, background: "var(--bg)", borderRadius: 3, position: "relative" }}>
                    <div
                      style={{
                        position: "absolute",
                        [f.value >= 0 ? "left" : "right"]: "50%",
                        top: 0,
                        width: `${width}%`,
                        height: "100%",
                        background: f.value >= 0 ? "#2D6A4F" : "#F19A9F",
                        borderRadius: f.value >= 0 ? "0 3px 3px 0" : "3px 0 0 3px",
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        left: "50%",
                        top: -2,
                        bottom: -2,
                        width: 1,
                        background: "var(--border-strong)",
                      }}
                    />
                  </div>
                  <span
                    className="mono tnum"
                    style={{
                      width: 48,
                      textAlign: "right",
                      fontSize: 10.5,
                      color: f.value >= 0 ? "var(--pos)" : "var(--neg)",
                    }}
                  >
                    {f.value >= 0 ? "+" : ""}
                    {f.value.toFixed(3)}
                  </span>
                </div>
              );
            })}
          </div>
          <div
            style={{
              marginTop: 12,
              padding: "8px 10px",
              background: "var(--bg)",
              borderRadius: 6,
              fontSize: 10.5,
              color: "var(--text-secondary)",
              lineHeight: 1.5,
            }}
          >
            <strong style={{ color: "var(--text)" }}>Interpretation:</strong> Momentum 12-1이 현재 가장 강한 시그널.
          </div>
        </Panel>
      </div>

      <Panel title="Factor Quintile Performance" muted="Q1 (STRONGEST) → Q5 · 12M" bodyPadding="tight">
        <Heatmap
          firstColumnWidth="140px"
          columnHeaders={FACTORS_QUINTILE.columns}
          rowLabel="Factor"
          rows={FACTORS_QUINTILE.rows.map((r) => ({
            name: r.name,
            cells: r.cells.map(([value, level]) => ({ value, level })),
          }))}
        />
      </Panel>

      <div style={{ height: 10 }} />

      <div className="grid-2-equal" style={{ marginBottom: 10 }}>
        <Panel title="Factor Correlation Matrix" muted="60M · MONTHLY RETURNS" bodyPadding="tight">
          <Heatmap
            firstColumnWidth="80px"
            columnHeaders={FACTORS_CORR.columns}
            rows={FACTORS_CORR.rows.map((r) => ({
              name: r.name,
              cells: r.cells.map(([value, level]) => ({ value, level })),
            }))}
          />
        </Panel>
        <Panel title="Long-Short Equity Curve" muted="β-NEUTRAL · COST-ADJ">
          <svg viewBox="0 0 300 130" preserveAspectRatio="none" style={{ height: 150, width: "100%" }}>
            <defs>
              <pattern id="gridF" width="30" height="26" patternUnits="userSpaceOnUse">
                <path d="M 30 0 L 0 0 0 26" fill="none" stroke="#E6E2DB" strokeWidth="0.5" />
              </pattern>
            </defs>
            <rect width="300" height="130" fill="url(#gridF)" />
            <polyline fill="none" stroke="#1B4332" strokeWidth="2" points="0,110 25,104 50,98 75,88 100,82 125,92 150,74 175,62 200,68 225,54 250,42 275,32 300,22" />
            <polyline fill="none" stroke="#B08968" strokeWidth="1.5" points="0,108 25,101 50,96 75,92 100,84 125,88 150,76 175,70 200,72 225,64 250,52 275,44 300,36" />
            <polyline fill="none" stroke="#6B6B6B" strokeWidth="1.2" strokeDasharray="3,3" points="0,112 25,108 50,104 75,100 100,96 125,94 150,90 175,86 200,82 225,78 250,74 275,70 300,66" />
          </svg>
          <div style={{ display: "flex", gap: 12, marginTop: 8, fontSize: 10.5, color: "var(--text-secondary)", flexWrap: "wrap" }}>
            <span>Momentum L/S +82.4%</span>
            <span>Quality L/S +64.2%</span>
            <span>KOSPI +12.8%</span>
          </div>
        </Panel>
      </div>

      <Panel title="Factor Rebalance Log" muted="MONTHLY · 최근 8건" bodyPadding="p0">
        <ActivityLog entries={FACTORS_ACTIVITY} />
      </Panel>
    </>
  );
}
