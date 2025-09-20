#!/usr/bin/env bash
# Test: Index API Implementation Verification
# Tests the actual oc_session_index_* function implementations

set -euo pipefail

echo "=== Index API Implementation Test ==="
echo "Testing actual oc_session_index_* function implementations"
echo

# Source session helper functions
source ./lib/session-helper.sh

# Test directory setup
TEST_BASE="/tmp/index_api_test_$$"
mkdir -p "$TEST_BASE"
export OPENCODE_SESSION_DIR="$TEST_BASE"

echo "✅ Test environment setup: $TEST_BASE"
echo

# Test 1: Basic append and lookup
test_basic_append_lookup() {
    echo "🔬 Test 1: Basic Append and Lookup"

    local test_dir="$TEST_BASE/project1"
    mkdir -p "$test_dir"

    echo "Appending test record..."
    if oc_session_index_append "$test_dir" "http://127.0.0.1:4096" "ses_test123"; then
        echo "✅ Append succeeded"
    else
        echo "❌ Append failed"
        return 1
    fi

    echo "Looking up by session ID..."
    local result
    if result=$(oc_session_index_lookup_by_sid "ses_test123"); then
        if [[ -n "$result" ]]; then
            echo "✅ Lookup succeeded: $result"
        else
            echo "❌ Lookup returned empty result"
            return 1
        fi
    else
        echo "❌ Lookup failed"
        return 1
    fi

    echo "✅ Basic append and lookup test passed"
    return 0
}

# Test 2: Duplicate prevention
test_duplicate_prevention() {
    echo "🔬 Test 2: Duplicate Prevention"

    local test_dir="$TEST_BASE/project2"
    mkdir -p "$test_dir"

    echo "Appending first record..."
    if oc_session_index_append "$test_dir" "http://127.0.0.1:4096" "ses_test456"; then
        echo "✅ First append succeeded"
    else
        echo "❌ First append failed"
        return 1
    fi

    echo "Attempting duplicate append..."
    if oc_session_index_append "$test_dir" "http://127.0.0.1:4096" "ses_test456" 2>/dev/null; then
        echo "❌ Duplicate append should have failed but succeeded"
        return 1
    else
        echo "✅ Duplicate append correctly prevented"
    fi

    echo "✅ Duplicate prevention test passed"
    return 0
}

# Test 3: File-based corruption handling
test_corruption_handling() {
    echo "🔬 Test 3: Corruption Handling"

    local index_file="$TEST_BASE/opencode/sessions/index.jsonl"
    mkdir -p "$(dirname "$index_file")"

    # Create index with some valid and some broken lines
    cat > "$index_file" << 'EOF'
{"dir":"/test/valid1","dirHash":"hash1","hostPort":"127.0.0.1:4096","session":"ses_valid1","created":"1695100000"}
{broken_json_line: invalid
{"dir":"/test/valid2","dirHash":"hash2","hostPort":"127.0.0.1:4096","session":"ses_valid2","created":"1695200000"}
EOF

    echo "Reading with corruption handling..."
    local valid_count=0
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            valid_count=$((valid_count + 1))
        fi
    done < <(oc_session_index_read_safe)

    if [[ $valid_count -eq 2 ]]; then
        echo "✅ Corruption handling: $valid_count valid records recovered"
    else
        echo "❌ Expected 2 valid records, got $valid_count"
        return 1
    fi

    echo "✅ Corruption handling test passed"
    return 0
}

# Test 4: Path normalization
test_path_normalization() {
    echo "🔬 Test 4: Path Normalization"

    cd "$TEST_BASE"
    mkdir -p "relative/project"

    echo "Testing relative path normalization..."
    local normalized
    if normalized=$(oc_session_index_normalize_dir "relative/project"); then
        if [[ "$normalized" =~ ^/ ]] && [[ ! "$normalized" =~ /$ ]]; then
            echo "✅ Path normalization: '$normalized'"
        else
            echo "❌ Path normalization failed: '$normalized'"
            return 1
        fi
    else
        echo "❌ Path normalization function failed"
        return 1
    fi

    echo "✅ Path normalization test passed"
    return 0
}

# Cleanup function
cleanup() {
    rm -rf "$TEST_BASE"
}
trap cleanup EXIT

# Run all tests
echo "🔄 Running Index API Implementation Tests"
echo

test_count=0
passed_count=0

echo "Test 1/4: Basic Append and Lookup"
if test_basic_append_lookup; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 2/4: Duplicate Prevention"
if test_duplicate_prevention; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 3/4: Corruption Handling"
if test_corruption_handling; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

echo "Test 4/4: Path Normalization"
if test_path_normalization; then
    passed_count=$((passed_count + 1))
fi
test_count=$((test_count + 1))
echo

# Final results
if [[ $passed_count -eq $test_count ]]; then
    echo "🟢 INDEX API IMPLEMENTATION: ALL TESTS PASSED (GREEN) ✅"
    echo "   Passed: $passed_count/$test_count implementation tests"
    echo "   All oc_session_index_* functions working correctly"
else
    echo "🔴 INDEX API IMPLEMENTATION: SOME TESTS FAILED (RED) ❌"
    echo "   Passed: $passed_count/$test_count implementation tests"
fi

echo
echo "🏁 Index API Implementation Test Completed!"
echo "   Tested functions: append, lookup, duplicate prevention, corruption handling, normalization"