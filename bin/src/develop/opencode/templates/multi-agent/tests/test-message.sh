#!/usr/bin/env bash
set -euo pipefail

# Test suite for message.sh - OpenCode API message functionality
# Add parent directory to PATH so tests can find scripts
export PATH="$(dirname "$PWD"):$PATH"

# Test configuration
readonly TEST_DIR="/tmp/opencode-message-test-$$"
readonly SESSION_BASE="/tmp/opencode-sessions"

# Test counters
TESTS_RUN=0
TESTS_FAILED=0

# Helper functions
setup_test() {
    mkdir -p "$TEST_DIR"
    mkdir -p "$SESSION_BASE"
    cd "$TEST_DIR"
    export OPENCODE_SESSION_DIR="$SESSION_BASE"
    TESTS_RUN=$((TESTS_RUN + 1))
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
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

pass_test() {
    local test_name="$1"
    echo "✅ PASS: $test_name"
}

assert_command_exists() {
    local cmd="$1"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Test: Command existence check
test_message_command_exists() {
    setup_test
    local test_name="test_message_command_exists"
    
    # Check if message command exists
    if ! assert_command_exists "message"; then
        fail_test "$test_name" "message command not found in PATH"
        cleanup_test
        return 0
    fi
    
    pass_test "$test_name"
    cleanup_test
}

# Test: Basic OpenCode API payload format
test_opencode_payload_format() {
    setup_test
    local test_name="test_opencode_payload_format"
    
    if ! assert_command_exists "message"; then
        fail_test "$test_name" "message command not found in PATH"
        cleanup_test
        return 0
    fi
    
    # Create a mock session directory
    local session_dir="$SESSION_BASE/test-session"
    mkdir -p "$session_dir"
    export OPENCODE_SESSION_PATH="$session_dir"
    
    # Mock API endpoint that captures the payload
    local mock_port="3939"
    local mock_log="$TEST_DIR/mock_api.log"
    
    # Start a simple HTTP server that logs requests (in background)
    (
        while true; do
            nc -l -p "$mock_port" -c "
                while read line; do
                    echo \"\$line\" >> '$mock_log'
                    [[ \"\$line\" == $'\r' ]] && break
                done
                echo 'HTTP/1.1 200 OK'
                echo 'Content-Type: application/json'
                echo ''
                echo '{\"success\":true}'
            " 2>/dev/null || break
        done
    ) &
    local server_pid=$!
    
    # Give server time to start
    sleep 0.5
    
    # Test message command with basic text
    local test_message="Hello, OpenCode!"
    if message --session="test-session" --host="127.0.0.1:$mock_port" "$test_message" 2>/dev/null; then
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        
        # Check if the payload contains expected OpenCode format
        if [[ -f "$mock_log" ]]; then
            local payload_line
            if payload_line=$(grep -o '{.*}' "$mock_log" 2>/dev/null); then
                # Verify the payload has the correct structure: {parts:[{type:"text",text:MSG}]}
                if echo "$payload_line" | grep -q '"parts":\[' && \
                   echo "$payload_line" | grep -q '"type":"text"' && \
                   echo "$payload_line" | grep -q '"text":"Hello, OpenCode!"'; then
                    pass_test "$test_name"
                else
                    fail_test "$test_name" "Payload format incorrect. Expected {parts:[{type:\"text\",text:\"$test_message\"}]}, got: $payload_line"
                fi
            else
                fail_test "$test_name" "No JSON payload found in request"
            fi
        else
            fail_test "$test_name" "No request captured by mock server"
        fi
    else
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        fail_test "$test_name" "message command failed to send request"
    fi
    
    cleanup_test
}

# Test: Optional model field handling
test_model_field_optional() {
    setup_test
    local test_name="test_model_field_optional"
    
    if ! assert_command_exists "message"; then
        fail_test "$test_name" "message command not found in PATH"
        cleanup_test
        return 0
    fi
    
    # Create a mock session directory
    local session_dir="$SESSION_BASE/test-session-model"
    mkdir -p "$session_dir"
    export OPENCODE_SESSION_PATH="$session_dir"
    
    # Mock API endpoint that captures the payload
    local mock_port="3940"
    local mock_log="$TEST_DIR/mock_api_model.log"
    
    # Start a simple HTTP server that logs requests
    (
        while true; do
            nc -l -p "$mock_port" -c "
                while read line; do
                    echo \"\$line\" >> '$mock_log'
                    [[ \"\$line\" == $'\r' ]] && break
                done
                echo 'HTTP/1.1 200 OK'
                echo 'Content-Type: application/json'
                echo ''
                echo '{\"success\":true}'
            " 2>/dev/null || break
        done
    ) &
    local server_pid=$!
    
    # Give server time to start
    sleep 0.5
    
    # Test message command with model specification
    local test_message="Test with model"
    if message --session="test-session-model" --host="127.0.0.1:$mock_port" --model-provider="anthropic" --model-id="claude-3-haiku" "$test_message" 2>/dev/null; then
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        
        # Check if the payload contains model field
        if [[ -f "$mock_log" ]]; then
            local payload_line
            if payload_line=$(grep -o '{.*}' "$mock_log" 2>/dev/null); then
                # Verify the payload has model field: model:{providerID,modelID}
                if echo "$payload_line" | grep -q '"model":{' && \
                   echo "$payload_line" | grep -q '"providerID":"anthropic"' && \
                   echo "$payload_line" | grep -q '"modelID":"claude-3-haiku"'; then
                    pass_test "$test_name"
                else
                    fail_test "$test_name" "Model field format incorrect. Expected model:{providerID:\"anthropic\",modelID:\"claude-3-haiku\"}, got: $payload_line"
                fi
            else
                fail_test "$test_name" "No JSON payload found in request"
            fi
        else
            fail_test "$test_name" "No request captured by mock server"
        fi
    else
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        fail_test "$test_name" "message command failed to send request with model"
    fi
    
    cleanup_test
}

# Test: 4xx error handling
test_4xx_error_handling() {
    setup_test
    local test_name="test_4xx_error_handling"
    
    if ! assert_command_exists "message"; then
        fail_test "$test_name" "message command not found in PATH"
        cleanup_test
        return 0
    fi
    
    # Create a mock session directory
    local session_dir="$SESSION_BASE/test-session-error"
    mkdir -p "$session_dir"
    export OPENCODE_SESSION_PATH="$session_dir"
    
    # Mock API endpoint that returns 4xx error
    local mock_port="3941"
    
    # Start a simple HTTP server that returns 400 error
    (
        while true; do
            nc -l -p "$mock_port" -c "
                while read line; do
                    [[ \"\$line\" == $'\r' ]] && break
                done
                echo 'HTTP/1.1 400 Bad Request'
                echo 'Content-Type: application/json'
                echo ''
                echo '{\"error\":\"Invalid request format\"}'
            " 2>/dev/null || break
        done
    ) &
    local server_pid=$!
    
    # Give server time to start
    sleep 0.5
    
    # Test message command should fail with 4xx error
    local test_message="Test error handling"
    local error_output
    if error_output=$(message --session="test-session-error" --host="127.0.0.1:$mock_port" "$test_message" 2>&1); then
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        fail_test "$test_name" "message command should have failed with 4xx error"
    else
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        
        # Check if error output contains HTTP code and response body
        if echo "$error_output" | grep -q "400" && \
           echo "$error_output" | grep -q "Invalid request format"; then
            pass_test "$test_name"
        else
            fail_test "$test_name" "Error output should contain HTTP code and response body. Got: $error_output"
        fi
    fi
    
    cleanup_test
}

# Test: Integration with unified-error-handler
test_unified_error_handler_integration() {
    setup_test
    local test_name="test_unified_error_handler_integration"
    
    if ! assert_command_exists "message"; then
        fail_test "$test_name" "message command not found in PATH"
        cleanup_test
        return 0
    fi
    
    if ! assert_command_exists "unified-error-handler"; then
        fail_test "$test_name" "unified-error-handler command not found in PATH"
        cleanup_test
        return 0
    fi
    
    # Create a mock session directory
    local session_dir="$SESSION_BASE/test-session-integration"
    mkdir -p "$session_dir"
    export OPENCODE_SESSION_PATH="$session_dir"
    
    # Test that message command uses unified-error-handler for network requests
    # We'll simulate this by checking that message command handles network errors consistently
    local test_message="Test integration"
    local error_output
    if error_output=$(message --session="test-session-integration" --host="127.0.0.1:9999" "$test_message" 2>&1); then
        fail_test "$test_name" "message command should fail for non-existent server"
    else
        # Check if error output follows unified-error-handler format
        if echo "$error_output" | grep -qE "^[A-Z_]+:.*:.*:"; then
            pass_test "$test_name"
        else
            fail_test "$test_name" "Error output should follow unified-error-handler format (ERROR_TYPE:URL:METHOD:DETAILS). Got: $error_output"
        fi
    fi
    
    cleanup_test
}

# Test: Basic message sending to session endpoint
test_basic_message_sending() {
    setup_test
    local test_name="test_basic_message_sending"
    
    if ! assert_command_exists "message"; then
        fail_test "$test_name" "message command not found in PATH"
        cleanup_test
        return 0
    fi
    
    # Create a mock session directory
    local session_dir="$SESSION_BASE/test-basic-session"
    mkdir -p "$session_dir"
    export OPENCODE_SESSION_PATH="$session_dir"
    
    # Mock API endpoint for successful response
    local mock_port="3942"
    local mock_response='{"id":"test-123","role":"assistant","content":[{"type":"text","text":"Hello! I received your message."}]}'
    
    # Start a simple HTTP server that returns success
    (
        while true; do
            nc -l -p "$mock_port" -c "
                while read line; do
                    [[ \"\$line\" == $'\r' ]] && break
                done
                echo 'HTTP/1.1 200 OK'
                echo 'Content-Type: application/json'
                echo 'Content-Length: ${#mock_response}'
                echo ''
                echo '$mock_response'
            " 2>/dev/null || break
        done
    ) &
    local server_pid=$!
    
    # Give server time to start
    sleep 0.5
    
    # Test basic message sending
    local test_message="Hello, can you help me?"
    local response_output
    if response_output=$(message --session="test-basic-session" --host="127.0.0.1:$mock_port" "$test_message" 2>/dev/null); then
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        
        # Check if we got a valid response
        if echo "$response_output" | grep -q "Hello! I received your message."; then
            pass_test "$test_name"
        else
            fail_test "$test_name" "Response should contain expected message. Got: $response_output"
        fi
    else
        # Kill the mock server
        kill $server_pid 2>/dev/null || true
        wait $server_pid 2>/dev/null || true
        fail_test "$test_name" "Basic message sending should succeed with mock server"
    fi
    
    cleanup_test
}

# Main test runner
main() {
    echo "🧪 Message Script Tests"
    echo "======================="
    echo ""
    
    # Check if message command exists at all
    if ! command -v message >/dev/null 2>&1; then
        echo "⚠️  MESSAGE COMMAND NOT FOUND - Tests will check for command existence"
        echo ""
    else
        echo "✅ MESSAGE COMMAND FOUND - Running functional tests"
        echo ""
    fi
    
    # Run all tests
    test_message_command_exists
    test_opencode_payload_format
    test_model_field_optional
    test_4xx_error_handling
    test_unified_error_handler_integration
    test_basic_message_sending
    
    # Summary
    echo ""
    echo "Test Summary:"
    echo "- Tests run: $TESTS_RUN"
    echo "- Tests failed: $TESTS_FAILED"
    echo "- Tests passed: $((TESTS_RUN - TESTS_FAILED))"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo ""
        echo "✅ ALL TESTS PASSED - Message functionality is working correctly"
        exit 0
    elif [[ $TESTS_FAILED -eq $TESTS_RUN ]]; then
        echo ""
        echo "❌ ALL TESTS FAILED - Check message.sh implementation or availability"
        exit 1
    else
        echo ""
        echo "⚠️  SOME TESTS FAILED - Partial message functionality"
        exit 1
    fi
}

# Trap to ensure cleanup on script exit
trap 'cleanup_test' EXIT

# Run tests
main "$@"