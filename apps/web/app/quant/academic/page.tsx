// Quant · Academic — 4 strategy dense cards + Top-N per strategy.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { AcademicDenseView } from "@/components/quant/AcademicDenseView";
import type { AcademicResponse } from "@/types/quant";

export const revalidate = 60;

const STRATEGIES: Array<[string, string]> = [
  ["magic_formula", "Magic Formula (Greenblatt)"],
  ["deep_value", "Deep Value (Graham)"],
  ["fast_growth", "Fast Growth"],
  ["super_quant", "Super Quant"],
];

export default async function QuantAcademicPage() {
  const bundles = await Promise.all(
    STRATEGIES.map(async ([s, displayName]) => {
      const res = await fetchEnvelope<AcademicResponse>(`/api/v1/quant/academic/${s}?n=10`);
      return { ...res, displayName };
    }),
  );
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Quant" }, { label: "4 학술 전략", current: true }]}
        title="4 학술 전략"
        meta="MAGIC FORMULA · DEEP VALUE · FAST GROWTH · SUPER QUANT"
      />
      <AcademicDenseView bundles={bundles} />
    </>
  );
}
