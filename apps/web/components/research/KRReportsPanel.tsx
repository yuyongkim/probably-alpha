"use client";
// KRReportsPanel — Naver Finance research reports by category.
import { useEffect, useState } from "react";
import { apiBase } from "@/lib/apiBase";
import type { KRReportsResponse } from "@/types/research";

const CATEGORIES: { slug: string; label: string }[] = [
  { slug: "company", label: "종목" },
  { slug: "industry", label: "산업" },
  { slug: "market", label: "시장" },
  { slug: "debriefing", label: "탐방" },
  { slug: "economy", label: "경제" },
];

export function KRReportsPanel() {
  const [cat, setCat] = useState("company");
  const [data, setData] = useState<KRReportsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ctrl = new AbortController();
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const url = `${apiBase()}/api/v1/research/krreports/list?category=${cat}&limit=25`;
        const res = await fetch(url, { signal: ctrl.signal });
        const body = (await res.json()) as {
          ok: boolean;
          data?: KRReportsResponse;
          error?: { message?: string };
        };
        if (!body.ok || !body.data) {
          setError(body.error?.message ?? "reports failed");
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
  }, [cat]);

  const summary = data?.summary;

  return (
    <div className="space-y-4">
      <div
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="flex flex-wrap gap-1.5">
          {CATEGORIES.map((c) => (
            <button
              key={c.slug}
              type="button"
              onClick={() => setCat(c.slug)}
              className="px-3 py-1 text-[12px] rounded border mono"
              style={{
                borderColor: "var(--border)",
                background:
                  cat === c.slug ? "var(--surface-raised)" : "transparent",
              }}
            >
              {c.label}
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between mt-2 text-[11px] text-[color:var(--fg-muted)]">
          <span>source · naver finance research</span>
          <span className="mono">
            {loading ? "fetching…" : `${data?.count ?? 0} reports`}
          </span>
        </div>
      </div>

      {summary ? (
        <div className="grid grid-cols-3 gap-2">
          <MiniKpi label="커버 증권사" value={summary.broker_count} tone="neutral" />
          <MiniKpi label="목표가 상향" value={summary.target_up} tone="pos" />
          <MiniKpi label="목표가 하향" value={summary.target_down} tone="neg" />
        </div>
      ) : null}

      {error ? (
        <div className="text-xs" style={{ color: "var(--neg)" }}>
          {error}
        </div>
      ) : null}

      <ul className="space-y-1.5">
        {data?.items.map((it, i) => (
          <li
            key={`${it.link}-${i}`}
            className="rounded-md border p-2.5 flex items-baseline justify-between gap-2"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <div className="min-w-0">
              <a
                href={it.link}
                target="_blank"
                rel="noreferrer"
                className="text-[13px] leading-snug hover:underline block truncate"
              >
                {it.title}
              </a>
              <div className="text-[11px] mono text-[color:var(--fg-muted)] mt-0.5">
                {it.broker}
                {it.symbol ? ` · ${it.symbol}` : ""}
                {it.published ? ` · ${it.published}` : ""}
              </div>
            </div>
            <DirectionChip dir={it.direction} tp={it.target_price} />
          </li>
        ))}
      </ul>
    </div>
  );
}

function MiniKpi({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
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

function DirectionChip({
  dir,
  tp,
}: {
  dir: "up" | "down" | null;
  tp: string | null;
}) {
  if (!dir && !tp) {
    return (
      <span className="text-[11px] mono text-[color:var(--fg-muted)]">—</span>
    );
  }
  const color =
    dir === "up" ? "var(--pos)" : dir === "down" ? "var(--neg)" : "var(--fg)";
  const arrow = dir === "up" ? "▲" : dir === "down" ? "▼" : "●";
  return (
    <span className="text-[11px] mono shrink-0" style={{ color }}>
      {arrow} {tp ? `₩${tp}` : dir}
    </span>
  );
}
