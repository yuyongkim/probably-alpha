

## MANUAL
Company_Credit should load shared environment variables from Desktop\QuantDB\.env before checking a repo-local .env. Use this as the primary source for API keys unless SEPA_ENV_FILE explicitly overrides it.


## WORKING MEMORY
[2026-03-11T11:58:44.049Z] 2026-03-11: verified env source at Desktop/QuantDB/mvp_platform/.env, patched config/env_loader.py to search nested QuantDB env, ran py -m sepa.pipeline.run_after_close successfully. Kiwoom keys loaded but token/ohlcv endpoint vars missing, so refresh used yfinance rows for all 28 symbols. Outputs remained alpha=6 beta=0 gamma=0 recommendations=2; beta gate is current bottleneck.

[2026-03-11T12:10:29.545Z] Frontend recommendations table now exposes Omega execution plan as a dedicated `Omega Plan` column instead of burying E/S/T/Qty under the R/R cell. Files: sepa/frontend/index.html, sepa/frontend/js/renderers/recommendations.js, sepa/frontend/js/renderers/shared.js, sepa/frontend/js/i18n.js, sepa/frontend/styles.css.
[2026-03-11T12:15:27.471Z] Kiwoom live price collection now works with shared QuantDB `.env` app/secret only. `sepa/data/kiwoom.py` was rewritten to use default Kiwoom base URL (`https://api.kiwoom.com`), built-in token/OHLCV endpoints, `ka10086` daily price API, suffix-based market code mapping (`.KS`->0, `.KQ`->10), and stale-cache refresh. Verified 2026-03-11 refresh pulled live Kiwoom rows for all 28 universe symbols with sample=0.
[2026-03-11T13:00:34.564Z] QuantDB integration upgraded to use split DB layout from Desktop/QuantDB/mvp_platform (`quant_platform.db`, `_snapshot`, `_history`) instead of preferring the 3.248GB backup. Universe now defaults to QuantDB top 80 names (`SEPA_UNIVERSE_SOURCE=auto`, `SEPA_QUANTDB_UNIVERSE_LIMIT=80`) with CSV fallback. EPS now merges QuantDB long history (older quarters) with local EPS CSV (newer quarters). Company facts prefer QuantDB quantking_snapshot. Dashboard UI got a control-band shell, denser KPI strip, actual board-grid/hero-grid CSS, and stronger analysis panel emphasis.