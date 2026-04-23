#!/usr/bin/env bash
# Page smoke — test all Next.js routes
BASE="http://127.0.0.1:8380"
OUT="/tmp/qa_pages_results.csv"
echo "route,http,time_ms,bytes" > "$OUT"

while IFS= read -r route; do
  # Use "/" for index (empty path)
  [ -z "$route" ] && route="/"
  local_path="$route"
  resp=$(curl -s -o /tmp/qa_resp_p -w "%{http_code},%{time_total},%{size_download}" \
    -H "User-Agent: QA-smoke" "$BASE$local_path" 2>/dev/null)
  http=$(echo "$resp" | cut -d, -f1)
  t=$(echo "$resp" | cut -d, -f2)
  bytes=$(echo "$resp" | cut -d, -f3)
  t_ms=$(awk "BEGIN{printf \"%.0f\", $t*1000}")
  echo "$route,$http,$t_ms,$bytes" >> "$OUT"
  if [ "$http" != "200" ]; then
    echo "  [page] $route -> $http (${t_ms}ms)" >&2
  fi
done < /tmp/pages.txt

echo "DONE"
awk -F, 'NR>1 {c[$2]++} END{for(k in c) printf "  %s : %d\n", k, c[k]}' "$OUT"
