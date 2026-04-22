// DartPane — 공시 timeline. Mock list keyed off symbol.
"use client";

interface Props {
  symbol: string;
}

interface Item {
  when: string;
  kind: string;
  title: string;
  material: boolean;
}

const SAMPLE: Item[] = [
  { when: "2026-04-18 17:02", kind: "수시공시", title: "주요사항보고서 - 자기주식 취득 결정",    material: true },
  { when: "2026-04-15 16:24", kind: "수시공시", title: "단일판매ㆍ공급계약체결 (SK하이닉스)",     material: true },
  { when: "2026-04-10 08:48", kind: "정기공시", title: "분기보고서 (2026.03) 제출",               material: false },
  { when: "2026-04-02 09:31", kind: "임원공시", title: "최대주주등 소유주식 변동신고서",          material: false },
  { when: "2026-03-28 16:15", kind: "투자설명", title: "IR Day 2026 개최 안내",                   material: false },
  { when: "2026-03-20 15:42", kind: "수시공시", title: "투자판단 관련 주요경영사항 (신규 CAPEX)", material: true },
  { when: "2026-03-12 17:18", kind: "지분공시", title: "주식등의대량보유상황보고서",              material: false },
  { when: "2026-02-28 16:00", kind: "정기공시", title: "사업보고서 (2025.12) 제출",               material: false },
];

export function DartPane({ symbol }: Props) {
  return (
    <div>
      <div className="text-[11px] text-[color:var(--fg-muted)] mb-3">
        DART 원문 링크 · 최근 90일 · {symbol}
      </div>
      <ol className="flex flex-col gap-2">
        {SAMPLE.map((it, i) => (
          <li
            key={`${it.when}-${i}`}
            className="flex items-start gap-3 py-2 px-2 rounded"
            style={{ background: "var(--surface-2)" }}
          >
            <span className="mono text-[10.5px] text-[color:var(--fg-muted)] whitespace-nowrap pt-[1px]">
              {it.when}
            </span>
            <span
              className="inline-block px-1.5 py-[1px] rounded text-[9.5px] font-medium"
              style={{
                background: it.material ? "var(--accent-soft)" : "var(--bg)",
                color: it.material ? "var(--accent)" : "var(--fg-muted)",
                border: "1px solid var(--border)",
                whiteSpace: "nowrap",
              }}
            >
              {it.kind}
            </span>
            <span className="text-[11.5px]">{it.title}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
