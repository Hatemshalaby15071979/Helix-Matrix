#!/usr/bin/env bash
# Verify the checkout: tests, compilation, JS syntax, JSON, version consistency.
# Exit 0 only when everything passes.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "==> test suite"
python3 -m pytest tests/ -q

echo "==> byte-compile the server"
python3 -m py_compile server/os_server.py server/os_engine.py

echo "==> syntax-check the client JS"
for f in assets/js/*.js; do node --check "$f"; done

echo "==> validate JSON data files"
python3 - <<'PY'
import json, pathlib
for p in sorted(pathlib.Path("data").glob("*.json")):
    json.loads(p.read_text(encoding="utf-8"))
    print(f"ok: {p}")
PY

echo "==> root-document hygiene (GOVERNANCE.md section 2)"
python3 scripts/check_root_docs.py
python3 scripts/check_root_docs.py --self-test

echo "==> confirm version strings agree"
VERSION="$(tr -d '[:space:]' < VERSION)"
# The server header carries the major.minor version (e.g. "1.0" from "1.0.0").
SHORT="${VERSION%.*}"
grep -q "HelixMatrix/${SHORT}" server/os_server.py \
  || { echo "FAIL: server header version != VERSION ($SHORT expected from $VERSION)"; exit 1; }
echo "version consistent: $SHORT (from $VERSION)"

echo "ALL CHECKS PASSED"
