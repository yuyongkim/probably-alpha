// Quant · Factor IC / IR — real IC bars on ky.db.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { ICBar } from "@/components/quant/ICBar";
import type { ICResponse } from "@/types/quant";

export const revalidate = 300;

const FACTORS = ["momentum", "value", "quality", "low_vol", "growth"] as const;

export default async function FactorICPage() {
  const ics = await Promise.all(
    FACTORS.map((f) => fetchEnvelope<ICResponse>(`/api/v1/quant/ic?factor=${f}&period=6m&as_of=2025-04-17`)),
  );
  const avgIc = ics.reduce((s, i) => s + (i.ic ?? 0), 0) / Math.max(ics.length, 1);
  const avgHit = ics.reduce((s, i) => s + i.hit_rate, 0) / Math.max(ics.length, 1);
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Factor IC / IR 분석", current: true }]}
        title="Factor IC / IR 분석"
        meta="INFORMATION COEFFICIENT · 6M · ky.db"
      />
      <DenseSummary
        cells={[
          { label: "Factors", value: String(FACTORS.length), delta: "tracked" },
          { label: "Avg IC", value: avgIc.toFixed(3), delta: "6M", tone: avgIc >= 0 ? "pos" : "neg" },
          { label: "Avg Hit Rate", value: `${(avgHit * 100).toFixed(1)}%`, delta: "decile wins", tone: "pos" },
          { label: "Strongest", value: [...ics].sort((a, b) => (b.ic ?? 0) - (a.ic ?? 0))[0]?.factor ?? "—", delta: "best IC" },
          { label: "Decay", value: "—", delta: "Phase 4" },
          { label: "Source", value: "ky.db", delta: "PIT-safe" },
        ]}
      />
      <Panel title="IC Bars" muted="6-month information coefficient">
        <div className="grid-2-equal">
          {ics.map((ic) => (
            <ICBar key={ic.factor} ic={ic} />
          ))}
        </div>
      </Panel>
    </>
  );
}
