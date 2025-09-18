#!/usr/bin/env bash
set -euo pipefail

# Ensure we're in the correct directory
cd "$(dirname "$0")/.."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test result tracking
declare -a TEST_RESULTS=()

# Helper function to log test results
log_test() {
    local test_name="$1"
    local status="$2"
    local message="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if [[ "$status" == "PASS" ]]; then
        echo -e "${GREEN}✅ $test_name: PASS${NC} - $message"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("PASS: $test_name")
    elif [[ "$status" == "FAIL" ]]; then
        echo -e "${RED}❌ $test_name: FAIL${NC} - $message"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("FAIL: $test_name")
    else
        echo -e "${YELLOW}⚠️  $test_name: $status${NC} - $message"
        TEST_RESULTS+=("$status: $test_name")
    fi
}

# Function to run a timed test
run_timed_test() {
    local test_name="$1"
    local command="$2"
    local timeout_seconds="$3"
    
    local start_time=$(date +%s%N)
    
    if timeout "$timeout_seconds" bash -c "$command" >/dev/null 2>&1; then
        local end_time=$(date +%s%N)
        local duration_ms=$(((end_time - start_time) / 1000000))
        log_test "$test_name" "PASS" "Completed in ${duration_ms}ms (within ${timeout_seconds}s limit)"
        return 0
    else
        local end_time=$(date +%s%N)
        local duration_ms=$(((end_time - start_time) / 1000000))
        log_test "$test_name" "FAIL" "Timed out or failed after ${duration_ms}ms (limit: ${timeout_seconds}s)"
        return 1
    fi
}

# Function to test contract validation with Nickel
test_contract_validation() {
    local test_name="$1"
    local test_data="$2"
    local should_pass="$3"
    
    local temp_file="./test_temp_$(date +%s%N).ncl"
    cat > "$temp_file" << EOF
let error_diagnostics = import "error_diagnostics.ncl" in
let test_data = $test_data in
error_diagnostics.validate_with_diagnostics test_data
EOF
    
    if nix develop -c nickel eval "$temp_file" >/dev/null 2>/dev/null; then
        if [[ "$should_pass" == "true" ]]; then
            log_test "$test_name" "PASS" "Valid data correctly accepted"
        else
            log_test "$test_name" "FAIL" "Invalid data incorrectly accepted"
        fi
    else
        if [[ "$should_pass" == "false" ]]; then
            log_test "$test_name" "PASS" "Invalid data correctly rejected"
        else
            log_test "$test_name" "FAIL" "Valid data incorrectly rejected"
        fi
    fi
    
    rm -f "$temp_file"
}

# Function to test basic contract validation
test_basic_validation() {
    local test_name="$1"
    local test_data="$2"
    local should_pass="$3"
    
    local temp_file="./test_temp_$(date +%s%N).ncl"
    cat > "$temp_file" << EOF
let contracts = import "contracts.ncl" in
let test_data = $test_data in
test_data & contracts.ProducerContract
EOF
    
    if nix develop -c nickel eval "$temp_file" >/dev/null 2>/dev/null; then
        if [[ "$should_pass" == "true" ]]; then
            log_test "$test_name" "PASS" "Valid data correctly accepted"
        else
            log_test "$test_name" "FAIL" "Invalid data incorrectly accepted"  
        fi
    else
        if [[ "$should_pass" == "false" ]]; then
            log_test "$test_name" "PASS" "Invalid data correctly rejected"
        else
            log_test "$test_name" "FAIL" "Valid data incorrectly rejected"
        fi
    fi
    
    rm -f "$temp_file"
}

# Function to test pipeline flow
test_pipeline_flow() {
    local test_name="$1"
    local producer_data="$2"
    local expected_consumer_response="$3"
    
    local temp_producer="./test_temp_producer_$(date +%s%N).ncl"
    
    # Create temporary producer that outputs specific data
    cat > "$temp_producer" << EOF
let contracts = import "contracts.ncl" in
$producer_data & contracts.ProducerContract
EOF
    
    # Test the producer part first
    if producer_output=$(nix develop -c nickel export --format json "$temp_producer" 2>/dev/null); then
        # Extract JSON from output (everything after the header lines)
        json_output=$(echo "$producer_output" | sed -n '/^{/,$p')
        if [[ -n "$json_output" ]] && echo "$json_output" | jq . >/dev/null 2>&1; then
            log_test "$test_name" "PASS" "Producer generated valid JSON output"
        else
            log_test "$test_name" "FAIL" "Producer generated invalid JSON"
        fi
    else
        log_test "$test_name" "FAIL" "Producer failed to generate valid output"
    fi
    
    rm -f "$temp_producer"
}

