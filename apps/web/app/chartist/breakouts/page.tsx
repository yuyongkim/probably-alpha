// Chartist · Breakouts — today's confirmed 52w high breakouts plus
// "near-high" candidates (within 2 % of the 252-day high).
import { fetchEnvelope } from "@/lib/api";
import type { BreakoutsResponse } from "@/types/chartist";
import { BreakoutsTable } from "@/components/chartist/breakouts/BreakoutsTable";

export const revalidate = 60;

export default async function ChartistBreakoutsPage() {
  const [breakouts, near] = await Promise.all([
    fetchEnvelope<BreakoutsResponse>(
      "/api/v1/chartist/breakouts/52w?vol_x_min=1.0&limit=50",
    ),
    fetchEnvelope<BreakoutsResponse>(
      "/api/v1/chartist/breakouts/near_52w?proximity_pct=2.0&vol_x_min=0.7&limit=80",
    ),
  ]);
  const today = new Date().toISOString().slice(0, 10);
  const stale = breakouts.as_of < today;

  return (
    <div>
      <div className="flex items-baseline justify-between mb-3">
        <div>
          <h1 className="display text-3xl">Breakouts</h1>
          <div className="text-xs text-[color:var(--fg-muted)] mt-1">
            KRX · as-of{" "}
            <span style={{ color: stale ? "var(--accent)" : "inherit" }}>
              {breakouts.as_of}
            </span>
            {stale && (
              <span
                className="ml-2 text-[10px] px-1.5 py-[1px] rounded border"
                style={{
                  borderColor: "var(--accent)",
                  color: "var(--accent)",
                  background: "var(--accent-soft)",
                }}
              >
                stale · today {today}
              </span>
            )}{" "}
            · 252일 고점 돌파 + 임박 후보
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <Section
          title="오늘 돌파"
          subtitle={`${breakouts.rows.length} 종목 · close ≥ 52w high · vol ≥ 1.0×`}
          empty="아직 확인된 돌파 종목이 없습니다. (임박 후보는 아래 확인)"
          rows={breakouts.rows}
        />
        <Section
          title="돌파 임박"
          subtitle={`${near.rows.length} 종목 · within 2.0 % of 52w high · vol ≥ 0.7×`}
          empty="2 % 근접 후보가 없습니다."
          rows={near.rows}
        />
      </div>
    </div>
  );
}

function Section({
  title,
  subtitle,
  empty,
  rows,
}: {
  title: string;
  subtitle: string;
  empty: string;
  rows: BreakoutsResponse["rows"];
}) {
  if (!rows || rows.length === 0) {
    return (
      <div
        className="rounded-md border px-4 py-5 text-[11.5px] text-[color:var(--fg-muted)]"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="display text-base text-[color:var(--fg)]">{title}</div>
        <div className="text-[10.5px] mt-0.5 mb-2">{subtitle}</div>
        <div>{empty}</div>
      </div>
    );
  }
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h2 className="display text-lg">{title}</h2>
        <span className="text-[10.5px] text-[color:var(--fg-muted)]">{subtitle}</span>
      </div>
      <BreakoutsTable rows={rows} />
    </div>
  );
}
