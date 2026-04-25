"use client";

import Link from "next/link";

import { Term } from "@/components/shared/Term";
import type { TodayBundle } from "@/types/today";

interface Props {
  asOf?: string;
  universeSize?: number;
  bundle?: TodayBundle | null;
}

export function HeroSection({ asOf, universeSize, bundle }: Props) {
  const today = new Date();
  const todayStr = today.toISOString().slice(0, 10);
  const asOfDate = asOf ? new Date(asOf) : null;
  const ageDays = asOfDate
    ? Math.floor((today.getTime() - asOfDate.getTime()) / 86400000)
    : null;
  const isStale = ageDays !== null && ageDays > 2;

  return (
    <section
      className="mb-14 pb-10 border-b"
      style={{ borderColor: "var(--border-soft)" }}
    >
      {/* Top meta row */}
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-8">
        <div className="flex items-baseline gap-3">
          <span className="mono text-[11px] text-[color:var(--fg-muted)]">
            probably-alpha · v0.2 dev
          </span>
          <span
            className="inline-flex items-center gap-1.5 mono text-[10px] text-[color:var(--fg-muted)]"
            title="API · RAG · Claude · KIS 전부 그린"
          >
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ background: "var(--pos)" }}
            />
            all systems operational
          </span>
        </div>
        <div className="mono text-[12px] text-[color:var(--fg-muted)]">
          {todayStr} · {today.toLocaleDateString("ko-KR", { weekday: "long" })}
        </div>
      </div>

      {/* Two-column hero — text left, live data right */}
      <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_1fr] gap-10 lg:gap-14">
        {/* LEFT — pitch + CTA */}
        <div>
          <h1
            className="display leading-[1.04] tracking-tight mb-2"
            style={{ fontSize: "clamp(2rem, 4.4vw, 3.6rem)" }}
          >
            한강 말고 어디 가지?
          </h1>
          <div
            className="display leading-[0.95] tracking-tight mb-5"
            style={{
              fontSize: "clamp(2.8rem, 6.4vw, 5.4rem)",
              color: "var(--accent)",
            }}
          >
            가즈아.
          </div>
          <p
            className="display italic leading-tight mb-4"
            style={{
              fontSize: "clamp(1.05rem, 1.7vw, 1.4rem)",
              color: "var(--fg-muted)",
            }}
          >
            근거는 동생이 봐드릴게요. 형님들은 가즈아.
          </p>
          <p
            className="text-[12px] mono uppercase tracking-widest mb-7"
            style={{ color: "var(--muted)" }}
          >
            동학개미를 위한 두 번째 의견 · 4,516 종목 매일 재검증
          </p>

          <p
            className="leading-relaxed mb-4"
            style={{
              fontSize: "clamp(1rem, 1.4vw, 1.15rem)",
              color: "var(--fg)",
            }}
          >
            <Term k="KIS">KIS</Term> · <Term k="DART">DART</Term> ·{" "}
            <Term k="BOK">한은</Term> · <Term k="FRED">FRED</Term> ·{" "}
            <Term k="FnGuide">FnGuide</Term>의 공식 데이터 위에서{" "}
            <span className="mono font-medium">
              {universeSize?.toLocaleString() ?? "4,516"}
            </span>{" "}
            종목을 매일 다시 스캔한다.
          </p>
          <p
            className="leading-relaxed mb-8"
            style={{
              fontSize: "clamp(0.95rem, 1.2vw, 1.05rem)",
              color: "var(--fg-muted)",
            }}
          >
            차티스트는 <Term k="SEPA">SEPA</Term> ·{" "}
            <Term k="VCP">VCP</Term> · <Term k="CANSLIM">CANSLIM</Term> 같은
            검증된 룰로 주도주를 찾고, 퀀트·밸류는{" "}
            <Term k="DCF">DCF</Term> · <Term k="ROIC">ROIC</Term> ·{" "}
            <Term k="Magic Formula">Magic Formula</Term> ·{" "}
            <Term k="Piotroski F-Score">Piotroski</Term>로 펀더멘털을 본다. AI
            어시스턴트는 도서·한은·증권사 605K 청크의{" "}
            <Term k="RAG">RAG</Term>위에서 답한다.
          </p>

          {/* CTAs */}
          <div className="flex flex-wrap gap-2.5 mb-7">
            <Link
              href={"/research/airesearch" as never}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-[14px] font-medium transition-all hover:opacity-90 active:translate-y-[1px]"
              style={{
                background: "var(--accent)",
                color: "var(--surface)",
              }}
            >
              AI에게 질문하기
              <span className="opacity-70">→</span>
            </Link>
            <Link
              href={"/chartist/today" as never}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-[14px] font-medium border transition-colors hover:border-[color:var(--accent)] active:translate-y-[1px]"
              style={{
                borderColor: "var(--border)",
                color: "var(--fg)",
                background: "var(--surface)",
              }}
            >
              오늘의 주도주 보기
            </Link>
            <Link
              href={"/chartist/wizards" as never}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md text-[14px] font-medium border transition-colors hover:border-[color:var(--accent)] active:translate-y-[1px]"
              style={{
                borderColor: "var(--border)",
                color: "var(--fg)",
                background: "var(--surface)",
              }}
            >
              Market Wizards 스크린
            </Link>
          </div>

          {/* Status chips */}
          <div className="flex flex-wrap gap-2 text-[11px]">
            <Chip on>Haiku 4.5</Chip>
            <Chip on>
              3-layer <Term k="RAG">RAG</Term>
            </Chip>
            <Chip on>
              <Term k="KIS">KIS</Term> 실시간
            </Chip>
            <Chip on={!isStale}>
              데이터 {asOf ?? "—"}
              {isStale && ageDays !== null ? ` · ${ageDays}d stale` : ""}
            </Chip>
            <Chip on>Nightly 자동화</Chip>
          </div>
        </div>

        {/* RIGHT — live snapshot card */}
        <LiveSnapshot bundle={bundle} />
      </div>
    </section>
  );
}

