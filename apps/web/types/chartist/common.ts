// Common chartist types (tone, market index, ticker ref).
// Shape mirrors packages/core/ky_core/chartist.py (pydantic models).

export type Tone = "pos" | "neg" | "neutral";

export interface MarketIndex {
  label: string;
  value: string;
  delta: string;
  tone: Tone;
}

export interface SummaryKPI {
  label: string;
  value: string;
  delta: string;
  tone: Tone;
}

// Stock Detail Modal — global tickable reference.
// Lives here so both chartist table rows and TickerName wrapper use one type.
export interface TickerRef {
  symbol: string;
  name: string;
  sector?: string;
}

export interface AsOfInfo {
  as_of: string;
  today: string;
  stale: boolean;
  universe_size: number;
}
