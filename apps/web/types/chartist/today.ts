// Today bundle shapes — consumed by the chartist landing page.

import type { MarketIndex, SummaryKPI } from "./common";

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
