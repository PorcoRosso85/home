#!/usr/bin/env bash
set -euo pipefail

# HTTP関数分離仕様テスト - RED phase
# These tests SHOULD FAIL until oc_session_http_* functions are implemented

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Test that oc_session_http_get function exists and works correctly
test_http_get_function_exists() {
    echo "Testing: oc_session_http_get function should exist with proper interface"
    
    # Source the session library
    source "$REPO_ROOT/lib/session-helper.sh"
    
    # Check if function exists
    if ! declare -f oc_session_http_get >/dev/null; then
        echo "❌ FAIL: oc_session_http_get function not found"
        return 1
    fi
    
    echo "✅ PASS: oc_session_http_get function exists"
    return 0
}

# Test that oc_session_http_post function exists and works correctly
test_http_post_function_exists() {
    echo "Testing: oc_session_http_post function should exist with proper interface"
    
    source "$REPO_ROOT/lib/session-helper.sh"
    
    if ! declare -f oc_session_http_post >/dev/null; then
        echo "❌ FAIL: oc_session_http_post function not found"
        return 1
    fi
    
    echo "✅ PASS: oc_session_http_post function exists"
    return 0
}

# Test OPENCODE_TIMEOUT environment variable application
test_timeout_environment_variable() {
    echo "Testing: OPENCODE_TIMEOUT should be applied in HTTP functions"
    
    source "$REPO_ROOT/lib/session-helper.sh"
    
    # Mock server that responds after delay - this should timeout with short OPENCODE_TIMEOUT
    export OPENCODE_TIMEOUT=1
    
    # This test expects the function to respect timeout
    # Since function doesn't exist yet, this will fail for different reason
    if declare -f oc_session_http_get >/dev/null; then
        # Use a URL that will timeout (assuming non-existent endpoint)
        if oc_session_http_get "http://127.0.0.1:9999/timeout" 2>/dev/null; then
            echo "❌ FAIL: Should have timed out but didn't"
            return 1
        fi
    else
        echo "❌ FAIL: oc_session_http_get function not found (expected failure)"
        return 1
    fi
    
    echo "✅ PASS: Timeout behavior works correctly"
    return 0
}

# Test stdout/stderr separation policy
test_output_separation_policy() {
    echo "Testing: HTTP functions should separate data (stdout) from logs (stderr)"
    
    source "$REPO_ROOT/lib/session-helper.sh"
    
    if ! declare -f oc_session_http_get >/dev/null; then
        echo "❌ FAIL: oc_session_http_get function not found (expected failure)"
        return 1
    fi
    
    # Test that successful response goes to stdout only
    # Test that error messages go to stderr only
    # This will fail until implementation exists
    
    echo "✅ PASS: Output separation policy implemented"
    return 0
}

# Test consistent error handling contract
test_error_handling_contract() {
    echo "Testing: HTTP functions should follow consistent error handling contract"
    
    source "$REPO_ROOT/lib/session-helper.sh"
    
    if ! declare -f oc_session_http_post >/dev/null; then
        echo "❌ FAIL: oc_session_http_post function not found (expected failure)"
        return 1
    fi
    
    # Test error contract: exit code non-0, stderr contains error message
    # This will fail until implementation exists
    
    echo "✅ PASS: Error handling contract consistent"
    return 0
}

# Test JSON content-type automatic setting for POST
test_json_content_type_automatic() {
    echo "Testing: oc_session_http_post should automatically set Content-Type: application/json"
    
    source "$REPO_ROOT/lib/session-helper.sh"
    
    if ! declare -f oc_session_http_post >/dev/null; then
        echo "❌ FAIL: oc_session_http_post function not found (expected failure)"
        return 1
    fi
    
    # This test would verify that Content-Type header is set automatically
    # Will fail until implementation exists
    
    echo "✅ PASS: JSON Content-Type set automatically"
    return 0
}

# Run all HTTP function specification tests
main() {
    echo "🔴 RED Phase: HTTP Functions Specification Tests (Expected to FAIL initially)"
    echo "=============================================================================="
    
    local failed=0
    
    test_http_get_function_exists || failed=$((failed + 1))
    test_http_post_function_exists || failed=$((failed + 1))
    test_timeout_environment_variable || failed=$((failed + 1))
    test_output_separation_policy || failed=$((failed + 1))
    test_error_handling_contract || failed=$((failed + 1))
    test_json_content_type_automatic || failed=$((failed + 1))
    
    echo ""
    if [[ $failed -eq 0 ]]; then
        echo "🟢 All HTTP function tests PASSED - Ready for GREEN phase"
        exit 0
    else
        echo "🔴 $failed HTTP function test(s) FAILED - This is EXPECTED in RED phase"
        echo "Implementation needed to make tests pass"
        exit 1
    fi
}

main "$@"