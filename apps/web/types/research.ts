// Research tab — shared types. Mirrors ky_core.research + router shapes.

export interface KnowledgeSearchResult {
  chunk_id: string;
  score: number;
  text: string;
  source_file: string;
  estimated_work: string;
  chunk_index: number;
  page_start: number | null;
  page_end: number | null;
  estimated_author: string | null;
}

export interface KnowledgeSearchResponse {
  query: string;
  top_k: number;
  results: KnowledgeSearchResult[];
  index?: {
    chunks?: number;
    files_indexed?: number;
    built_at?: string;
  };
  stale?: boolean;
  message?: string;
}

export interface KnowledgeStatus {
  ready: boolean;
  chunks?: number;
  files_indexed?: number;
  files_total?: number;
  built_at?: string;
  vocabulary_size?: number;
  reason?: string;
  hint?: string;
  index_dir?: string;
}

export interface BuffettWork {
  work: string;
  source_file: string;
  chunks: number;
  pages_min: number | null;
  pages_max: number | null;
}

export interface BuffettIndex {
  works: BuffettWork[];
  total_chunks: number;
  ready: boolean;
  reason?: string | null;
}

export interface BuffettSearchResponse {
  query: string;
  results: KnowledgeSearchResult[];
  count: number;
}

export interface FactorStats {
  mean: number;
  std: number;
  sharpe: number;
  total: number;
  n: number;
}

export interface FactorResult {
  factor: string;
  dates: string[];
  long_returns: number[];
  short_returns: number[];
  spread: number[];
  cumulative: number[];
  stats: FactorStats;
  universe_size: number;
  note: string;
  meta?: Record<string, unknown>;
}

export interface PapersResponse {
  papers: Array<{
    source_file: string;
    estimated_work: string;
    best_score: number;
    chunks: number;
    sample_text: string;
  }>;
  note?: string;
}

export interface ShellResponse {
  slug: string;
  title: string;
  note: string;
  data: unknown[];
}

// ---------------------------------------------------------------------------
// RAG topic filters (interviews / psychology / cycles / blogs)
// ---------------------------------------------------------------------------

export interface RagFilterWork {
  work: string;
  source_file: string;
  chunks: number;
  pages_min: number | null;
  pages_max: number | null;
}

export interface RagFilterIndex {
  slug: string;
  display: string;
  works: RagFilterWork[];
  total_chunks: number;
  ready: boolean;
  reason?: string | null;
}

export interface RagFilterSearchResponse {
  slug: string;
  query: string;
  results: KnowledgeSearchResult[];
  count: number;
}

// ---------------------------------------------------------------------------
// News
// ---------------------------------------------------------------------------

export interface NewsItem {
  title: string;
  description: string;
  link: string;
  pub_date: string;
  source: string;
  sentiment_score: number;
  sentiment_label: "positive" | "negative" | "neutral";
  pos_hits: string[];
  neg_hits: string[];
}

export interface NewsSearchResponse {
  query: string;
  items: NewsItem[];
  source: string;
  stale: boolean;
  summary: {
    n: number;
    avg_score: number;
    positive: number;
    negative: number;
    neutral: number;
  };
}

// ---------------------------------------------------------------------------
// KR brokerage reports
// ---------------------------------------------------------------------------

export interface KRReportItem {
  title: string;
  broker: string;
  published: string;
  link: string;
  symbol: string | null;
  target_price: string | null;
  direction: "up" | "down" | null;
  category: string;
}

export interface KRReportsResponse {
  category: string;
  items: KRReportItem[];
  count: number;
  stale: boolean;
  summary: {
    brokers: string[];
    broker_count: number;
    target_up: number;
    target_down: number;
    neutral: number;
  };
}

// ---------------------------------------------------------------------------
// Weekly / monthly review
// ---------------------------------------------------------------------------

export interface ReviewRow {
  name: string;
  score?: number | null;
  note?: string;
  symbol?: string;
  leader_score?: number;
  trend_template?: string;
}

export interface ReviewSection {
  title: string;
  rows: ReviewRow[];
}

export interface ReviewResponse {
  as_of: string;
  period: string;
  sections: ReviewSection[];
  stale_sources: string[];
}

// ---------------------------------------------------------------------------
// AI research agent
// ---------------------------------------------------------------------------

export interface AIAgentResponse {
  question: string;
  answer: string;
  mode: "claude" | "stub";
  model: string | null;
  citations: KnowledgeSearchResult[];
  stale?: boolean;
  reason?: string | null;
}
