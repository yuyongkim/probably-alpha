"""KOSIS (Statistics Korea) adapter.

This file ports the hardened JSONP parser + metadata-aware fetch flow from
``Finance_analysis/kosis_api_system/kosis_api.py`` (the "Finance_analysis"
project in a sibling checkout). Key port decisions:

1. Parser accepts **both** JSONP-wrapped forms KOSIS returns in practice —
   callback-style ``callback({...});`` *and* parenthesised literal ``({...})``
   — plus a graceful fallback to ``json5`` when the response uses JS-lossy
   values (single-quoted strings, trailing commas). We only depend on
   ``json5`` when the stdlib ``json`` module fails — it stays optional.
2. Typed error class ``KosisAPIError`` wraps all parse/transport failures so
   downstream callers can distinguish KOSIS-upstream problems from local
   bugs. It still inherits from ``AdapterError`` so the collector's blanket
   handling keeps working.
3. Date formatting for the three cycles (Y/Q/M) is centralised in
   ``format_kosis_date`` so operators never pass the wrong period slug.
4. Metadata resolution (``fetch_metadata`` + ``resolve_required_params``) is
   exposed as adapter methods so callers can discover a table's required
   ``itmId`` / ``objL1`` without hardcoding them in presets.

The two flavours of the base call remain:

- ``get_data`` — the original thin wrapper matching the scripts/collect.py
  contract (what the preset runner calls).
- ``get_statistical_data`` — the metadata-aware convenience path ported from
  Finance_analysis. Useful for ad-hoc data exploration / notebooks.

KOSIS exposes two main endpoint families:

- ``/openapi/Param/statisticsParameterData.do`` — query by (orgId, tblId)
- ``/openapi/statisticsData.do``                — preformatted datasets

We always request the ``format=json`` variant.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Optional

from ky_adapters.base import AdapterError, AuthError, BaseAdapter

logger = logging.getLogger(__name__)

KOSIS_BASE = "https://kosis.kr/openapi"


# --------------------------------------------------------------------------- #
# Typed error                                                                 #
# --------------------------------------------------------------------------- #


class KosisAPIError(AdapterError):
    """Any KOSIS-upstream problem: network, HTTP error, parse error, or
    the error envelope KOSIS returns inside a 200 OK response
    (``{"err":"30","errMsg":"..."}``).

    Subclasses AdapterError so the ``collect.py`` blanket handler still
    treats it as a soft-fail instead of crashing the bulk run.
    """


# --------------------------------------------------------------------------- #
# Date formatting (ported verbatim from Finance_analysis)                     #
# --------------------------------------------------------------------------- #


def format_kosis_date(date_str: str, prd_se: str) -> str:
    """Normalise a caller-supplied date/period string into the cycle-specific
    format KOSIS expects.

    Accepted inputs:

    - ``YYYY``              (any cycle)
    - ``YYYYMM``            (Y/Q/M)
    - ``YYYYMMDD``          (D — passed through)
    - ``YYYY-MM-DD`` etc.   (dashes stripped first)

    Returns:

    - ``Y`` -> ``YYYY``
    - ``Q`` -> ``YYYYQn`` (n computed from month when present, else ``Q1``)
    - ``M`` -> ``YYYYMM``
    - ``D`` -> ``YYYYMMDD``
    - anything else -> passed through untouched
    """
    try:
        raw = (date_str or "").strip().replace("-", "")
        if not raw:
            return ""
        if prd_se == "Y":
            return raw[:4]
        if prd_se == "Q":
            year = raw[:4]
            if len(raw) >= 6:
                month = int(raw[4:6])
                quarter = (month - 1) // 3 + 1
            else:
                quarter = 1
            return f"{year}Q{quarter}"
        if prd_se == "M":
            # Finance_analysis took raw[:6]; we guard the YYYY-only edge case.
            return raw[:6] if len(raw) >= 6 else raw + "01"
        if prd_se == "D":
            return raw[:8] if len(raw) >= 8 else raw
        return raw
    except Exception as exc:  # noqa: BLE001
        logger.warning("format_kosis_date failed for %r/%r: %s", date_str, prd_se, exc)
        return date_str


# --------------------------------------------------------------------------- #
# JSON / JSONP parsing                                                        #
# --------------------------------------------------------------------------- #

_JSONP_CALLBACK_RE = re.compile(r"^[\w\$]+\((?P<body>.+)\);?\s*$", re.DOTALL)


def parse_kosis_response(raw: str) -> Any:
    """Robust KOSIS response parser.

    Handles three observed forms:

    1. Plain JSON ``[...]`` or ``{...}`` (normal REST reply).
    2. Callback-style JSONP ``callback({...});`` (some meta endpoints).
    3. Parenthesised literal ``({...})`` (what the Finance_analysis author
       kept hitting — ``statisticsParameter.do``).

    Falls back to ``json5`` for responses with JS-lossy syntax when the
    stdlib ``json`` module raises. ``json5`` is declared optional here so
    repos can run the adapter without the extra dep when all their upstream
    payloads are strict JSON.
    """
    text = (raw or "").strip()
    if not text:
        return []

    # Form 2: callback({...});
    m = _JSONP_CALLBACK_RE.match(text)
    if m:
        text = m.group("body")

    # Form 3: raw parenthesised literal
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1]

    # First try stdlib json (fast path — the 99% case).
    try:
        return json.loads(text)
    except json.JSONDecodeError as stdlib_exc:
        # Fall back to json5 if available — some upstream replies use single
        # quotes or trailing commas.
        try:
            import json5  # type: ignore[import-not-found]
        except ImportError:
            raise KosisAPIError(
                f"KOSIS: cannot decode JSON/JSONP (json5 not installed): {stdlib_exc}"
            ) from stdlib_exc
        try:
            return json5.loads(text)
        except Exception as exc:  # noqa: BLE001
            raise KosisAPIError(f"KOSIS: cannot decode JSON/JSONP: {exc}") from exc


def _normalise_data_payload(data: Any) -> list[dict[str, Any]]:
    """Turn a parsed KOSIS body into a flat ``list[dict]`` of rows.

    KOSIS envelopes observed:

    - ``[{...}, {...}]``                     - the common form
    - ``{"DT": [...]}``                      - metadata-bearing wrapper
    - ``{"list": [...]}``                    - alternative wrapper
    - ``{"err": "30", "errMsg": "..."}``     - error envelope

    Anything else is treated as a single-row payload so callers never get
    an empty list when the upstream actually returned data.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "err" in data:
            raise KosisAPIError(
                f"KOSIS err={data.get('err')}: {data.get('errMsg', '(no message)')}"
            )
        for key in ("DT", "list", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []


# --------------------------------------------------------------------------- #
# Adapter                                                                     #
# --------------------------------------------------------------------------- #


class KOSISAdapter(BaseAdapter):
    source_id = "kosis"
    priority = 2

    def __init__(self, api_key: Optional[str] = None, base_url: str = KOSIS_BASE) -> None:
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_settings(cls) -> "KOSISAdapter":
        return cls(api_key=cls._env("KOSIS_API_KEY"))

    # --------- Contract ---------

    def healthcheck(self) -> dict[str, Any]:
        if not self.api_key:
            return self._timed_fail(self.source_id, "KOSIS_API_KEY not configured")
        t0 = time.perf_counter()
        try:
            # ping a well-known meta-list endpoint (orgId=101 is 통계청).
            resp = self._request(
                "GET",
                f"{self.base_url}/statisticsList.do",
                params={
                    "method": "getList",
                    "apiKey": self.api_key,
                    "vwCd": "MT_ZTITLE",
                    "parentListId": "A",
                    "format": "json",
                    "jsonVD": "Y",
                },
            )
            resp.raise_for_status()
            body = parse_kosis_response(resp.text)
            _normalise_data_payload(body)
            ok = True
        except KosisAPIError as exc:
            return self._timed_fail(self.source_id, str(exc))
        except Exception as exc:  # noqa: BLE001
            return self._timed_fail(self.source_id, str(exc))
        latency_ms = (time.perf_counter() - t0) * 1000
        return self._timed_ok(latency_ms, self.source_id, {"api_ok": ok})

    # --------- Metadata (ported from Finance_analysis) ---------

    def fetch_metadata(self, org_id: str, tbl_id: str) -> dict[str, Any]:
        """Fetch the parameter metadata for a KOSIS table.

        Returned dict matches the upstream shape — keys like ``objL1``,
        ``itmId``, ``prdSe`` each map to a list of ``{code, name}`` dicts.
        """
        if not self.api_key:
            raise AuthError("KOSIS_API_KEY not configured")
        resp = self._request(
            "GET",
            f"{self.base_url}/Param/statisticsParameter.do",
            params={
                "method": "getList",
                "apiKey": self.api_key,
                "orgId": org_id,
                "tblId": tbl_id,
                "format": "json",
            },
        )
        if resp.status_code != 200:
            raise KosisAPIError(f"KOSIS meta → HTTP {resp.status_code}: {resp.text[:200]}")
        data = parse_kosis_response(resp.text)
        if isinstance(data, dict) and "err" in data:
            raise KosisAPIError(
                f"KOSIS meta err={data.get('err')}: {data.get('errMsg')}"
            )
        # Meta responses are sometimes a flat list of {"LIST_NM": ...}
        # items; Finance_analysis returned them verbatim so downstream code
        # can inspect. We do the same.
        return data if isinstance(data, dict) else {"raw": data}

    @staticmethod
    def resolve_required_params(metadata: dict[str, Any]) -> dict[str, str]:
        """Heuristic defaults for ``itmId`` / ``objL1`` picked from metadata.

        Matches Finance_analysis preference order:

        - objL1: prefer "전국" / "전체" / "총계" / "지수" / code ``00`` / ``01``
        - itmId: prefer "전체" / "총계" / "지수" / well-known codes
        - Falls back to the first entry when no preferred token matches.
        """
        out: dict[str, str] = {}

        def _pick(key_list: str, key_code: str, key_name: str, prefs: list[str]) -> str | None:
            items = metadata.get(key_list)
            if not isinstance(items, list) or not items:
                return None
            for item in items:
                name = str(item.get(key_name, "")).lower()
                code = str(item.get(key_code, ""))
                if any(p in name or p == code for p in prefs):
                    return code
            first = items[0]
            return str(first.get(key_code, "")) or None

        obj = _pick(
            "objL1",
            "objL1",
            "objL1_NM",
            ["전국", "전체", "총계", "지수", "00", "01"],
        )
        if obj:
            out["objL1"] = obj
        itm = _pick(
            "itmId",
            "itmId",
            "itmId_NM",
            ["전체", "총계", "지수", "t10101", "t10102"],
        )
        if itm:
            out["itmId"] = itm
        return out

    # --------- API surface ---------

    def get_data(
        self,
        org_id: str,
        tbl_id: str,
        item_code: str | None = None,
        obj_l1: str | None = None,
        prd_se: str = "M",
        start_prd: str | None = None,
        end_prd: str | None = None,
        last_n_periods: int | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch a time-series slice from the parameterised KOSIS endpoint.

        Parameters
        ----------
        org_id, tbl_id
            Required table identifiers from the KOSIS portal.
        item_code
            ``itmId``. KOSIS tables almost always require it; we route it
            through even when the caller omits ``obj_l1`` so operators get a
            useful error from the upstream (``err=20 missing param``) rather
            than a silent empty list.
        obj_l1
            Classification dimension. Most macro tables accept the wildcard
            ``'ALL'`` which returns every objL1 bucket — callers can then
            filter downstream. For multi-dimension tables (sectoral/regional)
            pass the specific code.
        prd_se
            Period code: ``D`` / ``M`` / ``Q`` / ``A``. Defaults to monthly.
        start_prd, end_prd
            Inclusive period bounds in the endpoint-specific format. Anything
            the caller passes is run through :func:`format_kosis_date` so a
            raw ``YYYY-MM-DD`` / ``YYYYMMDD`` / ``YYYYMM`` all end up correct.
        last_n_periods
            Alternative to explicit bounds — returns the most recent N
            periods. KOSIS honours at most one of the two (bounds take
            priority when both are set).

        Returns
        -------
        list[dict]
            Raw KOSIS row dicts. Keys preserved verbatim; storage normalises
            them into Observation rows in ``scripts/collect.py``.
        """
        if not self.api_key:
            raise AuthError("KOSIS_API_KEY not configured")
        params: dict[str, Any] = {
            "method": "getList",
            "apiKey": self.api_key,
            "format": "json",
            "jsonVD": "Y",
            "orgId": org_id,
            "tblId": tbl_id,
            "prdSe": prd_se,
        }
        if item_code:
            params["itmId"] = item_code
        if obj_l1:
            params["objL1"] = obj_l1
        if start_prd:
            params["startPrdDe"] = format_kosis_date(start_prd, prd_se)
        if end_prd:
            params["endPrdDe"] = format_kosis_date(end_prd, prd_se)
        if last_n_periods and not (start_prd or end_prd):
            params["newEstPrdCnt"] = str(last_n_periods)

        resp = self._request(
            "GET",
            f"{self.base_url}/Param/statisticsParameterData.do",
            params=params,
        )
        if resp.status_code != 200:
            raise KosisAPIError(
                f"KOSIS → HTTP {resp.status_code}: {resp.text[:200]}"
            )
        data = parse_kosis_response(resp.text)
        return _normalise_data_payload(data)

    def get_statistical_data(
        self,
        tbl_id: str,
        itm_id: str | None = None,
        obj_l1: str | None = None,
        prd_se: str = "M",
        start: str | None = None,
        end: str | None = None,
        org_id: str = "101",
    ) -> list[dict[str, Any]]:
        """Metadata-aware convenience wrapper ported from Finance_analysis.

        If ``itm_id`` or ``obj_l1`` is omitted the adapter first calls the
        metadata endpoint, picks sensible defaults via
        :meth:`resolve_required_params`, then calls the data endpoint.

        This method exists for ad-hoc exploration; production collectors
        should curate tables in ``KOSIS_SERIES`` (storage/presets.py) and
        pass the codes explicitly to :meth:`get_data` so runs are
        reproducible.
        """
        if itm_id is None or obj_l1 is None:
            meta = self.fetch_metadata(org_id, tbl_id)
            resolved = self.resolve_required_params(meta)
            itm_id = itm_id or resolved.get("itmId")
            obj_l1 = obj_l1 or resolved.get("objL1")
            logger.info(
                "KOSIS %s/%s resolved itmId=%s objL1=%s from metadata",
                org_id, tbl_id, itm_id, obj_l1,
            )
        return self.get_data(
            org_id=org_id,
            tbl_id=tbl_id,
            item_code=itm_id,
            obj_l1=obj_l1,
            prd_se=prd_se,
            start_prd=start,
            end_prd=end,
        )


# --------------------------------------------------------------------------- #
# Back-compat re-exports                                                      #
# --------------------------------------------------------------------------- #

# The old private name was ``_parse_kosis_body``. Keep a module-level alias so
# any external call sites (there are none in-tree, but external consumers
# sometimes reach for it) don't break on upgrade.
def _parse_kosis_body(raw: str) -> list[dict[str, Any]]:
    data = parse_kosis_response(raw)
    return _normalise_data_payload(data)
