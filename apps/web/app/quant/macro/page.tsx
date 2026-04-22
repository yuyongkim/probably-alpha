// Quant · Macro Compass — dense KPI + Compass radar + playbook.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { CompassRadar } from "@/components/research/CompassRadar";
import { CompassPlaybook } from "@/components/quant/CompassPlaybook";
import type { CompassResponse } from "@/types/macro";

export const revalidate = 300;

export default async function MacroCompassPage() {
  const c = await fetchEnvelope<CompassResponse>("/api/v1/quant/macro/compass");
  const a = c.axes;
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "Macro Compass", current: true }]}
        title="Macro Compass"
        meta="FRED · ECOS · KOSIS · EIA · EXIM"
      />
      <DenseSummary
        cells={[
          { label: "국면", value: c.regime_hint, delta: `Composite ${c.composite.toFixed(2)}`, tone: c.composite >= 0 ? "pos" : "neg" },
          { label: "성장", value: a.growth.score.toFixed(2), delta: a.growth.note },
          { label: "물가", value: a.inflation.score.toFixed(2), delta: a.inflation.note },
          { label: "유동성", value: a.liquidity.score.toFixed(2), delta: a.liquidity.note },
          { label: "신용", value: a.credit.score.toFixed(2), delta: a.credit.note },
          { label: "Generated", value: c.generated_at.slice(11, 16), delta: c.stale ? "STALE" : "fresh", tone: c.stale ? "neg" : "pos" },
        ]}
      />
      <div className="grid-2-equal" style={{ marginBottom: 10 }}>
        <CompassRadar compass={c} />
        <Panel title={`섹터 Playbook · ${c.regime_hint}`} muted="Macro Driven">
          <CompassPlaybook entries={c.playbook} />
        </Panel>
      </div>
    </>
  );
}
