// Quant · Rotation — dense playbook cards for current regime.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DenseSummary } from "@/components/shared/DenseSummary";
import { StubCard } from "@/components/shared/StubCard";
import type { RotationResponse } from "@/types/macro";

export const revalidate = 600;

export default async function RotationPage() {
  const r = await fetchEnvelope<RotationResponse>("/api/v1/quant/macro/rotation");
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "섹터 로테이션 플레이북", current: true }]}
        title="섹터 로테이션 플레이북"
        meta="MACRO COMPASS → SECTOR"
      />
      <DenseSummary
        cells={[
          { label: "현 국면", value: r.regime, delta: `Composite ${r.composite.toFixed(2)}`, tone: "pos" },
          { label: "추천 섹터", value: String(r.playbook.length), delta: "우선순위 Top", tone: "pos" },
          { label: "매핑 방식", value: "정적", delta: "Phase 4: 검증" },
          { label: "리밸런싱", value: "분기 1회", delta: "국면 전환 시" },
          { label: "벤치마크", value: "KOSPI", delta: "섹터 초과수익" },
          { label: "Source", value: "QuantDB", delta: "흡수 완료" },
        ]}
      />
      {r.playbook.length === 0 ? (
        <StubCard icon="↻" title="국면 규칙 없음" desc="현재 국면에 매핑된 섹터 룰이 없습니다." />
      ) : (
        <div className="grid-3">
          {r.playbook.map((p, i) => (
            <div key={p.sector} className="kv-card">
              <div className="kv-label">Priority #{i + 1}</div>
              <div className="kv-value">{p.sector}</div>
              <div style={{ marginTop: 8, fontSize: 11.5, color: "var(--text-muted)", lineHeight: 1.5 }}>
                {p.rationale}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
