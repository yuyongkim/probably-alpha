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
- `GET /api/dashboard`
- `GET /api/leaders/sectors`
- `GET /api/leaders/stocks`
- `GET /api/recommendations/latest`
- `GET /api/briefing/latest`
- `GET /api/trader-debate`
- `GET /api/backtest/presets`
- Public backtest result endpoints are read-only; mutating or generative backtest execution is admin-only.

## Key docs

Start here:

- `docs/00_overview/PROJECT_OBJECTIVE_EN.md`
- `docs/00_overview/SYSTEM_MAP.md`
- `docs/40_operations/FRONTEND_BACKEND_RUNBOOK_EN.md`

Preset / wizard work:

- `docs/10_philosophy/TRADER_PRESET_AUDIT_20260415_KO.md`
- `docs/10_philosophy/trader_preset_mapping_20260415.csv`

## Current notes

- The repo currently tracks `main`.
- Market Wizards pages now expose preset runtime conditions directly from the preset API.
- API docs are disabled by default and must be explicitly enabled in dev/local configuration.
- Root-level `note.md` is used as a running session handoff note because long chat sessions can get flaky.

## License

No license has been added yet.
