// NightlyHistory — renders the nightly+weekly run log surfaced by
// /api/v1/admin/nightly_runs + /weekly_runs.
//
// Presentational only: the caller passes already-fetched arrays. The page
// owns the network calls so Next can revalidate both endpoints together.

import type { NightlyRunSummary, NightlyStageSummary } from "@/types/admin";

interface Props {
  nightly: NightlyRunSummary[];
  weekly: NightlyRunSummary[];
  opsRoot: string;
  warning?: string | null;
}

function fmtDuration(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds - m * 60);
  return `${m}m ${s}s`;
}

function fmtWhen(iso: string | null): string {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toISOString().replace("T", " ").slice(0, 19) + "Z";
  } catch {
    return iso;
  }
}

function statusTone(run: NightlyRunSummary): "pos" | "neg" | "amber" | undefined {
  if (run.error) return "neg";
  if (run.stage_fail > 0 && run.stage_ok > 0) return "amber"; // partial success
  if (run.stage_fail > 0) return "neg";
  if (run.dry_run) return "amber";
  return "pos";
}

function statusLabel(run: NightlyRunSummary): string {
  if (run.error) return "unreadable";
  if (run.dry_run) return "dry-run";
  if (run.stage_fail > 0 && run.stage_ok > 0) return "partial";
  if (run.stage_fail > 0) return "failed";
  return "ok";
}

function StageBar({ stage, maxDuration }: { stage: NightlyStageSummary; maxDuration: number }) {
  const pct = maxDuration > 0 ? Math.max(4, (stage.duration_s / maxDuration) * 100) : 0;
  const colour =
    stage.status === "fail"
      ? "var(--neg, #d03b3b)"
      : stage.status === "dry_run"
      ? "var(--text-muted, #8a8a8a)"
      : "var(--pos, #3b8f4f)";
  return (
    <div className="flex items-center gap-2 text-[11px]">
      <span className="mono" style={{ minWidth: 150 }}>
        {stage.name}
      </span>
      <div
        className="flex-1 h-2 rounded"
        style={{ background: "var(--surface-2, #1a1a1a)" }}
      >
        <div
          className="h-2 rounded"
          style={{ width: `${pct}%`, background: colour }}
        />
      </div>
      <span className="mono" style={{ minWidth: 60, textAlign: "right" }}>
        {fmtDuration(stage.duration_s)}
      </span>
      <span className="mono" style={{ minWidth: 70, textAlign: "right", color: "var(--text-muted)" }}>
        {stage.rows_added.toLocaleString()} rows
      </span>
    </div>
  );
}

function RunRow({ run }: { run: NightlyRunSummary }) {
  const tone = statusTone(run);
  const toneColor =
    tone === "pos"
      ? "var(--pos, #3b8f4f)"
      : tone === "neg"
      ? "var(--neg, #d03b3b)"
      : tone === "amber"
      ? "var(--amber, #c88a2a)"
      : "var(--text-muted)";
  return (
    <li
      className="rounded-md border p-3"
      style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <div>
          <span
            className="text-[10px] uppercase tracking-widest mr-2 px-1.5 py-0.5 rounded"
            style={{ background: "var(--surface-2)", color: toneColor }}
          >
            {statusLabel(run)}
          </span>
          <span className="mono text-sm">{run.file}</span>
        </div>
        <div className="mono text-[11px]" style={{ color: "var(--text-muted)" }}>
          {fmtWhen(run.started_at)} · {fmtDuration(run.duration_s)} ·{" "}
          {run.total_rows_added.toLocaleString()} rows
        </div>
      </div>
      {run.error ? (
        <pre className="text-[11px] mono leading-relaxed opacity-80 whitespace-pre-wrap"
             style={{ color: "var(--neg)" }}>
          {run.error}
        </pre>
      ) : run.stages.length === 0 ? (
        <p className="text-[11px] opacity-60">stages: (empty)</p>
      ) : (
        <div className="space-y-1">
          {run.stages.map((s) => (
            <StageBar
              key={s.name}
              stage={s}
              maxDuration={Math.max(
                1,
                ...run.stages.map((x) => x.duration_s),
              )}
            />
          ))}
        </div>
      )}
      {run.errors.length > 0 ? (
        <pre className="mt-2 text-[11px] mono leading-relaxed whitespace-pre-wrap"
             style={{ color: "var(--neg)" }}>
          {run.errors.join("\n")}
        </pre>
      ) : null}
    </li>
  );
}

export function NightlyHistory({ nightly, weekly, opsRoot, warning }: Props) {
  const nightlySucc = nightly.filter((r) => !r.error && r.stage_fail === 0 && !r.dry_run).length;
  const nightlyFail = nightly.filter((r) => r.stage_fail > 0 || !!r.error).length;
  const weeklySucc = weekly.filter((r) => !r.error && r.stage_fail === 0 && !r.dry_run).length;
  const weeklyFail = weekly.filter((r) => r.stage_fail > 0 || !!r.error).length;

  return (
    <div className="space-y-6">
      <p className="text-sm text-[color:var(--fg-muted)]">
        <code className="mono">{opsRoot}</code> — 최근 {nightly.length} nightly + {weekly.length} weekly 실행.
        {warning ? ` · ${warning}` : ""}
      </p>

      <section>
        <h2 className="text-sm uppercase tracking-widest mb-2" style={{ color: "var(--accent)" }}>
          Nightly (최근 {nightly.length}회 · ok {nightlySucc} · fail {nightlyFail})
        </h2>
        {nightly.length === 0 ? (
          <p className="text-sm opacity-60">아직 실행 기록이 없습니다. <code>python scripts/nightly.py --dry-run</code> 으로 시작.</p>
        ) : (
          <ul className="space-y-2">
            {nightly.map((r) => (
              <RunRow key={r.file} run={r} />
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-sm uppercase tracking-widest mb-2" style={{ color: "var(--accent)" }}>
          Weekly (최근 {weekly.length}회 · ok {weeklySucc} · fail {weeklyFail})
        </h2>
        {weekly.length === 0 ? (
          <p className="text-sm opacity-60">아직 실행 기록이 없습니다. 일요일 04:00 에 자동 실행됩니다.</p>
        ) : (
          <ul className="space-y-2">
            {weekly.map((r) => (
              <RunRow key={r.file} run={r} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
