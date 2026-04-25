"use client";

import Link from "next/link";

import { Term } from "@/components/shared/Term";

interface Props {
  asOf?: string;
  universeSize?: number;
}

export function HeroSection({ asOf, universeSize }: Props) {
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
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-7">
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

      {/* Hero title — generous serif display */}
      <h1
        className="display leading-[1.02] tracking-tight mb-7"
        style={{
          fontSize: "clamp(2.75rem, 7vw, 5.5rem)",
        }}
      >
        한국 주식 시장,
        <br />
        <span style={{ color: "var(--accent)" }}>세 렌즈</span>로 본다.
      </h1>

      {/* Lead paragraph — large, readable, with inline glossary */}
      <p
        className="leading-relaxed max-w-3xl mb-4"
        style={{
          fontSize: "clamp(1.05rem, 1.6vw, 1.25rem)",
          color: "var(--fg)",
        }}
      >
        <Term k="KIS" /> · <Term k="DART" /> · <Term k="BOK" /> ·{" "}
        <Term k="FRED" /> · <Term k="FnGuide" />의 공식 데이터 위에서{" "}
        <span className="mono font-medium">
          {universeSize?.toLocaleString() ?? "4,516"}
        </span>{" "}
        종목을 매일 다시 스캔한다.
      </p>
      <p
        className="leading-relaxed max-w-3xl mb-8"
        style={{
          fontSize: "clamp(0.98rem, 1.4vw, 1.1rem)",
          color: "var(--fg-muted)",
        }}
      >
        차티스트는 <Term k="SEPA" /> · <Term k="VCP" /> · <Term k="CANSLIM" />{" "}
        같은 검증된 룰로 주도주를 찾고, 퀀트·밸류는{" "}
        <Term k="DCF" /> · <Term k="ROIC" /> · <Term k="Magic Formula" /> ·{" "}
        <Term k="Piotroski F-Score" />로 펀더멘털을 본다. AI 어시스턴트는{" "}
        도서·한은·증권사 512K 청크의{" "}
        <Term k="RAG" />위에서 답한다.
      </p>

      {/* Primary CTAs — prominent */}
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
          <span className="opacity-70 transition-transform group-hover:translate-x-1">
            →
          </span>
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

      {/* Live status chips */}
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
    </section>
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
