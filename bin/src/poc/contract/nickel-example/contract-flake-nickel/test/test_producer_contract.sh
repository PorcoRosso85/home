#!/usr/bin/env bash
set -euo pipefail

echo "=== Producer Contract Test ==="

# Producer実行（内部実装は問わない）
OUTPUT=$(timeout 5 nix run .#producer 2>/dev/null)

# 契約準拠を検証
echo "Validating producer output against contract..."
TEMP_NCL=$(mktemp --suffix=.ncl)
trap 'rm -f "$TEMP_NCL"' EXIT

# Extract JSON fields using jq and convert to Nickel format
PROCESSED=$(echo "$OUTPUT" | jq -r '.processed')
FAILED=$(echo "$OUTPUT" | jq -r '.failed')
OUTPUT_ARRAY=$(echo "$OUTPUT" | jq -r '.output | @json')

# Create Nickel evaluation file with extracted data
cat > "$TEMP_NCL" << EOF
let contracts = import "${PWD}/contracts.ncl" in
let data = {
  processed = $PROCESSED,
  failed = $FAILED,
  output = $OUTPUT_ARRAY,
} in
data & contracts.ProducerContract
EOF

nix develop -c nickel eval "$TEMP_NCL"

if [ $? -eq 0 ]; then
    echo "✅ Producer contract: PASS"
else
    echo "❌ Producer contract: FAIL"
    exit 1
fi