# Function to test simple consumer with static input
test_consumer_basic() {
    local test_name="$1"
    
    # Test consumer with a simple hardcoded input that doesn't conflict with Nickel syntax
    local temp_consumer_test="./test_temp_consumer_$(date +%s%N).ncl"
    cat > "$temp_consumer_test" << 'EOF'
let contracts = import "contracts.ncl" in
{
  summary = "Test processed data",
  details = { processed = 5, failed = 1, output = ["test"] },
} & contracts.ConsumerContract
EOF
    
    if nix develop -c nickel export --format json "$temp_consumer_test" >/dev/null 2>&1; then
        log_test "$test_name" "PASS" "Consumer contract validation works"
    else
        log_test "$test_name" "FAIL" "Consumer contract validation failed"
    fi
    
    rm -f "$temp_consumer_test"
}

# Function to generate performance test data
generate_test_data() {
    local count=$1
    local output_array=""
    
    for i in $(seq 1 $count); do
        if [[ $i -eq 1 ]]; then
            output_array="\"item-$i\""
        else
            output_array="$output_array, \"item-$i\""
        fi
    done
    
    echo "{
        processed = $count,
        failed = 0,
        output = [$output_array],
    }"
}

echo "🧪 Starting Nickel Contract Pipeline Tests"
echo "=========================================="

# Test 1: Contract Type Checking
echo -e "\n${YELLOW}📋 Contract Type Checking Tests${NC}"
if nix develop -c nickel typecheck contracts.ncl >/dev/null 2>&1; then
    log_test "Contract Typecheck" "PASS" "All contracts are type-safe"
else
    log_test "Contract Typecheck" "FAIL" "Contract type checking failed"
fi

# Test 2: Basic Producer/Consumer Flow
echo -e "\n${YELLOW}🔄 Basic Pipeline Flow Tests${NC}"

test_pipeline_flow "Valid Pipeline Flow" "{
    processed = 10,
    failed = 0,
    output = [\"a\", \"b\", \"c\"],
}" "success"

test_pipeline_flow "Valid Pipeline with Failures" "{
    processed = 8,
    failed = 2,
    output = [\"item1\", \"item2\"],
}" "success"

# Test 3: Contract Validation Tests (Normal Cases)
echo -e "\n${YELLOW}✅ Normal Case Contract Validation${NC}"

test_basic_validation "Valid Producer Data" "{
    processed = 10,
    failed = 0,
    output = [\"a\", \"b\", \"c\"],
}" "true"

test_basic_validation "Valid Producer with Failures" "{
    processed = 5,
    failed = 3,
    output = [\"item1\", \"item2\"],
}" "true"

test_basic_validation "Valid Zero Processing" "{
    processed = 0,
    failed = 0,
    output = [\"placeholder\"],
}" "true"

# Test consumer validation
test_consumer_basic "Consumer Contract Validation"

# Test 4: Error Detection Tests (Abnormal Cases)
echo -e "\n${YELLOW}❌ Error Detection Tests${NC}"

# Function to test enhanced contract validation
test_enhanced_validation() {
    local test_name="$1"
    local test_data="$2"
    local should_pass="$3"
    
    local temp_file="./test_temp_enhanced_$(date +%s%N).ncl"
    cat > "$temp_file" << EOF
let error_diagnostics = import "error_diagnostics.ncl" in
let test_data = $test_data in
test_data & error_diagnostics.ProducerContractWithDiagnostics
EOF
    
    if nix develop -c nickel eval "$temp_file" >/dev/null 2>/dev/null; then
        if [[ "$should_pass" == "true" ]]; then
            log_test "$test_name" "PASS" "Valid data correctly accepted"
        else
            log_test "$test_name" "FAIL" "Invalid data incorrectly accepted"
        fi
    else
        if [[ "$should_pass" == "false" ]]; then
            log_test "$test_name" "PASS" "Invalid data correctly rejected"
        else
            log_test "$test_name" "FAIL" "Valid data incorrectly rejected"
        fi
    fi
    
    rm -f "$temp_file"
}

test_enhanced_validation "Negative Processed Count" "{
    processed = -1,
    failed = 0,
    output = [\"a\"],
}" "false"

