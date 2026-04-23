// Shape mirrors packages/core/ky_core/chartist.py (pydantic models).
// Keep manually in sync until codegen is introduced.

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

export interface Leader {
  symbol: string;
  name: string;
  sector: string;
  leader_score: number;
  trend_template: string;
  rs: number;
  d1: number;
  d5: number;
  m1: number;
  vol_x: number;
  pattern: string;
}

export interface Sector {
  rank: number;
  name: string;
  score: number;
  d1: number;
  d5: number;
  sparkline: number[];
}

export interface SectorHeatRow {
  name: string;
  p1d: number;
  p1d_h: number;
  p1w: number;
  p1w_h: number;
  p1m: number;
  p1m_h: number;
  p3m: number;
  p3m_h: number;
  pytd: number;
  pytd_h: number;
}

export interface Breakout {
  ticker: string;
  symbol: string;
  market: string;
  pct_up: number;
  vol_x: number;
  sector: string;
}

export interface WizardCount {
  name: string;
  condition: string;
  pass_count: number;
  total: number;
  delta_vs_yesterday: number;
}

export interface StageBucket {
  name: string;
  count: number;
  pct: number;
  color_hint: string;
}

export interface LogEvent {
  time: string;
  tag: string; // BUY | SELL | VCP | EPS | DART | BRK | SYS
  symbol: string | null;
  message: string;
}

export interface UpcomingEvent {
  date: string;
  ticker_or_event: string;
  type: string; // Earnings | Macro
  consensus_eps: string | null;
  note: string;
}

export interface TodayBundle {
  date: string;
  owner_id: string;
  universe_size: number;
  market: MarketIndex[];
  summary: SummaryKPI[];
  leaders: Leader[];
  sectors: Sector[];
  heatmap: SectorHeatRow[];
  breakouts: Breakout[];
  wizards_pass: WizardCount[];
  stage_dist: StageBucket[];
  activity_log: LogEvent[];
  upcoming_events: UpcomingEvent[];
  last_backtest_cagr: number | null;
}

// Stock Detail Modal — global tickable reference.
// Lives here so both chartist table rows and TickerName wrapper use one type.
export interface TickerRef {
  symbol: string;
  name: string;
  sector?: string;
}

// ===========================================================================
// Sub-section API responses (packages/core/ky_core/scanning/*).
// ===========================================================================

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

export interface AsOfInfo {
  as_of: string;
  today: string;
  stale: boolean;
  universe_size: number;
}

// FnGuide snapshot (Naver Mobile + NaverComp WiseReport + fnguide fallback).
export interface FnguidePeer {
  symbol: string | null;
  name: string | null;
  close: number | null;
  change_pct: number | null;
  market_cap: number | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
}

export interface FnguideFinRow {
  period: string | null;
  period_type?: string | null;
  is_estimate?: boolean;
  revenue?: number | null;
  operating_income?: number | null;
  operating_income_reported?: number | null;
  net_income?: number | null;
  net_income_controlling?: number | null;
  net_income_non_controlling?: number | null;
  pretax_income?: number | null;
  tax_expense?: number | null;
  eps?: number | null;
  bps?: number | null;
  roe?: number | null;
  roa?: number | null;
  operating_margin?: number | null;
  net_margin?: number | null;
  debt_ratio?: number | null;
  quick_ratio?: number | null;
  retention_ratio?: number | null;
  total_assets?: number | null;
  total_liabilities?: number | null;
  total_equity?: number | null;
  per?: number | null;
  pbr?: number | null;
  dividend_per_share?: number | null;
  dividend_yield?: number | null;
}

export interface FnguideMetricRow {
  period: string;
  is_estimate?: boolean;
  gross_margin?: number | null;
  operating_margin?: number | null;
  net_margin?: number | null;
  ebitda_margin?: number | null;
  roe?: number | null;
  roa?: number | null;
  roic?: number | null;
}

export interface FnguideSectorTriple {
  company: number | null;
  sector: number | null;
  market: number | null;
}

export interface FnguideInvestorTrendRow {
  date: string;
  foreign_net: number | null;
  foreign_hold_ratio: number | null;
  institution_net: number | null;
  individual_net: number | null;
  close: number | null;
  volume: number | null;
}

