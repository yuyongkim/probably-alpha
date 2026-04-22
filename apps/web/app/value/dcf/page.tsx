// Value · DCF — dense mockup port with real 2-stage DCF for selected symbol.

import { fetchEnvelope } from "@/lib/api";
import { PageHeader } from "@/components/shared/PageHeader";
import { DCFDenseView } from "@/components/value/DCFDenseView";
import type { DcfResponse } from "@/types/value";

export const revalidate = 60;

export default async function ValueDcfPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string; g?: string; gt?: string }>;
}) {
  const { symbol = "005930", g = "0.10", gt = "0.025" } = await searchParams;
  const dcf = await fetchEnvelope<DcfResponse>(
    `/api/v1/value/dcf/${symbol}?growth_high=${g}&growth_term=${gt}`,
  );
  return (
    <>
      <PageHeader
        crumbs={[{ label: "Value" }, { label: "DCF 모델", current: true }]}
        title="DCF Valuations"
        meta={`FAIR VALUE vs MARKET · ${symbol} · ${dcf.as_of}`}
        subNav={[
          { label: "전체", active: true },
          { label: "Upside ≥ 30%" },
          { label: "Deep Value" },
          { label: "A-Grade" },
          { label: "최근 공시" },
        ]}
      />
      <DCFDenseView dcf={dcf} />
    </>
  );
}
