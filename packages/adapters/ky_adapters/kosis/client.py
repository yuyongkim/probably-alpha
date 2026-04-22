"""KOSIS (Statistics Korea) adapter.

KOSIS exposes two main families of endpoints:

- ``/openapi/Param/statisticsParameterData.do`` — query by (orgId, tblId)
- ``/openapi/statisticsData.do``                — preformatted datasets

Responses are JSON (sometimes wrapped in ``.do``-style JSONP when the caller
asks for it). We always request the ``format=json`` variant.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

from ky_adapters.base import AdapterError, AuthError, BaseAdapter

KOSIS_BASE = "https://kosis.kr/openapi"


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
            # ping a well-known table metadata endpoint — orgId=101 (통계청)
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
            _parse_kosis_body(resp.text)
            ok = True
        except Exception as exc:  # noqa: BLE001
            return self._timed_fail(self.source_id, str(exc))
        latency_ms = (time.perf_counter() - t0) * 1000
        return self._timed_ok(latency_ms, self.source_id, {"api_ok": ok})

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
    ) -> list[dict[str, Any]]:
        """Fetch a time-series slice from the parameterised KOSIS endpoint.

        Returns a list of KOSIS row dicts (keys are preserved as-is), which the
        storage layer normalises into ``Observation`` rows later.
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
            params["startPrdDe"] = start_prd
        if end_prd:
            params["endPrdDe"] = end_prd

        resp = self._request(
            "GET",
            f"{self.base_url}/Param/statisticsParameterData.do",
            params=params,
        )
        if resp.status_code != 200:
            raise AdapterError(f"KOSIS → HTTP {resp.status_code}: {resp.text[:200]}")
        return _parse_kosis_body(resp.text)


# --------------------------------------------------------------------------- #
# JSON / JSONP parsing                                                        #
# --------------------------------------------------------------------------- #

_JSONP_RE = re.compile(r"^[\w\$]+\((?P<body>.+)\);?\s*$", re.DOTALL)


def _parse_kosis_body(raw: str) -> list[dict[str, Any]]:
    """Handle both JSON and JSONP-wrapped KOSIS responses."""
    text = (raw or "").strip()
    if not text:
        return []
    # JSONP form: callback({...});
    m = _JSONP_RE.match(text)
    if m:
        text = m.group("body")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AdapterError(f"KOSIS: cannot decode JSON/JSONP: {exc}") from exc
    if isinstance(data, dict):
        # error envelope example: {"err":"30","errMsg":"인증키가 유효하지 않습니다."}
        if "err" in data:
            raise AdapterError(f"KOSIS err={data.get('err')}: {data.get('errMsg')}")
        # some endpoints wrap the list: {"list": [...]} or {"items": [...]}
        for key in ("list", "items", "data"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    if isinstance(data, list):
        return data
    return []
