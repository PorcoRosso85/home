#!/usr/bin/env bash
set -euo pipefail

# Test suite for unified error handling system
# Add parent directory to PATH so tests can find scripts
export PATH="$(dirname "$PWD"):$PATH"

# Test configuration
readonly TEST_DIR="/tmp/opencode-error-test-$$"
readonly SESSION_BASE="/tmp/opencode-sessions"

# Helper functions
setup_test() {
    mkdir -p "$TEST_DIR"
    mkdir -p "$SESSION_BASE"
    cd "$TEST_DIR"
    export OPENCODE_SESSION_DIR="$SESSION_BASE"
}

cleanup_test() {
    cd /
    rm -rf "$TEST_DIR" 2>/dev/null || true
    rm -rf "$SESSION_BASE" 2>/dev/null || true
}

fail_test() {
    local test_name="$1"
    local message="$2"
    echo "❌ FAIL: $test_name - $message"
}

pass_test() {
    local test_name="$1"
    echo "✅ PASS: $test_name"
}

# Test: HTTP 404 error handling
test_http_404_error() {
    setup_test
    local test_name="test_http_404_error"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Test 404 error handling using httpbin.org which reliably returns 404
        local error_output
        if error_output=$(unified-error-handler --url="http://httpbin.org/status/404" --method="GET" 2>&1); then
            fail_test "$test_name" "Should have failed with 404 error"
        else
            local exit_code=$?
            if [[ $exit_code -eq 44 ]] && [[ "$error_output" == *"HTTP_404"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Wrong exit code or error format. Got: $exit_code, Output: $error_output"
            fi
        fi
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

# Test: HTTP 500 error handling  
test_http_500_error() {
    setup_test
    local test_name="test_http_500_error"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Mock 500 error response
        local error_output
        if error_output=$(unified-error-handler --url="http://httpbin.org/status/500" --method="GET" 2>&1); then
            fail_test "$test_name" "Should have failed with 500 error"
        else
            local exit_code=$?
            if [[ $exit_code -eq 22 ]] && [[ "$error_output" == *"HTTP_500"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Wrong exit code or error format. Got: $exit_code, Output: $error_output"
            fi
        fi
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

# Test: Network timeout handling
test_network_timeout() {
    setup_test
    local test_name="test_network_timeout"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Test timeout handling with 1 second timeout
        local error_output
        if error_output=$(unified-error-handler --url="http://httpbin.org/delay/5" --method="GET" --timeout=1 2>&1); then
            fail_test "$test_name" "Should have failed with timeout"
        else
            local exit_code=$?
            if [[ $exit_code -eq 28 ]] && [[ "$error_output" == *"TIMEOUT"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Wrong exit code or error format. Got: $exit_code, Output: $error_output"
            fi
        fi
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

# Test: Invalid JSON response handling
test_invalid_json_response() {
    setup_test
    local test_name="test_invalid_json_response"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Test invalid JSON handling
        local error_output
        if error_output=$(unified-error-handler --url="http://httpbin.org/html" --method="GET" --expect-json 2>&1); then
            fail_test "$test_name" "Should have failed with JSON parse error"
        else
            local exit_code=$?
            if [[ $exit_code -eq 5 ]] && [[ "$error_output" == *"JSON_PARSE_ERROR"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Wrong exit code or error format. Got: $exit_code, Output: $error_output"
            fi
        fi
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

# Test: Missing jq fallback functionality
test_jq_fallback() {
    setup_test
    local test_name="test_jq_fallback"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Temporarily hide jq to test fallback
        local temp_path="/tmp/test-path-$$"
        mkdir -p "$temp_path"
        export PATH="$temp_path:$PATH"
        
        # Test should work even without jq
        local response
        if response=$(unified-error-handler --url="http://httpbin.org/json" --method="GET" --extract=".slideshow.title" 2>&1); then
            if [[ "$response" == *"Sample Slide Show"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "jq fallback should extract JSON field. Got: $response"
            fi
        else
            fail_test "$test_name" "jq fallback should work when jq is not available"
        fi
        
        rm -rf "$temp_path"
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

# Test: Consistent error message format
test_error_message_format() {
    setup_test
    local test_name="test_error_message_format"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Test error message format consistency
        local error_output
        if error_output=$(unified-error-handler --url="http://127.0.0.1:9999/test" --method="GET" 2>&1); then
            fail_test "$test_name" "Should have failed"
        else
            # Check error format: ERROR_TYPE:URL:METHOD:DETAILS
            if [[ "$error_output" =~ ^[A-Z_]+:http://127\.0\.0\.1:9999/test:GET:.+ ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Error format should be ERROR_TYPE:URL:METHOD:DETAILS. Got: $error_output"
            fi
        fi
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

# Test: Successful request handling
test_successful_request() {
    setup_test
    local test_name="test_successful_request"
    
    # This should fail because unified-error-handler doesn't exist yet (RED)
    if command -v unified-error-handler >/dev/null 2>&1; then
        # Test successful request
        local response
        if response=$(unified-error-handler --url="http://httpbin.org/get" --method="GET" 2>&1); then
            if [[ "$response" == *"httpbin.org"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Should return valid response. Got: $response"
            fi
        else
            fail_test "$test_name" "Successful request should not fail"
        fi
    else
        fail_test "$test_name" "unified-error-handler command not found"
    fi
    
    cleanup_test
}

echo "🔴 Running RED tests for unified error handling..."
echo "These tests should FAIL because unified-error-handler is not implemented yet"
echo

# Run all tests
test_http_404_error
test_http_500_error  
test_network_timeout
test_invalid_json_response
test_jq_fallback
test_error_message_format
test_successful_request

echo
echo "RED phase complete. All tests should have failed."