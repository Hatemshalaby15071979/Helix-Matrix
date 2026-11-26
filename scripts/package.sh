#!/usr/bin/env bash
# Build a distributable tarball of the app (no caches, no personal learning state).
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

VERSION="$(tr -d '[:space:]' < VERSION)"
DIST="$DIR/dist"
OUT="$DIST/helix-matrix-${VERSION}.tar.gz"
rm -f "$OUT"
mkdir -p "$DIST"

tar \
  --exclude='*/__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='dist' \
  --exclude='learning-records/day-os' \
  --exclude='learning-records/quiz.json' \
  --exclude='learning-records/terms.json' \
  --exclude='learning-records/weekly' \
  --exclude='learning-records/day-notes' \
  --exclude='learning-records/metacognition/decisions.json' \
  -czf "$OUT" \
  app assets lessons reference data server tests scripts deploy docs .github \
  README.md CHANGELOG.md LICENSE VERSION

echo "packed: $OUT"
