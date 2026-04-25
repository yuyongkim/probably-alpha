"use client";

import { Term } from "@/components/shared/Term";

interface Source {
  id: string;
  /** Glossary key — drives the tooltip body. */
  termKey: string;
  /** Short display name. */
  label: string;
  /** Inline role description. */
  role: string;
}

const SOURCES: Source[] = [
  { id: "kis", termKey: "KIS", label: "KIS", role: "시세·호가·주문" },
  { id: "dart", termKey: "DART", label: "DART", role: "공시·PIT 재무" },
  { id: "fnguide", termKey: "FnGuide", label: "FnGuide", role: "스냅샷" },
  { id: "bok", termKey: "BOK", label: "한국은행", role: "거시 · 3.2K 리포트" },
  { id: "fred", termKey: "FRED", label: "FRED", role: "미 연준·BLS" },
  { id: "ecos", termKey: "ECOS", label: "ECOS", role: "한은 통계" },
  { id: "kosis", termKey: "KOSIS", label: "KOSIS", role: "통계청" },
  { id: "eia", termKey: "EIA", label: "EIA", role: "유가·에너지" },
  { id: "exim", termKey: "EXIM", label: "EXIM", role: "환율" },
];

export function DataSourcesBar() {
  return (
    <section
      className="mb-10 rounded-md border px-5 py-5"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border-soft)",
      }}
    >
      <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
        <h3 className="display text-lg md:text-xl tracking-tight">
          데이터 출처
        </h3>
        <span
          className="text-[10.5px] mono uppercase tracking-widest"
          style={{ color: "var(--muted)" }}
        >
          공식 API만 · 스크래핑 없음
        </span>
      </div>
      <div className="grid grid-cols-3 md:grid-cols-9 gap-2">
        {SOURCES.map((s) => (
          <div
            key={s.id}
            className="text-center py-3 px-2 rounded border"
            style={{
              borderColor: "var(--border-soft)",
              background: "var(--bg)",
            }}
          >
            <div className="display text-[13px]">
              <Term k={s.termKey}>{s.label}</Term>
            </div>
            <div
              className="text-[10px] mt-1 leading-tight"
              style={{ color: "var(--fg-muted)" }}
            >
              {s.role}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
