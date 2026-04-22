// WizardViewsPane — each of the 6 Market Wizards evaluates this ticker.
"use client";

interface Props {
  symbol: string;
}

interface Row {
  wizard: string;
  verdict: "PASS" | "WATCH" | "FAIL";
  score: number;   // 0..100
  notes: string;
}

// Mock: varies a little per symbol so the list feels alive.
function rowsFor(symbol: string): Row[] {
  const hash = symbol.split("").reduce((a, c) => a + c.charCodeAt(0), 0);
  const bias = hash % 3;
  const base: Row[] = [
    { wizard: "Minervini",  verdict: "PASS",  score: 87, notes: "SEPA 8/8 · VCP 3파 수축 · EPS +28%" },
    { wizard: "O'Neil",     verdict: "PASS",  score: 82, notes: "CANSLIM 5/7 · RS 91 · 52wH 98.2" },
    { wizard: "Darvas",     verdict: "WATCH", score: 66, notes: "Box 돌파 대기 · Vol 1.8× · 박스 58d" },
    { wizard: "Livermore",  verdict: "PASS",  score: 74, notes: "Line of Least Res. 상방 · Pivot 58.4k" },
    { wizard: "Zanger",     verdict: "WATCH", score: 58, notes: "Gap 미발생 · HOD 근접" },
    { wizard: "Weinstein",  verdict: "PASS",  score: 80, notes: "Stage 2 확인 · SMA30 상승 8주" },
  ];
  // rotate verdicts a bit
  return base.map((r, i) => {
    if (bias === 1 && i === 2) return { ...r, verdict: "FAIL" as const, score: 42 };
    if (bias === 2 && i === 4) return { ...r, verdict: "PASS" as const, score: 73 };
    return r;
  });
}

function verdictStyle(v: Row["verdict"]): { color: string; bg: string } {
  if (v === "PASS") return { color: "var(--pos)", bg: "var(--pos-soft)" };
  if (v === "FAIL") return { color: "var(--neg)", bg: "var(--neg-soft)" };
  return { color: "var(--accent)", bg: "var(--accent-soft)" };
}

export function WizardViewsPane({ symbol }: Props) {
  const rows = rowsFor(symbol);
  return (
    <table className="w-full text-[11.5px] border-collapse">
      <thead>
        <tr className="text-[9.5px] uppercase tracking-widest text-[color:var(--muted)]">
          <th className="py-1.5 px-2 text-left font-medium">Wizard</th>
          <th className="py-1.5 px-2 text-left font-medium">판정</th>
          <th className="py-1.5 px-2 text-right font-medium">Score</th>
          <th className="py-1.5 px-2 text-left font-medium">Notes</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => {
          const s = verdictStyle(r.verdict);
          return (
            <tr
              key={r.wizard}
              style={{ borderTop: "1px solid var(--border-soft)" }}
            >
              <td className="py-1.5 px-2 font-medium">{r.wizard}</td>
              <td className="py-1.5 px-2">
                <span
                  className="inline-block px-2 py-[1px] rounded text-[10px] font-medium"
                  style={{ color: s.color, background: s.bg }}
                >
                  {r.verdict}
                </span>
              </td>
              <td className="py-1.5 px-2 mono text-[11px] text-right tabular-nums">
                {r.score}
              </td>
              <td className="py-1.5 px-2 text-[color:var(--fg-muted)]">
                {r.notes}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
