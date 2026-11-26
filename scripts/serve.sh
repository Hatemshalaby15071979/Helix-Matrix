#!/usr/bin/env bash
# Start the Helix-Matrix server detached, with its own log file.
# Safe to run twice: it checks whether the page is already live.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="${HELIX_MATRIX_LOG:-/tmp/opencode/helix-matrix.log}"
URL="http://127.0.0.1:8765/"

if curl -fsS --max-time 2 "$URL" >/dev/null 2>&1; then
  echo "Helix-Matrix already live at $URL"
  exit 0
fi

mkdir -p "$(dirname "$LOG")"
cd "$DIR"
setsid nohup python3 server/os_server.py >"$LOG" 2>&1 < /dev/null &
echo "Helix-Matrix started at $URL (log: $LOG)"
