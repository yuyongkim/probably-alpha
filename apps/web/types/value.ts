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
