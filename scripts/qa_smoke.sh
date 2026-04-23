#!/usr/bin/env bash
# QA smoke — test API endpoints, record status + latency
BASE="http://127.0.0.1:8300"
OUT="/tmp/qa_api_results.csv"
echo "category,endpoint,http,time_ms,bytes" > "$OUT"

check() {
  local cat="$1" path="$2" method="${3:-GET}" data="${4:-}"
  if [ "$method" = "POST" ]; then
    local resp=$(curl -s -o /tmp/qa_resp -w "%{http_code},%{time_total},%{size_download}" \
      -X POST -H "Content-Type: application/json" -d "$data" "$BASE$path" 2>/dev/null)
  else
    local resp=$(curl -s -o /tmp/qa_resp -w "%{http_code},%{time_total},%{size_download}" \
      "$BASE$path" 2>/dev/null)
  fi
  local http=$(echo "$resp" | cut -d, -f1)
  local t=$(echo "$resp" | cut -d, -f2)
  local bytes=$(echo "$resp" | cut -d, -f3)
  local t_ms=$(awk "BEGIN{printf \"%.0f\", $t*1000}")
  echo "$cat,$path,$http,$t_ms,$bytes" >> "$OUT"
  if [ "$http" != "200" ]; then
    echo "  [$cat] $path -> $http (${t_ms}ms)" >&2
    if [ -s /tmp/qa_resp ]; then head -c 300 /tmp/qa_resp >&2; echo >&2; fi
  fi
}

# Health / admin
check core /api/health
check admin /api/v1/admin/status
check admin /api/v1/admin/data_health
check admin /api/v1/admin/nightly_runs
check admin /api/v1/admin/weekly_runs
check admin /api/v1/admin/tenants
check admin /api/v1/admin/keys
check admin /api/v1/admin/audit

# Chartist
check chartist /api/v1/chartist/today
check chartist /api/v1/chartist/leaders
check chartist /api/v1/chartist/sectors
check chartist /api/v1/chartist/breadth
check chartist /api/v1/chartist/breakouts/52w
check chartist /api/v1/chartist/breakouts/near_52w
check chartist /api/v1/chartist/wizards
check chartist /api/v1/chartist/wizards/minervini
check chartist /api/v1/chartist/wizards/oneil
check chartist /api/v1/chartist/wizards/darvas
check chartist /api/v1/chartist/wizards/livermore
check chartist /api/v1/chartist/wizards/zanger
check chartist /api/v1/chartist/wizards/weinstein
check chartist /api/v1/chartist/flow
check chartist /api/v1/chartist/themes
check chartist /api/v1/chartist/shortint
check chartist /api/v1/chartist/kiwoom_cond
check chartist /api/v1/chartist/patterns
check chartist /api/v1/chartist/candlestick
check chartist /api/v1/chartist/divergence
check chartist /api/v1/chartist/ichimoku
check chartist /api/v1/chartist/vprofile
check chartist /api/v1/chartist/support
check chartist "/api/v1/chartist/ohlcv/005930?days=250"
check chartist /api/v1/chartist/backtest/list

# Quant
check quant /api/v1/quant/factors
check quant /api/v1/quant/academic/magic_formula
check quant /api/v1/quant/academic/deep_value
check quant /api/v1/quant/academic/fast_growth
check quant /api/v1/quant/academic/super_quant
check quant /api/v1/quant/smart_beta
check quant /api/v1/quant/universe
check quant /api/v1/quant/pit/005930
check quant /api/v1/quant/ic
check quant /api/v1/quant/macro/compass
check quant /api/v1/quant/macro/regime
check quant "/api/v1/quant/macro/series?source=fred&series_id=GDP"
check quant /api/v1/quant/macro/corr
check quant /api/v1/quant/macro/rotation

# Value
check value /api/v1/value/dcf/005930
check value /api/v1/value/wacc/005930
check value /api/v1/value/trend/005930
check value /api/v1/value/mos
check value /api/v1/value/deep_value
check value /api/v1/value/evebitda
check value /api/v1/value/roic
check value /api/v1/value/magic
check value /api/v1/value/piotroski
check value /api/v1/value/altman
check value /api/v1/value/insider
check value /api/v1/value/buyback
check value /api/v1/value/consensus
check value /api/v1/value/moat
check value /api/v1/value/segment
check value /api/v1/value/dividend
check value /api/v1/value/comparables
check value /api/v1/value/dps/005930
check value /api/v1/value/dividend_growth/005930
check value /api/v1/value/piotroski_full/005930
check value /api/v1/value/altman_full/005930
check value /api/v1/value/moat_v2
check value /api/v1/value/quality
check value /api/v1/value/fcf_yield
check value /api/v1/value/earnings_quality
check value /api/v1/value/peg
check value /api/v1/value/fnguide/005930
check value /api/v1/value/eps/005930

# Execute
check execute /api/v1/execute/health
check execute /api/v1/execute/overview
check execute /api/v1/execute/quote/005930
check execute /api/v1/execute/orderbook/005930
check execute /api/v1/execute/investor/005930
check execute /api/v1/execute/program/005930
check execute /api/v1/execute/fluctuation
check execute /api/v1/execute/stream/status

# Research
check research /api/v1/research/papers
check research /api/v1/research/ffactor
check research /api/v1/research/reproduce
check research "/api/v1/research/knowledge/search?q=circle+of+competence"
check research "/api/v1/research/buffett/search?q=moat"
check research "/api/v1/research/news?q=%EC%82%BC%EC%84%B1"
check research /api/v1/research/krreports
check research /api/v1/research/review/latest
check research "/api/v1/research/interviews/search?q=turtle"
check research "/api/v1/research/psychology/search?q=discipline"
check research "/api/v1/research/cycles/search?q=bubble"

# Assistant
check assistant /api/v1/assistant/chat POST '{"messages":[{"role":"user","content":"test"}]}'

# Bearer token 401
echo -n "tenant_auth_401," >> "$OUT"
curl -s -o /dev/null -w "/api/v1/chartist/today,%{http_code},%{time_total},%{size_download}\n" \
  -H "Authorization: Bearer ky_trial_invalid" "$BASE/api/v1/chartist/today" | awk '{gsub(/,/,","); print}' >> "$OUT"

echo "DONE"
wc -l "$OUT"
