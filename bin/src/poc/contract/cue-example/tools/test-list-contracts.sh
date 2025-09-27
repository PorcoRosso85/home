#!/usr/bin/env bash
set -euo pipefail

# Test script for contract file enumeration
echo "🧪 Testing contract file enumeration..."

# Test 1: Generate index.json
echo "Test 1: Generating index.json..."
nix-instantiate --eval --json tools/list-contracts.nix > tools/index.json.tmp

# Test 2: Verify JSON structure
echo "Test 2: Verifying JSON structure..."
if ! jq empty tools/index.json.tmp 2>/dev/null; then
    echo "❌ Invalid JSON format"
    exit 1
fi

# Test 3: Check for contract files
echo "Test 3: Checking for contract files..."
CONTRACTS=$(jq -r '.[]' tools/index.json.tmp | grep -c "contract.cue" || true)
if [ "$CONTRACTS" -eq 0 ]; then
    echo "❌ No contract.cue files found"
    exit 1
fi

# Test 4: Verify sorting (UTF-8 lexicographic)
echo "Test 4: Verifying sort order..."
jq -r '.[]' tools/index.json.tmp > tools/actual_order.tmp
sort tools/actual_order.tmp > tools/expected_order.tmp

if ! diff tools/actual_order.tmp tools/expected_order.tmp; then
    echo "❌ Files not sorted correctly"
    exit 1
fi

# Test 5: Check for duplicates
echo "Test 5: Checking for duplicates..."
UNIQUE_COUNT=$(jq -r '.[]' tools/index.json.tmp | sort | uniq | wc -l)
TOTAL_COUNT=$(jq -r '.[]' tools/index.json.tmp | wc -l)

if [ "$UNIQUE_COUNT" -ne "$TOTAL_COUNT" ]; then
    echo "❌ Duplicate entries found"
    exit 1
fi

# Test 6: Verify paths exist
echo "Test 6: Verifying all paths exist..."
while IFS= read -r path; do
    if [ ! -f "$path" ]; then
        echo "❌ File does not exist: $path"
        exit 1
    fi
done < <(jq -r '.[]' tools/index.json.tmp)

# Cleanup temporary files
rm -f tools/*.tmp

echo "✅ All tests passed!"
echo "📄 Found $TOTAL_COUNT contract files"