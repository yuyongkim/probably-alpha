// Quant · Universe — dense list of tradable tickers.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { UniverseTable } from "@/components/quant/UniverseTable";
import type { UniverseResponse } from "@/types/quant";

export const revalidate = 600;

export default async function QuantUniversePage() {
  const data = await fetchEnvelope<UniverseResponse>("/api/v1/quant/universe");
  const kospi = data.rows.filter((r) => r.market === "KOSPI").length;
  const kosdaq = data.rows.filter((r) => r.market === "KOSDAQ").length;
  const sectors = new Set(data.rows.map((r) => r.sector)).size;
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "유니버스", current: true }]}
        title="유니버스 관리"
        meta="KRX + KIS 종목마스터"
      />
      <DenseSummary
        cells={[
          { label: "Total", value: String(data.n), delta: "tradable", tone: "pos" },
          { label: "KOSPI", value: String(kospi), delta: "" },
          { label: "KOSDAQ", value: String(kosdaq), delta: "" },
          { label: "Sectors", value: String(sectors), delta: "unique" },
          { label: "Source", value: "ky.db", delta: "KIS + KRX" },
          { label: "Status", value: "LIVE", delta: "자동 동기화", tone: "pos" },
        ]}
      />
      <Panel title="종목 유니버스 (Top 200)" muted={`전체 ${data.n}개`} bodyPadding="p0">
        <UniverseTable rows={data.rows.slice(0, 200)} />
      </Panel>
    </>
  );
}
