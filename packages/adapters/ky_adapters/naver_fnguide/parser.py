"""Parsers for the Naver / FnGuide snapshot payloads.

The two sources speak very different dialects:

* ``m.stock.naver.com/api/stock/{symbol}/integration`` — JSON. Compact but
  stable; we prefer it. It exposes summary quotes, consensus, peers, major
  shareholders and the most recent financial highlights.
* ``comp.fnguide.com/SVO2/ASP/SVD_Main.asp`` — HTML. Fallback; hand-parsed
  with BeautifulSoup. We extract only the Snapshot table so the parser is
  robust to most layout tweaks.

Both parsers return homogeneous ``FnguideSnapshot`` dicts keyed by the
fields in ``client.FnguideSnapshot``. Missing fields are ``None`` — never
fabricated.
"""
from __future__ import annotations

import re
from typing import Any


# --------------------------------------------------------------------------- #
# Naver mobile JSON                                                            #
# --------------------------------------------------------------------------- #


def parse_naver_integration(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse the mobile integration JSON payload into a snapshot dict.

    The real payload exposes (among other keys) ``totalInfos`` — a list of
    ``{code, key, value, valueDesc}`` tuples. We switch on the ``code`` field
    which is stable English (``per``, ``pbr``, ``eps``, ``bps``, ``roe``,
    ``dividendYieldRatio`` …)."""
    out: dict[str, Any] = {
        "source": "naver_mobile",
        "target_price": None,
        "investment_opinion": None,
        "per": None,
        "pbr": None,
        "eps": None,
        "bps": None,
        "roe": None,
        "roa": None,
        "debt_ratio": None,
        "dividend_yield": None,
        "market_cap": None,
        "foreign_ratio": None,
        "high_52w": None,
        "low_52w": None,
        "major_shareholder_pct": None,
        "major_shareholder_name": None,
        "financials_quarterly": [],
        "financials_annual": [],
        "peers": [],
        "summary_notes": [],
    }

    totals = payload.get("totalInfos") or []
    for item in totals if isinstance(totals, list) else []:
        code = (item.get("code") or "").strip()
        value = _num(item.get("value"))
        if code == "per":
            out["per"] = value
        elif code == "pbr":
            out["pbr"] = value
        elif code == "eps":
            out["eps"] = value
        elif code == "bps":
            out["bps"] = value
        elif code == "roe":
            out["roe"] = value
        elif code == "roa":
            out["roa"] = value
        elif code == "dividendYieldRatio":
            out["dividend_yield"] = value
        elif code == "foreignRate":
            out["foreign_ratio"] = value
        elif code == "highPriceOf52Weeks":
            out["high_52w"] = value
        elif code == "lowPriceOf52Weeks":
            out["low_52w"] = value
        elif code == "marketValue":
            # marketValue comes back as "1,337조 3,362억" — keep raw text too.
            out["market_cap"] = _num(item.get("value"))
            raw = item.get("value")
            if raw:
                out.setdefault("market_cap_raw", raw)

    # Consensus block
    consensus = payload.get("consensusInfo")
    if isinstance(consensus, dict):
        out["target_price"] = _num(consensus.get("priceTargetMean"))
        # recommMean is 1..5 (1=strong buy, 5=sell). Provide plain label.
        rec = _num(consensus.get("recommMean"))
        if rec is not None:
            out["investment_opinion"] = _recomm_label(rec)

    # Peers — industryCompareInfo is a flat list of company dicts.
    peers_raw = payload.get("industryCompareInfo") or []
    if isinstance(peers_raw, list):
        peers: list[dict[str, Any]] = []
        for p in peers_raw:
            if not isinstance(p, dict):
                continue
            peers.append(
                {
                    "symbol": p.get("itemCode"),
                    "name": p.get("stockName"),
                    "close": _num(p.get("closePrice")),
                    "change_pct": _num(p.get("fluctuationsRatio")),
                    "market_cap": _num(p.get("marketValue")),
                    "per": _num(p.get("per")),
                    "pbr": _num(p.get("pbr")),
                    "roe": _num(p.get("roe")),
                }
            )
        out["peers"] = peers[:5]

    # Researches contain recent analyst reports (optional).
    researches = payload.get("researches")
    if isinstance(researches, list) and researches:
        out["summary_notes"].append(f"Naver researches: {len(researches)}")

    name = payload.get("stockName")
    if name:
        out["summary_notes"].append(f"Naver: {name}")

    return out


def _recomm_label(rec: float) -> str:
    """Naver recommMean scale — 5=Strong Buy, 1=Sell (higher is more bullish)."""
    if rec >= 4.5:
        return "Strong Buy"
    if rec >= 3.5:
        return "Buy"
    if rec >= 2.5:
        return "Hold"
    if rec >= 1.5:
        return "Reduce"
    return "Sell"


def _num(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s in ("-", "N/A", "—"):
        return None
    # Strip commas, percent, trailing '배' (PER/PBR 단위), '원' (won).
    s = s.replace(",", "").replace("%", "")
    s = re.sub(r"[배원]+\s*$", "", s)
    s = s.strip()
    # Market cap comes with Korean unit words "조", "억", "백만". Convert.
    unit_multipliers = [("조", 1e12), ("억", 1e8), ("백만", 1e6), ("만", 1e4)]
    total = 0.0
    matched_unit = False
    remaining = s
    for unit, mult in unit_multipliers:
        m = re.search(rf"(-?[\d.]+)\s*{unit}", remaining)
        if m:
            try:
                total += float(m.group(1)) * mult
                matched_unit = True
                remaining = remaining.replace(m.group(0), "", 1).strip()
            except ValueError:
                pass
    if matched_unit:
        return total if total else None
    try:
        return float(s)
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# comp.fnguide.com HTML fallback                                               #
# --------------------------------------------------------------------------- #


def parse_fnguide_html(html: str) -> dict[str, Any]:
    """Parse the fnguide Snapshot page HTML. BeautifulSoup-powered; very
    defensive — missing tables leave fields as None."""
    try:
        from bs4 import BeautifulSoup  # type: ignore
    except ImportError:  # pragma: no cover
        return {"source": "fnguide", "summary_notes": ["bs4 missing"]}

    out: dict[str, Any] = {
        "source": "fnguide",
        "target_price": None,
        "investment_opinion": None,
        "per": None,
        "pbr": None,
        "eps": None,
        "bps": None,
        "roe": None,
        "roa": None,
        "debt_ratio": None,
        "dividend_yield": None,
        "market_cap": None,
        "foreign_ratio": None,
        "major_shareholder_pct": None,
        "major_shareholder_name": None,
        "financials_quarterly": [],
        "financials_annual": [],
        "peers": [],
        "summary_notes": [],
    }

    soup = BeautifulSoup(html, "html.parser")

    # Snapshot summary tables — FnGuide exposes key stats inside dl.dlst.
    for dl in soup.select("dl.dlst"):
        dt = dl.find("dt")
        dd = dl.find("dd")
        if not dt or not dd:
            continue
        key = dt.get_text(" ", strip=True)
        val = dd.get_text(" ", strip=True)
        num = _num(val)
        if "PER" in key and out["per"] is None:
            out["per"] = num
        elif "PBR" in key and out["pbr"] is None:
            out["pbr"] = num
        elif "EPS" in key and out["eps"] is None:
            out["eps"] = num
        elif "BPS" in key and out["bps"] is None:
            out["bps"] = num
        elif "ROE" in key:
            out["roe"] = num
        elif "ROA" in key:
            out["roa"] = num
        elif "부채비율" in key:
            out["debt_ratio"] = num
        elif "배당수익률" in key:
            out["dividend_yield"] = num
        elif "외국인" in key:
            out["foreign_ratio"] = num
        elif "시가총액" in key:
            out["market_cap"] = num

    # Target price — comp.fnguide renders inside #corp_group2 "적정주가".
    for row in soup.select("#corp_group2 tr"):
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        label = th.get_text(" ", strip=True)
        if "목표주가" in label or "적정주가" in label:
            out["target_price"] = _num(td.get_text(" ", strip=True))
        elif "투자의견" in label:
            out["investment_opinion"] = td.get_text(" ", strip=True)[:64]

    # Major shareholder table (#cTB13) — best-effort scrape.
    holder_tbl = soup.select_one("#cTB13") or soup.select_one(".us_table_ty1")
    if holder_tbl:
        first = holder_tbl.select_one("tbody tr")
        if first:
            cells = [c.get_text(" ", strip=True) for c in first.find_all(["td", "th"])]
            if len(cells) >= 2:
                out["major_shareholder_name"] = cells[0][:64]
                out["major_shareholder_pct"] = _num(cells[-1])

    # Quarterly highlights — HTML tables with class highlight_B.
    fin_tbl = soup.select_one(".highlight_B") or soup.select_one("#highlight_D_Q")
    if fin_tbl:
        headers = [th.get_text(" ", strip=True) for th in fin_tbl.select("thead th")]
        row_labels: dict[str, list[float | None]] = {}
        for tr in fin_tbl.select("tbody tr"):
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue
            label = cells[0].get_text(" ", strip=True)
            vals = [_num(c.get_text(" ", strip=True)) for c in cells[1:]]
            row_labels[label] = vals
        periods = headers[1:] if headers else []
        quarterly: list[dict[str, Any]] = []
        for i, p in enumerate(periods[:4]):
            quarterly.append(
                {
                    "period": p,
                    "revenue":          _pick(row_labels, ["매출액"], i),
                    "operating_income": _pick(row_labels, ["영업이익"], i),
                    "net_income":       _pick(row_labels, ["당기순이익"], i),
                    "eps":              _pick(row_labels, ["EPS"], i),
                    "bps":              _pick(row_labels, ["BPS"], i),
                    "roe":              _pick(row_labels, ["ROE"], i),
                    "debt_ratio":       _pick(row_labels, ["부채비율"], i),
                }
            )
        out["financials_quarterly"] = quarterly

    out["summary_notes"].append("fnguide html snapshot parsed")
    return out


def _pick(row_labels: dict[str, list[float | None]], keys: list[str], idx: int) -> float | None:
    for k in keys:
        for label, vals in row_labels.items():
            if k in label and idx < len(vals):
                return vals[idx]
    return None


_SYMBOL_RE = re.compile(r"^\d{6}$")


def is_valid_symbol(symbol: str) -> bool:
    return bool(_SYMBOL_RE.match(symbol or ""))
