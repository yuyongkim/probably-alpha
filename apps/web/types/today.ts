// Types mirroring /api/v1/chartist/today response (verified live 2026-04-24).
export interface KpiPill {
  label: string;
  value: string;
  delta?: string;
  tone?: "pos" | "neg" | "neutral";
}

export interface TodayLeader {
  symbol: string;
  name?: string;
  sector?: string;
  leader_score?: number;
  trend_template?: string;
  rs?: number;
  d1?: number;
  d5?: number;
  m1?: number;
  vol_x?: number;
  pattern?: string;
}

export interface TodaySector {
  rank?: number;
  name: string;
  score?: number;
  d1?: number;
  d5?: number;
  sparkline?: number[];
}

export interface TodayWizard {
  name: string;
  condition?: string;
  pass_count?: number;
  total?: number;
  delta_vs_yesterday?: number;
}

export interface TodayStage {
  name: string;
  count?: number;
  pct?: number;
  color_hint?: string;
}

export interface TodayBreakout {
  ticker?: string;
  symbol: string;
  market?: string;
  pct_up?: number;
  vol_x?: number;
  sector?: string;
}

export interface TodayBundle {
  date?: string;
  owner_id?: string;
  universe_size?: number;
  market: KpiPill[];
  summary: KpiPill[];
  leaders: TodayLeader[];
  sectors: TodaySector[];
  wizards_pass?: TodayWizard[];
  stage_dist?: TodayStage[];
  breakouts?: TodayBreakout[];
  last_backtest_cagr?: number | null;
}
