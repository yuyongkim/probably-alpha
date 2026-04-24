"use client";
// NewsPanel — keyword sentiment over Naver search news.
import { useEffect, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type { NewsSearchResponse } from "@/types/research";

const DEFAULT_PRESETS = ["삼성전자", "SK하이닉스", "코스피", "현대차", "카카오"];

export function NewsPanel() {
  const [q, setQ] = useState("삼성전자");
  const [data, setData] = useState<NewsSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!q.trim()) {
      setData(null);
      return;
    }
    const ctrl = new AbortController();
    const t = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const url = `${apiBase()}/api/v1/research/news/search?q=${encodeURIComponent(q)}&display=12`;
        const res = await fetch(url, { signal: ctrl.signal });
        const body = (await res.json()) as {
          ok: boolean;
          data?: NewsSearchResponse;
          error?: { message?: string };
        };
        if (!body.ok || !body.data) {
          setError(body.error?.message ?? "news failed");
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
    }, 300);
    return () => {
      ctrl.abort();
      clearTimeout(t);
    };
  }, [q]);

  const summary = data?.summary;

  return (
    <div className="space-y-4">
      <div
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <label className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
          news query
        </label>
        <input
          type="text"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full mt-1 py-2 px-3 rounded bg-transparent border mono text-sm outline-none"
          style={{ borderColor: "var(--border)" }}
          placeholder="종목명 또는 섹터명"
        />
        <div className="flex flex-wrap gap-1.5 mt-2">
          {DEFAULT_PRESETS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setQ(p)}
              className="px-2 py-0.5 text-[11px] rounded border mono"
              style={{
                borderColor: "var(--border)",
                background: q === p ? "var(--surface-raised)" : "transparent",
              }}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between mt-2 text-[11px] text-[color:var(--fg-muted)]">
          <span>
            source · <span className="mono">{data?.source ?? "—"}</span>
          </span>
          <span className="mono">
            {loading ? "fetching…" : summary ? `${summary.n} items` : "0 items"}
          </span>
        </div>
      </div>

      {summary ? (
        <div className="grid grid-cols-4 gap-2 text-center">
          <KpiCell label="avg score" value={summary.avg_score.toFixed(2)} tone="neutral" />
          <KpiCell
            label="positive"
            value={String(summary.positive)}
            tone="pos"
          />
          <KpiCell
            label="negative"
            value={String(summary.negative)}
            tone="neg"
          />
          <KpiCell
            label="neutral"
            value={String(summary.neutral)}
            tone="neutral"
          />
        </div>
      ) : null}

      {error ? (
        <div className="text-xs" style={{ color: "var(--neg)" }}>
          {error}
        </div>
      ) : null}

      <ul className="space-y-2">
        {data?.items.map((it, i) => (
          <li
            key={`${it.link}-${i}`}
            className="rounded-md border p-3"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <div className="flex items-baseline justify-between gap-2 text-[11px] mono text-[color:var(--fg-muted)]">
              <span className="truncate">{it.source || "—"}</span>
              <SentimentChip label={it.sentiment_label} score={it.sentiment_score} />
            </div>
            <a
              href={it.link}
              target="_blank"
              rel="noreferrer"
              className="text-sm mt-1 leading-snug block hover:underline"
            >
              {it.title}
            </a>
            {it.description ? (
              <p className="text-[12px] text-[color:var(--fg-muted)] mt-1 leading-snug line-clamp-2">
                {it.description}
              </p>
            ) : null}
            {it.pos_hits.length > 0 || it.neg_hits.length > 0 ? (
              <div className="flex flex-wrap gap-1 mt-2">
                {it.pos_hits.map((k) => (
                  <span
                    key={`p-${k}`}
                    className="text-[10px] mono px-1.5 py-0.5 rounded"
                    style={{
                      background: "var(--pos-surface, rgba(56,161,105,0.1))",
                      color: "var(--pos)",
                    }}
                  >
                    +{k}
                  </span>
                ))}
                {it.neg_hits.map((k) => (
                  <span
                    key={`n-${k}`}
                    className="text-[10px] mono px-1.5 py-0.5 rounded"
                    style={{
                      background: "var(--neg-surface, rgba(220,53,69,0.1))",
                      color: "var(--neg)",
                    }}
                  >
                    −{k}
                  </span>
                ))}
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}

function KpiCell({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "pos" | "neg" | "neutral";
}) {
  const color =
    tone === "pos" ? "var(--pos)" : tone === "neg" ? "var(--neg)" : "var(--fg)";
  return (
    <div
      className="rounded-md border p-2"
      style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
    >
      <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)]">
        {label}
      </div>
      <div className="text-lg mono" style={{ color }}>
        {value}
      </div>
    </div>
  );
}

function SentimentChip({
  label,
  score,
}: {
  label: "positive" | "negative" | "neutral";
  score: number;
}) {
  const color =
    label === "positive"
      ? "var(--pos)"
      : label === "negative"
      ? "var(--neg)"
      : "var(--fg-muted)";
  return (
    <span className="mono" style={{ color }}>
      {label} {score >= 0 ? "+" : ""}
      {score.toFixed(2)}
    </span>
  );
}
