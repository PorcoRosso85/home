#!/usr/bin/env bash
set -euo pipefail

# Test suite for simplified orchestrator implementation
# Add parent directory to PATH so tests can find scripts
export PATH="$(dirname "$PWD"):$PATH"

# Test configuration
readonly TEST_DIR="/tmp/opencode-orchestrator-test-$$"

# Helper functions
setup_test() {
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
}

cleanup_test() {
    cd /
    rm -rf "$TEST_DIR" 2>/dev/null || true
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

# Test: Orchestrator status and basic functionality
test_orchestrator_status() {
    setup_test
    local test_name="test_orchestrator_status"
    
    if command -v orchestrator >/dev/null 2>&1; then
        # Test status command
        local result
        if result=$(orchestrator status 2>&1); then
            if [[ "$result" == *"OpenCode Multi-Agent Orchestrator (Minimal)"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Status should show orchestrator info. Got: $result"
            fi
        else
            fail_test "$test_name" "Status command should succeed"
        fi
    else
        fail_test "$test_name" "orchestrator command not found"
    fi
    
    cleanup_test
}

# Test: Help functionality
test_orchestrator_help() {
    setup_test
    local test_name="test_orchestrator_help"
    
    if command -v orchestrator >/dev/null 2>&1; then
        local result
        if result=$(orchestrator --help 2>&1); then
            if [[ "$result" == *"Usage:"* ]] && [[ "$result" == *"A→B message forwarding"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Help should show usage information. Got: $result"
            fi
        else
            fail_test "$test_name" "Help command should succeed"
        fi
    else
        fail_test "$test_name" "orchestrator command not found"
    fi
    
    cleanup_test
}

# Test: Server connectivity test functionality
test_server_connectivity() {
    setup_test
    local test_name="test_server_connectivity"
    
    if command -v orchestrator >/dev/null 2>&1; then
        # Test with unreachable servers (should fail gracefully)
        local result
        if result=$(orchestrator --server-a="http://127.0.0.1:9999" --server-b="http://127.0.0.1:9998" test 2>&1); then
            # Should not succeed with unreachable servers, but command should run
            fail_test "$test_name" "Test should fail with unreachable servers"
        else
            # Expected to fail - test that error message is reasonable
            if [[ "$result" == *"not accessible"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Test should report connectivity issues clearly. Got: $result"
            fi
        fi
    else
        fail_test "$test_name" "orchestrator command not found"
    fi
    
    cleanup_test
}

# Test: Message forwarding argument validation
test_message_forwarding_validation() {
    setup_test
    local test_name="test_message_forwarding_validation"
    
    if command -v orchestrator >/dev/null 2>&1; then
        # Test forwarding without required session arguments
        local result
        if result=$(orchestrator forward "test message" 2>&1); then
            fail_test "$test_name" "Forward should fail without session IDs"
        else
            # Should fail with appropriate error message
            if [[ "$result" == *"--session-a and --session-b are required"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Forward should require session IDs. Got: $result"
            fi
        fi
    else
        fail_test "$test_name" "orchestrator command not found"
    fi
    
    cleanup_test
}

# Test: Default server configuration
test_default_servers() {
    setup_test
    local test_name="test_default_servers"
    
    if command -v orchestrator >/dev/null 2>&1; then
        local result
        if result=$(orchestrator status 2>&1); then
            if [[ "$result" == *"Server A: http://127.0.0.1:4096"* ]] && [[ "$result" == *"Server B: http://127.0.0.1:4097"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Should use default servers 4096 and 4097. Got: $result"
            fi
        else
            fail_test "$test_name" "Status command should succeed"
        fi
    else
        fail_test "$test_name" "orchestrator command not found"
    fi
    
    cleanup_test
}

# Test: Custom server configuration
test_custom_servers() {
    setup_test
    local test_name="test_custom_servers"
    
    if command -v orchestrator >/dev/null 2>&1; then
        local result
        if result=$(orchestrator --server-a="http://custom-a:8080" --server-b="http://custom-b:9090" status 2>&1); then
            if [[ "$result" == *"Server A: http://custom-a:8080"* ]] && [[ "$result" == *"Server B: http://custom-b:9090"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Should use custom server URLs. Got: $result"
            fi
        else
            fail_test "$test_name" "Status with custom servers should succeed"
        fi
    else
        fail_test "$test_name" "orchestrator command not found"
    fi
    
    cleanup_test
}

echo "🟡 Testing simplified orchestrator (minimal A→B forwarding)..."
echo "Testing minimal 2-server message forwarding functionality"
echo

# Run simplified tests
test_orchestrator_status
test_orchestrator_help
test_server_connectivity
test_message_forwarding_validation
test_default_servers
test_custom_servers

echo
echo "Testing complete. Focus on minimal A→B message forwarding."