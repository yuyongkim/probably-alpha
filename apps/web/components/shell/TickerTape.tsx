// TickerTape — marquee bar with 18 symbols (looped twice for seamless scroll).
// Purely visual; backed by hard-coded snapshot for now. When KIS realtime lands,
// swap TICKER_DATA for an SWR subscription — DOM is the same.
"use client";

type TickerTone = "pos" | "neg";

interface TickerRow {
  label: string;
  value: string;
  delta: string;
  tone: TickerTone;
}

// Mockup-matching default set (top-of-mind KR/US indices + oil/gold + 5 KR leaders).
const TICKER_DATA: TickerRow[] = [
  { label: "KOSPI",   value: "2,847.32", delta: "▲ 0.82%", tone: "pos" },
  { label: "KOSDAQ",  value: "864.11",   delta: "▲ 1.34%", tone: "pos" },
  { label: "USD/KRW", value: "1,342.50", delta: "▼ 0.21%", tone: "neg" },
  { label: "DJI",     value: "41,247.80",delta: "▲ 0.42%", tone: "pos" },
  { label: "SPX",     value: "5,842.91", delta: "▲ 0.58%", tone: "pos" },
  { label: "NDX",     value: "20,482.34",delta: "▲ 0.91%", tone: "pos" },
  { label: "N225",    value: "39,847.20",delta: "▼ 0.33%", tone: "neg" },
  { label: "HSI",     value: "22,147.80",delta: "▲ 0.67%", tone: "pos" },
  { label: "WTI",     value: "$82.34",   delta: "▲ 1.18%", tone: "pos" },
  { label: "GOLD",    value: "$2,748.20",delta: "▲ 0.42%", tone: "pos" },
  { label: "US10Y",   value: "3.18%",    delta: "▼ 4bp",   tone: "neg" },
  { label: "KR10Y",   value: "3.02%",    delta: "▼ 2bp",   tone: "neg" },
  { label: "BTC",     value: "$94,820",  delta: "▲ 2.14%", tone: "pos" },
  { label: "005930",  value: "75,400",   delta: "▲ 1.88%", tone: "pos" },
  { label: "000660",  value: "192,100",  delta: "▲ 2.34%", tone: "pos" },
  { label: "042700",  value: "134,500",  delta: "▲ 3.67%", tone: "pos" },
  { label: "403870",  value: "31,200",   delta: "▲ 4.21%", tone: "pos" },
  { label: "247540",  value: "204,500",  delta: "▼ 1.84%", tone: "neg" },
];

function Item({ row, keyPrefix }: { row: TickerRow; keyPrefix: string }) {
  return (
    <span key={`${keyPrefix}-${row.label}`} className="ticker-item">
      <span className="tl">{row.label}</span>
      <span className="tv">{row.value}</span>
      <span className={row.tone === "pos" ? "tp" : "tn"}>{row.delta}</span>
    </span>
  );
}

export function TickerTape() {
  // Duplicate the feed so the -50% translateX marquee loops seamlessly.
  const loop = [...TICKER_DATA, ...TICKER_DATA];
  return (
    <div className="ticker-tape" aria-label="Market ticker tape">
      <div className="ticker-track">
        {loop.map((row, i) => (
          <Item key={i} row={row} keyPrefix={`t${i}`} />
        ))}
      </div>
    </div>
  );
}
