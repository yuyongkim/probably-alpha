"use client";

import Link from "next/link";

interface LensCard {
  label: string;
  href: string;
  title: string;
  body: string;
  example: string;
  exampleHref: string;
}

const LENSES: LensCard[] = [
  {
    label: "차티스트 렌즈",
    href: "/chartist/today",
    title: "주도주·섹터를 스캔한다",
    body: "Minervini의 SEPA, O'Neil의 CANSLIM, Darvas Box 등 시장의 고수들이 쓰는 조건으로 매일 전 종목을 다시 스크린한다. 조건이 완화되어 종목 수를 늘리는 일은 없다.",
    example: "오늘 TT 8/8 통과 + RS 80+ + VCP 수축 종목은?",
    exampleHref: "/chartist/wizards/minervini",
  },
  {
    label: "퀀트·밸류 렌즈",
    href: "/value/dcf",
    title: "팩터와 재무로 본다",
    body: "Fama-French 팩터, Magic Formula, Piotroski F-Score, Altman Z. DCF·WACC·ROIC는 DART PIT 재무 위에서 계산하고, FnGuide 스냅샷과 교차 검증한다.",
    example: "ROIC > 20% & Piotroski 8+ 인 저평가 종목",
    exampleHref: "/value/roic",
  },
  {
    label: "리서치 렌즈",
    href: "/research/airesearch",
    title: "AI가 근거를 달아 답한다",
    body: "도서 41K + 한은 367K + 증권사 104K = 512K 청크의 3-layer RAG 위에서 Haiku 4.5가 답한다. 모든 답변에는 출처·연도·기관이 붙는다.",
    example: "2022년 금리 인상 배경과 당시 우려 리스크",
    exampleHref: "/research/airesearch",
  },
];

export function ValueProposition() {
  return (
    <section className="mb-10">
      <div className="flex items-baseline justify-between mb-4">
        <h2 className="display text-xl">이 플랫폼으로 할 수 있는 것</h2>
        <span className="mono text-[10.5px] text-[color:var(--fg-muted)]">
          WHAT YOU CAN DO HERE
        </span>
      </div>
      <div className="grid md:grid-cols-3 gap-3">
        {LENSES.map((l) => (
          <Link
            key={l.href}
            href={l.href as never}
            className="block p-5 rounded-md border hover:border-[color:var(--accent)] transition-colors group"
            style={{ borderColor: "var(--border)", background: "var(--surface)" }}
          >
            <div
              className="text-[10px] uppercase tracking-widest mb-2"
              style={{ color: "var(--accent)" }}
            >
              {l.label}
            </div>
            <h3 className="display text-[17px] mb-2 leading-snug">{l.title}</h3>
            <p
              className="text-[12.5px] leading-relaxed mb-4"
              style={{ color: "var(--fg-muted)" }}
            >
              {l.body}
            </p>
            <div
              className="text-[10.5px] border-t pt-3"
              style={{ borderColor: "var(--border-soft)" }}
            >
              <div
                className="mono uppercase tracking-wider mb-1"
                style={{ color: "var(--muted)" }}
              >
                예시 질문
              </div>
              <div className="text-[12px] italic" style={{ color: "var(--fg)" }}>
                "{l.example}"
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
