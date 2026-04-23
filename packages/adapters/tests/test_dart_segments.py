"""Deterministic tests for the DART segments heuristic parser.

These cover the 2026-04 rewrite that ported F:/SEC disclosure-parser
section-scoping heuristics into ``ky_adapters.dart.segments``. Each fixture
mirrors a real failure mode we hit during the top-50 backfill:

* ``GOOD`` — canonical 사업부문 / 매출액 / 비중 table (Samsung-like).
* ``SAMSUNG_PRIMARY`` — generic "구  분" header with DX/DS/SDC rows in the
  first column. DART ships this with double-space padding that earlier
  code couldn't see.
* ``SUBSIDIARY_LIST`` — 종속기업 footnote (Gauss Labs (*1), ... row=-1,-2).
  Was the SK hynix false-positive pre-fix.
* ``ACCOUNTING_NOTES`` — 매출채권 breakdown (미수수익/미수금/선급금).
  Was the Hyundai false-positive pre-fix.
* ``ROW_INDEX_PATHOLOGY`` — revenue column is -1..-N (subsidiaries listed
  with their row index instead of actual revenue).
* ``TIMESERIES`` — 사업부문 + 2025년(제58기) / 2024년(제57기) year columns
  with no explicit "매출" header. Common in 사업보고서 Item II.
* ``MIXED`` — subsidiary list followed by a real segment table; the
  section-scoped scan must pick the latter.
"""
from __future__ import annotations

import pytest

from ky_adapters.dart.segments import _parse_with_bs4


GOOD = """
<html><body>
<p>II. 사업의 내용</p>
<h2>사업부문별 매출</h2>
<table>
<tr><th>사업부문</th><th>매출액</th><th>비중</th></tr>
<tr><td>DS (반도체)</td><td>84,565,000</td><td>44.5</td></tr>
<tr><td>DX (디바이스)</td><td>93,120,000</td><td>49.0</td></tr>
<tr><td>SDC (디스플레이)</td><td>31,250,000</td><td>16.4</td></tr>
<tr><td>Harman</td><td>13,470,000</td><td>7.1</td></tr>
<tr><td>소계</td><td>222,405,000</td><td>117</td></tr>
</table>
</body></html>
"""

SAMSUNG_PRIMARY = """
<html><body>
<p>II. 사업의 내용</p>
<h2>2. 주요 제품 및 서비스</h2>
<table>
<tr><th>구  분</th><th>주요 제품</th><th>매  출  액</th><th>비중</th></tr>
<tr><td>DX 부문</td><td>TV, 모바일 등</td><td>1,879,673</td><td>56.3%</td></tr>
<tr><td>DS 부문</td><td>DRAM, NAND</td><td>1,301,282</td><td>39.0%</td></tr>
<tr><td>SDC</td><td>OLED 패널</td><td>298,417</td><td>8.9%</td></tr>
<tr><td>Harman</td><td>전장부품</td><td>157,830</td><td>4.7%</td></tr>
</table>
</body></html>
"""

SUBSIDIARY_LIST = """
<html><body>
<h3>종속기업 현황</h3>
<table>
<tr><th>회사명</th><th>소재지</th><th>지분율</th><th>매출</th></tr>
<tr><td>Gauss Labs Inc.(*1)</td><td>USA</td><td>100</td><td>500</td></tr>
<tr><td>SK hynix NAND(*1)</td><td>USA</td><td>100</td><td>800</td></tr>
<tr><td>SkyHigh Memory(*3)</td><td>BM</td><td>80</td><td>300</td></tr>
</table>
</body></html>
"""

ACCOUNTING_NOTES = """
<html><body>
<h3>8. 매출채권 및 기타채권</h3>
<table>
<tr><th>구분</th><th>매출</th></tr>
<tr><td>제58기</td><td>9,258,422</td></tr>
<tr><td>미수수익</td><td>19,479</td></tr>
<tr><td>선급금</td><td>1,745</td></tr>
<tr><td>미수금</td><td>30,960</td></tr>
<tr><td>미청구공사</td><td>2,719</td></tr>
<tr><td>합   계</td><td>9,310,606</td></tr>
</table>
</body></html>
"""

