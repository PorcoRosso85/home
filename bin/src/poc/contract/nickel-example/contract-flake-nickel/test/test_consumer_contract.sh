#!/usr/bin/env bash
set -euo pipefail

echo "=== Consumer Contract Tests ==="

test_consumer_contract() {
    local test_name="$1"
    local input="$2"
    echo "Test: $test_name"
    
    # Consumer実行
    OUTPUT=$(echo "$input" | timeout 5 nix run .#consumer 2>/dev/null)
    
    # 契約検証 - ConsumerContractの構造をチェック
    # Check if output has required fields: summary (string) and details (object)
    if echo "$OUTPUT" | jq -e 'has("summary") and has("details") and (.summary | type == "string") and (.details | type == "object")' >/dev/null; then
        echo "  ✅ PASS - jq structure validation"
    else
        echo "  ❌ FAIL - jq structure validation"
        echo "  Expected: {summary: String, details: Record}"
        echo "  Got: $OUTPUT"
        return 1
    fi
    
    # Nickel contract validation for consistency
    TEMP_NCL=$(mktemp --suffix=.ncl)
    trap 'rm -f "$TEMP_NCL"' EXIT
    
    # Extract values properly for Nickel syntax
    SUMMARY_JSON=$(echo "$OUTPUT" | jq -r '.summary|@json')
    PROCESSED=$(echo "$OUTPUT" | jq -r '.details.processed')
    FAILED=$(echo "$OUTPUT" | jq -r '.details.failed')
    OUTPUT_ARR=$(echo "$OUTPUT" | jq -c '.details.output')
    
    cat > "$TEMP_NCL" << EOF
let contracts = import "${PWD}/contracts.ncl" in
let test_data = {
  summary = $SUMMARY_JSON,
  details = {
    processed = $PROCESSED,
    failed = $FAILED,
    output = $OUTPUT_ARR,
  }
} in
test_data & contracts.ConsumerContract
EOF
    
    if nix develop -c nickel eval "$TEMP_NCL" >/dev/null 2>&1; then
        echo "  ✅ PASS - Nickel contract validation"
    else
        echo "  ❌ FAIL - Nickel contract validation"
        return 1
    fi
}

# 3つのテストケース
test_consumer_contract "Minimal input" '{"processed":0,"failed":0,"output":[]}'
test_consumer_contract "Representative input" '{"processed":5,"failed":1,"output":["a","b","c"]}'
test_consumer_contract "Large scale input" '{"processed":1000,"failed":50,"output":["batch1","batch2","batch3","batch4"]}'

echo ""
echo "=== All Consumer Contract Tests Completed ==="