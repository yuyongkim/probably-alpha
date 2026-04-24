#!/usr/bin/env bash
# Overnight RAG rebuild orchestrator.
#
# Waits for broker TF-IDF build (PID-based or meta.json timestamp) to finish,
# then kicks off the dense-vector rebuild so rag_broker_vec stays in sync.
#
# Usage (already running scripts/build_rag_broker.py in background):
#     bash scripts/overnight_rag_chain.sh
#
# Success = both indexes updated with today's (or newer) built_at.

set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
META="$HOME/.ky-platform/data/rag_broker/meta.json"
START_MTIME=$(stat -c %Y "$META" 2>/dev/null || echo 0)
LOG_DIR="$HOME/.ky-platform/data/ops"
mkdir -p "$LOG_DIR"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG="$LOG_DIR/overnight_rag_chain_$STAMP.log"

echo "[chain] started $STAMP" | tee -a "$LOG"
echo "[chain] waiting for rag_broker/meta.json mtime to advance past $START_MTIME" | tee -a "$LOG"

# Poll until meta.json is newer than when we started (broker TF-IDF completed).
# Bail out after 6 hours — if it hasn't finished by then, something is wrong.
DEADLINE=$(( $(date +%s) + 21600 ))
while :; do
  NOW_MTIME=$(stat -c %Y "$META" 2>/dev/null || echo 0)
  if [ "$NOW_MTIME" -gt "$START_MTIME" ]; then
    echo "[chain] broker TF-IDF rebuild complete (meta mtime $NOW_MTIME)" | tee -a "$LOG"
    break
  fi
  if [ "$(date +%s)" -gt "$DEADLINE" ]; then
    echo "[chain] 6h deadline exceeded; bailing" | tee -a "$LOG"
    exit 2
  fi
  sleep 120
done

# Run the dense vector rebuild against the freshly-built TF-IDF corpus.
echo "[chain] starting build_rag_broker_vec.py" | tee -a "$LOG"
cd "$ROOT"
python -u scripts/build_rag_broker_vec.py --device cuda 2>&1 | tee -a "$LOG"
RC=$?
echo "[chain] done rc=$RC at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LOG"
exit $RC
