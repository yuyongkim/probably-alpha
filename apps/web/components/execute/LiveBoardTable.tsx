// LiveBoardTable — mockup live WebSocket board table.
import type { LiveQuote } from "@/types/execute";

export function LiveBoardTable({ rows }: { rows: LiveQuote[] }) {
  return (
    <table className="mini">
      <thead>
        <tr>
          <th>Sym</th><th className="num">Last</th><th className="num">Chg</th>
          <th className="num">Vol</th><th className="num">Bid</th><th className="num">Ask</th><th>T</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((q) => {
          const tone = q.tone === "pos" ? "var(--pos)" : "var(--neg)";
          return (
            <tr key={q.sym}>
              <td className="mono">{q.sym}</td>
              <td className="num">{q.last}</td>
              <td className="num" style={{ color: tone }}>{q.chg}</td>
              <td className="num">{q.vol}</td>
              <td className="num">{q.bid}</td>
              <td className="num">{q.ask}</td>
              <td className="mono" style={{ color: tone }}>{q.arrow}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
