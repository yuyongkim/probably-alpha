// Execute tab — shared types for mock dense pages.

export interface Position {
  ticker: string;
  code: string;
  market: "KR" | "US";
  qty: number;
  avg: string;
  last: string;
  pnl: string;
  pct: string;
  change1d: string;
  stop: string;
  target: string;
  strategy: string;
  strategyTone?: "accent" | "amber" | "default";
  hold: string;
  tone: "pos" | "neg" | "neutral";
}

export interface LiveQuote {
  sym: string;
  last: string;
  chg: string;
  vol: string;
  bid: string;
  ask: string;
  arrow: "▲" | "▼";
  tone: "pos" | "neg";
}

export interface Fill {
  time: string;
  side: "BUY" | "SELL";
  ticker: string;
  qty: number;
  price: string;
  amount: string;
  venue: string;
  strategy: string;
  strategyTone?: "accent" | "amber";
}

export interface RiskMetric {
  metric: string;
  value: string;
  status: string;
  statusTone: "pos" | "neg" | "amber" | "default";
  limit: string;
  valueTone?: "pos" | "neg";
}

export interface LogEntry {
  time: string;
  tag: string;
  tagClass: "buy" | "sell" | "alert" | "sys";
  msg: string;
  sym?: string;
  symLabel?: string;
}

export interface Scenario {
  name: string;
  trigger: string;
  action: string;
  actionTone: "pos" | "neg" | "amber" | "default";
  safety: string;
  safetyTone: "pos" | "neg" | "amber" | "default";
}

export interface SafetyRail {
  idx: string;
  label: string;
  pct: string;
  fill: number; // 0..100
  color?: "amber" | "neg" | "pos";
}

export interface AllocationBar {
  label: string;
  pct: number;
  pctLabel: string;
  color: string;
}
