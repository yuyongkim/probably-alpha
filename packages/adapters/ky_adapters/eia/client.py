"""EIA adapter (oil, energy inventories, refinery utilisation).

API v2 endpoint: https://api.eia.gov/v2/seriesid/{SERIES}/data/?api_key=...
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

from ky_adapters.base import AdapterError, AuthError, BaseAdapter

EIA_BASE = "https://api.eia.gov/v2"


@dataclass
class EIAObservation:
    series_id: str
    date: str
    value: float | None
    unit: str | None = None

    def as_row(self, source_id: str = "eia") -> dict[str, Any]:
        return {
            "source_id": source_id,
            "series_id": self.series_id,
            "date": _normalise_date(self.date),
            "value": self.value,
            "unit": self.unit,
        }


class EIAAdapter(BaseAdapter):
    source_id = "eia"
    priority = 2

    def __init__(self, api_key: Optional[str] = None, base_url: str = EIA_BASE) -> None:
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_settings(cls) -> "EIAAdapter":
        return cls(api_key=cls._env("EIA_API_KEY"))

    # --------- Contract ---------

    def healthcheck(self) -> dict[str, Any]:
        if not self.api_key:
            return self._timed_fail(self.source_id, "EIA_API_KEY not configured")
        t0 = time.perf_counter()
        try:
            resp = self._request(
                "GET",
                f"{self.base_url}/",
                params={"api_key": self.api_key},
            )
            resp.raise_for_status()
            body = resp.json()
            ok = "response" in body or "data" in body
        except Exception as exc:  # noqa: BLE001
            return self._timed_fail(self.source_id, str(exc))
        latency_ms = (time.perf_counter() - t0) * 1000
        return self._timed_ok(latency_ms, self.source_id, {"api_ok": ok})

    # --------- API surface ---------

    def get_series(
        self,
        series_id: str,
        start: str | None = None,
        end: str | None = None,
        length: int = 5000,
    ) -> list[EIAObservation]:
        if not self.api_key:
            raise AuthError("EIA_API_KEY not configured")
        params: dict[str, Any] = {
            "api_key": self.api_key,
            "length": length,
        }
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        url = f"{self.base_url}/seriesid/{series_id}/data/"
        resp = self._request("GET", url, params=params)
        if resp.status_code != 200:
            raise AdapterError(f"EIA → HTTP {resp.status_code}: {resp.text[:200]}")
        payload = resp.json()
        resp_obj = payload.get("response") or {}
        rows = resp_obj.get("data") or []
        unit = None
        # v2 responses include unit inside response.data[i].unit or response.units
        if "units" in resp_obj and isinstance(resp_obj["units"], list) and resp_obj["units"]:
            unit = resp_obj["units"][0]
        out: list[EIAObservation] = []
        for row in rows:
            val_raw = row.get("value")
            try:
                val = float(val_raw) if val_raw not in (None, "") else None
            except (TypeError, ValueError):
                val = None
            date_raw = row.get("period") or row.get("date") or ""
            out.append(
                EIAObservation(
                    series_id=series_id,
                    date=date_raw,
                    value=val,
                    unit=row.get("unit") or unit,
                )
            )
        return out


def _normalise_date(raw: str) -> str:
    raw = (raw or "").strip()
    # EIA returns YYYY-MM-DD for weekly/daily, YYYY-MM for monthly.
    if len(raw) == 7 and raw[4] == "-":
        return f"{raw}-01"
    return raw
