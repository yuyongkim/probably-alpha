"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:31300";

interface TodayBundle {
  as_of?: string;
  top_sectors?: Array<{ sector: string; score?: number; pct_chg?: number }>;
  top_leaders?: Array<{
    symbol: string;
    name?: string;
    sector?: string;
    leader_score?: number;
    pct_chg?: number;
  }>;
  market?: { kospi?: number; kosdaq?: number; fx_usd_krw?: number };
  [k: string]: unknown;
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
    details: "KIS OAuth · 호가/체결 SSE · 백테스트 실행 (일부 ROADMAP)",
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

function fmt(v: number | undefined, digits = 0): string {
  if (v == null || !isFinite(v)) return "—";
  return v.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function fmtPct(v: number | undefined): { text: string; pos: boolean | null } {
  if (v == null || !isFinite(v)) return { text: "—", pos: null };
  return { text: `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`, pos: v >= 0 };
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

  const market = bundle?.market ?? {};
  const topSectors = (bundle?.top_sectors ?? []).slice(0, 5);
  const topLeaders = (bundle?.top_leaders ?? []).slice(0, 5);

  return (
    <div className="max-w-6xl">
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-4">
        <h1 className="display text-4xl">probably-alpha</h1>
        <div className="mono text-[11px] text-[color:var(--fg-muted)]">
          {todayStr} · {today.toLocaleDateString("ko-KR", { weekday: "long" })}
        </div>
      </div>
      <p className="text-[color:var(--fg-muted)] mb-8 text-[13px] leading-relaxed max-w-3xl">
        한국 주식 시장용 6-탭 통합 리서치 플랫폼. Chartist로 주도주/섹터를 스캔하고,
        Quant/Value로 팩터·재무를 분석하며, Execute로 KIS를 통해 주문·관찰한다.
        Research 탭의 AI 어시스턴트는 도서 41K · 한은 367K · 증권사 104K 청크의
        3-layer RAG 위에서 Haiku 4.5가 답한다.
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <SnapshotCard
          label="KOSPI"
          value={fmt(market.kospi, 2)}
          sub={bundle?.as_of ? `as-of ${bundle.as_of}` : "—"}
        />
        <SnapshotCard
          label="KOSDAQ"
          value={fmt(market.kosdaq, 2)}
          sub={bundle?.as_of ? `as-of ${bundle.as_of}` : "—"}
        />
        <SnapshotCard
          label="USD/KRW"
          value={fmt(market.fx_usd_krw, 2)}
          sub="EXIM / ECOS"
        />
        <SnapshotCard
          label="Top Sector"
          value={topSectors[0]?.sector ?? "—"}
          sub={
            topSectors[0]?.score != null
              ? `score ${topSectors[0].score.toFixed(2)}`
              : "—"
          }
        />
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <Panel title="Top Sectors (오늘)" href="/chartist/sectors">
          {err ? (
            <ErrorRow msg={err} />
          ) : topSectors.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {topSectors.map((s, i) => {
                const p = fmtPct(s.pct_chg);
                return (
                  <li
                    key={s.sector}
                    className="flex items-center justify-between py-1.5 px-1 text-[12px]"
                    style={{ borderBottom: "1px solid var(--border-soft)" }}
                  >
                    <span>
                      <span className="mono text-[10px] text-[color:var(--fg-muted)] mr-2">
                        {i + 1}.
                      </span>
                      {s.sector}
                    </span>
                    <span className="flex items-center gap-3">
                      {s.score != null && (
                        <span className="mono text-[11px] text-[color:var(--fg-muted)]">
                          {s.score.toFixed(2)}
                        </span>
                      )}
                      {p.pos !== null && (
                        <span
                          className="mono text-[11px]"
                          style={{ color: p.pos ? "var(--pos)" : "var(--neg)" }}
                        >
                          {p.text}
                        </span>
                      )}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>

        <Panel title="Top Leaders (오늘)" href="/chartist/leaders">
          {err ? (
            <ErrorRow msg={err} />
          ) : topLeaders.length === 0 ? (
            <EmptyRow />
          ) : (
            <ul className="flex flex-col">
              {topLeaders.map((l, i) => {
                const p = fmtPct(l.pct_chg);
                return (
                  <li
                    key={l.symbol}
                    className="flex items-center justify-between py-1.5 px-1 text-[12px]"
                    style={{ borderBottom: "1px solid var(--border-soft)" }}
                  >
                    <span>
                      <span className="mono text-[10px] text-[color:var(--fg-muted)] mr-2">
                        {i + 1}.
                      </span>
                      <span className="mono mr-2">{l.symbol}</span>
                      {l.name ?? ""}
                    </span>
                    <span className="flex items-center gap-3">
                      {l.leader_score != null && (
                        <span className="mono text-[11px] text-[color:var(--fg-muted)]">
                          {l.leader_score.toFixed(2)}
                        </span>
                      )}
                      {p.pos !== null && (
                        <span
                          className="mono text-[11px]"
                          style={{ color: p.pos ? "var(--pos)" : "var(--neg)" }}
                        >
                          {p.text}
                        </span>
                      )}
                    </span>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>
      </div>

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
          <span>
            <Link href={"/research/airesearch" as never} className="underline">
              AI에게 질문하기
            </Link>
          </span>
          <span>
            <Link href={"/admin/status" as never} className="underline">
              시스템 상태
            </Link>
          </span>
        </div>
      </div>
    </div>
  );
}

function SnapshotCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div
      className="p-3 rounded-md border"
      style={{ borderColor: "var(--border-soft)", background: "var(--bg)" }}
    >
      <div className="text-[10.5px] uppercase tracking-widest text-[color:var(--muted)] mb-1">
        {label}
      </div>
      <div className="mono text-lg">{value}</div>
      <div className="text-[10px] text-[color:var(--fg-muted)] mt-1">{sub}</div>
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
      아직 데이터가 준비되지 않았습니다 (nightly 파이프라인 실행 필요).
    </div>
  );
}

function ErrorRow({ msg }: { msg: string }) {
  return (
    <div className="text-[11px] text-[color:var(--neg)] py-3">
      데이터를 불러오지 못했습니다: {msg}
    </div>
  );
}
