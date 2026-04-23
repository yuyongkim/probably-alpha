// Value types — mirror ky_core.value response shapes.

export interface DcfStage1Row {
  year: number;
  fcf: number;
  pv: number;
}

export interface WaccBreakdown {
  symbol?: string;
  wacc: number;
  override?: boolean;
  cost_of_equity?: number;
  cost_of_debt_after_tax?: number;
  w_equity?: number;
  w_debt?: number;
  rf?: number;
  erp?: number;
  beta?: number;
  fallback?: boolean;
}

export interface DcfResponse {
  symbol: string;
  as_of: string;
  assumptions: {
    growth_high: number;
    years_high: number;
    growth_term: number;
    wacc: number;
  };
  fcf0: number;
  stage1: DcfStage1Row[];
  pv_stage1: number;
  terminal_value: number;
  pv_terminal: number;
  enterprise_value: number;
  shares_outstanding_proxy: number | null;
  per_share_value: number | null;
  wacc_breakdown: WaccBreakdown;
  note?: string;
}

export interface WaccResponse extends WaccBreakdown {
  symbol: string;
  as_of: string;
}

export interface TrendRow {
  period_end: string;
  period_type: string;
  revenue: number | null;
  operating_income: number | null;
  net_income: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  total_equity: number | null;
  source_id: string;
}

export interface TrendResponse {
  symbol: string;
  meta: { name: string | null; sector: string | null } | null;
  series: TrendRow[];
}

export interface LeaderRow {
  symbol: string;
  name: string | null;
  market: string | null;
  sector: string | null;
  close: number | null;
  [k: string]: unknown;
}

export interface LeaderListResponse {
  as_of: string;
  n: number;
  rows: LeaderRow[];
  mode?: string;
}

export interface PiotroskiFlags {
  roa_positive: number | null;
  cfo_positive: number | null;
  delta_roa: number | null;
  accrual: number | null;
  delta_leverage: number | null;
  delta_liquidity: number | null;
  no_new_shares: number | null;
  delta_margin: number | null;
  delta_turnover: number | null;
}

export interface PiotroskiResponse {
  symbol: string;
  as_of: string;
  flags: PiotroskiFlags;
  score: number;
  max_possible: number;
}

export interface AltmanResponse {
  symbol: string;
  as_of: string;
  A_wc_assets: number;
  B_re_assets: number;
  C_ebit_assets: number;
  D_mcap_liab: number;
  E_sales_assets: number;
  z_score: number;
  zone: "safe" | "grey" | "distress";
  proxy: boolean;
}

// --------------------------------------------------------------------------- //
// Disclosure / quality sub-sections                                           //
// --------------------------------------------------------------------------- //

export interface InsiderRow {
  date: string;
  corp_code: string | null;
  corp_name: string | null;
  stock_code: string | null;
  report_name: string;
  kind: "insider" | "insider_plan" | "bulk_ownership";
  filer_name: string | null;
  receipt_no: string | null;
  signal: string;
}

export interface InsiderKpi {
  total: number;
  insider: number;
  bulk_ownership: number;
  plan: number;
  lookback_days: number;
}

export interface InsiderResponse {
  lookback_days: number;
  kind: string;
  kpi: InsiderKpi;
  rows: InsiderRow[];
}

export interface BuybackRow {
  date: string;
  corp_code: string | null;
  corp_name: string | null;
  stock_code: string | null;
  report_name: string;
  action: "buyback" | "dispose" | "cancel" | "trust" | "other";
  status: "decision" | "result";
  receipt_no: string | null;
}

export interface BuybackKpi {
  total: number;
  buyback_decision: number;
  buyback_result: number;
  cancel: number;
  trust: number;
  dispose: number;
  lookback_days: number;
}

export interface BuybackResponse {
  lookback_days: number;
  action: string;
  kpi: BuybackKpi;
  rows: BuybackRow[];
}

export interface ConsensusRow {
  symbol: string;
  name: string | null;
  sector: string | null;
  market: string | null;
  close: number | null;
  opinion: string | null;
  recomm_score: number | null;
  consensus_per: number | null;
  consensus_eps: number | null;
  forward_eps_estimate: number | null;
  eps_rev: number | null;
  target_price: number | null;
  tp_upside: number | null;
  sentiment: "positive" | "neutral" | "negative";
}

export interface ConsensusKpi {
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  eps_rev_up: number;
  eps_rev_down: number;
}

export interface ConsensusResponse {
  mode: string;
  kpi?: ConsensusKpi;
  rows: ConsensusRow[];
  n?: number;
}

export interface MoatRow {
  symbol: string;
  name: string | null;
  sector: string | null;
  market: string | null;
  roic_10y_mean: number;
  roic_10y_std: number;
  roe_years_above_10pct: number;
  years_used: number;
  revenue_cagr: number | null;
  moat: "wide" | "narrow" | "none";
}

export interface MoatKpi {
  total: number;
  wide: number;
  narrow: number;
  none: number;
}

export interface MoatResponse {
  mode: string;
  kpi: MoatKpi;
  rows: MoatRow[];
}

export interface SegmentRow {
  symbol: string;
  name: string | null;
  sector: string | null;
  market: string | null;
  market_cap: number;
  sotp_proxy: number;
  discount: number;
  pbr: number;
  sector_median_pbr: number;
  proxy: boolean;
}

export interface SegmentKpi {
  candidates: number;
  discount_gt_20: number;
  premium_gt_20: number;
  proxy_mode: boolean;
}

export interface SegmentResponse {
  kpi: SegmentKpi;
  rows: SegmentRow[];
}

export interface DividendRow {
  symbol: string;
  name: string | null;
  sector: string | null;
  market: string | null;
  dividend_yield: number | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
  ni_growth_streak: number;
  reported_years: number;
  aristocrat: boolean;
  aristocrat_proxy: boolean;
}

export interface DividendKpi {
  with_yield: number;
  aristocrats: number;
  yield_gt_5pct: number;
}

export interface DividendResponse {
  mode: string;
  kpi?: DividendKpi;
  rows: DividendRow[];
  aristocrats?: DividendRow[];
  n?: number;
}

export interface ComparablesRow {
  symbol: string;
  name: string | null;
  sector: string | null;
  market: string | null;
  per: number | null;
  pbr: number | null;
  roe: number | null;
  dividend_yield: number | null;
  market_cap: number | null;
  sector_peer_count: number;
  per_rank_pct: number | null;
  pbr_rank_pct: number | null;
  sector_median_per: number | null;
  sector_median_pbr: number | null;
  per_vs_median: number | null;
  pbr_vs_median: number | null;
  outlier_cheap: boolean;
}

export interface ComparablesKpi {
  ranked: number;
  outlier_cheap: number;
  sectors_covered: number;
}

export interface ComparablesResponse {
  mode: string;
  kpi?: ComparablesKpi;
  rows?: ComparablesRow[];
  outliers?: ComparablesRow[];
  top_sectors?: { sector: string; count: number }[];
  sector?: string;
  n?: number;
}