ROW_INDEX_PATHOLOGY = """
<html><body>
<p>II. 사업의 내용</p>
<h2>부문별 매출</h2>
<table>
<tr><th>사업부문</th><th>매출</th></tr>
<tr><td>Subsidiary A</td><td>-1</td></tr>
<tr><td>Subsidiary B</td><td>-2</td></tr>
<tr><td>Subsidiary C</td><td>-3</td></tr>
<tr><td>Subsidiary D</td><td>-4</td></tr>
<tr><td>Subsidiary E</td><td>-5</td></tr>
</table>
</body></html>
"""

TIMESERIES = """
<html><body>
<p>II. 사업의 내용</p>
<h2>2. 부문별 실적</h2>
<table>
<tr><th>사업부문</th><th>구분</th><th>2025년(제58기)</th><th>2024년(제57기)</th></tr>
<tr><td>차량부문</td><td>매출</td><td>103,200,000</td><td>98,500,000</td></tr>
<tr><td>금융부문</td><td>매출</td><td>18,800,000</td><td>17,400,000</td></tr>
<tr><td>기타부문</td><td>매출</td><td>13,700,000</td><td>11,200,000</td></tr>
</table>
</body></html>
"""

MIXED = """
<html><body>
<p>I. 회사의 개요</p>
<h3>종속기업 현황</h3>
<table>
<tr><th>회사명</th><th>소재지</th><th>지분율</th></tr>
<tr><td>Gauss Labs Inc.(*1)</td><td>USA</td><td>100</td></tr>
<tr><td>SK NAND(*2)</td><td>USA</td><td>100</td></tr>
</table>
<p>II. 사업의 내용</p>
<h2>사업부문별 매출 현황</h2>
<table>
<tr><th>사업부문</th><th>매출액</th><th>비중</th></tr>
<tr><td>메모리반도체</td><td>35,700,000</td><td>85.3</td></tr>
<tr><td>기타</td><td>6,150,000</td><td>14.7</td></tr>
</table>
</body></html>
"""


def test_good_explicit_segment_table():
    rows = _parse_with_bs4(GOOD)
    assert len(rows) == 4
    names = [r["name"] for r in rows]
    assert "DS (반도체)" in names[0]
    assert rows[0]["revenue"] == 84565000.0
    assert abs((rows[0]["revenue_share"] or 0) - 0.445) < 0.001


def test_samsung_generic_header_with_double_spaces():
    rows = _parse_with_bs4(SAMSUNG_PRIMARY)
    assert len(rows) == 4
    names = [r["name"] for r in rows]
    assert any("DX" in n for n in names)
    assert any("DS" in n for n in names)
    # Check share captured despite "매  출  액" / "구  분" doubled whitespace.
    assert abs((rows[0]["revenue_share"] or 0) - 0.563) < 0.001


def test_subsidiary_list_rejected():
    assert _parse_with_bs4(SUBSIDIARY_LIST) == []


def test_accounting_notes_rejected():
    assert _parse_with_bs4(ACCOUNTING_NOTES) == []


def test_row_index_pathology_rejected():
    assert _parse_with_bs4(ROW_INDEX_PATHOLOGY) == []


def test_timeseries_year_column_as_revenue():
    rows = _parse_with_bs4(TIMESERIES)
    assert len(rows) == 3
    names = [r["name"] for r in rows]
    assert "차량부문" in names
    assert "금융부문" in names
    # Revenue should come from the leftmost year column (2025년).
    assert rows[0]["revenue"] == 103200000.0


def test_mixed_section_scoping_picks_real_segment_table():
    rows = _parse_with_bs4(MIXED)
    assert len(rows) == 2
    assert rows[0]["name"] == "메모리반도체"
    assert rows[0]["revenue"] == 35700000.0
