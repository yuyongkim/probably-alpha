// Quant · QuantKing Strategies — 6 kv-cards (dense grid-3).

import { PageHeader } from "@/components/shared/PageHeader";
import { STRATEGY_CARDS } from "@/lib/quant/mockData";

export const revalidate = 60;

export default function QuantStrategiesPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "QuantKing 전략", current: true }]}
        title="QuantKing 전략 라이브러리"
        meta="12 STRATEGIES · 주간 리밸런싱"
      />
      <div className="grid-3">
        {STRATEGY_CARDS.map((c) => (
          <div key={c.label} className="kv-card">
            <div className="kv-label">{c.label}</div>
            <div className="kv-value">{c.value}</div>
            <div
              style={{
                marginTop: 10,
                display: "flex",
                justifyContent: "space-between",
                fontSize: 11.5,
                color: "var(--text-muted)",
              }}
            >
              <span>{c.meta}</span>
              <span className={`chip${c.chipTone === "pos" ? " pos" : ""}`}>{c.chip}</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
