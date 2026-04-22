// Side-by-side strategy cards. Each card shows the top-N picks for a
// Greenblatt/Graham-style academic strategy.

import { DenseTable, type DenseColumn } from "@/components/shared/DenseTable";
import type { AcademicRow } from "@/types/quant";

const num = (v: number | null | undefined, digits = 0) =>
  v == null ? "–" : v.toLocaleString(undefined, { maximumFractionDigits: digits });

const COLUMNS: DenseColumn<AcademicRow>[] = [
  { key: "symbol", header: "Sym" },
  { key: "name", header: "Name" },
  { key: "sector", header: "Sector" },
  { key: "close", header: "Close", align: "right", format: (v) => num(v as number | null) },
];

export function AcademicStrategyCards({
  strategy,
  rows,
  extraColumn,
}: {
  strategy: string;
  rows: AcademicRow[];
  extraColumn?: DenseColumn<AcademicRow>;
}) {
  const cols = extraColumn ? [...COLUMNS, extraColumn] : COLUMNS;
  return (
    <section className="border border-border rounded-md p-4 bg-[color:var(--surface)]">
      <header className="flex items-baseline justify-between mb-3">
        <h3 className="display text-lg capitalize">
          {strategy.replace("_", " ")}
        </h3>
        <span className="text-xs text-[color:var(--fg-muted)]">
          Top {rows.length} · ky.db
        </span>
      </header>
      <DenseTable
        columns={cols}
        rows={rows}
        rowKey={(r) => r.symbol}
        emptyLabel="Strategy returned no picks"
      />
    </section>
  );
}
