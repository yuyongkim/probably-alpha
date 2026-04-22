// MiniTable — dense table matching mockup `table.mini`.
// Columns declare header + alignment; rows are ReactNode[] (pre-formatted cells).
// Keeps styling purely via class; caller passes already-formatted values.

import type { ReactNode } from "react";

export interface MiniColumn {
  header: ReactNode;
  align?: "left" | "right";
  isNum?: boolean;      // shortcut for .num
  isMono?: boolean;     // .mono
}

interface Props {
  columns: MiniColumn[];
  rows: ReactNode[][]; // each row: same length as columns; cells pre-formatted
  className?: string;
  style?: React.CSSProperties;
}

export function MiniTable({ columns, rows, className, style }: Props) {
  return (
    <table className={`mini ${className ?? ""}`.trim()} style={style}>
      <thead>
        <tr>
          {columns.map((c, i) => (
            <th key={i} className={c.isNum ? "num" : undefined}>
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => (
          <tr key={ri}>
            {row.map((cell, ci) => {
              const col = columns[ci];
              const cls =
                col?.isNum && col?.isMono
                  ? "num mono"
                  : col?.isNum
                    ? "num"
                    : col?.isMono
                      ? "mono"
                      : undefined;
              return (
                <td key={ci} className={cls}>
                  {cell}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