export interface FnguideSnapshot {
  symbol: string;
  fetched_at: number;
  source: string;
  degraded: boolean;
  cached?: boolean;
  stale?: boolean;
  age_seconds?: number;
  fetch_error?: string;
  target_price: number | null;
  investment_opinion: string | null;
  consensus_recomm_score?: number | null;
  consensus_per?: number | null;
  consensus_eps?: number | null;
  per: number | null;
  pbr: number | null;
  eps: number | null;
  bps: number | null;
  roe: number | null;
  roa: number | null;
  debt_ratio: number | null;
  dividend_yield: number | null;
  market_cap: number | null;
  market_cap_raw?: string;
  foreign_ratio: number | null;
  high_52w?: number | null;
  low_52w?: number | null;
  industry_code?: string | null;
  major_shareholder_name: string | null;
  major_shareholder_pct: number | null;
  float_ratio?: number | null;
  shares_outstanding?: number | null;
  beta_52w?: number | null;
  financials_quarterly: FnguideFinRow[];
  financials_annual: FnguideFinRow[];
  financial_metrics?: FnguideMetricRow[];
  sector_comparison?: Record<string, FnguideSectorTriple>;
  investor_trend?: FnguideInvestorTrendRow[];
  peers: FnguidePeer[];
  summary_notes: string[];
  sources_used?: string[];
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

// ===========================================================================
// Korean-market sub-sections: flow · themes · shortint · kiwoom conditions
// (owned by other agents, re-declared here to keep web types in one file)
// ===========================================================================

export interface FlowRow {
  rank: number;
  symbol: string;
  name: string;
  sector: string;
  market: string;
  d1: number;
  d5: number;
  d20: number;
  streak: number;
  price_pct: number;
  close: number;
}

export interface SectorFlow {
  name: string;
  members: number;
  d1: number;
  d5: number;
  d20: number;
}

export interface FlowResponse {
  as_of: string;
  universe_size: number;
  covered: number;
  foreign_top: FlowRow[];
  institution_top: FlowRow[];
  individual_top: FlowRow[];
  sector_foreign: SectorFlow[];
}

export interface ThemeMember {
  symbol: string;
  name: string;
  sector: string;
  weight: number;
  d1: number;
  w1: number;
  m1: number;
  ytd: number;
}

export interface ThemeRow {
  code: string;
  name: string;
  bucket: string;
  members: number;
  covered: number;
  d1: number;
  w1: number;
  m1: number;
  m3: number;
  ytd: number;
  rank_now: number;
  rank_w1: number;
  rank_w2: number;
  rank_w4: number;
  delta_4w: number;
  trend: string;
  top_member: string | null;
  constituents: ThemeMember[];
}

export interface ThemesResponse {
  as_of: string;
  universe_size: number;
  count: number;
  rows: ThemeRow[];
}

export interface ShortIntRow {
  rank: number;
  symbol: string;
  name: string;
  sector: string;
  market: string;
  close: number;
  pct_5d: number;
  pct_20d: number;
  vol_ratio_20: number;
  short_proxy_pct: number;
  status: string;
  source: string;
}

export interface SqueezeRow {
  rank: number;
  symbol: string;
  name: string;
  sector: string;
  market: string;
  close: number;
  pct_5d: number;
  pct_20d: number;
  vol_ratio_5: number;
  trigger: string;
  risk: string;
  short_proxy_pct: number;
  source: string;
}

export interface SectorShort {
  name: string;
  members: number;
  mean_proxy_pct: number;
  overheated: number;
}

export interface ShortIntResponse {
  as_of: string;
  universe_size: number;
  notice: string;
  overheated: ShortIntRow[];
  squeeze: SqueezeRow[];
  sector_overheat: SectorShort[];
}

export interface KiwoomCondHit {
  symbol: string;
  name: string;
  market: string;
  sector: string;
  close: number;
  vol: number;
  vol_ratio: number;
  ma5: number;
  ma20: number;
  ma60: number;
  pct_1d: number;
  reason: string;
}

export interface KiwoomCondBucket {
  id: string;
  name: string;
  desc: string;
  pass_count: number;
  top: KiwoomCondHit[];
}

export interface KiwoomCondResponse {
  as_of: string;
  universe_size: number;
  buckets: KiwoomCondBucket[];
  intersection_4of7: KiwoomCondHit[];
  intersection_all: KiwoomCondHit[];
  total_pass: number;
}

// ===========================================================================
// Technicals 6 subsections — patterns / candlestick / divergence / ichimoku /
// vprofile / support.
// Shapes mirror packages/core/ky_core/scanning/{vcp,candlestick,divergence,
// ichimoku,vprofile,support}.py.
// ===========================================================================

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

// ===========================================================================
// Backtest — mirrors packages/core/ky_core/backtest artefacts.
// ===========================================================================

export interface BacktestMetrics {
  start: string;
  end: string;
  n_days: number;
  final_equity: number;
  total_return: number;
  cagr: number;
  max_drawdown: number;
  sharpe: number;
  sortino: number;
  calmar: number;
  volatility: number;
  win_rate: number;
  profit_factor: number;
  n_trades: number;
  avg_holding_days: number;
  best_trade: number;
  worst_trade: number;
}

export interface BacktestEquityPoint {
  date: string;
  equity: number;
  cash?: number;
  n_positions?: number;
}

export interface BacktestBenchmarkPoint {
  date: string;
  value: number;
}

export interface BacktestTrade {
  symbol: string;
  name: string;
  sector: string;
  entry_date: string;
  entry_price: number;
  exit_date: string;
  exit_price: number;
  shares: number;
  pnl: number;
  pnl_pct: number;
  holding_days: number;
  exit_reason: string;
}

export interface BacktestSectorAttribution {
  n_trades: number;
  gross_pnl: number;
  gross_win: number;
  gross_loss: number;
  wins: number;
  losses: number;
  win_rate: number;
}

export interface BacktestConfigPayload {
  strategy_name: string;
  start: string;
  end: string;
  initial_cash: number;
  markets: string[];
  max_positions: number;
  max_per_sector: number;
  risk_per_trade_pct: number;
  stop_loss_pct: number;
  benchmark_symbol?: string | null;
  cost: {
    buy_commission: number;
    sell_commission: number;
    slippage: number;
    sell_tax: number;
  };
}

export interface BacktestRun {
  run_id: string;
  config: BacktestConfigPayload;
  equity_curve: BacktestEquityPoint[];
  benchmark_curve: BacktestBenchmarkPoint[];
  trades: BacktestTrade[];
  metrics: BacktestMetrics;
  sector_attribution: Record<string, BacktestSectorAttribution>;
  universe_size: number;
  n_trading_days: number;
  generated_at: string;
}

export interface BacktestRunSummary {
  run_id: string;
  strategy: string;
  start: string;
  end: string;
  generated_at: string;
  universe_size: number;
  n_trades: number;
  cagr: number;
  max_drawdown: number;
  sharpe: number;
  win_rate: number;
  final_equity: number;
  total_return: number;
  path: string;
}

export interface BacktestListResponse {
  count: number;
  runs: BacktestRunSummary[];
}
