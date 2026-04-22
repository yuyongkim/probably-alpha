// CorrTable — macro × sector correlation heatmap table (dense).

import type { CorrResponse } from "@/types/macro";

function toneBg(corr: number): string {
  const c = Math.max(-1, Math.min(1, corr));
  const alpha = Math.abs(c) * 0.7;
  if (c >= 0) return `rgba(45,106,79,${alpha.toFixed(2)})`;
  return `rgba(188,75,81,${alpha.toFixed(2)})`;
}

export function CorrTable({ data }: { data: CorrResponse }) {
  const byKey: Record<string, number> = {};
  for (const c of data.cells) byKey[`${c.sector}|${c.macro}`] = c.corr;
  if (data.sectors.length === 0) {
    return <p className="text-xs" style={{ color: "var(--text-muted)" }}>데이터 없음</p>;
  }
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="mini">
        <thead>
          <tr>
            <th>Sector</th>
            {data.macros.map((m) => (
              <th key={m} className="num">{m}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.sectors.map((s) => (
            <tr key={s}>
              <td>{s}</td>
              {data.macros.map((m) => {
                const v = byKey[`${s}|${m}`] ?? 0;
                return (
                  <td key={m} className="num mono" style={{ background: toneBg(v), minWidth: 72 }}>
                    {v.toFixed(2)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
