"use client";

import Link from "next/link";

import { Term } from "@/components/shared/Term";

interface LensCard {
  index: string;
  label: string;
  href: string;
  title: string;
  body: React.ReactNode;
  example: React.ReactNode;
  bullets: string[];
}

const LENSES: LensCard[] = [
  {
    index: "01",
    label: "Chartist",
    href: "/chartist/today",
    title: "주도주·섹터를 스캔한다",
    body: (
      <>
        Minervini의 <Term k="SEPA">SEPA</Term>, O'Neil의{" "}
        <Term k="CANSLIM">CANSLIM</Term>, <Term k="Darvas Box">Darvas Box</Term> 등
        시장의 고수들이 쓰는 조건으로 매일 전 종목을 다시 스크린한다. 조건을
        완화해 종목 수를 늘리는 일은 없다.
      </>
    ),
    example: (
      <>
        오늘 <Term k="TT">TT</Term> 8/8 통과 + <Term k="RS">RS</Term> 70+ ·{" "}
        <Term k="VCP">VCP</Term> 수축 종목은?
      </>
    ),
    bullets: [
      "TT 8/8 · VCP 수축 · 52주 신고가 돌파",
      "Minervini · O'Neil · Darvas · Weinstein 6명 위저드별 화면",
      "섹터 강도 점수 + 로테이션 트래킹",
    ],
  },
  {
    index: "02",
    label: "Quant · Value",
    href: "/value/dcf",
    title: "팩터와 재무로 본다",
    body: (
      <>
        <Term k="Fama-French">Fama-French</Term> 팩터,{" "}
        <Term k="Magic Formula">Magic Formula</Term>,{" "}
        <Term k="Piotroski F-Score">Piotroski</Term>,{" "}
        <Term k="Altman Z-Score">Altman Z</Term>. <Term k="DCF">DCF</Term> ·{" "}
        <Term k="WACC">WACC</Term> · <Term k="ROIC">ROIC</Term>는{" "}
        <Term k="DART">DART</Term> <Term k="PIT">PIT</Term> 재무 위에서 계산하고{" "}
        <Term k="FnGuide">FnGuide</Term> 스냅샷과 교차 검증한다.
      </>
    ),
    example: (
      <>
        <Term k="ROIC">ROIC</Term> 20%+ ·{" "}
        <Term k="Piotroski F-Score">F-Score</Term> 8+ 저평가
      </>
    ),
    bullets: [
      "DCF 모델 · WACC · 5요소 Z-Score · 9-point F-Score",
      "Magic Formula · QMJ · Deep Value · Moat v2",
      "사업부문 매출 분해 · 컨센서스 · 자사주 매입",
    ],
  },
  {
    index: "03",
    label: "Research",
    href: "/research/airesearch",
    title: "AI가 근거를 달아 답한다",
    body: (
      <>
        도서 41K + <Term k="BOK">한은</Term> 367K + 증권사 197K = 605K 청크의
        3-layer <Term k="RAG">RAG</Term> 위에서 Haiku 4.5가 답한다. 모든 답변에는
        출처·연도·기관이 붙는다.
      </>
    ),
    example: (
      <>
        2022년 <Term k="기준금리">기준금리</Term> 인상 배경과 우려 리스크
      </>
    ),
    bullets: [
      "도서 147권 · 한은 3.2K 보고서 · 증권사 22K PDF",
      "BGE-M3 의미 검색 + TF-IDF 키워드 매칭 하이브리드",
      "Haiku 4.5 응답에 시점·발행기관 인용 자동",
    ],
  },
];

export function ValueProposition() {
  return (
    <section className="mb-14">
      <div className="flex items-baseline justify-between mb-6 flex-wrap gap-2">
        <h2 className="display text-2xl md:text-3xl tracking-tight">
          이 플랫폼으로 할 수 있는 것
        </h2>
        <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
          WHAT YOU CAN DO HERE
        </span>
      </div>

      {/* 3 equal Bento cards on lg. Content is rich (icon-index + title +
          body + bullet list + example), so this is a proper feature trio,
          not the shallow "3-equal-feature-row" cliché. */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {LENSES.map((l) => (
          <Link
            key={l.href}
            href={l.href as never}
            className="group block rounded-md border transition-all hover:border-[color:var(--accent)] active:translate-y-[1px]"
            style={{
              borderColor: "var(--border)",
              background: "var(--surface)",
            }}
          >
            <div className="p-6 md:p-7 h-full flex flex-col">
              {/* Header — index + label */}
              <div className="flex items-baseline gap-3 mb-4">
                <span
                  className="display text-[28px] leading-none"
                  style={{ color: "var(--accent)", opacity: 0.5 }}
                >
                  {l.index}
                </span>
                <span
                  className="text-[10.5px] uppercase tracking-widest mono"
                  style={{ color: "var(--accent)" }}
                >
                  {l.label}
                </span>
              </div>

              {/* Title */}
              <h3 className="display text-xl md:text-[22px] leading-snug tracking-tight mb-3">
                {l.title}
              </h3>

              {/* Body */}
              <p
                className="text-[13.5px] leading-relaxed mb-4 flex-1"
                style={{ color: "var(--fg)" }}
              >
                {l.body}
              </p>

              {/* Bullets — quick spec list */}
              <ul
                className="text-[11.5px] mb-4 space-y-1"
                style={{ color: "var(--fg-muted)" }}
              >
                {l.bullets.map((b) => (
                  <li
                    key={b}
                    className="flex items-baseline gap-2 leading-relaxed"
                  >
                    <span
                      className="inline-block w-1 h-1 rounded-full mt-1.5 shrink-0"
                      style={{ background: "var(--accent)" }}
                    />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>

              {/* Example query — divided footer */}
              <div
                className="border-t pt-3 text-[12px]"
                style={{ borderColor: "var(--border-soft)" }}
              >
                <div
                  className="mono uppercase tracking-wider mb-1.5 text-[9.5px]"
                  style={{ color: "var(--muted)" }}
                >
                  예시 질문
                </div>
                <div
                  className="italic flex items-baseline gap-2"
                  style={{ color: "var(--fg-muted)" }}
                >
                  <span className="text-[color:var(--accent)] font-bold not-italic">
                    "
                  </span>
                  <span>{l.example}</span>
                  <span className="text-[color:var(--accent)] font-bold not-italic">
                    "
                  </span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
