// DCFDenseView — full mockup port for Value · DCF subsection.
// Real DCF response for the selected symbol + mock top-N table + activity log.

import { DenseQuote } from "@/components/shared/DenseQuote";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { ActivityLog } from "@/components/shared/ActivityLog";
import type { DcfResponse } from "@/types/value";
import { DCF_KPI, DCF_ROWS, DCF_ACTIVITY } from "@/lib/value/mockData";

interface Props {
  dcf: DcfResponse;
}

const num = (v: number | null | undefined, digits = 0) =>
  v == null ? "—" : v.toLocaleString(undefined, { maximumFractionDigits: digits });

export function DCFDenseView({ dcf }: Props) {
  const w = dcf.wacc_breakdown;
  const kpiWithPerShare: typeof DCF_KPI = [
    ...DCF_KPI.slice(0, 5),
    {
      label: `${dcf.symbol} Per-Share`,
      value: dcf.per_share_value ? Math.round(dcf.per_share_value).toLocaleString() : "—",
      delta: `DCF · WACC ${(dcf.assumptions.wacc * 100).toFixed(2)}%`,
      tone: "pos",
    },
  ];
  return (
    <>
      <DenseQuote
        quote="Price is what you pay. Value is what you get. The difference between the two is your margin of safety."
        attribution="Warren Buffett · Berkshire 1989 Letter"
      />
      <DenseSummary cells={kpiWithPerShare} />

      <div className="grid-2" style={{ marginBottom: 10 }}>
        <Panel
          title="Fair Value vs Market — Top 10"
          muted="FCF · WACC · g · TERM · FV · UPSIDE · CONF"
          bodyPadding="p0"
        >
          <table className="mini">
            <thead>
              <tr>
                <th>#</th>
                <th>Ticker</th>
                <th>Sector</th>
                <th className="num">Price</th>
                <th className="num">WACC</th>
                <th className="num">Fair</th>
                <th className="num">Upside</th>
                <th className="num">MoS</th>
                <th>Conf</th>
              </tr>
            </thead>
            <tbody>
              {DCF_ROWS.map((r) => (
                <tr key={r.rank}>
                  <td className="mono">{r.rank}</td>
                  <td>
                    <span className="ticker-name">{r.ticker}</span>
                    <span className="mono" style={{ marginLeft: 6, color: "var(--text-muted)" }}>
                      {r.code}
                    </span>
                  </td>
                  <td><span className="chip accent">{r.sector}</span></td>
                  <td className="num">{r.price}</td>
                  <td className="num">{r.wacc}</td>
                  <td className="num">{r.fair}</td>
                  <td
                    className="num"
                    style={{ color: r.upsideTone === "pos" ? "var(--pos)" : "var(--neg)", fontWeight: 600 }}
                  >
                    {r.upside}
                  </td>
                  <td className="num">{r.mos}</td>
                  <td>
                    <span className={`chip${r.confTone === "pos" ? " pos" : r.confTone === "neg" ? " neg" : ""}`}>
                      {r.conf}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title={`WACC Breakdown — ${dcf.symbol}`} muted="CAPM · COST OF DEBT">
          <table className="mini">
            <thead>
              <tr>
                <th colSpan={2}>Cost of Equity (Re) · CAPM</th>
                <th className="num">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr><td colSpan={2}>Risk-Free Rate</td><td className="num">{w.rf != null ? `${(w.rf * 100).toFixed(2)}%` : "—"}</td></tr>
              <tr><td colSpan={2}>Equity Risk Premium</td><td className="num">{w.erp != null ? `${(w.erp * 100).toFixed(2)}%` : "—"}</td></tr>
              <tr><td colSpan={2}>β (60M)</td><td className="num">{w.beta != null ? w.beta.toFixed(2) : "—"}</td></tr>
              <tr><td colSpan={2} style={{ fontWeight: 500 }}>Re = Rf + β × ERP</td><td className="num" style={{ fontWeight: 600, color: "var(--accent)" }}>{w.cost_of_equity != null ? `${(w.cost_of_equity * 100).toFixed(2)}%` : "—"}</td></tr>
            </tbody>
          </table>
          <table className="mini" style={{ marginTop: 10 }}>
            <thead>
              <tr>
                <th colSpan={2}>Capital Structure</th>
                <th className="num">Weight</th>
              </tr>
            </thead>
            <tbody>
              <tr><td colSpan={2}>Equity</td><td className="num">{w.w_equity != null ? `${(w.w_equity * 100).toFixed(1)}%` : "—"}</td></tr>
              <tr><td colSpan={2}>Debt</td><td className="num">{w.w_debt != null ? `${(w.w_debt * 100).toFixed(1)}%` : "—"}</td></tr>
              <tr><td colSpan={2}>After-tax Rd</td><td className="num">{w.cost_of_debt_after_tax != null ? `${(w.cost_of_debt_after_tax * 100).toFixed(2)}%` : "—"}</td></tr>
            </tbody>
          </table>
          <div
            style={{
              marginTop: 10,
              padding: "10px 12px",
              background: "var(--accent-soft)",
              borderRadius: 6,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontFamily: "var(--font-serif)", fontSize: 14, color: "var(--accent)", fontWeight: 500 }}>WACC</span>
            <span className="mono" style={{ fontSize: 16, color: "var(--accent)", fontWeight: 600 }}>
              {(w.wacc * 100).toFixed(2)}%
            </span>
          </div>
        </Panel>
      </div>

      <Panel title="DCF 상세 — Stage-1 Projected Cash Flows" muted={`Enterprise ${num(dcf.enterprise_value)}`} bodyPadding="p0" style={{ marginBottom: 10 }}>
        <table className="mini">
          <thead>
            <tr>
              <th>Year</th>
              <th className="num">Projected FCF</th>
              <th className="num">Discounted PV</th>
            </tr>
          </thead>
          <tbody>
            {dcf.stage1.map((s) => (
              <tr key={s.year}>
                <td>t+{s.year}</td>
                <td className="num">{num(s.fcf)}</td>
                <td className="num">{num(s.pv)}</td>
              </tr>
            ))}
            <tr>
              <td style={{ fontWeight: 600 }}>Terminal</td>
              <td className="num">—</td>
              <td className="num" style={{ fontWeight: 600, color: "var(--accent)" }}>{num(dcf.pv_terminal)}</td>
            </tr>
          </tbody>
        </table>
      </Panel>

      <Panel title="DCF Update Log" muted="MODEL REBUILDS · 최근 8건" bodyPadding="p0">
        <ActivityLog entries={DCF_ACTIVITY} />
      </Panel>
    </>
  );
}
