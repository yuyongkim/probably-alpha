// Value · DCF — 2-stage DCF for a given symbol (default: Samsung).

import { fetchEnvelope } from "@/lib/api";
import { DCFResult } from "@/components/value/DCFResult";
import type { DcfResponse } from "@/types/value";

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
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">DCF Workbench</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">
          2-stage FCF · ?symbol=005930&amp;g=0.10&amp;gt=0.025
        </p>
      </header>
      <DCFResult dcf={dcf} />
    </div>
  );
}
