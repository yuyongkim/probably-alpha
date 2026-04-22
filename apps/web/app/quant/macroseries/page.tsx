// Quant · Macro Series — FRED/ECOS timeseries with dense wrapper.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { Panel } from "@/components/shared/Panel";
import { MacroSeriesChart } from "@/components/research/MacroSeriesChart";
import type { MacroSeriesResponse } from "@/types/macro";

export const revalidate = 600;

const SERIES = [
  { source: "fred", id: "DFF", label: "US Fed Funds Rate" },
  { source: "fred", id: "GDP", label: "US GDP" },
  { source: "ecos", id: "722Y001/0101000", label: "KR 기준금리" },
];

export default async function MacroSeriesPage() {
  const results = await Promise.all(
    SERIES.map((s) =>
      fetchEnvelope<MacroSeriesResponse>(
        `/api/v1/quant/macro/series?source=${s.source}&series_id=${encodeURIComponent(s.id)}`,
      ),
    ),
  );
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "매크로 시계열", current: true }]}
        title="매크로 시계열"
        meta="FRED · ECOS · KOSIS · EIA · EXIM"
      />
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {SERIES.map((s, i) => (
          <Panel key={s.id} title={s.label} muted={`${s.source.toUpperCase()} · ${s.id}`} bodyPadding="tight">
            <MacroSeriesChart label={s.label} data={results[i]} />
          </Panel>
        ))}
      </div>
    </>
  );
}
