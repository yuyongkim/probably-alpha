#!/usr/bin/env bash
# register_scheduler.sh
# Installs ky-platform nightly (daily 02:00) + weekly (Sunday 04:00) runners
# into the current user's crontab. Intended for WSL and macOS.
#
# Usage:
#     bash scripts/register_scheduler.sh
# or pipe:
#     bash scripts/register_scheduler.sh --show    # show the entries only
#
# The script is idempotent: it removes any existing ky-platform-* lines
# before appending the new ones.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$(command -v python3 || command -v python)"

if [[ -z "$PY" ]]; then
    echo "ERROR: python not found on PATH" >&2
    exit 1
fi

NIGHTLY="$REPO_ROOT/scripts/nightly.py"
WEEKLY="$REPO_ROOT/scripts/weekly.py"

[[ -f "$NIGHTLY" ]] || { echo "ERROR: $NIGHTLY missing" >&2; exit 1; }
[[ -f "$WEEKLY"  ]] || { echo "ERROR: $WEEKLY missing"  >&2; exit 1; }

NIGHTLY_LINE="0 2 * * *   $PY $NIGHTLY   # ky-platform-nightly"
WEEKLY_LINE="0 4 * * 0   $PY $WEEKLY    # ky-platform-weekly"

if [[ "${1:-}" == "--show" ]]; then
    echo "$NIGHTLY_LINE"
    echo "$WEEKLY_LINE"
    exit 0
fi

# Preserve the existing crontab minus our lines, then append ours.
existing="$(crontab -l 2>/dev/null || true)"
filtered="$(printf '%s\n' "$existing" | grep -v 'ky-platform-nightly' | grep -v 'ky-platform-weekly' || true)"

{
    if [[ -n "$filtered" ]]; then
        printf '%s\n' "$filtered"
    fi
    printf '%s\n' "$NIGHTLY_LINE"
    printf '%s\n' "$WEEKLY_LINE"
} | crontab -

echo "Installed. Current ky-platform crontab entries:"
crontab -l | grep 'ky-platform-' || true

echo
echo "To remove:"
echo "    crontab -l | grep -v 'ky-platform-' | crontab -"
