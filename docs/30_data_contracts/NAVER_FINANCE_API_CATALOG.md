# Naver Finance API - Complete Data Catalog

> Exhaustive analysis of all Naver Finance data sources.
> Test stock: 005930 (Samsung Electronics). Verified 2026-04-04.

---

## Source Summary

| # | Source | Base URL | Auth | Format |
|---|--------|----------|------|--------|
| 1 | Mobile API | `m.stock.naver.com/api/stock` | None (User-Agent required) | JSON |
| 2 | NaverComp (WiseReport) | `navercomp.wisereport.co.kr/v2/company` | Session cookie + encparam | JSON/HTML |
| 3 | Chart Data API | `fchart.stock.naver.com/sise.nhn` | None | XML |
| 4 | Realtime Polling API | `polling.finance.naver.com/api/realtime` | None | JSON |
| 5 | PC Finance (Legacy) | `finance.naver.com/item` | None | HTML (EUC-KR) |

---

## 1. Mobile API (m.stock.naver.com)

### 1.1 Integration (Main Overview)

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/integration`

**Data Fields:**

```
stockEndType          : "stock"
itemCode              : "005930"
reutersCode           : "005930"
stockName             : "삼성전자"

totalInfos[] (key-value array):
  lastClosePrice      : 전일 종가
  openPrice           : 시가 (+ compareToPreviousPrice)
  highPrice           : 고가
  lowPrice            : 저가
  accumulatedTradingVolume : 거래량
  accumulatedTradingValue  : 거래대금 (백만 단위 문자열)
  marketValue         : 시가총액 (문자열: "1,102조 2,366억")
  foreignRate         : 외국인소진율 (예: "48.40%")
  highPriceOf52Weeks  : 52주 최고
  lowPriceOf52Weeks   : 52주 최저
  per                 : PER (+ valueDesc 기준일)
  eps                 : EPS
  cnsPer              : 추정 PER (consensus)
  cnsEps              : 추정 EPS (consensus)
  pbr                 : PBR
  bps                 : BPS
  dividendYieldRatio  : 배당수익률
  dividend            : 주당배당금

dealTrendInfos[] (최근 5일 투자자별 동향):
  bizdate                : 영업일 (YYYYMMDD)
  foreignerPureBuyQuant  : 외국인 순매수
  foreignerHoldRatio     : 외국인 보유비율
  organPureBuyQuant      : 기관 순매수
  individualPureBuyQuant : 개인 순매수
  closePrice             : 종가
  compareToPreviousClosePrice : 전일대비
  compareToPreviousPrice : {code, text, name} (RISING/FALLING)
  accumulatedTradingVolume : 거래량

researches[] (최근 증권사 리포트 5건):
  id, cd, nm, bnm(증권사명), tit(제목), rcnt(조회수), wdt(작성일)

industryCode          : "278" (업종코드)

industryCompareInfo[] (동일업종 비교 종목 6개):
  itemCode, stockName, closePrice, fluctuationsRatio,
  marketValue, stockExchangeType

consensusInfo:
  recommMean           : 투자의견 평균 (1-5 scale)
  priceTargetMean      : 목표주가 평균
```

**Period:** Current snapshot only.
**Consensus:** Yes (cnsPer, cnsEps, consensusInfo).

---

### 1.2 Finance Annual

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/finance/annual`

**Structure:**
```json
{
  "itemCode": "005930",
  "financePeriodType": "annual",
  "financeInfo": {
    "trTitleList": [
      {"isConsensus": "N", "title": "2023.12.", "key": "202312"},
      {"isConsensus": "N", "title": "2024.12.", "key": "202412"},
      {"isConsensus": "N", "title": "2025.12.", "key": "202512"},
      {"isConsensus": "Y", "title": "2026.12.", "key": "202612"}
    ],
    "rowList": [...]
  },
  "corporationSummary": {
    "comment1": "...", "comment2": "...", "comment3": "..."
  }
}
```

**Row Items (16 metrics):**

