"""KIS 국내주식 재무 API skeleton.

Mirrors ``_tmp_kis_repo/examples_llm/domestic_stock/finance_*/`` — eight
endpoints that together cover balance sheet, income statement, and six ratio
families (growth / profit / stability / financial / other-major / ratio
leaderboard).  We define the URL, TR ID, parameter shape, and output schema
here so downstream code (``value.fnguide.crosscheck``, ``apps/api`` value
endpoints, …) can call these as soon as KIS credentials are provisioned.

Until ``KIS_APP_KEY`` / ``KIS_APP_SECRET`` are set, every call raises
``NotImplementedError`` with a clear pointer to ``docs/30_data_contracts``.
The shape is deliberately compatible with ``FnguideSnapshot`` so the output
can be merged 1:1 with FnGuide rows (``revenue`` / ``operating_income`` /
``net_income`` / ``eps`` / ``roe`` / ``debt_ratio`` …).

KIS finance endpoint table (domestic stock, v1):

  ========================================  ========  ==========================================
  endpoint                                  tr_id     path
  ========================================  ========  ==========================================
  balance-sheet (재무상태표)                 FHKST66430100  /uapi/domestic-stock/v1/finance/balance-sheet
  income-statement (손익계산서)              FHKST66430200  /uapi/domestic-stock/v1/finance/income-statement
  financial-ratio (재무비율)                 FHKST66430300  /uapi/domestic-stock/v1/finance/financial-ratio
  profit-ratio (수익성비율)                  FHKST66430400  /uapi/domestic-stock/v1/finance/profit-ratio
  other-major-ratios (기타주요비율)          FHKST66430500  /uapi/domestic-stock/v1/finance/other-major-ratios
  stability-ratio (안정성비율)               FHKST66430600  /uapi/domestic-stock/v1/finance/stability-ratio
  growth-ratio (성장성비율)                  FHKST66430800  /uapi/domestic-stock/v1/finance/growth-ratio
  ranking/finance-ratio (재무비율 순위)      FHPST01750000  /uapi/domestic-stock/v1/ranking/finance-ratio
  ========================================  ========  ==========================================

Common parameters for all ``/finance/*`` endpoints:

  FID_DIV_CLS_CODE           "0" = 연간, "1" = 분기
  fid_cond_mrkt_div_code     "J" (주식)
  fid_input_iscd             6-digit ticker (e.g. "005930")

Output normalisation maps KIS field names to the same snake_case keys
FnGuide uses.  See :data:`KIS_OUTPUT_MAP` — callers should use the normalised
keys rather than the raw KIS fields so the UI does not need a second code
path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from ky_adapters.base import AdapterError, BaseAdapter, HealthStatus


# --------------------------------------------------------------------------- #
# Endpoint catalogue                                                          #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class KISFinanceEndpoint:
    """Shape of a single KIS finance endpoint."""

    name: str
    url: str
    tr_id: str
    description: str
    supports_period: bool = True  # all finance/* endpoints take FID_DIV_CLS_CODE


KIS_ENDPOINTS: dict[str, KISFinanceEndpoint] = {
    "balance_sheet": KISFinanceEndpoint(
        name="balance_sheet",
        url="/uapi/domestic-stock/v1/finance/balance-sheet",
        tr_id="FHKST66430100",
        description="국내주식 대차대조표 (v1_국내주식-078)",
    ),
    "income_statement": KISFinanceEndpoint(
        name="income_statement",
        url="/uapi/domestic-stock/v1/finance/income-statement",
        tr_id="FHKST66430200",
        description="국내주식 손익계산서 (v1_국내주식-079)",
    ),
    "financial_ratio": KISFinanceEndpoint(
        name="financial_ratio",
        url="/uapi/domestic-stock/v1/finance/financial-ratio",
        tr_id="FHKST66430300",
        description="국내주식 재무비율 (v1_국내주식-080)",
    ),
    "profit_ratio": KISFinanceEndpoint(
        name="profit_ratio",
        url="/uapi/domestic-stock/v1/finance/profit-ratio",
        tr_id="FHKST66430400",
        description="국내주식 수익성비율 (v1_국내주식-081)",
    ),
    "other_major_ratios": KISFinanceEndpoint(
        name="other_major_ratios",
        url="/uapi/domestic-stock/v1/finance/other-major-ratios",
        tr_id="FHKST66430500",
        description="국내주식 기타주요비율 (v1_국내주식-082)",
    ),
    "stability_ratio": KISFinanceEndpoint(
        name="stability_ratio",
        url="/uapi/domestic-stock/v1/finance/stability-ratio",
        tr_id="FHKST66430600",
        description="국내주식 안정성비율 (v1_국내주식-083)",
    ),
    "growth_ratio": KISFinanceEndpoint(
        name="growth_ratio",
        url="/uapi/domestic-stock/v1/finance/growth-ratio",
        tr_id="FHKST66430800",
        description="국내주식 성장성비율 (v1_국내주식-084)",
    ),
    "ranking_finance_ratio": KISFinanceEndpoint(
        name="ranking_finance_ratio",
        url="/uapi/domestic-stock/v1/ranking/finance-ratio",
        tr_id="FHPST01750000",
        description="국내주식 재무비율 순위",
        supports_period=False,
    ),
}


PeriodLiteral = Literal["annual", "quarterly"]


def _period_code(period: PeriodLiteral) -> str:
    if period == "annual":
        return "0"
    if period == "quarterly":
        return "1"
    raise ValueError(f"period must be 'annual' or 'quarterly', got {period!r}")


# --------------------------------------------------------------------------- #
# Output schema mapping                                                       #
# --------------------------------------------------------------------------- #
# KIS returns raw Korean field codes (e.g. ``sale_account``, ``bsop_prti``)
# while FnGuide uses snake_case English.  We normalise to the FnGuide flavour
# so consumer code (FundamentalsPane / value/trend) needs one vocabulary.

KIS_OUTPUT_MAP: dict[str, dict[str, str]] = {
    "income_statement": {
        "stac_yymm": "period",            # "202412"
        "sale_account": "revenue",
        "sale_cost": "cost_of_sales",
        "sale_totl_prfi": "gross_profit",
        "bsop_prti": "operating_income",
        "bsop_non_ernn": "non_op_income",
        "bsop_non_expn": "non_op_expense",
        "thtr_ntin": "net_income",
    },
    "balance_sheet": {
        "stac_yymm": "period",
        "cras": "current_assets",
        "fxas": "non_current_assets",
        "total_aset": "total_assets",
        "flow_lblt": "current_liabilities",
        "fix_lblt": "non_current_liabilities",
        "total_lblt": "total_liabilities",
        "cpfn": "capital",
        "cfp_surp": "capital_surplus",
        "prfi_surp": "retained_earnings",
        "total_cptl": "total_equity",
    },
    "financial_ratio": {
        "stac_yymm": "period",
        "grs": "sales_growth",
        "bsop_prfi_inrt": "op_income_growth",
        "ntin_inrt": "net_income_growth",
        "roe_val": "roe",
        "eps": "eps",
        "sps": "sps",
        "bps": "bps",
        "rsrv_rate": "retention_ratio",
        "lblt_rate": "debt_ratio",
    },
    "profit_ratio": {
        "stac_yymm": "period",
        "cptl_ntin_rate": "roa",
        "self_cptl_ntin_inrt": "roe",
        "sale_ntin_rate": "net_margin",
        "sale_totl_rate": "gross_margin",
    },
    "stability_ratio": {
        "stac_yymm": "period",
        "lblt_rate": "debt_ratio",
        "bram_depn": "borrowings_ratio",
        "crnt_rate": "current_ratio",
        "quck_rate": "quick_ratio",
    },
    "growth_ratio": {
        "stac_yymm": "period",
        "grs": "sales_growth",
        "bsop_prfi_inrt": "op_income_growth",
        "equt_inrt": "equity_growth",
        "ntin_inrt": "net_income_growth",
    },
    "other_major_ratios": {
        "stac_yymm": "period",
        "payout_rate": "payout_ratio",
        "eva": "eva",
        "ebitda": "ebitda",
        "ev_ebitda": "ev_ebitda",
    },
}


def _normalise_output(endpoint: str, raw: dict[str, Any]) -> dict[str, Any]:
    mapping = KIS_OUTPUT_MAP.get(endpoint, {})
    if not mapping:
        return dict(raw)
    out: dict[str, Any] = {}
    for kis_field, value in raw.items():
        out[mapping.get(kis_field, kis_field)] = value
    return out


# --------------------------------------------------------------------------- #
# Adapter                                                                     #
# --------------------------------------------------------------------------- #


class KISFinanceAdapter(BaseAdapter):
    """Stub-only adapter — all finance calls raise until KIS creds land.

    The base :class:`ky_adapters.kis.KISAdapter` focuses on quotes/universe
    and will eventually do token management.  We deliberately keep finance
    here so (a) ``ky_adapters.kis.client`` stays small and (b) when KIS is
    enabled we can wire the token plumbing in one place.
    """

    source_id = "kis_finance"
    priority = 2  # FnGuide is P1 for fundamentals; KIS is cross-check.

    def __init__(
        self,
        *,
        app_key: str | None = None,
        app_secret: str | None = None,
        base_url: str | None = None,
        env: str | None = None,
    ) -> None:
        super().__init__()
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url or "https://openapi.koreainvestment.com:9443"
        self.env = env or "prod"

    @classmethod
    def from_settings(cls) -> "KISFinanceAdapter":
        return cls(
            app_key=cls._env("KIS_APP_KEY"),
            app_secret=cls._env("KIS_APP_SECRET"),
            base_url=cls._env("KIS_BASE_URL"),
            env=cls._env("KIS_ENV"),
        )

    # --------- Contract ---------

    def healthcheck(self) -> dict[str, Any]:
        if not self.app_key or not self.app_secret:
            return HealthStatus(
                ok=False,
                source_id=self.source_id,
                last_error="KIS_APP_KEY/KIS_APP_SECRET not configured",
                extra={
                    "message": (
                        "KIS finance skeleton — configure KIS credentials in "
                        ".env to enable real calls. See "
                        "docs/30_data_contracts/KIWOOM_ENDPOINT_SPEC.md for "
                        "the endpoint catalogue."
                    ),
                    "endpoints": list(KIS_ENDPOINTS.keys()),
                },
            ).to_dict()
        return HealthStatus(
            ok=False,
            source_id=self.source_id,
            last_error="skeleton — real calls disabled",
            extra={
                "message": (
                    "KISFinanceAdapter is currently a no-op scaffold. The "
                    "URL / TR_ID / parameter table is defined; network plumbing "
                    "(_issue_token / _signed_request) is pending."
                ),
                "endpoints": list(KIS_ENDPOINTS.keys()),
            },
        ).to_dict()

    # --------- Request helpers (unimplemented) ---------

    def _ensure_credentials(self) -> None:
        if not self.app_key or not self.app_secret:
            raise NotImplementedError(
                "KIS finance endpoints require KIS_APP_KEY / KIS_APP_SECRET — "
                "configure KIS credentials to enable. "
                "See _tmp_kis_repo/examples_llm/domestic_stock/finance_* for "
                "the upstream reference implementation."
            )

    def _call_endpoint(
        self,
        endpoint: str,
        symbol: str,
        *,
        period: PeriodLiteral = "annual",
        market: str = "J",
    ) -> list[dict[str, Any]]:
        """Shared plumbing — builds the request but stops at network boundary.

        When KIS creds are wired this becomes the single place where we
        ``_signed_request`` + paginate via the ``tr_cont`` header.  For now
        we raise early so callers see a clear error.
        """
        self._ensure_credentials()
        ep = KIS_ENDPOINTS.get(endpoint)
        if ep is None:
            raise AdapterError(f"unknown KIS finance endpoint: {endpoint!r}")

        params: dict[str, Any] = {
            "fid_cond_mrkt_div_code": market,
            "fid_input_iscd": str(symbol).zfill(6),
        }
        if ep.supports_period:
            params["FID_DIV_CLS_CODE"] = _period_code(period)

        raise NotImplementedError(
            f"KIS endpoint {endpoint!r} (tr_id={ep.tr_id}, url={ep.url}) is a "
            f"skeleton — network plumbing not implemented yet. params={params}"
        )

    # --------- Public API surface ---------

    def get_balance_sheet(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("balance_sheet", symbol, period=period)
        return [_normalise_output("balance_sheet", r) for r in rows]

    def get_income_statement(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("income_statement", symbol, period=period)
        return [_normalise_output("income_statement", r) for r in rows]

    def get_financial_ratio(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("financial_ratio", symbol, period=period)
        return [_normalise_output("financial_ratio", r) for r in rows]

    def get_profit_ratio(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("profit_ratio", symbol, period=period)
        return [_normalise_output("profit_ratio", r) for r in rows]

    def get_stability_ratio(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("stability_ratio", symbol, period=period)
        return [_normalise_output("stability_ratio", r) for r in rows]

    def get_growth_ratio(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("growth_ratio", symbol, period=period)
        return [_normalise_output("growth_ratio", r) for r in rows]

    def get_other_major_ratios(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> list[dict[str, Any]]:
        rows = self._call_endpoint("other_major_ratios", symbol, period=period)
        return [_normalise_output("other_major_ratios", r) for r in rows]

    def get_ranking_finance_ratio(self) -> list[dict[str, Any]]:
        rows = self._call_endpoint("ranking_finance_ratio", "", period="annual")
        return rows  # ranking rows have different shape — no normalisation yet

    # --------- Cross-check helper ---------

    def crosscheck_fnguide(
        self, symbol: str, *, period: PeriodLiteral = "annual"
    ) -> dict[str, Any]:
        """Return a dict compatible with the FnGuide fields.

        Intended to let callers do ``{**fnguide_row, **kis_row}`` for a
        belt-and-suspenders sanity check.  Raises the same
        ``NotImplementedError`` until KIS is live.
        """
        rows_is = self.get_income_statement(symbol, period=period)
        rows_bs = self.get_balance_sheet(symbol, period=period)
        rows_fr = self.get_financial_ratio(symbol, period=period)
        merged: dict[str, Any] = {}
        for bucket in (rows_is, rows_bs, rows_fr):
            if bucket:
                merged.update(bucket[0])
        return merged


__all__ = [
    "KISFinanceAdapter",
    "KISFinanceEndpoint",
    "KIS_ENDPOINTS",
    "KIS_OUTPUT_MAP",
]
