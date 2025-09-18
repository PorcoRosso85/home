#!/usr/bin/env bash
set -euo pipefail

# Test suite for simplified session-manager implementation
# Add parent directory to PATH so tests can find scripts
export PATH="$(dirname "$PWD"):$PATH"

# Test configuration
readonly TEST_DIR="/tmp/opencode-session-test-$$"

# Helper functions
setup_test() {
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    # Use test directory for session storage
    export XDG_STATE_HOME="$TEST_DIR/.state"
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

# Test: Session manager basic functionality
test_session_manager_status() {
    setup_test
    local test_name="test_session_manager_status"
    
    if command -v session-manager >/dev/null 2>&1; then
        local result
        if result=$(session-manager status 2>&1); then
            if [[ "$result" == *"OpenCode Session Manager (Simplified)"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Status should show simplified session manager info. Got: $result"
            fi
        else
            fail_test "$test_name" "Status command should succeed"
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

# Test: Auto strategy creates session file
test_auto_strategy() {
    setup_test
    local test_name="test_auto_strategy"
    
    if command -v session-manager >/dev/null 2>&1; then
        local session_file
        if session_file=$(session-manager auto --url=http://127.0.0.1:4096 --project=test 2>/dev/null); then
            if [[ -f "$session_file" ]] && [[ "$session_file" == *"127.0.0.1:4096/test.session" ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Auto should create session file with correct format. Got: $session_file"
            fi
        else
            fail_test "$test_name" "Auto strategy should create session file"
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

# Test: New strategy creates session file
test_new_strategy() {
    setup_test
    local test_name="test_new_strategy"
    
    if command -v session-manager >/dev/null 2>&1; then
        local session_file
        if session_file=$(session-manager new --url=http://127.0.0.1:4097 --project=newtest 2>/dev/null); then
            if [[ -f "$session_file" ]] && [[ "$session_file" == *"127.0.0.1:4097/newtest.session" ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "New should create session file with correct format. Got: $session_file"
            fi
        else
            fail_test "$test_name" "New strategy should create session file"
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

# Test: Attach strategy validation
test_attach_strategy() {
    setup_test
    local test_name="test_attach_strategy"
    
    if command -v session-manager >/dev/null 2>&1; then
        # Test attach without session ID (should fail)
        if session-manager attach 2>/dev/null; then
            fail_test "$test_name" "Attach should fail without session ID"
        else
            # Test attach with session ID (should succeed)
            local session_file
            if session_file=$(session-manager attach --session-id=test123 --url=http://127.0.0.1:4096 --project=attach 2>/dev/null); then
                if [[ -f "$session_file" ]] && [[ "$session_file" == *"127.0.0.1:4096/attach.session" ]]; then
                    local session_id
                    session_id=$(cat "$session_file" 2>/dev/null)
                    if [[ "$session_id" == "test123" ]]; then
                        pass_test "$test_name"
                    else
                        fail_test "$test_name" "Session file should contain correct session ID. Got: $session_id"
                    fi
                else
                    fail_test "$test_name" "Attach should create session file with correct format. Got: $session_file"
                fi
            else
                fail_test "$test_name" "Attach strategy with session ID should succeed"
            fi
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

# Test: URL normalization
test_url_normalization() {
    setup_test
    local test_name="test_url_normalization"
    
    if command -v session-manager >/dev/null 2>&1; then
        # Test with trailing slash URL
        local session_file
        if session_file=$(session-manager auto --url=http://127.0.0.1:4096/ --project=normalize 2>/dev/null); then
            # Should normalize to 127.0.0.1:4096 (no trailing slash in path)
            if [[ "$session_file" == *"127.0.0.1:4096/normalize.session" ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "URL should be normalized (no trailing slash). Got: $session_file"
            fi
        else
            fail_test "$test_name" "URL normalization test should succeed"
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

# Test: Optional strategies fallback
test_optional_strategies() {
    setup_test
    local test_name="test_optional_strategies"
    
    if command -v session-manager >/dev/null 2>&1; then
        # Test shared strategy (should fall back to auto)
        local result
        if result=$(session-manager shared --project=sharedtest 2>&1); then
            if [[ "$result" == *"optional and not implemented"* ]] && [[ "$result" == *"sharedtest.session" ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Shared should show optional message and fall back to auto. Got: $result"
            fi
        else
            fail_test "$test_name" "Shared strategy should work (fallback to auto)"
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

# Test: Help functionality
test_help_functionality() {
    setup_test
    local test_name="test_help_functionality"
    
    if command -v session-manager >/dev/null 2>&1; then
        local result
        if result=$(session-manager --help 2>&1); then
            if [[ "$result" == *"STRATEGIES (Mandatory)"* ]] && [[ "$result" == *"auto"* ]] && [[ "$result" == *"new"* ]] && [[ "$result" == *"attach"* ]]; then
                pass_test "$test_name"
            else
                fail_test "$test_name" "Help should show mandatory strategies. Got: $result"
            fi
        else
            fail_test "$test_name" "Help command should succeed"
        fi
    else
        fail_test "$test_name" "session-manager command not found"
    fi
    
    cleanup_test
}

echo "🟡 Testing simplified session-manager..."
echo "Testing mandatory strategies (auto/new/attach) and session storage"
echo

# Run simplified tests
test_session_manager_status
test_auto_strategy
test_new_strategy
test_attach_strategy
test_url_normalization
test_optional_strategies
test_help_functionality

echo
echo "Testing complete. Focus on mandatory strategies (auto/new/attach)."