| # | title (metric) | Unit | Notes |
|---|---------------|------|-------|
| 1 | 매출액 | 억원 | Revenue |
| 2 | 영업이익 | 억원 | Operating Income |
| 3 | 당기순이익 | 억원 | Net Income |
| 4 | 지배주주순이익 | 억원 | Net Income (controlling) |
| 5 | 비지배주주순이익 | 억원 | Net Income (non-controlling) |
| 6 | 영업이익률 | % | Operating Margin |
| 7 | 순이익률 | % | Net Margin |
| 8 | ROE | % | Return on Equity |
| 9 | 부채비율 | % | Debt Ratio |
| 10 | 당좌비율 | % | Quick Ratio |
| 11 | 유보율 | % | Retention Ratio |
| 12 | EPS | 원 | Earnings Per Share |
| 13 | PER | 배 | Price-Earnings Ratio |
| 14 | BPS | 원 | Book Value Per Share |
| 15 | PBR | 배 | Price-Book Ratio |
| 16 | 주당배당금 | 원 | Dividend Per Share |

**Period:** 3 years actual + 1 year estimate (E).
**Consensus:** Yes, last column is marked `isConsensus: "Y"`.

---

### 1.3 Finance Quarter

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/finance/quarter`

Same 16 metrics as annual. **Period:** 5 quarters actual + 1 quarter estimate (E).

---

### 1.4 Price (Daily OHLCV)

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/price`

**Fields per day:**
```
localTradedAt                  : "2026-04-03" (날짜)
closePrice                     : "186,200" (종가, 문자열)
compareToPreviousClosePrice    : "7,800" (전일대비)
compareToPreviousPrice         : {code, text, name}
fluctuationsRatio              : "4.37" (등락률)
openPrice                      : "182,900" (시가)
highPrice                      : "187,200" (고가)
lowPrice                       : "181,000" (저가)
accumulatedTradingVolume       : 39791920 (거래량, 정수)
```

**Period:** ~20 most recent trading days.

---

### 1.5 Disclosure (공시)

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/disclosure`

**Fields per item:**
```
itemCode      : "005930"
disclosureId  : 1625302
title         : "삼성전자(주) 주식 소각 결정"
datetime      : "2026-03-31T06:50:02"
author        : "KOSCOM"
```

**Period:** ~20 most recent disclosures (~2 months).

---

### 1.6 Basic (Stock Info)

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/basic`

**Fields:**
```
stockEndType       : "stock"
itemCode           : "005930"
reutersCode        : "005930"
stockName          : "삼성전자"
itemLogoUrl        : SVG logo URL
itemLogoPngUrl     : PNG logo URL
sosok              : "0" (0=KOSPI, 1=KOSDAQ)
closePrice         : "186,200"
compareToPreviousClosePrice : "7,800"
compareToPreviousPrice      : {code, text, name}
fluctuationsRatio  : "4.37"
marketStatus       : "CLOSE" | "OPEN"
localTradedAt      : ISO-8601 timestamp
tradeStopType      : {code, text, name} (TRADING/SUSPENDED)
stockExchangeType  : {code(KS/KQ), nameKor, stockType, etc.}

imageCharts:       : Pre-rendered chart image URLs
  candleDay, candleWeek, candleMonth
  day, areaMonthThree, areaYear, areaYearThree, areaYearTen
  transparent, dayUp

scriptChartTypes[] : ["candleMinuteFive","candleDay","candleWeek","candleMonth",
                      "day","areaMonthThree","areaYear","areaYearThree","areaYearTen"]

overMarketPriceInfo: (시간외 거래)
  tradingSessionType : "AFTER_MARKET"
  overMarketStatus   : "CLOSE"
  overPrice          : "185,800"
  fluctuationsRatio  : "4.15"

newlyListed        : false
nationType         : "KOR"
```

---

### 1.7 Trend (Investor Flow)

**URL:** `GET https://m.stock.naver.com/api/stock/{code}/trend`

**Fields per day (10 days):**
```
itemCode                   : "005930"
bizdate                    : "20260403"
foreignerPureBuyQuant      : "+516,352" (외국인 순매수)
foreignerHoldRatio         : "48.41%" (외국인 지분율)
organPureBuyQuant          : "+1,916,117" (기관 순매수)
individualPureBuyQuant     : "-4,955,613" (개인 순매수)
closePrice                 : "186,200"
compareToPreviousClosePrice: "7,800"
compareToPreviousPrice     : {code, text, name}
accumulatedTradingVolume   : "20,194,447"
```

**Period:** ~10 most recent trading days.

---

### 1.8 Endpoints That Do NOT Exist

The following m.stock.naver.com/api/stock/{code}/... paths all return **404**:
`investor`, `short`, `discuss`, `news`, `similar`, `askbid`, `chart`,
`research`, `consensus`, `dividend`, `shareholders`, `overview`,
`trading`, `quotation`, `fluctuation`, `performance`, `related`, `theme`,
`index`, `deal-trend`, `foreign`, `institution`, `supply-demand`,
`stockholders`, `corpInfo`, `info`, `company`, `summary`, `detail`,
`sise`, `real`, `poll`, `majorHolder`, `financial`, `financials`,
`dealTrend`, `majorShareholders`, `shareholdersReturn`, `peers`,
`consensusInfo`, `financeSummary`

---

## 2. NaverComp / WiseReport (Detailed Financial Statements)

### Authentication Flow

1. **GET** the parent page (e.g., `c1030001.aspx?cmp_cd={code}`) to get session cookie + `encparam` token.
2. Parse `encparam` from JavaScript: `encparam: 'BASE64TOKEN'`
3. **GET** the AJAX endpoint with same session cookie, passing `encparam` as query param.
4. Headers required: `Referer`, `X-Requested-With: XMLHttpRequest`

**CRITICAL:** `encparam` is per-session and changes every request to the parent page. Must use the same session's cookie + encparam together.

---

### 2.1 Tab Pages (HTML)

| Tab | URL | Content |
|-----|-----|---------|
| c1010001 | 기업현황 | Summary: price, returns, shares, beta, ownership |
| c1020001 | 기업개요 | Company description, business segments |
| c1030001 | 재무분석 | Financial statements (AJAX -> cF3002) |
| c1040001 | 투자지표 | Investment metrics (AJAX -> cF4002) |
| c1050001 | 컨센서스 | Consensus estimates (AJAX -> cF5001, cF5002) |
| c1060001 | 업종분석 | Industry analysis (AJAX -> cF6001) |
| c1070001 | 지분현황 | Ownership/shareholding (embedded HTML) |
| c1090001 | 섹터분석 | Sector analysis (AJAX -> cF9001) |

---

### 2.2 c1010001 - Company Overview (HTML)

Directly embedded in HTML page. Key data from `table#cTB11`:

```
주가/전일대비/수익률    : 186,200 / +7,800 / +4.37%
52Weeks 최고/최저      : 223,000 / 52,900
액면가                 : 100원
거래량/거래대금         : 20,194,400주 / 37,447억원
시가총액               : 11,022,366억원
52주베타               : 1.21
발행주식수/유동비율     : 5,846,278,608주 / 75.23%
외국인지분율            : 48.40%
수익률 (1M/3M/6M/1Y)  : -4.56% / +44.90% / +109.21% / +223.26%
```

**Header bar data:**
```
EPS: 6,564 | BPS: 63,997 | PER: 28.37 | 업종PER: 20.91 | PBR: 2.91
현금배당수익률: 0.90% | 결산월: 12월 | WICS: 반도체와반도체장비
KOSPI: 코스피 전기전자
```

---

### 2.3 cF1001 - Financial Summary (HTML iframe)

**URL:** `GET /v2/company/cF1001.aspx?cmp_cd={code}`
(Loaded as iframe in c1010001. Returns HTML table, no AJAX needed.)

**Data:** 4 years annual + 4 quarters, all in one table.

**Row items:**
```
매출액, 영업이익, 영업이익(발표기준), 세전계속사업이익,
당기순이익, 당기순이익(지배), 당기순이익(비지배),
자산총계, 부채총계, 자본총계,
자본총계(지배), 자본총계(비지배),
자본금, 부채비율, 유보율, 영업이익률, 지배주주순이익률,
EPS(원), BPS(원), DPS(원), PER(배), PBR(배),
발행주식수(보통주)
```

**Period:** Annual: 4 years actual. Quarterly: 4 quarters actual.

---

### 2.4 cF1002 - Financial Summary (Alternative)

**URL:** `GET /v2/company/cF1002.aspx?cmp_cd={code}&finGubun={MAIN|IFRSL|IFRSS}`
(AJAX from c1010001, returns HTML.)

**Data:** 3 years actual + 2 years estimate (E).

**Row items:**
```
재무년월, 매출액(금액, YoY%), 영업이익, 당기순이익,
EPS, PER, PBR, ROE, EV/EBITDA, 순부채비율, 주재무제표
```

**Period:** 3 actual + 2 estimate years.
**Consensus:** Yes, estimate years marked (E).

---

### 2.5 cF3002 - Detailed Financial Statements (JSON)

**URL:** `GET /v2/company/cF3002.aspx?cmp_cd={code}&frq_typ={Y|Q}&rpt_typ={ISM|BSM|CFM}&encparam={token}`

**IMPORTANT:** Despite the `rpt_typ` parameter, this endpoint returns ALL financial data (IS+BS+CF combined) in a single 244-row response. The `rpt_typ` parameter appears to have no effect.

**Response Structure:**
```json
{
  "YYMM": ["2021/12 (IFRS연결)", ..., "2026/12(E) (IFRS연결)", "전년대비 (YoY)", "전년대비 (YoY)"],
  "DATA": [ {row}, {row}, ... ],
  "FIN": "IFRS연결",
  "FRQ": "연간"
}
```

**Row Structure:**
```
ACKIND    : "A" (account kind)
ACCODE    : "200000" (account code, hierarchical)
ACC_NM    : "매출액(수익)" (account name in Korean)
LVL       : 1|3|4|5 (depth level)
GRP_TYP   : grouping type
UNT_TYP   : unit type (2=억원)
P_ACCODE  : parent account code

DATA1..DATA6 : Values for periods (YYMM[0]..YYMM[5])
YYOY      : Year-over-Year % (actual)
YEYOY     : Year-over-Year % (vs estimate)

DATAQ1..DATAQ6 : Quarterly values (when frq_typ=Y, these are last 4+1 quarters)
QOQ       : Quarter-over-Quarter %
YOY       : Year-over-Year % (quarterly)
QOQ_COMMENT : Detailed QoQ calculation text
YOY_COMMENT : Detailed YoY calculation text
QOQ_E     : Estimated QoQ %
YOY_E     : Estimated YoY %
POINT_CNT : Number of analyst estimates
```

**Period (Annual):** 5 years actual + 1 year estimate (E). Also includes latest 4+1 quarter data.
**Period (Quarterly):** Not separately verified (same 244 rows returned).

**Complete Account Names (244 items) - Income Statement portion:**

```
LVL=1 매출액(수익)
LVL=1 *내수
LVL=1 *수출
LVL=3 ....제품매출액
LVL=3 ....상품매출액
LVL=3 ....재화의판매로인한수익(상품,제품매출액)
LVL=3 ....건설계약으로인한수익(공사수익)
LVL=3 ....분양수익
LVL=3 ....용역의제공으로인한수익(매출액)
LVL=3 ....지분법이익
LVL=3 ....금융수익
LVL=3 ....배당수익
LVL=3 ....이자수익
LVL=3 ....기타수익
LVL=1 매출원가
LVL=3 ....(16 sub-items: 제품매출원가, 상품매출원가, etc.)
LVL=1 매출총이익
LVL=1 판매비와관리비
LVL=3 ....급여, 퇴직급여, 명예퇴직금, 복리후생비, 주식보상비,
         교육훈련비, 수도광열비, 세금과공과, 임차료, 보험료,
         지급수수료, 감가상각비, 개발비상각, 기타무형자산상각비,
         연구개발비, 특허권등사용료, 기타관리비, 광고선전비,
         수출비용, 판매촉진비, 판매수수료, 기타물류원가,
         애프터서비스비, 대손상각비, 기타판매비, 기타원가성비용,
         기타, *인건비및복리후생비, *일반관리비, *판매비
LVL=1 영업이익
LVL=1 *기타영업손익
      ....(이자수익, 배당금수익, 외환거래이익/손실, 임대료,
           대손충당금환입, 자산처분이익/손실, 자산평가이익/손실,
           파생상품이익/손실, 자산손상차손, 지분법, etc.)
LVL=1 영업이익(발표기준)
LVL=1 금융수익
LVL=3 ....이자수익, 배당금수익, 외환거래이익(외환차익, 외화환산이익),
         대손충당금환입, 당기손익-공정가치측정금융자산관련이익,
         금융자산처분이익(FVTPL, FVOCI, 상각후원가, 단기, 장기, 기타),
         금융자산평가이익, 파생상품이익, 금융자산손상차손환입,
         종속기업/공동지배기업/관계기업(지분법)관련이익, 기타
LVL=1 금융원가
LVL=3 ....(mirror of 금융수익 - 손실 versions)
LVL=1 기타영업외수익
LVL=1 기타영업외비용
LVL=1 종속기업/관계기업관련손익
LVL=1 세전계속사업이익
LVL=1 법인세비용
LVL=1 계속사업이익
LVL=1 중단사업이익
LVL=1 당기순이익
LVL=3 ....(지배주주지분)당기순이익
LVL=3 ....(비지배주주지분)당기순이익
LVL=1 기타포괄손익 (with sub-items: 재분류, 외화환산, 파생상품, etc.)
LVL=1 총포괄이익
LVL=1 *주당계속사업이익
LVL=1 *주당순이익
LVL=1 *희석주당계속사업이익
LVL=1 *희석주당순이익
```

**The 244 rows include IS + BS + CF all combined.** This is the most granular financial data source.

---

### 2.6 cF4002 - Investment Metrics (JSON)

**URL:** `GET /v2/company/cF4002.aspx?cmp_cd={code}&frq_typ={Y|Q}&encparam={token}`

**Metrics (23 rows):**
```
매출총이익률 (Gross Margin %)
  매출총이익<당기>, 매출액<당기>
영업이익률 (Operating Margin %)
  영업이익<당기>, 매출액<당기>
순이익률 (Net Margin %)
  당기순이익<당기>, 매출액<당기>
EBITDA마진율
  EBITDA<당기>, 매출액<당기>
ROE
  당기순이익(지배)<당기>, 자본총계(지배)<전기>, 자본총계(지배)<당기>
ROA
  당기순이익<당기>, 자산총계<전기>, 자산총계<당기>
ROIC
  NOPLAT, IC
```

**Period:** Same as cF3002 (5Y actual + 1Y estimate + quarterly).

---

### 2.7 cF5001/cF5002 - Consensus (JSON)

**URL:** `GET /company/ajax/cF5001.aspx?cmp_cd={code}&dt={YYYYMMDD}&yymm=&frq={Y|Q}&acc_cd=&fingubun=IFRSL&chartType=svg`

**Note:** These use `/company/ajax/` path prefix (not `/v2/company/`).

**Response:** Two nested JSON chart objects (`chart1`, `chart2`), each containing:
```
select_item_unit
select_item_name
categories[]      : period labels
close_price[]     : actual stock prices
target_price[]    : consensus target prices
select_item[]     : consensus metric values
```

**Usage:** Chart data for consensus trends over time.

---

### 2.8 cF6001 - Industry Analysis Header (JSON)

**URL:** `GET /company/ajax/cF6001.aspx?cmp_cd={code}&finGubun=IFRSL&frq=Y`

**Response:**
```json
{
  "oDt_header": [
    {"SEQ": 1, "CMP_CD": "005930", "CMP_KOR": "삼성전자",
     "YYMM": "202512", "MKT_VAL": 11022365.81, "FIN_GUBUN": "IFRS연결", "CAP_SIZE": 1}
  ]
}
```

---

### 2.9 cF9001 - Sector Analysis (JSON)

**URL:** `GET /company/ajax/cF9001.aspx?cmp_cd={code}&data_typ={1|2}&sec_cd=&chartType=svg`

**Response Structure:**
```
dt0: {data: [...], yymm: ["2021",...,"2026(E)"]}
  ITEM codes:
    3 = 매출액 증가율 (Revenue Growth YoY)
    6 = 부채비율 (Debt Ratio)
    7 = 수익률 (Stock Return)
    8 = 배당수익률 (Dividend Yield)
    9 = ROE
    11 = 매출총이익률 (Gross Margin)
  GUBN:
    1 = Company (삼성전자)
    2 = Sector (반도체)
    3 = Market (코스피)
  Fields: FY_4, FY_3, FY_2, FY_1, FY0, FY1 (6 years of data)

dt1: Time-series return data
  TRD_DT[]   : Timestamps (monthly, ~64 points spanning ~5 years)
  STK_RTN[]  : Stock cumulative return %
  SEC_RTN[]  : Sector cumulative return %
  MKT_RTN[]  : Market cumulative return %

dt3: Valuation comparison (same ITEM/GUBN structure as dt0)
  PER, PBR, 매출액증가율, 부채비율, 배당수익률, ROE, 매출총이익률
  Each with company / sector / market values + component data

finStdList: [{GUBN, GUBN_NM, FY_4..FY1}] (period labels)
```

**Period:** 6 years (5 actual + 1 estimate).

---

## 3. Chart Data API (fchart.stock.naver.com)

**URL:** `GET https://fchart.stock.naver.com/sise.nhn?symbol={code}&timeframe={tf}&count={n}&requestType=0`

**Timeframes:** `day`, `week`, `month`, `minute`

**Response:** XML
```xml
<chartdata symbol="005930" name="삼성전자" count="1000" timeframe="day" precision="0" origintime="19900103">
  <item data="20260403|184200|187200|182700|186200|20194447" />
  <!-- format: date|open|high|low|close|volume -->
</chartdata>
```

**Period:**
- Day: Up to ~1000 days (tested with count=1000, got 2015 lines = ~1000 data points)
- Week: Up to ~1000 weeks
- Month: Up to ~1000 months
- Minute: Intraday minute bars (last few days)

**Data format:** `YYYYMMDD|open|high|low|close|volume`
For minutes: `YYYYMMDDHHmm|open|high|low|close|volume`

---

## 4. Realtime Polling API

**URL:** `GET https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}`

**Fields:**
```json
{
  "cd": "005930",          // code
  "nm": "삼성전자",         // name
  "sv": 178400,            // previous close (숫자)
  "nv": 186200,            // current price (숫자)
  "cv": 7800,              // change vs previous
  "cr": 4.37,              // change ratio %
  "rf": "2",               // direction (2=up, 5=down)
  "mt": "1",               // market type
  "ms": "CLOSE",           // market status
  "pcv": 178400,           // previous close value
  "ov": 184200,            // open
  "hv": 187200,            // high
  "lv": 182700,            // low
  "ul": 231500,            // upper limit
  "ll": 124900,            // lower limit
  "aq": 20194447,          // accumulated volume
  "aa": 3744696000000,     // accumulated value (원)
  "keps": 4950,            // K-IFRS EPS
  "eps": 6564,             // EPS
  "bps": 63997.24,         // BPS
  "cnsEps": 25389,         // consensus EPS
  "dv": 1668.0,            // dividend
  "countOfListedStock": 5919637922,
  "nxtOverMarketPriceInfo": {...}  // after-hours trading
}
```

**Usage:** Real-time/near-real-time price polling. `pollingInterval` field suggests refresh interval (70000ms = 70 seconds when market closed).

---

## 5. PC Finance Legacy (finance.naver.com)

### 5.1 Daily Price History (HTML)

**URL:** `GET https://finance.naver.com/item/sise_day.naver?code={code}&page={n}`

**Fields:** 날짜, 종가, 전일비, 시가, 고가, 저가, 거래량

**Period:** Paginated, ~10 rows per page. Can go back years.
**Encoding:** EUC-KR

### 5.2 Foreign/Institution Trading (HTML)

**URL:** `GET https://finance.naver.com/item/frgn.naver?code={code}&page={n}`

