#!/usr/bin/env bash
# Start Helix-Matrix and open it in the browser.
# Safe to run twice: serve.sh leaves an already-live server alone.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="http://127.0.0.1:8765/"
LOG="/tmp/opencode/helix-matrix.log"

say() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "Helix-Matrix" "$1" || true
  fi
  printf '%s\n' "$1" >&2
}

if [[ ! -x "$ROOT/scripts/serve.sh" ]]; then
  say "This checkout is missing scripts/serve.sh — restore it before starting."
  exit 1
fi

bash "$ROOT/scripts/serve.sh"

for _ in $(seq 1 40); do
  if curl -fsS --max-time 1 "$URL" >/dev/null 2>&1; then
    xdg-open "$URL"
    exit 0
  fi
  sleep 0.25
done

say "The app did not come up. See $LOG"
exit 1
