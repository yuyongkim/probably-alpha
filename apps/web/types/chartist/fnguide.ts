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
