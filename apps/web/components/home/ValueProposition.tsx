"use client";

import Link from "next/link";

import { Term } from "@/components/shared/Term";

interface LensCard {
  label: string;
  href: string;
  title: string;
  body: React.ReactNode;
  example: React.ReactNode;
  exampleHref: string;
}

const LENSES: LensCard[] = [
  {
    label: "차티스트 렌즈",
    href: "/chartist/today",
    title: "주도주·섹터를 스캔한다",
    body: (
      <>
        Minervini의 <Term k="SEPA" />, O'Neil의 <Term k="CANSLIM" />,{" "}
        <Term k="Darvas Box">Darvas Box</Term> 등 시장의 고수들이 쓰는 조건으로
        매일 전 종목을 다시 스크린한다. 조건을 완화해 종목 수를 늘리는 일은 없다.
      </>
    ),
    example: (
      <>
        오늘 <Term k="TT">TT</Term> 8/8 통과 + <Term k="RS">RS</Term> 70+ ·{" "}
        <Term k="VCP" /> 수축 종목은?
      </>
    ),
    exampleHref: "/chartist/wizards/minervini",
  },
  {
    label: "퀀트·밸류 렌즈",
    href: "/value/dcf",
    title: "팩터와 재무로 본다",
    body: (
      <>
        <Term k="Fama-French" /> 팩터, <Term k="Magic Formula" />,{" "}
        <Term k="Piotroski F-Score" />, <Term k="Altman Z-Score" />.{" "}
        <Term k="DCF" /> · <Term k="WACC" /> · <Term k="ROIC" />는{" "}
        <Term k="DART" /> <Term k="PIT" /> 재무 위에서 계산하고{" "}
        <Term k="FnGuide" /> 스냅샷과 교차 검증한다.
      </>
    ),
    example: (
      <>
        <Term k="ROIC" /> 20%+ & <Term k="Piotroski F-Score">F-Score</Term> 8+
        저평가
      </>
    ),
    exampleHref: "/value/roic",
  },
  {
    label: "리서치 렌즈",
    href: "/research/airesearch",
    title: "AI가 근거를 달아 답한다",
    body: (
      <>
        도서 41K + <Term k="BOK">한은</Term> 367K + 증권사 197K = 605K 청크의
        3-layer <Term k="RAG" /> 위에서 Haiku 4.5가 답한다. 모든 답변에는
        출처·연도·기관이 붙는다.
      </>
    ),
    example: (
      <>2022년 <Term k="기준금리" /> 인상 배경과 우려 리스크</>
    ),
    exampleHref: "/research/airesearch",
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

      {/* Asymmetric zig-zag — break the 3-equal-card cliché */}
      <div className="flex flex-col gap-4">
        {LENSES.map((l, i) => (
          <Link
            key={l.href}
            href={l.href as never}
            className={`block rounded-md border hover:border-[color:var(--accent)] transition-colors active:translate-y-[1px] ${
              i % 2 === 0 ? "md:mr-[12%]" : "md:ml-[12%]"
            }`}
            style={{
              borderColor: "var(--border)",
              background: "var(--surface)",
            }}
          >
            <div className="grid md:grid-cols-[1fr_2fr] gap-0">
              {/* Left side — label only, big breathing room */}
              <div
                className="p-6 md:p-8 border-b md:border-b-0 md:border-r flex flex-col justify-between"
                style={{ borderColor: "var(--border-soft)" }}
              >
                <div
                  className="text-[10.5px] uppercase tracking-widest mb-3 mono"
                  style={{ color: "var(--accent)" }}
                >
                  렌즈 {String(i + 1).padStart(2, "0")} · {l.label}
                </div>
                <h3 className="display text-2xl md:text-[28px] leading-tight tracking-tight">
                  {l.title}
                </h3>
              </div>

              {/* Right side — body + example */}
              <div className="p-6 md:p-8">
                <p
                  className="text-[14px] leading-relaxed mb-5"
                  style={{ color: "var(--fg)" }}
                >
                  {l.body}
                </p>
                <div
                  className="border-t pt-3 text-[12.5px]"
                  style={{ borderColor: "var(--border-soft)" }}
                >
                  <div
                    className="mono uppercase tracking-wider mb-1.5 text-[10px]"
                    style={{ color: "var(--muted)" }}
                  >
                    예시 질문
                  </div>
                  <div className="italic" style={{ color: "var(--fg-muted)" }}>
                    "{l.example}"
                  </div>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
