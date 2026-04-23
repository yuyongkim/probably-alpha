"""DART 사업부문별 매출 (segment revenue) extractor.

OpenDART exposes the full business report text via the ``document.xml``
endpoint — a ZIP archive containing the filing's XBRL + HTML. The segment
breakdown lives inside the HTML under section II (사업의 내용) → "사업부문별
매출" table. There is no structured JSON endpoint for this data, so we have to
scrape.

Parsing strategy (best-effort):

1. For a given ``corp_code``, fetch the latest annual 사업보고서 receipt via
   ``list.json`` (pblntf_detail_ty=A001).
2. ``GET /api/document.xml?rcept_no=...`` returns ``application/octet-stream``
   (a ZIP). Unzip in-memory.
3. Pick the first HTML-ish member whose Korean name contains "사업보고서".
4. Parse with BeautifulSoup; find tables whose preceding heading mentions
   "사업부문" + "매출" and whose header row contains "매출" / "비중".
5. Emit one row per segment:
   ``{symbol, period_end, segment_name, revenue, operating_income,
     revenue_share, source_id='dart'}``

Every step can fail; the caller should treat this as an ``Optional`` result
and fall back to the PBR proxy in :mod:`ky_core.value.segment`.
"""
from __future__ import annotations

import io
import logging
import re
import zipfile
from dataclasses import dataclass
from datetime import date
from typing import Any, Optional

from ky_adapters.base import AdapterError, AuthError, BaseAdapter
from ky_adapters.dart.client import DART_BASE, REPORT_CODES, _yyyymmdd

log = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Data model                                                                  #
# --------------------------------------------------------------------------- #


@dataclass
class Segment:
    symbol: str
    corp_code: str
    period_end: str           # ISO YYYY-12-31
    segment_name: str
    revenue: float | None = None
    operating_income: float | None = None
    revenue_share: float | None = None  # 0..1
    source_id: str = "dart"

    def as_row(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "corp_code": self.corp_code,
            "period_end": self.period_end,
            "period_type": "FY",
            "segment_name": self.segment_name,
            "revenue": self.revenue,
            "operating_income": self.operating_income,
            "revenue_share": self.revenue_share,
            "source_id": self.source_id,
        }


# --------------------------------------------------------------------------- #
# Segment-table heuristics                                                    #
# --------------------------------------------------------------------------- #

# Korean-number parser: handles comma separators, negative signs, "△" used on
# Korean filings for negative numbers, and trailing units we ignore.
_NUM_RE = re.compile(r"[+\-−△▽]?\d[\d,]*(?:\.\d+)?")

_KOR_SEG_HEADERS = ("사업부문", "부문명", "부문구분")
_KOR_REV_HEADERS = ("매출", "수익", "매출액")
_KOR_PCT_HEADERS = ("비중", "구성비", "비율")
_KOR_OPINCOME_HEADERS = ("영업이익", "영업손익")


def _parse_num(text: str) -> float | None:
    if not text:
        return None
    t = text.strip().replace(",", "")
    # △ / ▽ are Korean-filing negative markers.
    neg = False
    if t.startswith(("△", "▽", "(")) or t.endswith(")"):
        neg = True
        t = t.strip("()△▽ ")
    match = _NUM_RE.search(t)
    if not match:
        return None
    try:
        v = float(match.group(0).replace(",", ""))
    except ValueError:
        return None
    if neg:
        v = -v
    return v


def _looks_like_segment_table(headers: list[str]) -> bool:
    """Heuristic: does this table header row mention segment + revenue?"""
    hjoin = " ".join(headers)
    has_seg = any(tok in hjoin for tok in _KOR_SEG_HEADERS)
    has_rev = any(tok in hjoin for tok in _KOR_REV_HEADERS)
    return has_seg and has_rev


# --------------------------------------------------------------------------- #
# Adapter                                                                     #
# --------------------------------------------------------------------------- #