test_enhanced_validation "Negative Failed Count" "{
    processed = 10,
    failed = -5,
    output = [\"a\", \"b\"],
}" "false"

test_enhanced_validation "Empty Output Array" "{
    processed = 10,
    failed = 0,
    output = [],
}" "false"

test_basic_validation "Missing Required Field" "{
    failed = 0,
    output = [\"a\", \"b\"],
}" "false"

test_basic_validation "Wrong Type for Processed" "{
    processed = \"not_a_number\",
    failed = 0,
    output = [\"a\"],
}" "false"

# Test 5: Error Diagnostics Integration
echo -e "\n${YELLOW}🔍 Error Diagnostics Tests${NC}"

# Test specific error diagnostic scenarios
temp_error_test="./test_temp_error_$(date +%s%N).ncl"
cat > "$temp_error_test" << 'EOF'
let error_diagnostics = import "error_diagnostics.ncl" in
error_diagnostics.invalid_data_examples.negative_processed 
  & error_diagnostics.ProducerContractWithDiagnostics
EOF

if ! nix develop -c nickel eval "$temp_error_test" >/dev/null 2>&1; then
    log_test "Negative Value Detection" "PASS" "Error diagnostics correctly caught negative value"
else
    log_test "Negative Value Detection" "FAIL" "Error diagnostics missed negative value"
fi
rm -f "$temp_error_test"

# Test 6: Performance Tests
echo -e "\n${YELLOW}⚡ Performance Tests${NC}"

# Test with 100 items in 1 second
test_data_100=$(generate_test_data 100)
run_timed_test "100 Items Validation" "
    temp_perf=\"./test_temp_perf_100_\$(date +%s%N).ncl\"
    cat > \"\$temp_perf\" << 'PERF_EOF'
let contracts = import \"contracts.ncl\" in
$test_data_100 & contracts.ProducerContract
PERF_EOF
    nix develop -c nickel eval \"\$temp_perf\" > /dev/null
    rm -f \"\$temp_perf\"
" 1

# Test with 50 items for comparison
test_data_50=$(generate_test_data 50)
run_timed_test "50 Items Validation" "
    temp_perf=\"./test_temp_perf_50_\$(date +%s%N).ncl\"
    cat > \"\$temp_perf\" << 'PERF_EOF'
let contracts = import \"contracts.ncl\" in
$test_data_50 & contracts.ProducerContract
PERF_EOF
    nix develop -c nickel eval \"\$temp_perf\" > /dev/null
    rm -f \"\$temp_perf\"
" 1

# Test with 10 items for basic performance
test_data_10=$(generate_test_data 10)
run_timed_test "10 Items Validation" "
    temp_perf=\"./test_temp_perf_10_\$(date +%s%N).ncl\"
    cat > \"\$temp_perf\" << 'PERF_EOF'
let contracts = import \"contracts.ncl\" in
$test_data_10 & contracts.ProducerContract
PERF_EOF
    nix develop -c nickel eval \"\$temp_perf\" > /dev/null
    rm -f \"\$temp_perf\"
" 1

# Test 7: Edge Cases
echo -e "\n${YELLOW}🎯 Edge Case Tests${NC}"

test_basic_validation "Large Numbers" "{
    processed = 999999,
    failed = 888888,
    output = [\"item1\"],
}" "true"

test_basic_validation "Single Item Output" "{
    processed = 1,
    failed = 0,
    output = [\"single\"],
}" "true"

test_basic_validation "All Processing Failed" "{
    processed = 0,
    failed = 100,
    output = [\"error_log\"],
}" "true"

# Test 8: Integration with nix flake check
echo -e "\n${YELLOW}🛠️  Nix Integration Tests${NC}"

if nix flake check --no-build >/dev/null 2>&1; then
    log_test "Nix Flake Check" "PASS" "All flake checks passed"
else
    log_test "Nix Flake Check" "FAIL" "Nix flake check failed"
fi

# Test Summary
echo -e "\n${YELLOW}📊 Test Results Summary${NC}"
echo "=========================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

# Cleanup any remaining test files
rm -f ./test_temp_*.ncl

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "\n${GREEN}🎉 All tests passed! The Nickel contract system is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some tests failed. Please review the failures above.${NC}"
    echo -e "\n${YELLOW}Failed Tests:${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        if [[ "$result" =~ ^FAIL ]]; then
            echo -e "  ${RED}• $result${NC}"
        fi
    done
    exit 1
fi