// Admin · Pipeline — real nightly + weekly run history surfaced from
// ~/.ky-platform/data/ops/ via /api/v1/admin/nightly_runs & /weekly_runs.
import { fetchEnvelope } from "@/lib/api";
import type { NightlyRunsResponse } from "@/types/admin";
import { DensePage } from "@/components/shared/DensePage";
import { SummaryCards, type RawSummaryCell } from "@/components/shared/SummaryCards";
import { NightlyHistory } from "@/components/admin/NightlyHistory";

export const revalidate = 60;

async function loadRuns(path: string): Promise<NightlyRunsResponse> {
  try {
    return await fetchEnvelope<NightlyRunsResponse>(path);
  } catch {
    // Graceful empty-state when the API is down or the ops/ directory doesn't
    // exist yet. Surfacing this via `warning` is intentional — users can still
    // navigate the page and learn what to run.
    return {
      root: "~/.ky-platform/data/ops",
      kind: path.includes("weekly") ? "weekly" : "nightly",
      limit: 0,
      runs: [],
      warning: "API unreachable — showing empty state",
    };
  }
}

export default async function PipelinePage() {
  const [nightly, weekly] = await Promise.all([
    loadRuns("/api/v1/admin/nightly_runs?limit=7"),
    loadRuns("/api/v1/admin/weekly_runs?limit=7"),
  ]);

  const nRuns = nightly.runs;
  const wRuns = weekly.runs;

  const nOk = nRuns.filter((r) => !r.error && r.stage_fail === 0 && !r.dry_run).length;
  const nFail = nRuns.filter((r) => r.stage_fail > 0 || !!r.error).length;
  const lastNightly = nRuns[0];
  const rowsLast = lastNightly?.total_rows_added ?? 0;
  const durationLast =
    lastNightly && lastNightly.duration_s > 0
      ? lastNightly.duration_s >= 60
        ? `${Math.floor(lastNightly.duration_s / 60)}m ${Math.round(lastNightly.duration_s % 60)}s`
        : `${lastNightly.duration_s.toFixed(1)}s`
      : "—";

  const kpis: RawSummaryCell[] = [
    {
      label: "Nightly · 7일",
      value: `${nOk}/${nRuns.length}`,
      delta: `성공 ${nOk} · 실패 ${nFail}`,
      tone: nFail === 0 ? "pos" : nOk > 0 ? "amber" : "neg",
    },
    {
      label: "Weekly · 7주",
      value: `${wRuns.filter((r) => r.stage_fail === 0 && !r.error).length}/${wRuns.length}`,
      delta: wRuns.length > 0 ? `마지막 ${wRuns[0]?.file ?? ""}` : "기록 없음",
      tone: wRuns.some((r) => r.stage_fail > 0) ? "amber" : "pos",
    },
    {
      label: "최근 Nightly Rows",
      value: rowsLast.toLocaleString(),
      delta: lastNightly?.started_at
        ? new Date(lastNightly.started_at).toISOString().slice(0, 10)
        : "—",
    },
    {
      label: "최근 Nightly 소요",
      value: durationLast,
      delta: lastNightly
        ? `stage ok ${lastNightly.stage_ok}/${lastNightly.stage_count}`
        : "—",
      tone:
        lastNightly && lastNightly.stage_fail > 0 ? "amber" : "pos",
    },
  ];

  return (
    <DensePage
      tab="Admin"
      current="파이프라인 Runner"
      title="Nightly · Weekly 파이프라인 운영"
      meta="OPS · NIGHTLY + WEEKLY RUN HISTORY"
    >
      <SummaryCards cells={kpis} />
      <NightlyHistory
        nightly={nRuns}
        weekly={wRuns}
        opsRoot={nightly.root}
        warning={nightly.warning ?? weekly.warning}
      />
    </DensePage>
  );
}
