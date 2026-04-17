# probably-alpha

SEPA-based Korea stock signal engine with Market Wizards presets, backtests, and dashboard tooling.

This repo is building a rule-based decision stack for the Korea market. The shape is simple:

- ingest market data
- run Alpha to Omega signal stages
- persist daily artifacts
- expose them through a FastAPI backend and static dashboard
- layer Market Wizards style presets on top for alternate ranking and interpretation

## What is in here

- **Data pipeline**: refresh, after-close run, backfill
- **Signal chain**: Alpha, Beta, Gamma, Delta, Omega
- **Leader scan**: sector and stock leadership views
- **Backtests**: preset-driven strategy evaluation
- **Frontend**: dashboard, Market Wizards pages, trader debate
- **API**: public read endpoints plus admin generation flows

## Project layout

- `sepa/agents/` - Alpha to Omega agents and related logic
- `sepa/data/` - market data loaders, adapters, universe, facts
- `sepa/pipeline/` - refresh, after-close, live-cycle, backfill
- `sepa/api/` - FastAPI app and routes
- `sepa/frontend/` - static HTML, JS, CSS dashboard
- `sepa/backtest/` - preset configs and backtest engine
- `docs/` - architecture, philosophy, contracts, operations

## Quick start

### 1) Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2) Start the local stack

Windows:

```powershell
scripts\start_local.bat
```

Optional dependency install during bootstrap:

```powershell
scripts\start_local.bat -InstallDeps
```

### 3) Run the after-close pipeline explicitly

```bash
python -m sepa.pipeline.run_after_close
```

### 4) Run tests

```bash
python -m pytest
```

## Local services

Backend:

```bash
uvicorn sepa.api.app:app --host 127.0.0.1 --port 8200
```

Main frontend is served by the FastAPI app. If you want a separate static server:

```bash
python -m http.server 8280 --directory sepa/frontend
```

## Useful endpoints

- `GET /api/health`
- `GET /api/kis/health`
- `GET /api/kis/catalog`
- `GET /api/dashboard`
- `GET /api/leaders/sectors`
- `GET /api/leaders/stocks`
- `GET /api/recommendations/latest`
- `GET /api/briefing/latest`
- `GET /api/trader-debate`
- `GET /api/backtest/presets`
- `GET /api/etf/{symbol}/analysis`
- `GET /api/etf/universe`
- `GET /api/overseas/stock/{symbol}/analysis`
- `POST /api/etf/recommendations/profile`
- Public backtest result endpoints are read-only; mutating or generative backtest execution is admin-only.

## KIS product scope

The KIS sample repo exposes multiple product families:

- domestic stocks
- domestic ETF/ETN
- overseas stocks
- domestic bonds
- domestic futures/options
- overseas futures/options
- ELW

In this project, the current priority lanes are:

- domestic stocks
- domestic ETF/ETN
- overseas stocks (info lookup only, backtests not yet wired)

Use `GET /api/kis/catalog` to inspect:

- what KIS itself supports
- what this project already supports for info lookup
- what this project already supports for backtests

## KIS ETF pipeline

This repo now has a minimal Korea Investment Open API bridge for ETF workflows:

- `GET /api/kis/health` checks whether KIS auth is configured and whether token issuance works
- `GET /api/etf/{symbol}/analysis` fetches live ETF quote + daily chart + support/resistance summary
- `POST /api/etf/recommendations/profile` ranks a user-provided ETF candidate list by risk profile
- `POST /api/admin/kis/order-preview` checks orderable cash/qty against the configured KIS account
- `POST /api/admin/kis/order-cash` submits a cash order when `SEPA_KIS_ORDER_ENABLED=1`
- `POST /api/admin/kis/etf-history/backfill` fetches ETF daily history from KIS and stores it into `ohlcv.db`
- `POST /api/admin/backtest/etf/run` runs the existing backtest engine against an ETF symbol whitelist

ETF backtest flow:

1. Edit `config/krx_etf_universe.csv` to match your ETF candidate pool
2. Call `POST /api/admin/kis/etf-history/backfill` for the ETFs you want to test
3. Call `POST /api/admin/backtest/etf/run` with those symbols and a date range
4. Use `GET /api/etf/{symbol}/analysis` and `POST /api/etf/recommendations/profile` for review/exploration

Required env vars:

