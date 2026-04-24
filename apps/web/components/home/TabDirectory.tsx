"use client";

import Link from "next/link";

interface TabEntry {
  href: string;
  label: string;
  blurb: string;
  details: string;
}

const TABS: TabEntry[] = [
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

export function TabDirectory() {
  return (
    <>
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
    </>
  );
}
