# Project Objective (English)

Date: 2026-03-09

## 1) Objective
The goal of this project is to implement the Minervini SEPA strategy with an
**OmX Multi-Agent architecture** using a **Design First** approach,
and to transfer your EPC engineering decision framework into the financial domain.

The three key deliverables are:
1. Daily signal outputs (Alpha to Omega)
2. A reproducible, rule-based decision chain
3. Production-ready standards for validation, operations, and recovery

## 2) Current Execution Objective
As of 2026-03-09, the active objective is:
- **Week 1 MVP:** operational Alpha screener
- **Parallel expansion:** improved Beta (VCP) auto-detection
- **Documentation lock:** formalized input/output schemas, ops rules, and failover rules

## 3) Done Definition
- Alpha consistently produces top candidates from the market universe
- Beta assigns VCP confidence scores to Alpha-passed symbols
- Outputs are persisted at `.omx/artifacts/daily-signals/{YYYYMMDD}/`
- Error/recovery traces are persisted at `.omx/artifacts/audit-logs/`

## 4) Business View
- Short-term: internal decision automation
- Mid-term: subscription report product (Freemium/Basic/Premium)
- Long-term: B2B API for brokers and asset managers

## 5) Principles
1. Design First (lock design before implementation)
2. Rule Integrity (no compromise on core Minervini rules)
3. Auditability (traceable decision process)
4. Safe Execution (Paper Trading by default)

## 6) Implementation Update (2026-03-09)
- Live refresh pipeline draft: `sepa/pipeline/refresh_market_data.py`
- Daily cycle runner: `sepa/pipeline/run_live_cycle.py`
- Kiwoom adapter: `sepa/data/kiwoom.py` (env-driven endpoint injection)
- Added symbol mapping logic: `.KS/.KQ -> Kiwoom code` (`sepa/data/symbols.py`)
- Documented Kiwoom endpoint spec: `docs/specs/KIWOOM_ENDPOINT_SPEC.md`
- Kiwoom adapter hardened: multi-shape parsing + retry/backoff + audit logs
- `run_mvp` now triggers refresh first when `SEPA_LIVE_MODE=1`
- Beta scoring tuned: stricter contraction/volume rules and noisy-pattern filter
- Backend API added: `sepa/api/app.py` (FastAPI)
- Frontend dashboard added: `sepa/frontend/*` (static HTML/JS)
- Run guide: `docs/FRONTEND_BACKEND_RUNBOOK_EN.md`
