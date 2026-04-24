"use client";

import Link from "next/link";

interface SampleQuery {
  category: string;
  query: string;
  why: string;
}

// Queries verified to return good 3-layer RAG answers during /qa.
const SAMPLES: SampleQuery[] = [
  {
    category: "매크로 · 2022",
    query: "2022년 한국은행이 기준금리를 1.75% → 3.25%로 올린 배경과 우려 리스크",
    why: "통화신용정책보고서 2022-06/09 + 연차보고서 원문 인용",
  },
  {
    category: "섹터 · 반도체",
    query: "SK하이닉스 HBM 투자 계획과 최근 증권사 컨센서스",
    why: "DS투자증권·SK증권 등 리포트 본문 본문 매칭",
  },
  {
    category: "기업 · 삼성전자",
    query: "삼성전자 CAPEX 전략이 반도체 사이클과 어떻게 맞물리나?",
    why: "신한투자 2017-18 Big Cycle 시리즈 + 최근 리포트",
  },
  {
    category: "방법론",
    query: "Minervini의 Trend Template 8조건을 왜 완화하면 안 되는가?",
    why: "도서 RAG의 Trade Like a Stock Market Wizard 원문",
  },
];

export function SampleQueries() {
  return (
    <section className="mb-10">
      <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
        <h2 className="display text-xl">이런 질문을 해보세요</h2>
        <Link
          href={"/research/airesearch" as never}
          className="text-[11px] hover:underline"
          style={{ color: "var(--accent)" }}
        >
          AI 리서치 에이전트 전체보기 →
        </Link>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {SAMPLES.map((s) => (
          <Link
            key={s.query}
            href={`/research/airesearch?q=${encodeURIComponent(s.query)}` as never}
            className="block p-4 rounded-md border hover:border-[color:var(--accent)] transition-colors"
            style={{
              borderColor: "var(--border-soft)",
              background: "var(--surface)",
            }}
          >
            <div
              className="text-[9.5px] uppercase tracking-widest mb-1.5 mono"
              style={{ color: "var(--muted)" }}
            >
              {s.category}
            </div>
            <div
              className="text-[13px] leading-relaxed mb-2"
              style={{ color: "var(--fg)" }}
            >
              {s.query}
            </div>
            <div
              className="text-[10.5px] border-t pt-2"
              style={{
                borderColor: "var(--border-soft)",
                color: "var(--fg-muted)",
              }}
            >
              <span className="mono mr-2" style={{ color: "var(--accent)" }}>
                →
              </span>
              {s.why}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