class DARTSegmentExtractor(BaseAdapter):
    """Fetches & parses segment revenue breakdowns from DART filings.

    Instantiate via ``DARTSegmentExtractor.from_settings()`` — reuses the same
    ``DART_API_KEY`` that :class:`DARTAdapter` consumes.
    """

    source_id = "dart_segments"
    priority = 10

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DART_BASE,
    ) -> None:
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url

    @classmethod
    def from_settings(cls) -> "DARTSegmentExtractor":
        return cls(api_key=cls._env("DART_API_KEY"))

    def healthcheck(self) -> dict[str, Any]:
        if not self.api_key:
            return self._timed_fail(self.source_id, "DART_API_KEY not configured")
        return self._timed_ok(0.0, self.source_id, {"configured": True})

    # ---------- API surface ----------

    def find_latest_annual_receipt(
        self,
        corp_code: str,
        year: int | None = None,
    ) -> Optional[tuple[str, str]]:
        """Return ``(receipt_no, period_end_iso)`` for the latest 사업보고서.

        Walks the ``list.json`` endpoint with ``pblntf_detail_ty=A001`` which
        tags annual reports. We try the requested year first (default: most
        recent fiscal year that's likely filed, i.e. last-year 12-31) and step
        back one year at a time for up to three tries.
        """
        if not self.api_key:
            raise AuthError("DART_API_KEY not configured")
        target_year = year or (date.today().year - 1)
        for offset in range(0, 3):
            y = target_year - offset
            bgn = f"{y}0101"
            end = f"{y + 1}0601"  # annual filings typically land by Q2 of next year
            try:
                resp = self._request(
                    "GET",
                    f"{self.base_url}/list.json",
                    params={
                        "crtfc_key": self.api_key,
                        "corp_code": corp_code,
                        "bgn_de": bgn,
                        "end_de": end,
                        "pblntf_detail_ty": "A001",
                        "page_count": 20,
                        "page_no": 1,
                    },
                )
            except AdapterError as exc:
                log.warning("dart list failed for %s: %s", corp_code, exc)
                continue
            if resp.status_code != 200:
                continue
            body = resp.json()
            if body.get("status") != "000":
                continue
            for row in body.get("list", []):
                name = str(row.get("report_nm", ""))
                # Exclude amendments & partial reports; keep the cleanest one.
                if "사업보고서" in name and "기재정정" not in name:
                    return (row.get("rcept_no", ""), f"{y}-12-31")
            # else keep searching older years
        return None

    def fetch_document_archive(self, receipt_no: str) -> bytes:
        """Download a filing archive. Returns raw ZIP bytes."""
        if not self.api_key:
            raise AuthError("DART_API_KEY not configured")
        resp = self._request(
            "GET",
            f"{self.base_url}/document.xml",
            params={"crtfc_key": self.api_key, "rcept_no": receipt_no},
            timeout=30.0,
        )
        if resp.status_code != 200:
            raise AdapterError(f"DART document → HTTP {resp.status_code}")
        return resp.content

    def extract_segments(
        self,
        symbol: str,
        corp_code: str,
        year: int | None = None,
    ) -> list[Segment]:
        """End-to-end: list → document → parse. Empty list on any failure."""
        try:
            rcept = self.find_latest_annual_receipt(corp_code, year=year)
        except Exception as exc:  # noqa: BLE001
            log.warning("segment receipt lookup failed for %s: %s", symbol, exc)
            return []
        if not rcept:
            return []
        receipt_no, period_end = rcept

        try:
            archive = self.fetch_document_archive(receipt_no)
        except Exception as exc:  # noqa: BLE001
            log.warning("segment archive fetch failed for %s: %s", symbol, exc)
            return []

        docs = _unzip_filing(archive)
        if not docs:
            return []

        for raw in docs:
            try:
                rows = _parse_segment_tables(raw)
            except Exception as exc:  # noqa: BLE001
                log.debug("parse attempt failed for %s: %s", symbol, exc)
                continue
            if rows:
                return [
                    Segment(
                        symbol=symbol,
                        corp_code=corp_code,
                        period_end=period_end,
                        segment_name=r["name"],
                        revenue=r.get("revenue"),
                        operating_income=r.get("operating_income"),
                        revenue_share=r.get("revenue_share"),
                    )
                    for r in rows
                ]
        return []


# --------------------------------------------------------------------------- #
# Parsing                                                                     #
# --------------------------------------------------------------------------- #


def _unzip_filing(archive: bytes) -> list[bytes]:
    """Return filing body bytes. DART's document.xml response is a ZIP.

    Falls back to returning ``archive`` itself if it's plain text/HTML (the
    API occasionally returns raw XML for small reports).
    """
    if not archive:
        return []
    # ZIP magic.
    if archive[:2] == b"PK":
        try:
            zf = zipfile.ZipFile(io.BytesIO(archive))
        except zipfile.BadZipFile:
            return []
        out: list[bytes] = []
        for name in zf.namelist():
            lower = name.lower()
            if lower.endswith((".xml", ".html", ".htm", ".xhtml")):
                try:
                    out.append(zf.read(name))
                except Exception:  # noqa: BLE001
                    continue
        return out
    return [archive]


def _parse_segment_tables(raw_bytes: bytes) -> list[dict[str, Any]]:
    """Parse segment tables from a DART filing body (XML/HTML bytes).

    Strategy: BS4 first (robust), fall back to the raw regex scanner.
    """
    text = _decode(raw_bytes)
    rows = _parse_with_bs4(text)
    if rows:
        return rows
    return _parse_with_regex(text)


