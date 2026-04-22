// Value · Magic Formula — dense KPI + real top-N (Greenblatt).

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseQuote } from "@/components/shared/DenseQuote";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { MagicTable } from "@/components/value/MagicTable";
import type { AcademicResponse } from "@/types/quant";
import { MAGIC_KPI } from "@/lib/value/mockData";

export const revalidate = 300;

export default async function ValueMagicPage() {
  const data = await fetchEnvelope<AcademicResponse>("/api/v1/quant/academic/magic_formula?n=30");
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "Magic Formula", current: true }]}
        title="Magic Formula (Greenblatt)"
        meta="EARNINGS YIELD + RETURN ON CAPITAL · JOEL GREENBLATT"
      />
      <DenseQuote quote="Buy good companies at bargain prices." attribution="Joel Greenblatt · The Little Book That Beats the Market" />
      <DenseSummary cells={MAGIC_KPI} />
      <Panel title={`Magic Formula Top ${data.rows.length}`} muted={`ROC + EY 합산 · as of ${data.as_of}`} bodyPadding="p0">
        <MagicTable rows={data.rows} />
      </Panel>
    </>
  );
}