**Fields:** 날짜, 종가, 전일비, 거래량, 기관순매매량, 외국인순매매량, 외국인보유주수, 외국인보유율

---

## Category-Based Summary

### 1. 가격/시세 (Price/Quote)

| Source | Endpoint | Data | Period |
|--------|----------|------|--------|
| Mobile API | `/basic` | Real-time price, market status, after-hours | Current |
| Mobile API | `/price` | Daily OHLCV | ~20 days |
| Mobile API | `/integration` | Quote summary + 52w range | Current |
| Polling API | `realtime?query=SERVICE_ITEM:{code}` | Real-time OHLCV + limits | Current |
| Chart API | `sise.nhn?timeframe=day&count=1000` | Historical OHLCV | ~1000 days |
| Chart API | `sise.nhn?timeframe=week` | Weekly OHLCV | ~1000 weeks |
| Chart API | `sise.nhn?timeframe=month` | Monthly OHLCV | ~1000 months |
| Chart API | `sise.nhn?timeframe=minute` | Intraday minute bars | ~3 days |
| PC Finance | `sise_day.naver` | Daily OHLCV (paginated HTML) | Many years |

### 2. 기업개요 (Company Overview)

| Source | Endpoint | Data |
|--------|----------|------|
| Mobile API | `/integration` | stockName, industryCode, industryCompareInfo |
| Mobile API | `/basic` | Logo URLs, sosok (market), exchange type |
| Mobile API | `/finance/annual` | corporationSummary (3 comments) |
| NaverComp | `c1010001` | EPS, BPS, PER, PBR, 업종PER, WICS sector, 결산월, 52주베타, 발행주식수, 유동비율, 수익률(1M/3M/6M/1Y) |
| NaverComp | `c1020001` | Business description, segments |

### 3. 손익계산서 (Income Statement)

| Source | Endpoint | Granularity | Period |
|--------|----------|-------------|--------|
| Mobile API | `/finance/annual` | 16 summary metrics | 3Y + 1E |
| Mobile API | `/finance/quarter` | 16 summary metrics | 5Q + 1E |
| NaverComp | `cF3002 (ISM)` | **244 line items** (full IS+BS+CF) | 5Y + 1E |
| NaverComp | `cF1001` | Summary HTML | 4Y + 4Q |
| NaverComp | `cF1002` | Summary HTML | 3Y + 2E |

