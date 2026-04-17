# Security

This repository is public. Please treat security issues, credential leaks, and operational misconfigurations carefully.

## Reporting a security issue

If you discover a vulnerability:

1. Prefer GitHub's private security advisory flow if it is enabled for this repository.
2. If that is not available, open a normal issue only if you can avoid exposing sensitive exploit details publicly.
3. Do not post secrets, live credentials, or exploit steps in a public discussion before the issue has been reviewed.

## Current security defaults

- Public API endpoints are intended to stay read-only.
- Administrative backtest execution requires `SEPA_ADMIN_TOKEN`.
- API docs are off by default and should only be enabled explicitly for local or controlled development use.
- Live KIS order submission stays disabled unless `SEPA_KIS_ORDER_ENABLED=1`.
- Browser automation tooling is treated as a dev dependency, not a production runtime dependency.

## Operational cautions

This project is not fully production-hardened. Before exposing it publicly or placing it behind real user traffic, review:

- rate limiting strategy
- CSP tightening and inline script cleanup
- admin authentication and token rotation
- KIS credential handling and environment separation
- dependency audit status after any lockfile or package update

## What to assume

Do not assume that:

- every endpoint is safe for internet exposure
- every feature is production ready
- every local default is suitable for deployment
- live trading or order submission is safe until the relevant flags and credentials are intentionally configured

