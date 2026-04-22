// Value · Commodities — 원자재 대시보드 (mock · public API only).

import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { Panel } from "@/components/shared/Panel";
import { Heatmap } from "@/components/shared/Heatmap";
import { CommoditiesLinks } from "@/components/value/CommoditiesLinks";
import { COMMODITIES_KPI, COMMODITIES_HEATMAP, COMMODITIES_LINKS } from "@/lib/value/mockData";

export default function ValueCommoditiesPage() {
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "원자재 대시보드", current: true }]}
        title="원자재 대시보드"
        meta="FRED · EIA · LME · KOMIS · 한국석유공사 · 공개 데이터 전용"
      />
      <DenseSummary cells={COMMODITIES_KPI} />
      <Panel title="원자재 × 기간 Heatmap" muted="공개 소스 · 한국 상장사 연관성 태그" bodyPadding="tight" style={{ marginBottom: 10 }}>
        <Heatmap
          firstColumnWidth="130px"
          rowLabel="Commodity"
          columnHeaders={COMMODITIES_HEATMAP.columns}
          rows={COMMODITIES_HEATMAP.rows.map((r) => ({
            name: r.name,
            cells: r.cells.map(([value, level]) => ({ value, level })),
          }))}
        />
      </Panel>
      <Panel title="원자재 연관 KR 종목" muted="민감도 + 방향 동조" bodyPadding="p0">
        <CommoditiesLinks rows={COMMODITIES_LINKS} />
      </Panel>
    </>
  );
}
