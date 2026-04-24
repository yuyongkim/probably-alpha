"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:31300";

// Exact shape of /api/v1/chartist/today (confirmed from live API 2026-04-24).
interface KpiPill {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "neutral";
}
interface Leader {
  symbol: string;
  name?: string;
  sector?: string;
  leader_score?: number;
  trend_template?: string;
  rs?: number;
  d1?: number;
  d5?: number;
  m1?: number;
  vol_x?: number;
  pattern?: string;
}
interface SectorRow {
  rank?: number;
  name: string;
  score?: number;
  d1?: number;
  d5?: number;
  sparkline?: number[];
}
interface WizardPass {
  name: string;
  condition?: string;
  pass_count?: number;
  total?: number;
  delta_vs_yesterday?: number;
}
interface StageRow {
  name: string;
  count?: number;
  pct?: number;
  color_hint?: string;
}
interface Breakout {
  ticker?: string;
  symbol: string;
  market?: string;
  pct_up?: number;
  vol_x?: number;
  sector?: string;
}
interface TodayBundle {
  date?: string;
  owner_id?: string;
  universe_size?: number;
  market: KpiPill[];
  summary: KpiPill[];
  leaders: Leader[];
  sectors: SectorRow[];
  wizards_pass?: WizardPass[];
  stage_dist?: StageRow[];
  breakouts?: Breakout[];
  last_backtest_cagr?: number | null;
}

const TABS: Array<{
  href: string;
  label: string;
  blurb: string;
  details: string;
}> = [
  {
    href: "/chartist/today",
    label: "Chartist",
    blurb: "오늘의 시장 · 섹터 · 리더",
    details: "Top sectors · leader scan · TT 8/8 · 위저드별 화면",
  },
  {
    href: "/quant/factors",
    label: "Quant",
    blurb: "팩터 · 백테스트 · 리서치",
    details: "Fama-French · Magic Formula · 매크로 컴퍼스 · walk-forward",
  },
  {
    href: "/value/dcf",
    label: "Value",
    blurb: "DCF · 재무 · 버핏 RAG",
    details: "WACC · ROIC · Piotroski9 · Altman5 · Moat v2 · 세그먼트",
  },
  {
    href: "/execute/overview",
    label: "Execute",
    blurb: "포지션 · 주문 · 리스크",
    details: "KIS OAuth · 호가/체결 SSE · 백테스트 실행",
  },
  {
    href: "/research/airesearch",
    label: "Research",
    blurb: "AI · 논문 · 리포트",
    details: "Haiku 4.5 + 3-layer RAG · 한은 367K · 증권사 104K · 도서 41K",
  },
  {
    href: "/admin/status",
    label: "Admin",
    blurb: "상태 · 잡 · 감사",
    details: "테넌트 · API 키 · nightly/weekly · 감사 로그",
  },
];

