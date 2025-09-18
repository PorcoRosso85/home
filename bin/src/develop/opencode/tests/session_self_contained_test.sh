#!/usr/bin/env bash
set -euo pipefail

# Self-contained session continuity tests with mock server
# GREEN phase: Tests verify implementation with no external dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

# Test configuration
TEST_STATE_DIR="/tmp/opencode_self_test_$$"
MOCK_PORT="4099"
MOCK_SERVER_PID=""
export XDG_STATE_HOME="$TEST_STATE_DIR"
export OPENCODE_URL="http://127.0.0.1:$MOCK_PORT"

# Test setup and cleanup
setup_test_env() {
    mkdir -p "$TEST_STATE_DIR"
    
    # Start mock server in background
    chmod +x "$SCRIPT_DIR/session_mock_server.sh"
    "$SCRIPT_DIR/session_mock_server.sh" "$MOCK_PORT" &
    MOCK_SERVER_PID=$!
    
    # Wait for server to be ready
    for i in {1..10}; do
        if curl -s "http://127.0.0.1:$MOCK_PORT/doc" >/dev/null 2>&1; then
            echo "Mock server ready on port $MOCK_PORT"
            return 0
        fi
        sleep 0.5
    done
    
    echo "Failed to start mock server"
    return 1
}

cleanup_test_env() {
    if [[ -n "$MOCK_SERVER_PID" ]]; then
        kill "$MOCK_SERVER_PID" 2>/dev/null || true
        wait "$MOCK_SERVER_PID" 2>/dev/null || true
    fi
    rm -rf "$TEST_STATE_DIR"
}

create_test_dir() {
    local dir_name="$1"
    local test_dir="$TEST_STATE_DIR/$dir_name"
    mkdir -p "$test_dir"
    echo "$test_dir"
}

# Test functions using lib/session-helper.sh directly
test_session_library_functions() {
    echo "Testing: lib/session-helper.sh functions work correctly"
    
    # Source the session library
    source "$REPO_ROOT/lib/session-helper.sh"
    
    # Test base directory function
    local base_dir
    base_dir=$(oc_session_get_base_dir)
    if [[ "$base_dir" != "$TEST_STATE_DIR/opencode/sessions" ]]; then
        echo "❌ FAIL: oc_session_get_base_dir returned '$base_dir', expected '$TEST_STATE_DIR/opencode/sessions'"
        return 1
    fi
    
    # Test URL normalization
    local norm_url
    norm_url=$(oc_session_normalize_url "http://test.com/")
    if [[ "$norm_url" != "http://test.com" ]]; then
        echo "❌ FAIL: oc_session_normalize_url failed"
        return 1
    fi
    
    # Test session file path generation
    local test_dir
    test_dir=$(create_test_dir "test_project")
    local session_file
    session_file=$(oc_session_get_file_path "$OPENCODE_URL" "$test_dir")
    local expected_file="$base_dir/127.0.0.1:$MOCK_PORT${test_dir//\//_}.session"
    if [[ "$session_file" != "$expected_file" ]]; then
        echo "❌ FAIL: Session file path '$session_file' != expected '$expected_file'"
        return 1
    fi
    
    echo "✅ PASS: Session library functions work correctly"
    return 0
}

test_session_creation_and_reuse() {
    echo "Testing: Session creation and reuse functionality"
    
    source "$REPO_ROOT/lib/session-helper.sh"
    local test_dir
    test_dir=$(create_test_dir "project_session_test")
    
    # First call should create new session
    local session1
    session1=$(cd "$test_dir" && oc_session_get_or_create "$OPENCODE_URL")
    if [[ -z "$session1" ]]; then
        echo "❌ FAIL: Failed to create new session"
        return 1
    fi
    
    # Second call from same directory should reuse session
    local session2
    session2=$(cd "$test_dir" && oc_session_get_or_create "$OPENCODE_URL")
    if [[ "$session1" != "$session2" ]]; then
        echo "❌ FAIL: Session not reused. First: '$session1', Second: '$session2'"
        return 1
    fi
    
    # Call from different directory should create different session
    local test_dir2
    test_dir2=$(create_test_dir "different_project")
    local session3
    session3=$(cd "$test_dir2" && oc_session_get_or_create "$OPENCODE_URL")
    if [[ "$session1" == "$session3" ]]; then
        echo "❌ FAIL: Different directories should have different sessions"
        return 1
    fi
    
    echo "✅ PASS: Session creation and reuse work correctly"
    return 0
}

test_integrated_client_functionality() {
    echo "Testing: Integrated opencode-client functionality"
    
    local test_dir
    test_dir=$(create_test_dir "client_integration_test")
    
    # Test that opencode-client command works with mock server
    local output
    if output=$(cd "$test_dir" && nix run "$REPO_ROOT#opencode-client" -- "test message" 2>&1); then
        if echo "$output" | grep -q "Mock response"; then
            echo "✅ PASS: opencode-client integration works"
            return 0
        else
            echo "❌ FAIL: opencode-client did not receive mock response: $output"
            return 1
        fi
    else
        echo "❌ FAIL: opencode-client execution failed: $output"
        return 1
    fi
}

# Main test execution
main() {
    echo "🧪 Self-Contained Session Continuity Tests"
    echo "============================================"
    
    local failed=0
    
    # Setup test environment
    if ! setup_test_env; then
        echo "❌ FAIL: Test environment setup failed"
        exit 1
    fi
    
    # Cleanup trap
    trap cleanup_test_env EXIT
    
    # Run tests
    test_session_library_functions || failed=$((failed + 1))
    test_session_creation_and_reuse || failed=$((failed + 1))
    test_integrated_client_functionality || failed=$((failed + 1))
    
    echo ""
    if [[ $failed -eq 0 ]]; then
        echo "🟢 All self-contained tests PASSED"
        exit 0
    else
        echo "🔴 $failed test(s) FAILED"
        exit 1
    fi
}

main "$@"