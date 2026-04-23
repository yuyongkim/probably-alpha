// Admin tab — shared types.

export interface AdminDB {
  db_path: string | null;
  db_size_bytes: number | null;
  rows: Record<string, number>;
  rag?: {
    ready: boolean;
    chunks?: number;
    files_indexed?: number;
    files_total?: number;
    built_at?: string;
    bytes?: number;
  };
  error?: string;
}

export interface AdminStatus {
  owner_id: string;
  shared_env_loaded: boolean;
  secrets_present: Record<string, boolean>;
  feature_flags: Record<string, boolean>;
  // ``db`` is populated by the introspection path; older / lightweight
  // responses may omit it entirely, so it must be optional.
  db?: AdminDB;
}

export interface AdapterHealth {
  source_id: string;
  ok: boolean;
  latency_ms?: number | null;
  last_error?: string | null;
  configured?: boolean;
  import_error?: string;
  [k: string]: unknown;
}

export interface DataHealth {
  adapters: AdapterHealth[];
}

export interface JobEntry {
  name: string;
  kind: string;
  size_bytes: number;
  modified_at: string;
  tail: string[];
}

export interface JobsResponse {
  jobs: JobEntry[];
  root: string;
  warning?: string;
}

export interface FddRule {
  rule: string;
  sql: string;
  severity: string;
  description: string;
  count: number;
  error?: string;
}

export interface FddResponse {
  rules: FddRule[];
}

export interface KeyStatus {
  name: string;
  status: "present" | "missing";
}

export interface KeysResponse {
  keys: KeyStatus[];
  shared_env_loaded: boolean;
}

// ---- Multi-tenant control plane --------------------------------------------

export interface TenantRow {
  tenant_id: string;
  display_name: string;
  plan: string;
  rate_limit_per_min: number;
  enabled: boolean;
  created_at: string | null;
}

export interface TenantListResponse {
  count: number;
  tenants: TenantRow[];
}

export interface UsageSummaryRow {
  tenant_id: string;
  calls: number;
  avg_latency_ms: number;
  plan: string;
  monthly_fee_usd: number;
}

export interface UsageEvent {
  id: number;
  tenant_id: string;
  endpoint: string;
  latency_ms: number;
  status_code: number;
  ts: string;
}

export interface UsageResponse {
  since: string;
  summary: UsageSummaryRow[];
  events: UsageEvent[];
}

export interface AuditEvent {
  id: number;
  tenant_id: string;
  action: string;
  detail: string | null;
  ts: string;
}

export interface AuditResponse {
  count: number;
  events: AuditEvent[];
}

// ---- Nightly / weekly run history ------------------------------------------

export interface NightlyStageSummary {
  name: string;
  status: "ok" | "fail" | "skipped" | "dry_run" | "pending";
  duration_s: number;
  rows_added: number;
  symbols_processed: number;
  error: string | null;
}

export interface NightlyRunSummary {
  file: string;
  kind: "nightly" | "weekly" | string;
  started_at: string | null;
  ended_at: string | null;
  duration_s: number;
  total_rows_added: number;
  stage_count: number;
  stage_ok: number;
  stage_fail: number;
  partial_success: boolean;
  dry_run: boolean;
  errors: string[];
  stages: NightlyStageSummary[];
  // Backend returns only ``error`` + ``started_at`` when a report file is
  // unreadable; everything else may be absent.
  error?: string;
}

export interface NightlyRunsResponse {
  root: string;
  kind: string;
  limit: number;
  runs: NightlyRunSummary[];
  warning: string | null;
}
