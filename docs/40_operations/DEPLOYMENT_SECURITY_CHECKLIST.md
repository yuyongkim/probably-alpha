# Deployment Security Checklist

Use this checklist before exposing the app beyond localhost or a private VPN.

## Minimum environment gates

- Keep `SEPA_ENABLE_DOCS=0` in every non-dev environment.
- Set `SEPA_ADMIN_TOKEN` or `SEPA_ADMIN_TOKENS` with rotated secrets from your deploy platform secret store.
- Leave `SEPA_KIS_ORDER_ENABLED=0` unless you are deliberately testing live order submission.
- Configure `SEPA_RATE_LIMIT_TRUST_PROXY_HEADERS=1` only when you also set `SEPA_RATE_LIMIT_TRUSTED_PROXY_IPS`.

## Reverse proxy / edge checks

- Terminate HTTPS before traffic reaches the FastAPI app.
- Preserve and forward `X-Forwarded-For` / `X-Real-IP` only from trusted proxy hops.
- Do not let CDN or reverse proxy layers overwrite the app CSP with a weaker policy.
- Add edge-level request throttling; the built-in limiter is still process-local.

## Admin surface

- Expose `/api/admin/*` only to trusted operators or internal networks.
- Rotate admin bearer tokens when people or environments change.
- Review auth failure logs and alert on repeated 401 / 429 bursts.

## Data + KIS safety

- Keep KIS credentials in the deploy secret store, never in tracked files.
- Validate KIS demo/prod routing before enabling any cash order path.
- Restrict outbound network access if your deploy platform supports egress controls.

## Verification before go-live

- Run `python -m pytest -q`.
- Run `npm audit --json`.
- Hit `/api/health` and confirm CSP, HSTS, and rate-limit headers are present.
- Manually verify key pages (`/`, `/backtest.html`, `/market-wizards-korea.html`, `/trader-debate.html`) load without CSP console errors.
