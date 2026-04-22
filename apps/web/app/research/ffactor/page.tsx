// Research · Fama-French — simple SIZE / MOM / VAL factor returns.
import { fetchEnvelope } from "@/lib/api";
import type { FactorResult } from "@/types/research";
import { FactorChart } from "@/components/research/FactorChart";
import { DensePage } from "@/components/shared/DensePage";

export const revalidate = 300;

async function loadFactor(factor: string): Promise<FactorResult> {
  return fetchEnvelope<FactorResult>(
    `/api/v1/research/ffactor?factor=${factor}&lookback_days=252`,
  );
}

export default async function FamaFrenchPage() {
  const [mom, size, val] = await Promise.all([
    loadFactor("MOM"), loadFactor("SIZE"), loadFactor("VAL"),
  ]);
  return (
    <DensePage tab="Research" current="Fama-French · AQR" title="Academic Factor Research" meta={`UNIVERSE ${mom.universe_size.toLocaleString()} · QUINTILE L/S · MONTHLY REBAL · 12M`}>
      <div className="quote-strip">&ldquo;The key to understanding the cross-section of stock returns is factor exposure.&rdquo; <span className="attr">— Eugene Fama · Nobel Prize 2013</span></div>
      <div className="space-y-4">
        <FactorChart result={mom} />
        <FactorChart result={size} />
        <FactorChart result={val} />
      </div>
      <p className="mt-6 text-[11px] text-[color:var(--fg-muted)]">
        Note: VAL is a proxy (no book values in PIT yet). SIZE uses close-price as a weak proxy.
        Production HML requires market-cap + book-value joins — see
        <code className="mono mx-1">docs/20_architecture/LEADER_SCORING_SPEC.md</code>.
      </p>
    </DensePage>
  );
}
