// Heatmap primitive (mockup-compatible): header row + color-class cells.

export interface HeatCellProps {
  v: string;
  h: number;
}

export function Heatmap({
  headers,
  rows,
  firstColWidth = "140px",
}: {
  headers: string[];
  rows: { name: string; cells: HeatCellProps[] }[];
  firstColWidth?: string;
}) {
  const cols = headers.length;
  return (
    <div
      className="heatmap"
      style={{
        display: "grid",
        gridTemplateColumns: `${firstColWidth} repeat(${cols - 1}, 1fr)`,
        gap: "1px",
        background: "var(--border)",
        border: "1px solid var(--border)",
        borderRadius: 6,
        overflow: "hidden",
      }}
    >
      {headers.map((h, i) => (
        <div
          key={h + i}
          className={`hm-head ${i === 0 ? "first" : ""}`}
          style={{
            background: "var(--bg)",
            padding: "6px 10px",
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.04em",
            color: "var(--muted)",
            fontWeight: 500,
            textAlign: i === 0 ? "left" : "center",
          }}
        >
          {h}
        </div>
      ))}
      {rows.map((r) => (
        <HmRow key={r.name} r={r} />
      ))}
    </div>
  );
}

function HmRow({ r }: { r: { name: string; cells: HeatCellProps[] } }) {
  return (
    <>
      <div
        className="hm-name"
        style={{
          background: "var(--surface)",
          padding: "5px 10px",
          fontSize: 11.5,
          fontWeight: 500,
          display: "flex",
          alignItems: "center",
        }}
      >
        {r.name}
      </div>
      {r.cells.map((c, i) => (
        <div key={i} className={`hm-cell h${c.h}`}>
          {c.v}
        </div>
      ))}
    </>
  );
}