**Key IS accounts in cF3002:** 매출액, *내수/*수출, 매출원가, 매출총이익, 판매비와관리비 (28 sub-items), 영업이익, 금융수익/금융원가 (30+ sub-items), 기타영업외손익, 세전계속사업이익, 법인세비용, 당기순이익(지배/비지배), 총포괄이익, EPS(기본/희석)

### 4. 재무상태표 (Balance Sheet)

| Source | Endpoint | Data |
|--------|----------|------|
| Mobile API | `/finance/*` | 부채비율, 당좌비율, 유보율, BPS, PBR |
| NaverComp | `cF3002` | Full BS embedded in 244-row response |
| NaverComp | `cF1001` | 자산총계, 부채총계, 자본총계, 자본금, 발행주식수 |

**Key BS accounts in cF3002:** (embedded within same 244-row response as IS/CF)

### 5. 현금흐름표 (Cash Flow Statement)

| Source | Endpoint | Data |
|--------|----------|------|
| NaverComp | `cF3002` | Full CF embedded in 244-row response |

### 6. 투자지표 (Investment Metrics)

| Source | Endpoint | Metrics |
|--------|----------|---------|
| Mobile API | `/integration` | PER, EPS, PBR, BPS, 배당수익률, cnsPER, cnsEPS |
| Mobile API | `/finance/*` | ROE, PER, PBR, EPS, BPS, 영업이익률, 순이익률 |
| NaverComp | `cF4002` | 매출총이익률, 영업이익률, 순이익률, EBITDA마진율, ROE, ROA, ROIC |
| NaverComp | `c1010001` | 52주베타, 업종PER, 수익률(1M/3M/6M/1Y) |
| NaverComp | `cF9001` | Sector comparison: PER, PBR, ROE, 매출증가율, 부채비율, 매출총이익률, 배당수익률 (vs sector vs market) |
| Polling API | `realtime` | EPS, BPS, cnsEps, DPS (numeric, not formatted) |

### 7. 수급/외국인 (Supply/Foreign)

| Source | Endpoint | Data | Period |
|--------|----------|------|--------|
| Mobile API | `/integration` | dealTrendInfos: 외국인/기관/개인 순매수 | 5 days |
| Mobile API | `/trend` | Same as above, more detail | 10 days |
| PC Finance | `frgn.naver` | 외국인/기관 순매매, 보유주수, 보유율 | Paginated |

### 8. 컨센서스 (Consensus)

| Source | Endpoint | Data |
|--------|----------|------|
| Mobile API | `/integration` | consensusInfo: recommMean (1-5), priceTargetMean |
| Mobile API | `/integration` | cnsPer, cnsEps (추정 PER/EPS) |
| Mobile API | `/finance/*` | isConsensus: "Y" columns = estimate data |
| NaverComp | `cF5001/cF5002` | Trend charts: target price, consensus over time |
| NaverComp | `cF3002` | DATA6 column + YEYOY = estimate year data |
| NaverComp | `cF1002` | 2 estimate years (E) in summary table |
| NaverComp | `cF9001` | FY1 column with (E) sector comparison |

### 9. 뉴스/공시 (News/Disclosure)

| Source | Endpoint | Data | Period |
|--------|----------|------|--------|
| Mobile API | `/disclosure` | DART 공시 목록 | ~20 items |
| Mobile API | `/integration` | researches: 증권사 리포트 | 5 items |

### 10. 섹터/업종 (Sector/Industry)

| Source | Endpoint | Data |
|--------|----------|------|
| Mobile API | `/integration` | industryCode, industryCompareInfo (6 peers) |
| NaverComp | `cF6001` | Industry header: market cap, fin type |
| NaverComp | `cF9001` | Full sector comparison: returns, valuations (5Y+1E), time-series cumulative returns (monthly, ~64 points) |
| NaverComp | `c1010001` | WICS sector name, KOSPI sector name |

---

## Implementation Priority for SEPA Pipeline

### Tier 1 - Already Implemented (fetch_naver_all.py)
- Mobile `/integration` (price, PER, EPS, consensus)
- Mobile `/finance/annual` and `/finance/quarter` (16 summary metrics)
- Mobile `corporationSummary`

### Tier 2 - High Value, Should Add
- **Chart API** (`fchart.stock.naver.com`): 1000+ days of OHLCV for SMA calculation
- **Mobile `/trend`**: 10 days of foreign/institution flow
- **NaverComp `cF9001`**: Sector-relative metrics (critical for sector strength scoring)
- **Polling API**: Clean numeric EPS/BPS/cnsEps values (no parsing needed)

### Tier 3 - Detailed Analysis
- **NaverComp `cF3002`**: 244-item granular financial statements (deep fundamental analysis)
- **NaverComp `cF4002`**: ROA, ROIC, EBITDA margin
- **NaverComp `c1010001`**: 52주베타, 수익률(1M/3M/6M/1Y), 업종PER

### Tier 4 - Nice to Have
- Mobile `/disclosure`: Corporate actions monitoring
- Mobile `/integration` researches: Analyst report tracking
- NaverComp `cF5001/cF5002`: Consensus trend visualization
- PC Finance `sise_day.naver`: Backup OHLCV source

---

## API Rate Limiting Notes

- Mobile API: No observed rate limit with reasonable delays (~0.5s between calls)
- NaverComp: Session-based auth, encparam rotates per session
- Chart API: No auth, XML response, appears unrestricted
- Polling API: Suggests 70-second polling interval (market closed)
- All endpoints require `User-Agent` header

---

## Encoding Notes

- Mobile API: UTF-8 JSON
- NaverComp AJAX: UTF-8 JSON (Content-Type says utf-8, confirmed working)
- NaverComp HTML: UTF-8
- Chart API: EUC-KR XML
- PC Finance: EUC-KR HTML
