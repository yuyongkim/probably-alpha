// RegimeView — HMM-style 4-state probability display with cond-list bars.

import { DenseSummary, type DenseSummaryCell } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import type { RegimeResponse } from "@/types/macro";
import { REGIME_STATES } from "@/lib/quant/mockData";

interface Props {
  regime: RegimeResponse;
}

export function RegimeView({ regime }: Props) {
  const kpi: DenseSummaryCell[] = [
    { label: "현재 레짐", value: regime.current, delta: `Composite ${regime.composite.toFixed(2)}`, tone: "pos" },
    ...REGIME_STATES.slice(1, 4).map((s) => ({ label: s.label, value: `${s.pct}%`, delta: "probability" })),
    { label: "Regime 기반 CAGR", value: "+28.4%", delta: "vs B&H +18.2%", tone: "pos" as const },
    { label: "False Signal Rate", value: "14%", delta: "조기 경보 오탐" },
  ];
  const probs = regime.probabilities;
  const labels = Object.keys(probs);
  return (
    <>
      <DenseSummary cells={kpi} />
      <Panel title="4-State HMM 확률" muted="현재 시장 레짐 분포">
        <div className="cond-list">
          {labels.map((l) => {
            const p = (probs[l] ?? 0) * 100;
            const active = l === regime.current;
            return (
              <div key={l} className="cond-row">
                <span className="cond-check">{active ? "●" : "○"}</span>
                <span className="cond-label">{l}{active ? " (현재)" : ""}</span>
                <div className="cond-bar">
                  <div
                    className="cond-bar-fill"
                    style={{ width: `${p}%`, background: active ? "var(--pos)" : "var(--amber)" }}
                  />
                </div>
                <span className="cond-pct">{p.toFixed(1)}%</span>
              </div>
            );
          })}
        </div>
        <div
          style={{
            marginTop: 14,
            padding: "10px 12px",
            background: "var(--pos-soft)",
            borderRadius: 6,
            fontSize: 11.5,
            color: "var(--text)",
            lineHeight: 1.5,
          }}
        >
          <strong style={{ color: "var(--pos)" }}>권장 전략 ({regime.current}):</strong>{" "}
          Momentum + Growth 비중 70%, Value 20%, Cash 10%. 레버리지 1.0x. 손절 폭 넓게.
        </div>
      </Panel>
    </>
  );
}
