import Link from "next/link";

const TABS = [
  { href: "/chartist/today", label: "Chartist", blurb: "오늘의 시장 · 섹터 · 리더" },
  { href: "/quant/factors", label: "Quant", blurb: "팩터 · 백테스트 · 리서치" },
  { href: "/value/dcf", label: "Value", blurb: "DCF · 재무 · 버핏 RAG" },
  { href: "/execute/overview", label: "Execute", blurb: "포지션 · 주문 · 리스크" },
  { href: "/research/papers", label: "Research", blurb: "논문 · 리포트 · 매크로" },
  { href: "/admin/status", label: "Admin", blurb: "상태 · 잡 · 감사" },
];

export default function HomePage() {
  return (
    <div className="max-w-5xl">
      <h1 className="display text-4xl mb-2">probably-alpha</h1>
      <p className="text-[color:var(--fg-muted)] mb-8">6 탭 통합 금융 플랫폼 (Phase 2 scaffold)</p>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {TABS.map((t) => (
          <Link
            key={t.href}
            href={t.href as never}
            className="block p-4 rounded-md border border-border hover:border-[color:var(--accent)] transition-colors"
          >
            <div className="display text-lg">{t.label}</div>
            <div className="text-xs text-[color:var(--fg-muted)] mt-1">{t.blurb}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
