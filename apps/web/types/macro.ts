// Macro tab — shared types. Mirrors ky_core.macro.

export type AxisId = "growth" | "inflation" | "liquidity" | "credit";

export interface AxisDetail {
  axis: AxisId;
  score: number;
  series_id: string | null;
  latest_value: number | null;
  prior_value: number | null;
  change_pct: number | null;
  note: string;
}

export interface CompassResponse {
  axes: Record<AxisId, AxisDetail>;
  composite: number;
  regime_hint: string;
  generated_at: string;
  stale: boolean;
  warnings: string[];
  playbook: PlaybookEntry[];
}

export interface PlaybookEntry {
  sector: string;
  rationale: string;
}

export interface RegimeTimeseriesItem {
  month: string;
  fed_funds: number;
  label: string;
  delta_bp: number | null;
}

export interface RegimeResponse {
  current: string;
  probabilities: Record<string, number>;
  composite: number;
  compass: CompassResponse;
  timeseries: RegimeTimeseriesItem[];
  warnings: string[];
}

export interface RotationResponse {
  regime: string;
  composite: number;
  playbook: PlaybookEntry[];
}

export interface CorrCell {
  sector: string;
  macro: string;
  corr: number;
}

export interface CorrResponse {
  window: number;
  sectors: string[];
  macros: string[];
  cells: CorrCell[];
  warning?: string;
}

export interface MacroSeriesObs {
  source_id: string;
  series_id: string;
  date: string;
  value: number | null;
  unit: string | null;
  meta: Record<string, unknown> | null;
}

export interface MacroSeriesResponse {
  source: string;
  series_id: string;
  observations: MacroSeriesObs[];
  stale_data: boolean;
  warning?: string;
}