- `KIS_APP_KEY`
- `KIS_APP_SECRET`
- `KIS_ACCOUNT_NO`
- `KIS_ACCOUNT_PRODUCT_CODE`
- `KIS_ENV=prod|demo`
- `SEPA_ADMIN_TOKEN`

Optional hardening env vars:

- `SEPA_ADMIN_PREVIOUS_TOKENS` and `SEPA_ADMIN_TOKENS` for short-lived rotation windows
- `SEPA_ADMIN_ALLOW_LEGACY_HEADER=0` to disable the temporary `X-SEPA-Admin-Token` fallback
- `SEPA_RATE_LIMIT_API_RPM`, `SEPA_RATE_LIMIT_STATIC_RPM`, `SEPA_RATE_LIMIT_WINDOW_SECONDS`
- `SEPA_RATE_LIMIT_TRUST_PROXY_HEADERS=1` plus `SEPA_RATE_LIMIT_TRUSTED_PROXY_IPS=...` when the app sits behind a trusted reverse proxy

Safety note:

- live order submission stays off until `SEPA_KIS_ORDER_ENABLED=1`
- preview and analysis routes are safe read-only checks

## Security defaults

These are the current defaults, not a claim that every deployment is production-hardened:

- Public endpoints stay read-only; mutating or generative backtest execution is admin-only.
- `POST /api/admin/backtest/run` and other admin routes require `Authorization: Bearer <SEPA_ADMIN_TOKEN>`.
- Token rotation can use `SEPA_ADMIN_PREVIOUS_TOKENS`, and parallel admin clients can use `SEPA_ADMIN_TOKENS`.
- The legacy `X-SEPA-Admin-Token` header is only a migration fallback and can be disabled with `SEPA_ADMIN_ALLOW_LEGACY_HEADER=0`.
- API docs are **off by default**; enable them explicitly with `SEPA_ENABLE_DOCS=1` for local/dev use.
- Rate limiting is proxy-aware when configured with `SEPA_RATE_LIMIT_TRUST_PROXY_HEADERS=1` and `SEPA_RATE_LIMIT_TRUSTED_PROXY_IPS=...`.
- CSP no longer relies on inline scripts; `script-src` stays on `'self'`, while `style-src` still allows `'unsafe-inline'` until the remaining inline styles are moved into CSS.
- Live KIS order submission stays off unless `SEPA_KIS_ORDER_ENABLED=1`.
- Browser automation tooling (`puppeteer`) is tracked as a dev dependency, and `npm audit` is currently clean.
- Full deployment checklist: `docs/40_operations/SECURITY_HARDENING.md`.

## Production readiness

This repo is useful for research, local development, and controlled internal runs. It is **not yet a fully hardened internet-facing deployment**.

Be especially careful with:

- in-memory rate limiting, which is now proxy-aware but still weak for multi-worker or public deployments without an edge/global limiter
- inline styles that still require `style-src 'unsafe-inline'`
- static bearer-token admin auth, which now supports rotation but is still simpler than fully managed identity
- any KIS live-order workflow, which should stay disabled unless you are deliberately testing with the right account and environment

If you are deploying beyond a local or private environment, review `docs/40_operations/SECURITY_HARDENING.md` and `docs/40_operations/FRONTEND_BACKEND_RUNBOOK_EN.md` before exposing the app.

## Key docs

Start here:

- `docs/00_overview/PROJECT_OBJECTIVE_EN.md`
- `docs/00_overview/SYSTEM_MAP.md`
- `docs/40_operations/FRONTEND_BACKEND_RUNBOOK_EN.md`
- `docs/40_operations/SECURITY_HARDENING.md`

Preset / wizard work:

- `docs/10_philosophy/TRADER_PRESET_AUDIT_20260415_KO.md`
- `docs/10_philosophy/trader_preset_mapping_20260415.csv`

## Current notes

- The repo currently tracks `main`.
- Market Wizards pages now expose preset runtime conditions directly from the preset API.
- API docs are disabled by default and must be explicitly enabled in dev/local configuration.
- Browser-driven backtest generation now requires an admin token and the admin API; public endpoints stay read-only.
- Reverse-proxy deployments should explicitly set the `SEPA_RATE_LIMIT_TRUST_PROXY_*` envs instead of assuming raw client IPs are trustworthy.
- Root-level `note.md` is used as a running session handoff note because long chat sessions can get flaky.

## License

No license has been added yet.
