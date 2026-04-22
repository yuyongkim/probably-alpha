// OverviewLower — allocation bars + recent fills + risk metrics + AI prompts.
import { AllocationBars } from "@/components/execute/AllocationBars";
import {
  aiPrompts,
  assetAllocation,
  recentFills,
  riskMetrics,
  sectorAllocation,
  strategyAllocation,
} from "@/lib/execute/mockData";

export function OverviewLower() {
  return (
    <>
      <div className="panel" style={{ marginBottom: 10 }}>
        <div className="panel-header"><h2>자산 배분</h2><span className="muted">자산군 / 통화 / 섹터 집중도</span></div>
        <div className="panel-body">
          <div className="grid-3">
            <AllocationBars heading="자산군" bars={assetAllocation} />
            <AllocationBars heading="섹터" bars={sectorAllocation} />
            <AllocationBars heading="전략별" bars={strategyAllocation} />
          </div>
        </div>
      </div>
      <div className="grid-2" style={{ marginBottom: 10 }}>
        <div className="panel">
          <div className="panel-header"><h2>최근 체결</h2><span className="muted">TODAY · 7 FILLS</span></div>
          <div className="panel-body p0">
            <table className="mini">
              <thead>
                <tr>
                  <th>Time</th><th>Side</th><th>Ticker</th><th className="num">Qty</th>
                  <th className="num">Price</th><th className="num">Amount</th><th>Venue</th><th>Strategy</th>
                </tr>
              </thead>
              <tbody>
                {recentFills.map((f, i) => (
                  <tr key={`${f.time}-${i}`}>
                    <td className="mono">{f.time}</td>
                    <td><span className={`chip ${f.side === "BUY" ? "pos" : "neg"}`}>{f.side}</span></td>
                    <td><span className="ticker-name">{f.ticker}</span></td>
                    <td className="num">{f.qty}</td>
                    <td className="num">{f.price}</td>
                    <td className="num">{f.amount}</td>
                    <td>{f.venue}</td>
                    <td>
                      <span className={`chip${f.strategyTone === "accent" ? " accent" : f.strategyTone === "amber" ? " amber" : ""}`}>
                        {f.strategy}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="panel">
          <div className="panel-header"><h2>리스크 메트릭</h2><span className="muted">PORTFOLIO-LEVEL</span></div>
          <div className="panel-body">
            <table className="mini">
              <thead><tr><th>Metric</th><th className="num">Value</th><th>Status</th><th className="num">Limit</th></tr></thead>
              <tbody>
                {riskMetrics.map((m) => (
                  <tr key={m.metric}>
                    <td>{m.metric}</td>
                    <td className="num" style={m.valueTone === "neg" ? { color: "var(--neg)" } : undefined}>
                      {m.value}
                    </td>
                    <td>
                      <span className={`chip${m.statusTone !== "default" ? ` ${m.statusTone}` : ""}`}>
                        {m.status}
                      </span>
                    </td>
                    <td className="num">{m.limit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div style={{ marginTop: 10, padding: "8px 10px", background: "var(--amber-soft)", borderRadius: 6, fontSize: 10.5, color: "var(--amber)", lineHeight: 1.5 }}>
              <strong>ALERT:</strong> 반도체 섹터 42.1% → 리밸런스 권고. 한미반도체/HPSP 1 step 익절 또는 타 섹터 신규 진입.
            </div>
          </div>
        </div>
      </div>
      <div className="panel" style={{ marginBottom: 10 }}>
        <div className="panel-header"><h2>Ask Claude — MCP Trading</h2><span className="muted">자연어 지시 → KIS 실제 주문 · OAuth 토큰 기반</span></div>
        <div className="panel-body">
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {aiPrompts.map((p) => (
              <div key={p} style={{ padding: "8px 12px", background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12, color: "var(--text-secondary)" }}>
                <span style={{ color: "var(--accent)", fontFamily: "var(--font-mono)", fontSize: 10.5, marginRight: 8 }}>&gt;_</span>
                {p}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
