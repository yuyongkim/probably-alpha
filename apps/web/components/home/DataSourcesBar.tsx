"use client";

interface Source {
  id: string;
  label: string;
  role: string;
}

const SOURCES: Source[] = [
  { id: "kis", label: "KIS", role: "시세·호가·주문" },
  { id: "dart", label: "DART", role: "공시·PIT 재무" },
  { id: "fnguide", label: "FnGuide", role: "스냅샷" },
  { id: "bok", label: "한국은행", role: "거시 · 3.2K 리포트" },
  { id: "fred", label: "FRED", role: "미 연준·BLS" },
  { id: "ecos", label: "ECOS", role: "한은 통계" },
  { id: "kosis", label: "KOSIS", role: "통계청" },
  { id: "eia", label: "EIA", role: "유가·에너지" },
  { id: "exim", label: "EXIM", role: "환율" },
];

export function DataSourcesBar() {
  return (
    <section
      className="mb-8 rounded-md border px-4 py-4"
      style={{
        background: "var(--surface)",
        borderColor: "var(--border-soft)",
      }}
    >
      <div className="flex items-baseline justify-between mb-3 flex-wrap gap-2">
        <h3 className="display text-[15px]">
          데이터 출처{" "}
          <span
            className="text-[10.5px] mono uppercase tracking-widest ml-2"
            style={{ color: "var(--muted)" }}
          >
            공식 API만 · 스크래핑 없음
          </span>
        </h3>
      </div>
      <div className="grid grid-cols-3 md:grid-cols-9 gap-2">
        {SOURCES.map((s) => (
          <div
            key={s.id}
            className="text-center py-2 px-1 rounded border"
            style={{
              borderColor: "var(--border-soft)",
              background: "var(--bg)",
            }}
          >
            <div className="display text-[12px]">{s.label}</div>
            <div
              className="text-[9px] mt-1 leading-tight"
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
