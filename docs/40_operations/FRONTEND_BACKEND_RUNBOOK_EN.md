# Frontend/Backend Runbook (EN)

## 0) One-shot local bootstrap
```powershell
scripts\start_local.bat
scripts\start_local.bat -InstallDeps
```

`start_local` reads `.env` values, falls back to `.env.example`, and uses `requirements.txt` when dependency installation is needed.

Read APIs stay read-only now. If a date bundle is missing, generate it explicitly with `POST /api/admin/daily-signals` or run `python -m sepa.pipeline.run_after_close`. If persistence history must be backfilled, use `POST /api/admin/history/backfill`.

## 1) Generate pipeline artifacts
```bash
python3 -m sepa.pipeline.run_live_cycle
```

## 2) Run backend API
```bash
uvicorn sepa.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Production-facing defaults to keep in mind:

- keep `SEPA_ENABLE_DOCS=0` unless docs are deliberately exposed
- set `SEPA_ADMIN_TOKEN` before using any `/api/admin/*` route
- if you sit behind nginx/Caddy/Cloudflare, only enable `SEPA_RATE_LIMIT_TRUST_PROXY_HEADERS=1` after setting `SEPA_RATE_LIMIT_TRUSTED_PROXY_IPS`
- public routes are read-only; expensive or file-writing jobs stay behind admin auth

Key endpoints:
- `/api/summary`
- `/api/alpha`
- `/api/beta`
- `/api/gamma`
- `/api/delta`
- `/api/omega`

## 3) Run frontend
Serve static files:
```bash
python3 -m http.server 8080 --directory sepa/frontend
```
Open: `http://127.0.0.1:8080`

API Base value: `http://127.0.0.1:8000`

## 4) Security hardening references

- deployment checklist: `docs/40_operations/SECURITY_HARDENING.md`
- runtime defaults: `.env.example`
- admin requests should prefer `Authorization: Bearer <token>`; the `X-SEPA-Admin-Token` header is a temporary migration fallback
