"use client";

import Link from "next/link";

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
    <section className="mb-10 pb-8 border-b" style={{ borderColor: "var(--border-soft)" }}>
      {/* Top meta row */}
      <div className="flex items-baseline justify-between flex-wrap gap-2 mb-5">
        <div className="flex items-baseline gap-3">
          <span className="mono text-[11px] text-[color:var(--fg-muted)]">
            probably-alpha · v0.2 dev
          </span>
          <span
            className="inline-flex items-center gap-1.5 mono text-[10px] text-[color:var(--fg-muted)]"
            title="API · RAG · Claude · KIS 전부 그린"
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: "var(--pos)" }}
            />
            all systems operational
          </span>
        </div>
        <div className="mono text-[11px] text-[color:var(--fg-muted)]">
          {todayStr} · {today.toLocaleDateString("ko-KR", { weekday: "long" })}
        </div>
      </div>

      {/* Hero title */}
      <h1 className="display text-5xl md:text-6xl leading-tight tracking-tight mb-4">
        한국 주식 시장,{" "}
        <span style={{ color: "var(--accent)" }}>세 렌즈</span>로 본다.
      </h1>
      <p
        className="text-[15px] leading-relaxed max-w-2xl mb-6"
        style={{ color: "var(--fg-muted)" }}
      >
        차트와 팩터, 재무와 공시, 그리고 AI 기반 리서치까지. KIS · DART · 한국은행 ·
        FRED · FnGuide의 실데이터 위에서{" "}
        <span className="mono">{universeSize?.toLocaleString() ?? "4,516"}</span>{" "}
        종목을 매일 재스캔하고, 512K 청크의 3-layer RAG로 질문에 답한다.
      </p>

      {/* Primary CTAs */}
      <div className="flex flex-wrap gap-2 mb-5">
        <Link
          href={"/research/airesearch" as never}
          className="inline-flex items-center gap-2 px-4 py-2 rounded text-[13px] font-medium transition-colors"
          style={{
            background: "var(--accent)",
            color: "var(--surface)",
          }}
        >
          AI에게 질문하기 <span className="opacity-70">→</span>
        </Link>
        <Link
          href={"/chartist/today" as never}
          className="inline-flex items-center gap-2 px-4 py-2 rounded text-[13px] font-medium border transition-colors"
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
          className="inline-flex items-center gap-2 px-4 py-2 rounded text-[13px] font-medium border transition-colors"
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
      <div className="flex flex-wrap gap-3 text-[10.5px] text-[color:var(--fg-muted)]">
        <Chip on>Haiku 4.5</Chip>
        <Chip on>RAG 3-layer</Chip>
        <Chip on>KIS 실시간</Chip>
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
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border mono"
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