def _decode(raw: bytes) -> str:
    for enc in ("utf-8", "euc-kr", "cp949", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _parse_with_bs4(text: str) -> list[dict[str, Any]]:
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except Exception:  # noqa: BLE001
        return []
    soup = BeautifulSoup(text, "html.parser")

    out: list[dict[str, Any]] = []
    for tbl in soup.find_all("table"):
        rows = tbl.find_all("tr")
        if len(rows) < 2:
            continue
        header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        if not _looks_like_segment_table(header_cells):
            continue

        # Locate the relevant columns by header keyword match.
        col_name = _match_col(header_cells, _KOR_SEG_HEADERS)
        col_rev = _match_col(header_cells, _KOR_REV_HEADERS, _KOR_OPINCOME_HEADERS)
        col_pct = _match_col(header_cells, _KOR_PCT_HEADERS)
        col_opinc = _match_col(header_cells, _KOR_OPINCOME_HEADERS)
        if col_name is None or col_rev is None:
            continue

        parsed: list[dict[str, Any]] = []
        for body_row in rows[1:]:
            cells = [c.get_text(strip=True) for c in body_row.find_all(["td", "th"])]
            if not cells or col_name >= len(cells):
                continue
            name = cells[col_name]
            if not name or name.startswith(("합계", "총계", "계", "소계")):
                continue
            # Reject obvious non-segment rows (blank/number-only first cell).
            if re.fullmatch(r"[\d,\.\- ]+", name):
                continue
            revenue = _parse_num(cells[col_rev]) if col_rev < len(cells) else None
            pct = _parse_num(cells[col_pct]) if (col_pct is not None and col_pct < len(cells)) else None
            op_income = (
                _parse_num(cells[col_opinc])
                if (col_opinc is not None and col_opinc != col_rev and col_opinc < len(cells))
                else None
            )
            share = None
            if pct is not None:
                # "47.2" → 0.472 ; already-0.47 style is rare but handled.
                share = pct / 100.0 if pct > 1.5 else pct
            parsed.append(
                {
                    "name": name,
                    "revenue": revenue,
                    "operating_income": op_income,
                    "revenue_share": share,
                }
            )
        # Heuristic quality gate: ≥2 segments w/ a revenue share OR revenue.
        usable = [r for r in parsed if r.get("revenue") or r.get("revenue_share")]
        if len(usable) >= 2:
            out = usable
            break  # first matching table wins
    return out


def _match_col(
    headers: list[str],
    want: tuple[str, ...],
    exclude: tuple[str, ...] = (),
) -> int | None:
    for i, h in enumerate(headers):
        if any(tok in h for tok in exclude):
            continue
        if any(tok in h for tok in want):
            return i
    return None


def _parse_with_regex(text: str) -> list[dict[str, Any]]:
    """Very loose regex fallback. Returns rows only when we're confident.

    Looks for blocks like ``사업부문별 매출`` followed by table-style lines
    "반도체\t12,345,678\t47.2%". The XML output of DART filings is frequently
    well-formed HTML so bs4 wins most of the time; this path catches pure-XML
    exports.
    """
    block_re = re.compile(
        r"사업부문별[^<]*?매출[\s\S]{0,3000}?</table>",
        re.IGNORECASE,
    )
    m = block_re.search(text)
    if not m:
        return []
    block = m.group(0)
    # Strip tags but keep row/cell separators.
    block = re.sub(r"</tr>", "\n", block, flags=re.IGNORECASE)
    block = re.sub(r"</td>|</th>", "\t", block, flags=re.IGNORECASE)
    block = re.sub(r"<[^>]+>", "", block)
    out: list[dict[str, Any]] = []
    for line in block.splitlines():
        cells = [c.strip() for c in line.split("\t") if c.strip()]
        if len(cells) < 2:
            continue
        name = cells[0]
        if re.fullmatch(r"[\d,\.\- %]+", name):
            continue
        if name.startswith(("합계", "총계", "계", "소계", "사업부문", "부문명")):
            continue
        revenue = _parse_num(cells[1]) if len(cells) > 1 else None
        pct = None
        for c in cells[2:]:
            if "%" in c or "." in c:
                pct = _parse_num(c)
                if pct is not None:
                    break
        share = (pct / 100.0) if (pct is not None and pct > 1.5) else pct
        if revenue is None and share is None:
            continue
        out.append(
            {
                "name": name,
                "revenue": revenue,
                "operating_income": None,
                "revenue_share": share,
            }
        )
    return out[:12]  # cap — reports never have 12+ useful segments


# Re-export unused constants to silence "imported but unused" warnings when
# downstream modules import from this module.
_ = (REPORT_CODES, _yyyymmdd)
