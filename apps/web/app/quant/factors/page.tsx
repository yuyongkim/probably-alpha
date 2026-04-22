// Quant · Factors — real ky.db factor screener.

import { fetchEnvelope } from "@/lib/api";
import { QuantFactorTable } from "@/components/quant/QuantFactorTable";
import type { FactorResponse } from "@/types/quant";

export default async function QuantFactorsPage() {
  const data = await fetchEnvelope<FactorResponse>("/api/v1/quant/factors?limit=100");
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">Factor Screener</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">
          KOSPI+KOSDAQ · 팩터 백분위 랭크 · as of {data.as_of}
        </p>
      </header>
      <QuantFactorTable rows={data.rows} />
    </div>
  );
}
