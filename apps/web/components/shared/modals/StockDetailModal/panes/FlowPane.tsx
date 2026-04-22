// FlowPane — 외인/기관/개인 일별 순매수 (mock).
"use client";

interface Props {
  symbol: string;
}

interface Row {
  date: string;
  foreign: number;
  inst: number;
  retail: number;
}

const SAMPLE: Row[] = [
  { date: "04-22", foreign: +1247, inst: +412,  retail: -1659 },
  { date: "04-21", foreign: +982,  inst: -184,  retail: -798 },
  { date: "04-18", foreign: +641,  inst: +228,  retail: -869 },
  { date: "04-17", foreign: +512,  inst: -314,  retail: -198 },
  { date: "04-16", foreign: -312,  inst: +844,  retail: -532 },
  { date: "04-15", foreign: +128,  inst: +412,  retail: -540 },
  { date: "04-14", foreign: +484,  inst: -128,  retail: -356 },
  { date: "04-11", foreign: -84,   inst: +248,  retail: -164 },
  { date: "04-10", foreign: +322,  inst: +312,  retail: -634 },
  { date: "04-09", foreign: +114,  inst: -84,   retail: -30 },
];

function signed(v: number): string {
  if (v > 0) return `+${v.toLocaleString()}`;
  return v.toLocaleString();
}
function col(v: number): string {
  if (v > 0) return "var(--pos)";
  if (v < 0) return "var(--neg)";
  return "var(--neutral)";
}

export function FlowPane({ symbol }: Props) {
  return (
    <div>
      <div className="text-[11px] text-[color:var(--fg-muted)] mb-2">
        외인 · 기관 · 개인 순매수 (억원) · {symbol} · mock
      </div>
      <table className="w-full text-[11.5px] border-collapse">
        <thead>
          <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
            <th className="py-1.5 px-2 text-left font-medium">Date</th>
            <th className="py-1.5 px-2 text-right font-medium">외인</th>
            <th className="py-1.5 px-2 text-right font-medium">기관</th>
            <th className="py-1.5 px-2 text-right font-medium">개인</th>
          </tr>
        </thead>
        <tbody>
          {SAMPLE.map((r) => (
            <tr key={r.date} style={{ borderTop: "1px solid var(--border-soft)" }}>
              <td className="py-1.5 px-2 mono">{r.date}</td>
              <td className="py-1.5 px-2 mono text-right" style={{ color: col(r.foreign) }}>
                {signed(r.foreign)}
              </td>
              <td className="py-1.5 px-2 mono text-right" style={{ color: col(r.inst) }}>
                {signed(r.inst)}
              </td>
              <td className="py-1.5 px-2 mono text-right" style={{ color: col(r.retail) }}>
                {signed(r.retail)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
