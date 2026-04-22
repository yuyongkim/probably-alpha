// DenseTable — Bloomberg-density tabular component.
// Columns define alignment + formatter; rows are opaque records.
// Target ≤ 100 lines.

export type Align = "left" | "right" | "center";

export interface DenseColumn<Row> {
  key: keyof Row & string;
  header: string;
  align?: Align;
  width?: string;           // e.g. "80px", "10%"
  format?: (v: Row[keyof Row], row: Row) => React.ReactNode;
  tone?: (row: Row) => "pos" | "neg" | "neutral" | undefined;
}

export interface DenseTableProps<Row> {
  columns: DenseColumn<Row>[];
  rows: Row[];
  rowKey: (row: Row, index: number) => string;
  onRowClick?: (row: Row) => void;
  emptyLabel?: string;
}

export function DenseTable<Row>({
  columns,
  rows,
  rowKey,
  onRowClick,
  emptyLabel = "No data",
}: DenseTableProps<Row>) {
  if (rows.length === 0) {
    return (
      <div className="text-xs text-[color:var(--fg-muted)] p-4 border border-dashed border-border rounded-md">
        {emptyLabel}
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm mono border-collapse">
        <thead>
          <tr className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] border-b border-border">
            {columns.map((c) => (
              <th
                key={c.key}
                style={{ width: c.width, textAlign: c.align ?? "left" }}
                className="py-2 px-2 font-medium"
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={rowKey(row, i)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={[
                "border-b border-[color:var(--border-soft)]",
                onRowClick ? "cursor-pointer hover:bg-[color:var(--surface-2)]" : "",
              ].join(" ")}
            >
              {columns.map((c) => {
                const tone = c.tone?.(row);
                const cls =
                  tone === "pos"
                    ? "text-[color:var(--pos)]"
                    : tone === "neg"
                    ? "text-[color:var(--neg)]"
                    : "";
                const v = row[c.key];
                return (
                  <td
                    key={c.key}
                    style={{ textAlign: c.align ?? "left" }}
                    className={`py-1.5 px-2 ${cls}`}
                  >
                    {c.format ? c.format(v, row) : String(v ?? "")}
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
