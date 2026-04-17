# Deployment & Security Hardening Checklist

Use this before deploying `probably-alpha` to a public environment.

## 1) Environment variables

- [ ] Set `SEPA_ADMIN_TOKEN` to a long random secret.
- [ ] Populate `SEPA_ADMIN_PREVIOUS_TOKENS` / `SEPA_ADMIN_TOKENS` during rotation windows instead of sharing one forever-token.
- [ ] Disable the legacy migration header once callers are updated: `SEPA_ADMIN_ALLOW_LEGACY_HEADER=0`.
- [ ] Set `SEPA_ENABLE_DOCS=0` in production.
- [ ] If the app is behind a proxy, set `SEPA_RATE_LIMIT_TRUSTED_PROXY_IPS` before enabling `SEPA_RATE_LIMIT_TRUST_PROXY_HEADERS=1`.
- [ ] Confirm any CORS/origin settings only include approved public hosts.
- [ ] Keep secrets out of git; use local `.env` only for development.

## 2) Public endpoint boundaries

- [ ] Keep public routes read-only unless the route is explicitly intended to write.
- [ ] Keep `/api/admin/backtest/run` admin-only.
- [ ] Do not expose any public endpoint that writes result files or launches expensive jobs without auth.
- [ ] Re-check `sepa/api/routes_public.py` and `sepa/api/routes_admin.py` on each release for boundary drift.

## 3) Admin token handling

- [ ] Require bearer auth for all admin routes.
- [ ] Use constant-time comparison for token checks.
- [ ] Rotate the token periodically and whenever access changes.
- [ ] Prefer a deployment secret store or vault over checked-in config.
- [ ] Log failed admin auth attempts and review for abuse.

## 4) Rate limiting

- [ ] Treat the current in-memory limiter as single-instance protection, not a complete abuse-prevention system.
- [ ] Prefer upstream rate limiting at the reverse proxy or WAF for public deployments.
- [ ] Only trust `X-Forwarded-For` / `X-Real-IP` from explicitly-listed proxy IPs.
- [ ] Apply tighter limits to compute-heavy, write-heavy, and report-generation endpoints.

## 5) CSP status

- [x] Inline scripts have been externalized so `script-src 'self'` can stay strict.
- [ ] Inline styles still exist across the frontend, so `style-src 'unsafe-inline'` remains for now.
- [ ] Re-test the main dashboard pages after any CSP change and confirm no blocked assets or console errors.

## 6) Release gate

- [ ] Run `python -m pytest -q`.
- [ ] Run `npm audit --json` if frontend dependencies changed.
- [ ] Check `/api/health`, public dashboard pages, and any admin endpoint used during deployment.
- [ ] Confirm docs remain disabled unless deliberately enabled.
- [ ] Confirm no public endpoint writes result files unless explicitly intended.

## Current status snapshot

- [x] Public backtest execution is admin-only.
- [x] API docs are disabled by default.
- [x] Admin token comparison uses constant-time logic with token rotation support.
- [x] Public preset routes avoid mutating shared preset state.
- [x] Inline scripts no longer require `unsafe-inline`.
- [ ] Rate limiting is still in-memory only (proxy-aware, but still single-instance).
- [ ] Admin auth is still a static shared-token model even with rotation support.