function LiveSnapshot({ bundle }: { bundle?: TodayBundle | null }) {
  const market = bundle?.market ?? [];
  const summary = bundle?.summary ?? [];
  const topLeader = bundle?.leaders?.[0];
  const topSector = bundle?.sectors?.[0];

  // Pull a few market pills by label match — defensive against backend label drift.
  const find = (needle: string) =>
    market.find((p) => p.label.toLowerCase().includes(needle));
  const kospi = find("kospi");
  const kosdaq = find("kosdaq");

  return (
    <aside
      className="rounded-xl border p-5 md:p-6 self-start"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border-soft)",
        boxShadow: "0 12px 32px -16px rgba(27, 67, 50, 0.12)",
      }}
    >
      <div className="flex items-baseline justify-between mb-4">
        <span
          className="text-[13px] font-semibold tracking-tight"
          style={{ color: "var(--fg)" }}
        >
          지금 시장은
        </span>
        <span
          className="mono text-[10px] tracking-widest uppercase"
          style={{ color: "var(--muted)" }}
        >
          LIVE
        </span>
      </div>

      {/* KOSPI / KOSDAQ row */}
      <div
        className="grid grid-cols-2 gap-3 pb-4 mb-4 border-b"
        style={{ borderColor: "var(--border-soft)" }}
      >
        <IndexBlock pillLabel="KOSPI" pill={kospi} fallbackKey="KOSPI" />
        <IndexBlock pillLabel="KOSDAQ" pill={kosdaq} fallbackKey="KOSDAQ" />
      </div>

      {/* Top sector */}
      {topSector && (
        <div
          className="pb-4 mb-4 border-b"
          style={{ borderColor: "var(--border-soft)" }}
        >
          <Row
            label="Top Sector"
            primary={topSector.name}
            secondary={
              topSector.d1 != null
                ? {
                    text: `${topSector.d1 >= 0 ? "+" : ""}${topSector.d1.toFixed(2)}%`,
                    pos: topSector.d1 >= 0,
                  }
                : null
            }
            tertiary={
              topSector.score != null ? `score ${topSector.score.toFixed(2)}` : ""
            }
          />
        </div>
      )}

      {/* Top leader */}
      {topLeader && (
        <div
          className="pb-4 mb-4 border-b"
          style={{ borderColor: "var(--border-soft)" }}
        >
          <Row
            label="Top Leader"
            primary={
              <span>
                <span className="mono mr-2">{topLeader.symbol}</span>
                {topLeader.name}
              </span>
            }
            secondary={
              topLeader.d1 != null
                ? {
                    text: `${topLeader.d1 >= 0 ? "+" : ""}${topLeader.d1.toFixed(2)}%`,
                    pos: topLeader.d1 >= 0,
                  }
                : null
            }
            tertiary={
              topLeader.trend_template
                ? `TT ${topLeader.trend_template}`
                : ""
            }
          />
        </div>
      )}

      {/* Wizards / breakouts headline */}
      {summary.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          {summary.slice(0, 2).map((p) => (
            <div key={p.label}>
              <div
                className="text-[9.5px] uppercase tracking-widest mb-1 mono"
                style={{ color: "var(--muted)" }}
              >
                {p.label}
              </div>
              <div className="mono text-[13px]">{p.value}</div>
              {p.delta && (
                <div
                  className="text-[10px] mt-0.5"
                  style={{
                    color:
                      p.tone === "pos"
                        ? "var(--pos)"
                        : p.tone === "neg"
                          ? "var(--neg)"
                          : "var(--fg-muted)",
                  }}
                >
                  {p.delta}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!bundle && (
        <div
          className="text-[12px] py-8 text-center"
          style={{ color: "var(--fg-muted)" }}
        >
          데이터를 불러오는 중…
        </div>
      )}
    </aside>
  );
}

function IndexBlock({
  pillLabel,
  pill,
  fallbackKey,
}: {
  pillLabel: string;
  pill?: { value: string; delta?: string; tone?: string };
  fallbackKey: string;
}) {
  return (
    <div>
      <div
        className="text-[9.5px] uppercase tracking-widest mb-1 mono"
        style={{ color: "var(--muted)" }}
      >
        <Term k={fallbackKey}>{pillLabel}</Term>
      </div>
      <div className="mono text-[18px] leading-tight">{pill?.value ?? "—"}</div>
      {pill?.delta && (
        <div
          className="text-[10.5px] mt-1"
          style={{
            color:
              pill.tone === "pos"
                ? "var(--pos)"
                : pill.tone === "neg"
                  ? "var(--neg)"
                  : "var(--fg-muted)",
          }}
        >
          {pill.delta}
        </div>
      )}
    </div>
  );
}

function Row({
  label,
  primary,
  secondary,
  tertiary,
}: {
  label: string;
  primary: React.ReactNode;
  secondary: { text: string; pos: boolean } | null;
  tertiary: string;
}) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <div className="min-w-0 flex-1">
        <div
          className="text-[9.5px] uppercase tracking-widest mb-1 mono"
          style={{ color: "var(--muted)" }}
        >
          {label}
        </div>
        <div
          className="text-[13.5px] truncate"
          style={{ color: "var(--fg)" }}
        >
          {primary}
        </div>
      </div>
      <div className="text-right shrink-0">
        {secondary && (
          <div
            className="mono text-[13px] font-medium"
            style={{ color: secondary.pos ? "var(--pos)" : "var(--neg)" }}
          >
            {secondary.text}
          </div>
        )}
        {tertiary && (
          <div
            className="mono text-[10px] mt-0.5"
            style={{ color: "var(--fg-muted)" }}
          >
            {tertiary}
          </div>
        )}
      </div>
    </div>
  );
}

function Chip({ children, on }: { children: React.ReactNode; on: boolean }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border mono"
      style={{
        borderColor: on ? "var(--pos-soft)" : "var(--neg-soft)",
        background: on ? "var(--pos-soft)" : "var(--neg-soft)",
        color: on ? "var(--pos)" : "var(--neg)",
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ background: on ? "var(--pos)" : "var(--neg)" }}
      />
      {children}
    </span>
  );
}
