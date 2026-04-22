// Quant types — mirror ky_core.quant response shapes.

export interface FactorRow {
  symbol: string;
  market: string;
  name: string | null;
  sector: string | null;
  close: number | null;
  momentum: number | null;
  low_vol: number | null;
  value: number | null;
  quality: number | null;
  growth: number | null;
  composite: number | null;
}

export interface FactorResponse {
  as_of: string;
  sort: string;
  n: number;
  rows: FactorRow[];
}

export interface AcademicRow extends FactorRow {
  roc?: number;
  earnings_yield?: number;
  magic_score?: number;
  pb_proxy?: number;
  rev_yoy?: number | null;
  ni_yoy?: number | null;
  score?: number;
  super_score?: number;
  ebit_ttm?: number;
}

export interface AcademicResponse {
  as_of: string;
  strategy: string;
  n: number;
  rows: AcademicRow[];
}

export interface SmartBetaHolding {
  symbol: string;
  name: string | null;
  market: string | null;
  sector: string | null;
  weight: number;
  score: number | null;
}

export interface SmartBetaResponse {
  variant: string;
  as_of: string;
  n: number;
  holdings: SmartBetaHolding[];
}

export interface PITTtm {
  symbol: string;
  as_of: string;
  period_end: string;
  revenue_ttm: number | null;
  operating_income_ttm: number | null;
  net_income_ttm: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  total_equity: number | null;
  n_quarters: number;
  source: string;
}

export interface PITSeriesRow {
  symbol: string;
  period_end: string;
  period_type: string;
  report_date: string | null;
  revenue: number | null;
  operating_income: number | null;
  net_income: number | null;
  total_assets: number | null;
  total_liabilities: number | null;
  total_equity: number | null;
  source_id: string;
}

export interface PITResponse {
  symbol: string;
  as_of: string;
  meta: {
    ticker: string;
    market: string;
    name: string | null;
    sector: string | null;
    industry: string | null;
  } | null;
  ttm: PITTtm | null;
  series: PITSeriesRow[];
}

export interface ICResponse {
  factor: string;
  period: string;
  as_of: string;
  n: number;
  ic: number | null;
  hit_rate: number;
}

export interface UniverseResponse {
  market: string[];
  n: number;
  rows: Array<{
    symbol: string;
    market: string;
    name: string | null;
    sector: string | null;
    industry: string | null;
  }>;
}
