// Korean-market sub-sections: flow · themes · shortint · kiwoom conditions
// (owned by other agents, re-declared here to keep web types in one file)

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
