// Value · Altman Z-Score — dense KPI + single-symbol gauge (real).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { AltmanGauge } from "@/components/value/AltmanGauge";
import type { AltmanResponse } from "@/types/value";
import { ALTMAN_KPI } from "@/lib/value/mockData";

export const revalidate = 300;

export default async function ValueAltmanPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol = "005930" } = await searchParams;
  const z = await fetchEnvelope<AltmanResponse>(`/api/v1/value/altman?symbol=${symbol}`);
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "Altman Z-Score", current: true }]}
        title="Altman Z-Score"
        meta={`BANKRUPTCY RISK · EDWARD ALTMAN 1968 · ${symbol}`}
      />
      <DenseSummary cells={ALTMAN_KPI} />
      <Panel title={`Z-Score — ${symbol}`} muted={`Zone ${z.zone.toUpperCase()} · as of ${z.as_of}`}>
        <AltmanGauge z={z} />
        <div
          style={{
            marginTop: 10,
            padding: "10px 12px",
            background: "var(--neg-soft)",
            borderRadius: 6,
            fontSize: 11,
            color: "var(--neg)",
            lineHeight: 1.5,
          }}
        >
          <strong>Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5</strong>
          <br />
          X1: 운전자본/총자산 · X2: 이익잉여금/총자산 · X3: EBIT/총자산 · X4: 시총/총부채 · X5: 매출/총자산. Z &lt; 1.8 → 2년내 파산확률 80%+.
        </div>
      </Panel>
    </>
  );
}
