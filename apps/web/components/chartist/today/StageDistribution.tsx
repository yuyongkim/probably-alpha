// StageDistribution — horizontal bar chart for VCP stages.
// 6 rows: Stage 1 → Fail, each with a pct width + count tally.
import type { StageBucket } from "@/types/chartist";

interface Props {
  items: StageBucket[];
}

export function StageDistribution({ items }: Props) {
  return (
    <div
      className="rounded-md border overflow-hidden"
      style={{ background: "var(--surface)", borderColor: "var(--border)" }}
    >
      <div
        className="flex items-baseline justify-between px-3 py-2 border-b"
        style={{ borderColor: "var(--border)" }}
      >
        <h2 className="display text-base">VCP Stage 분포</h2>
        <span className="text-[10px] text-[color:var(--fg-muted)]">
          통과 종목 스테이지별
        </span>
      </div>
      <div className="px-3 py-3 flex flex-col gap-2">
        {items.map((s) => (
          <div
            key={s.name}
            className="flex items-center gap-2 text-[11.5px]"
          >
            <span
              className="text-[color:var(--fg-muted)]"
              style={{ width: "100px" }}
            >
              {s.name}
            </span>
            <div
              className="flex-1 rounded relative"
              style={{ height: "16px", background: "var(--bg)" }}
            >
              <div
                className="rounded h-full"
                style={{
                  width: `${Math.min(100, Math.max(0, s.pct))}%`,
                  background: s.color_hint,
                }}
              />
            </div>
            <span
              className="mono tabular-nums text-right text-[10.5px]"
              style={{ width: "32px" }}
            >
              {s.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
