#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Build the release zip (spec DST-001, DST-003, DST-004).
# Usage: scripts/build_zip.sh [version]   e.g. scripts/build_zip.sh 0.1.0
set -euo pipefail

DOMAIN="thermogeist"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/custom_components/$DOMAIN"
OUT_DIR="$ROOT/dist"
VERSION="${1:-}"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp -R "$SRC/." "$STAGE/"
find "$STAGE" -name "__pycache__" -type d -prune -exec rm -rf {} +
find "$STAGE" -name "*.pyc" -delete
cp "$ROOT/LICENSE" "$STAGE/LICENSE"

if [[ -n "$VERSION" ]]; then
  python3 - "$STAGE/manifest.json" "$VERSION" <<'PY'
import json, sys
path, version = sys.argv[1], sys.argv[2]
with open(path, encoding="utf-8") as f:
    manifest = json.load(f)
manifest["version"] = version
with open(path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
PY
fi

mkdir -p "$OUT_DIR"
rm -f "$OUT_DIR/$DOMAIN.zip"
(cd "$STAGE" && zip -qr "$OUT_DIR/$DOMAIN.zip" .)
echo "Built $OUT_DIR/$DOMAIN.zip${VERSION:+ (version $VERSION)}"
