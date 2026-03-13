#!/usr/bin/env bash
# Export a Figma node screenshot to a local PNG file with white background.
#
# Usage:
#   ./export_screenshot.sh <node-id> <output-filename> [file-key]
#
# Arguments:
#   node-id         Figma node ID (e.g., "38435:3910904" or "38435-3910904")
#   output-filename Output filename without extension (saved to artifacts/figma/)
#   file-key        Optional Figma file key (defaults to Noveo-TTT)
#
# Prerequisites:
#   - Figma PAT in .claude/context/secrets/figma-token.txt
#   - Node.js with sharp installed in /tmp (run: cd /tmp && npm install sharp)

set -euo pipefail

NODE_ID="${1:?Usage: $0 <node-id> <output-filename> [file-key]}"
OUTPUT_NAME="${2:?Usage: $0 <node-id> <output-filename> [file-key]}"
FILE_KEY="${3:-H2aXBseq7Ui60zlh5vhyjy}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

TOKEN_FILE="$PROJECT_DIR/.claude/context/secrets/figma-token.txt"
if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Error: Figma token not found at $TOKEN_FILE" >&2
  exit 1
fi
FIGMA_TOKEN=$(cat "$TOKEN_FILE")

OUTPUT_DIR="$PROJECT_DIR/artifacts/figma"
mkdir -p "$OUTPUT_DIR"
OUTPUT_PATH="$OUTPUT_DIR/${OUTPUT_NAME}.png"

# Normalize node ID: accept both 38435-3910904 and 38435:3910904
NODE_ID_API="${NODE_ID//-/:}"

echo "Fetching export URL for node $NODE_ID_API..."
IMAGE_URL=$(curl -s \
  -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/$FILE_KEY?ids=$NODE_ID_API&format=png&scale=2" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(list(d['images'].values())[0])")

if [[ -z "$IMAGE_URL" || "$IMAGE_URL" == "None" ]]; then
  echo "Error: Failed to get image URL from Figma API" >&2
  exit 1
fi

echo "Downloading PNG..."
TEMP_PATH="/tmp/figma_export_$$.png"
curl -s -o "$TEMP_PATH" "$IMAGE_URL"

echo "Flattening transparency to white background..."
cd /tmp && node -e "
const sharp = require('sharp');
sharp('$TEMP_PATH')
  .flatten({ background: '#ffffff' })
  .toFile('${OUTPUT_PATH}')
  .then(() => {
    console.log('OK');
    require('fs').unlinkSync('$TEMP_PATH');
  })
  .catch(e => { console.error(e); process.exit(1); });
"

echo "Saved: $OUTPUT_PATH"
file "$OUTPUT_PATH"
ls -lh "$OUTPUT_PATH"