function toneColor(tone?: string): string {
  if (tone === "pos") return "var(--pos)";
  if (tone === "neg") return "var(--neg)";
  return "var(--fg-muted)";
}
function pctColor(v: number | undefined): string {
  if (v == null) return "var(--fg-muted)";
  return v >= 0 ? "var(--pos)" : "var(--neg)";
}
function pctFmt(v: number | undefined): string {
  if (v == null || !isFinite(v)) return "—";
  return `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}
// Strip UTF-16 lone surrogates that come through from bytes encoded with
// Python's surrogateescape (ingestion pipeline issue we haven't fully fixed).
function clean(s: string | undefined | null): string {
  if (!s) return "";
  return s.replace(/[\uD800-\uDFFF]/g, "");
}

export default function HomePage() {
  const [bundle, setBundle] = useState<TodayBundle | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API_BASE}/api/v1/chartist/today`)
      .then((r) => r.json())
      .then((body) => {
        if (cancelled) return;
        if (body?.ok && body.data) setBundle(body.data as TodayBundle);
        else setErr(body?.error?.message ?? "no data");
      })
      .catch((e) => {
        if (!cancelled) setErr(String(e?.message ?? e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const marketPills = bundle?.market ?? [];
  const summaryPills = bundle?.summary ?? [];
  const leaders = bundle?.leaders ?? [];
  const sectors = bundle?.sectors ?? [];
  const wizards = bundle?.wizards_pass ?? [];
  const stages = bundle?.stage_dist ?? [];
  const breakouts = bundle?.breakouts ?? [];

  const asOf = bundle?.date;
  const asOfDate = asOf ? new Date(asOf) : null;
  const ageDays = asOfDate
    ? Math.floor((today.getTime() - asOfDate.getTime()) / 86400000)
    : null;
  const isStale = ageDays !== null && ageDays > 2;

  return (
    <div className="max-w-6xl">
      {/* Header */}
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-4">
        <h1 className="display text-4xl">probably-alpha</h1>
        <div className="flex items-baseline gap-3">
          <span className="mono text-[11px] text-[color:var(--fg-muted)]">
            {todayStr} · {today.toLocaleDateString("ko-KR", { weekday: "long" })}
          </span>
          {asOf && (
            <span
              className="mono text-[10px] px-1.5 py-[1px] rounded border"
              style={{
                borderColor: isStale ? "var(--neg)" : "var(--border)",
                color: isStale ? "var(--neg)" : "var(--fg-muted)",
                background: "var(--bg)",
              }}
              title={`data as-of ${asOf}, today is ${todayStr}`}
            >
              데이터 as-of {asOf}
              {isStale ? ` (${ageDays}d stale)` : ""}
            </span>
          )}
        </div>
      </div>
      <p className="text-[color:var(--fg-muted)] mb-6 text-[13px] leading-relaxed max-w-3xl">
        한국 주식 시장용 6-탭 통합 리서치 플랫폼. Chartist로 주도주/섹터를 스캔하고,
        Quant/Value로 팩터·재무를 분석하며, Execute로 KIS를 통해 주문·관찰한다.
        Research 탭의 AI 어시스턴트는 도서 41K · 한은 367K · 증권사 104K 청크의
        3-layer RAG 위에서 Haiku 4.5가 답한다.
      </p>

      {/* Market pills (universe, KOSPI, KOSDAQ, ETF…) */}
      {marketPills.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
          {marketPills.map((p) => (
            <PillCard key={p.label} pill={p} />
          ))}
        </div>
      )}

      {/* Summary pills (Top Sector, Top Leader, wizards, etc) */}
      {summaryPills.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-6">
          {summaryPills.map((p) => (
            <PillCard key={p.label} pill={p} compact />
          ))}
        </div>
      )}

      {/* Main two-column: sectors + leaders */}
      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <Panel title="Top Sectors (오늘)" href="/chartist/sectors">
          {err ? (
            <ErrorRow msg={err} />
          ) : sectors.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {sectors.slice(0, 8).map((s) => (
                <li
                  key={s.name}
                  className="flex items-center justify-between py-1.5 px-1 text-[12px]"
                  style={{ borderBottom: "1px solid var(--border-soft)" }}
                >
                  <span className="flex items-baseline gap-2">
                    <span className="mono text-[10px] text-[color:var(--fg-muted)] w-4 inline-block">
                      {s.rank}.
                    </span>
                    <span>{clean(s.name)}</span>
                  </span>
                  <span className="flex items-center gap-3">
                    {s.score != null && (
                      <span className="mono text-[11px] text-[color:var(--fg-muted)]">
                        {s.score.toFixed(2)}
                      </span>
                    )}
                    <span
                      className="mono text-[11px] w-14 text-right"
                      style={{ color: pctColor(s.d1) }}
                    >
                      {pctFmt(s.d1)}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Top Leaders (오늘)" href="/chartist/leaders">
          {err ? (
            <ErrorRow msg={err} />
          ) : leaders.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {leaders.slice(0, 8).map((l, i) => (
                <li
                  key={l.symbol}
                  className="flex items-center justify-between py-1.5 px-1 text-[12px]"
                  style={{ borderBottom: "1px solid var(--border-soft)" }}
                >
                  <span className="flex items-baseline gap-2 truncate">
                    <span className="mono text-[10px] text-[color:var(--fg-muted)] w-4 inline-block">
                      {i + 1}.
                    </span>
                    <span className="mono">{l.symbol}</span>
                    <span className="truncate max-w-[14ch]">{clean(l.name)}</span>
                    {l.trend_template && (
                      <span className="mono text-[9.5px] text-[color:var(--muted)]">
                        TT {l.trend_template}
                      </span>
                    )}
                  </span>
                  <span className="flex items-center gap-3">
                    {l.leader_score != null && (
                      <span className="mono text-[11px] text-[color:var(--fg-muted)]">
                        {l.leader_score.toFixed(2)}
                      </span>
                    )}
                    <span
                      className="mono text-[11px] w-14 text-right"
                      style={{ color: pctColor(l.d1) }}
                    >
                      {pctFmt(l.d1)}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      {/* Wizards + breakouts + stages */}
      <div className="grid md:grid-cols-3 gap-4 mb-6">
        <Panel title="Wizards Pass" href="/chartist/wizards">
          {wizards.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {wizards.map((w) => (
                <li
                  key={w.name}
                  className="flex items-center justify-between py-1 px-1 text-[11.5px]"
                  style={{ borderBottom: "1px solid var(--border-soft)" }}
                >
                  <span className="truncate">{w.name}</span>
                  <span className="flex items-baseline gap-2">
                    <span className="mono">
                      {w.pass_count}/{w.total}
                    </span>
                    {w.delta_vs_yesterday != null && w.delta_vs_yesterday !== 0 && (
                      <span
                        className="mono text-[10px]"
                        style={{ color: pctColor(w.delta_vs_yesterday) }}
                      >
                        {w.delta_vs_yesterday > 0 ? "+" : ""}
                        {w.delta_vs_yesterday}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Breakouts" href="/chartist/breakouts/52w">
          {breakouts.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {breakouts.map((b) => (
                <li
                  key={b.symbol}
                  className="flex items-center justify-between py-1 px-1 text-[11.5px]"
                  style={{ borderBottom: "1px solid var(--border-soft)" }}
                >
                  <span className="flex items-baseline gap-2 truncate">
                    <span className="mono">{b.symbol}</span>
                    <span className="truncate max-w-[10ch]">
                      {clean(b.ticker)}
                    </span>
                  </span>
                  <span className="flex items-baseline gap-2">
                    <span
                      className="mono text-[11px]"
                      style={{ color: "var(--pos)" }}
                    >
                      {pctFmt(b.pct_up)}
                    </span>
                    {b.vol_x != null && (
                      <span className="mono text-[10px] text-[color:var(--fg-muted)]">
                        ×{b.vol_x.toFixed(1)}
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <Panel title="Stage Distribution" href="/chartist/wizards/minervini">
          {stages.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {stages.map((s) => (
                <li
                  key={s.name}
                  className="flex items-center justify-between py-1 px-1 text-[11.5px]"
                  style={{ borderBottom: "1px solid var(--border-soft)" }}
                >
                  <span className="flex items-baseline gap-2 truncate">
                    {s.color_hint && (
                      <span
                        className="inline-block w-2.5 h-2.5 rounded"
                        style={{ background: s.color_hint }}
                      />
                    )}
                    <span className="truncate">{s.name}</span>
                  </span>
                  <span className="mono text-[11px]">
                    {s.count} · {s.pct?.toFixed(1)}%
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      </div>

      {/* Tab directory */}
      <h2 className="display text-lg mb-3 text-[color:var(--fg-muted)]">
        탭 바로가기
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-6">
        {TABS.map((t) => (
          <Link
            key={t.href}
            href={t.href as never}
            className="block p-4 rounded-md border hover:border-[color:var(--accent)] transition-colors"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="display text-lg">{t.label}</div>
            <div className="text-xs text-[color:var(--fg-muted)] mt-1">
              {t.blurb}
            </div>
            <div className="text-[10.5px] text-[color:var(--muted)] mt-2 leading-snug">
              {t.details}
            </div>
          </Link>
        ))}
      </div>

      {/* Footer */}
      <div
        className="text-[11px] text-[color:var(--fg-muted)] border-t pt-3 mt-6"
        style={{ borderColor: "var(--border-soft)" }}
      >
        <div className="flex flex-wrap gap-3">
          <span>
            <span className="mono">GET /api/v1/assistant/health</span> →
            mode=claude
          </span>
          <span>
            RAG: <span className="mono">book + 한은 + 증권사</span> (3 layers)
          </span>
          <Link
            href={"/research/airesearch" as never}
            className="underline hover:text-[color:var(--fg)]"
          >
            AI에게 질문하기
          </Link>
          <Link
            href={"/admin/status" as never}
            className="underline hover:text-[color:var(--fg)]"
          >
            시스템 상태
          </Link>
          {bundle?.universe_size != null && (
            <span className="ml-auto mono">
              universe {bundle.universe_size.toLocaleString()}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function PillCard({ pill, compact = false }: { pill: KpiPill; compact?: boolean }) {
  return (
    <div
      className={`rounded-md border ${compact ? "p-2" : "p-3"}`}
      style={{ borderColor: "var(--border-soft)", background: "var(--bg)" }}
    >
      <div
        className={`text-[10px] uppercase tracking-widest text-[color:var(--muted)] ${compact ? "mb-0.5" : "mb-1"}`}
      >
        {pill.label}
      </div>
      <div className={`mono ${compact ? "text-[13px]" : "text-lg"}`}>
        {pill.value}
      </div>
      {pill.delta && (
        <div
          className="text-[10px] mt-1"
          style={{ color: toneColor(pill.tone) }}
        >
          {pill.delta}
        </div>
      )}
    </div>
  );
}

function Panel({
  title,
  href,
  children,
}: {
  title: string;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-md border p-3"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="flex items-baseline justify-between mb-2">
        <span className="display text-[13px]">{title}</span>
        <Link
          href={href as never}
          className="text-[10.5px] text-[color:var(--fg-muted)] hover:underline"
        >
          전체보기 →
        </Link>
      </div>
      {children}
    </div>
  );
}

function EmptyRow() {
  return (
    <div className="text-[11px] text-[color:var(--fg-muted)] py-3 text-center">
      데이터 없음 (nightly 파이프라인 대기).
    </div>
  );
}

function ErrorRow({ msg }: { msg: string }) {
  return (
    <div className="text-[11px] text-[color:var(--neg)] py-3">
      불러오지 못했습니다: {msg}
    </div>
  );
}
