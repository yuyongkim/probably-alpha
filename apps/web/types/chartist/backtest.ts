// Backtest — mirrors packages/core/ky_core/backtest artefacts.

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
