// Heatmap — generic heatmap matching mockup `.heatmap` grid.
// Cell classes h0..h6 are already in globals.css.
// Caller passes rows (rowName + cells: {value, level}).

export type HeatLevel = 0 | 1 | 2 | 3 | 4 | 5 | 6;

export interface HeatCell {
  value: string;
  level: HeatLevel;
}

interface Props {
  columnHeaders: string[];
  rowLabel?: string;
  rows: Array<{ name: string; cells: HeatCell[] }>;
  firstColumnWidth?: string; // default: 110px
  style?: React.CSSProperties;
}

export function Heatmap({ columnHeaders, rowLabel = "", rows, firstColumnWidth = "110px", style }: Props) {
  const template = `${firstColumnWidth} repeat(${columnHeaders.length}, 1fr)`;
  return (
    <div className="heatmap" style={{ gridTemplateColumns: template, ...style }}>
      <div className="hm-head first">{rowLabel}</div>
      {columnHeaders.map((h) => (
        <div key={h} className="hm-head">
          {h}
        </div>
      ))}
      {rows.map((r) => (
        <Row key={r.name} name={r.name} cells={r.cells} />
      ))}
    </div>
  );
}

function Row({ name, cells }: { name: string; cells: HeatCell[] }) {
  return (
    <>
      <div className="hm-name">{name}</div>
      {cells.map((c, i) => (
        <div key={i} className={`hm-cell h${c.level}`}>
          {c.value}
        </div>
      ))}
    </>
  );
}
