// Technicals 6 subsections — patterns / candlestick / divergence / ichimoku /
// vprofile / support.
// Shapes mirror packages/core/ky_core/scanning/{vcp,candlestick,divergence,
// ichimoku,vprofile,support}.py.

export interface PatternRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  pattern: string; // 'VCP' | 'Cup&Handle' | 'Flat Base' | 'Asc Triangle'
  stage: number;
  score: number;
  pct_of_52w_high: number;
  depth_pct: number;
  duration_days: number;
  volume_dry_up: boolean;
}

export interface PatternsResponse {
  as_of: string;
  universe_size: number;
  count: number;
  summary: Record<string, number>;
  rows: PatternRow[];
}

export interface CandleRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  pattern: string;
  pattern_ko: string;
  type: string;
  tone: "pos" | "neg" | "neutral";
  close: number;
  win_rate: number;
  avg_fwd_5d: number;
  vol_x: number;
  sample_n: number;
  confluence: string;
}

export interface CandlestickResponse {
  as_of: string;
  universe_size: number;
  count: number;
  summary: { bullish: number; bearish: number; neutral: number };
  rows: CandleRow[];
}

export interface DivergenceRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  indicator: "RSI" | "MACD" | "OBV";
  kind: "bullish" | "bearish" | "hidden_bullish" | "hidden_bearish";
  tone: "pos" | "neg";
  close: number;
  rsi: number;
  d5_pct: number;
  strength: number;
  strength_label: string;
}

export interface DivergenceResponse {
  as_of: string;
  universe_size: number;
  count: number;
  summary: Record<string, number>;
  rows: DivergenceRow[];
}

export interface IchimokuRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  tenkan: number;
  kijun: number;
  senkou_a: number;
  senkou_b: number;
  cloud_top: number;
  cloud_bot: number;
  cloud_thickness_pct: number;
  vs_cloud: "ABOVE" | "BELOW" | "INSIDE";
  tk_cross: "BULL" | "BEAR" | "—";
  chikou: "ABOVE" | "BELOW" | "—";
  three_cross_bull: boolean;
  three_cross_bear: boolean;
  tone: "pos" | "neg" | "neutral";
}

export interface IchimokuResponse {
  as_of: string;
  universe_size: number;
  count: number;
  summary: Record<string, number>;
  rows: IchimokuRow[];
}

export interface VProfileRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  poc: number;
  vah: number;
  val: number;
  price_to_poc_pct: number;
  position: "ABOVE_VAH" | "NEAR_POC" | "INSIDE_VA" | "BELOW_VAL";
  signal: "SUPPORT" | "RESISTANCE" | "BREAKOUT" | "BREAKDOWN" | "NEUTRAL";
  tone: "pos" | "neg" | "amber";
  value_area_pct: number;
}

export interface VProfileResponse {
  as_of: string;
  universe_size: number;
  count: number;
  summary: Record<string, number>;
  rows: VProfileRow[];
}

export interface SRLevelEntry {
  price: number;
  kind: "S" | "R" | "PIVOT";
  strength: number;
  distance_pct: number;
}

export interface SupportRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  state: "AT_S" | "AT_R" | "MID";
  nearest_support: number | null;
  nearest_resistance: number | null;
  dist_support_pct: number | null;
  dist_resistance_pct: number | null;
  levels: SRLevelEntry[];
  tone: "pos" | "neg" | "neutral";
}

export interface SupportResponse {
  as_of: string;
  universe_size: number;
  count: number;
  summary: Record<string, number>;
  rows: SupportRow[];
}
