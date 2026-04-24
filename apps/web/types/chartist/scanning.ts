// Sub-section API responses (packages/core/ky_core/scanning/*).
// Leaders, sectors, breakouts, OHLCV, breadth, wizards.

export interface LeaderRow {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  leader_score: number;
  tt_passes: number;
  trend_template: string;
  rs: number;
  rs_percentile: number;
  d1: number;
  d5: number;
  m1: number;
  vol_x: number;
  vcp_stage: number;
  pattern: string;
  eps_signal: number;
  sector_strength: number;
  reason: string;
}

export interface LeadersResponse {
  as_of: string;
  universe_size: number;
  count: number;
  rows: LeaderRow[];
}

export interface SectorRow {
  rank: number;
  name: string;
  members: number;
  score: number;
  d1: number;    // fraction (e.g. 0.0214 = 2.14%)
  d5: number;
  m1: number;
  m3: number;
  ytd: number;
  sparkline: number[];
}

export interface SectorsResponse {
  as_of: string;
  count: number;
  rows: SectorRow[];
}

export interface BreakoutRow52w {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  pct_up: number;
  vol_x: number;
  high52w: number;
  dist_from_high_pct?: number;
}

export interface BreakoutsResponse {
  as_of: string;
  count: number;
  rows: BreakoutRow52w[];
}

// OHLCV candle payload for ChartPane.
export interface OHLCVCandle {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  sma50: number | null;
  sma200: number | null;
}

export interface OHLCVResponse {
  symbol: string;
  market: string | null;
  as_of: string | null;
  count: number;
  candles: OHLCVCandle[];
}

export interface BreadthResponse {
  as_of: string;
  universe: number;
  advancers: number;
  decliners: number;
  unchanged: number;
  pct_above_sma20: number;
  pct_above_sma50: number;
  pct_above_sma200: number;
  new_highs_52w: number;
  new_lows_52w: number;
  up_volume: number;
  down_volume: number;
  up_vol_pct: number;
  mcclellan: number;
  ad_line_series: number[];
}

export interface WizardPresetCount {
  key: string;
  name: string;
  condition: string;
  pass_count: number;
  total: number;
  delta_vs_yesterday: number;
}

export interface WizardsOverview {
  as_of: string;
  universe_size: number;
  presets: WizardPresetCount[];
}

export interface WizardHit {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  pct_1d: number;
  vol_x: number;
  reason: string;
}

export interface WizardDetail {
  as_of: string;
  key: string;
  name: string;
  condition: string;
  count: number;
  rows: WizardHit[];
}
