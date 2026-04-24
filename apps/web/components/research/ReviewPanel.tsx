"use client";
// ReviewPanel — renders /research/review/latest on-demand.
import { useEffect, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type { ReviewResponse } from "@/types/research";

export function ReviewPanel() {
  const [period, setPeriod] = useState<"weekly" | "monthly">("weekly");
  const [data, setData] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const url = `${apiBase()}/api/v1/research/review/latest?period=${period}`;
        const res = await fetch(url, { signal: ctrl.signal });
        const body = (await res.json()) as {
          ok: boolean;
          data?: ReviewResponse;
          error?: { message?: string };
        };
        if (!body.ok || !body.data) {
          setError(body.error?.message ?? "review failed");
          setData(null);
        } else {
          setData(body.data);
        }
      } catch (exc: unknown) {
        if ((exc as { name?: string }).name !== "AbortError") {
          setError(String(exc));
        }
      } finally {
        setLoading(false);
      }
    })();
    return () => ctrl.abort();
  }, [period, tick]);

  return (
    <div className="space-y-4">
      <div
        className="rounded-md border p-3 flex items-center justify-between"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="flex gap-1.5">
          {(["weekly", "monthly"] as const).map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPeriod(p)}
              className="px-3 py-1 text-[12px] rounded border mono"
              style={{
                borderColor: "var(--border)",
                background:
                  period === p ? "var(--surface-raised)" : "transparent",
              }}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 text-[11px] mono text-[color:var(--fg-muted)]">
          <span>as_of {data?.as_of ?? "—"}</span>
          <button
            type="button"
            onClick={() => setTick((t) => t + 1)}
            className="px-2 py-0.5 rounded border"
            style={{ borderColor: "var(--border)" }}
          >
            regenerate
          </button>
        </div>
      </div>

      {error ? (
        <div className="text-xs" style={{ color: "var(--neg)" }}>
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="text-xs text-[color:var(--fg-muted)] mono">loading…</div>
      ) : null}

      {data?.stale_sources && data.stale_sources.length > 0 ? (
        <div className="text-[11px] mono text-[color:var(--fg-muted)]">
          stale sources: {data.stale_sources.join(", ")}
        </div>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data?.sections.map((s) => (
          <div
            key={s.title}
            className="rounded-md border p-3"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <h3 className="text-[13px] font-semibold mb-2">{s.title}</h3>
            <ul className="space-y-1">
              {s.rows.map((r, i) => (
                <li
                  key={`${s.title}-${i}`}
                  className="flex items-baseline justify-between gap-2 text-[12px]"
                >
                  <span className="min-w-0 truncate">
                    {r.symbol ? (
                      <span className="mono text-[color:var(--fg-muted)] mr-1">
                        {r.symbol}
                      </span>
                    ) : null}
                    {r.name}
                    {r.trend_template ? (
                      <span className="ml-1 text-[10px] mono text-[color:var(--fg-muted)]">
                        TT {r.trend_template}
                      </span>
                    ) : null}
                  </span>
                  <span className="mono text-[color:var(--fg-muted)] shrink-0">
                    {r.leader_score !== undefined
                      ? r.leader_score.toFixed(3)
                      : r.score !== undefined && r.score !== null
                      ? Number(r.score).toFixed(3)
                      : ""}
                    {r.note ? ` · ${r.note}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
