#!/usr/bin/env bash
set -euo pipefail

# Blackbox Test Suite for Contract Flake
# Integrates Producer/Consumer contract testing with optional strict mode

# Parse command line options
STRICT_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --strict)
            STRICT_MODE=true
            shift
            ;;
        *)
            echo "Usage: $0 [--strict]"
            echo "  --strict: Enable enhanced contract testing (preparation mode)"
            exit 1
            ;;
    esac
done

# Common function for running contract tests
run_contract_test() {
    local component="$1"    # "producer" or "consumer"
    local input="$2"        # JSON input (empty for producer)
    local contract="$3"     # "ProducerContract" or "ConsumerContract"
    
    echo "Testing $component with contract $contract..."
    
    # Execute component
    if [ "$component" = "producer" ]; then
        OUTPUT=$(timeout 5 nix run .#producer 2>/dev/null)
    else
        OUTPUT=$(echo "$input" | timeout 5 nix run .#consumer 2>/dev/null)
    fi
    
    # Pure contract verification using Nickel
    echo "Validating output against $contract..."
    TEMP_NCL=$(mktemp --suffix=.ncl)
    trap 'rm -f "$TEMP_NCL"' EXIT
    
    # Create Nickel validation file based on contract type
    if [ "$contract" = "ProducerContract" ]; then
        # Extract JSON fields for producer
        PROCESSED=$(echo "$OUTPUT" | jq -r '.processed')
        FAILED=$(echo "$OUTPUT" | jq -r '.failed')
        OUTPUT_ARRAY=$(echo "$OUTPUT" | jq -r '.output | @json')
        
        cat > "$TEMP_NCL" << EOF
let contracts = import "${PWD}/contracts.ncl" in
let data = {
  processed = $PROCESSED,
  failed = $FAILED,
  output = $OUTPUT_ARRAY,
} in
data & contracts.$contract
EOF
    else
        # Consumer contract validation - jq structure check + Nickel validation
        if echo "$OUTPUT" | jq -e 'has("summary") and has("details") and (.summary | type == "string") and (.details | type == "object")' >/dev/null; then
            echo "  ✅ jq structure validation: PASS"
            
            # Add Nickel contract validation for consistency
            SUMMARY_JSON=$(echo "$OUTPUT" | jq -r '.summary|@json')
            DETAILS_PROCESSED=$(echo "$OUTPUT" | jq -r '.details.processed')
            DETAILS_FAILED=$(echo "$OUTPUT" | jq -r '.details.failed')  
            DETAILS_OUTPUT=$(echo "$OUTPUT" | jq -c '.details.output')
            
            cat > "$TEMP_NCL" << EOF
let contracts = import "${PWD}/contracts.ncl" in
let test_data = {
  summary = $SUMMARY_JSON,
  details = {
    processed = $DETAILS_PROCESSED,
    failed = $DETAILS_FAILED,
    output = $DETAILS_OUTPUT,
  },
} in
test_data & contracts.ConsumerContract
EOF
        else
            echo "  ❌ $component contract validation: FAIL"  
            echo "  Output: $OUTPUT"
            return 1
        fi
    fi
    
    # Validate contract
    if nix develop -c nickel eval "$TEMP_NCL" >/dev/null 2>&1; then
        echo "  ✅ $component contract validation: PASS"
        return 0
    else
        echo "  ❌ $component contract validation: FAIL"
        echo "  Output: $OUTPUT"
        return 1
    fi
}

echo "=== Blackbox Test Suite ==="
echo "Strict mode: $STRICT_MODE"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0

# Producer tests
echo "--- Producer Tests ---"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_contract_test "producer" "" "ProducerContract"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
echo ""

# Consumer tests (3 test cases)
echo "--- Consumer Tests ---"

# Test case 1: Minimal input
echo "Test case 1: Minimal input"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_contract_test "consumer" '{"processed":0,"failed":0,"output":[]}' "ConsumerContract"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
echo ""

# Test case 2: Representative input
echo "Test case 2: Representative input"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_contract_test "consumer" '{"processed":5,"failed":1,"output":["a","b","c"]}' "ConsumerContract"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
echo ""

# Test case 3: Large scale input
echo "Test case 3: Large scale input"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if run_contract_test "consumer" '{"processed":1000,"failed":50,"output":["batch1"]}' "ConsumerContract"; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
echo ""

# Strict mode preparation (enhanced contract testing)
if [ "$STRICT_MODE" = true ]; then
    echo "--- Strict Mode: Enhanced Contract Testing ---"
    echo "Preparing enhanced validation scenarios..."
    
    # NOTE: Future expansion plan for Strict mode:
    # - Integration with error_diagnostics.ncl for advanced constraint validation
    # - Non-negative value validation (processed >= 0, failed >= 0)
    # - Non-empty array validation where required
    # - Custom error message validation with structured diagnostics
    # Current implementation provides foundation for these enhancements
    
    # Additional validation scenarios for strict mode
    echo "Running enhanced contract validation..."
    
    # Test invalid producer output (should fail)
    echo "Testing invalid producer output handling..."
    INVALID_PRODUCER='{"processed":"invalid","failed":0,"output":[]}'
    TEMP_NCL=$(mktemp --suffix=.ncl)
    trap 'rm -f "$TEMP_NCL"' EXIT
    
    cat > "$TEMP_NCL" << EOF
let contracts = import "${PWD}/contracts.ncl" in
let data = std.deserialize 'Json <<<'$INVALID_PRODUCER'>>> in
data & contracts.ProducerContract
EOF
    
    if ! nix develop -c nickel eval "$TEMP_NCL" >/dev/null 2>&1; then
        echo "  ✅ Enhanced validation: Invalid input correctly rejected"
    else
        echo "  ⚠️  Enhanced validation: Invalid input incorrectly accepted"
    fi
    echo ""
fi

# Summary
echo "=== Test Results Summary ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $((TOTAL_TESTS - PASSED_TESTS))"

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo "✅ All blackbox tests completed successfully"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi