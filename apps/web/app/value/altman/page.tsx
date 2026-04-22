// Value · Altman — single symbol Z-Score gauge, default Samsung.

import { fetchEnvelope } from "@/lib/api";
import { AltmanGauge } from "@/components/value/AltmanGauge";
import type { AltmanResponse } from "@/types/value";

export default async function ValueAltmanPage({
  searchParams,
}: {
  searchParams: Promise<{ symbol?: string }>;
}) {
  const { symbol = "005930" } = await searchParams;
  const z = await fetchEnvelope<AltmanResponse>(
    `/api/v1/value/altman?symbol=${symbol}`,
  );
  return (
    <div className="space-y-4">
      <header>
        <h1 className="display text-3xl">Altman Z-Score</h1>
        <p className="text-sm text-[color:var(--fg-muted)]">?symbol=005930</p>
      </header>
      <AltmanGauge z={z} />
    </div>
  );
}
