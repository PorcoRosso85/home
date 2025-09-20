#!/usr/bin/env bash
# Test: Strict No-Fallback Policy - Invalid SID Error Verification
# Tests that invalid SID results in clear error instead of automatic recreation

set -euo pipefail

echo "=== Strict No-Fallback Policy Test ==="
echo "Testing that invalid SID produces clear error instead of auto-recreation"
echo

OPENCODE_URL="http://127.0.0.1:4096"
TEST_DIR="/tmp/no_fallback_test_$$"
mkdir -p "$TEST_DIR"

# Source session helper functions
source ./lib/session-helper.sh

# Test invalid SID strict error behavior
test_invalid_sid_strict_error() {
    echo "🔬 Testing Invalid SID Strict Error Behavior"

    cd "$TEST_DIR"

    # Create fake invalid session file
    local session_file
    session_file=$(oc_session_get_file_path "$OPENCODE_URL" "$TEST_DIR")

    mkdir -p "$(dirname "$session_file")"
    echo "ses_invalid_fake_session_id_12345" > "$session_file"

    echo "Created fake invalid session file: $session_file"
    echo "Invalid SID: $(cat "$session_file")"

    # Attempt to get/create session - should fail with clear error
    echo "Testing invalid SID error behavior..."

    local error_output
    local exit_code=0

    # Capture both stdout and stderr, and exit code
    if error_output=$(oc_session_get_or_create "$OPENCODE_URL" "$TEST_DIR" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi

    echo "Exit code: $exit_code"
    echo "Output: '$error_output'"

    # Verify strict error behavior
    if [[ $exit_code -eq 0 ]]; then
        echo "❌ FAIL: Function should have failed with non-zero exit code"
        echo "   Automatic session creation is FORBIDDEN"
        return 1
    fi

    # Verify error message contains expected content
    if [[ "$error_output" =~ "invalid session ID in file" ]] && [[ "$error_output" =~ "Remove the file or select another OPENCODE_PROJECT_DIR" ]]; then
        echo "✅ SUCCESS: Clear error message provided"
        echo "   Message: $error_output"
        return 0
    else
        echo "❌ FAIL: Error message not sufficiently clear"
        echo "   Expected: Message about 'invalid session ID in file' with guidance"
        echo "   Actual: '$error_output'"
        return 1
    fi
}

# Test that automatic recreation is completely prevented
test_no_automatic_recreation() {
    echo "🔬 Testing No Automatic Recreation"

    cd "$TEST_DIR"

    # Create another fake invalid session
    local session_file
    session_file=$(oc_session_get_file_path "$OPENCODE_URL" "$TEST_DIR")

    echo "ses_another_invalid_session_67890" > "$session_file"

    # Count existing sessions before
    local sessions_before=0
    if curl -fsS "$OPENCODE_URL/sessions" >/dev/null 2>&1; then
        sessions_before=$(curl -fsS "$OPENCODE_URL/sessions" | jq '. | length' 2>/dev/null || echo "0")
    fi

    echo "Sessions before: $sessions_before"

    # Attempt operation
    local exit_code=0
    oc_session_get_or_create "$OPENCODE_URL" "$TEST_DIR" >/dev/null 2>&1 || exit_code=$?

    # Count sessions after
    local sessions_after=0
    if curl -fsS "$OPENCODE_URL/sessions" >/dev/null 2>&1; then
        sessions_after=$(curl -fsS "$OPENCODE_URL/sessions" | jq '. | length' 2>/dev/null || echo "0")
    fi

    echo "Sessions after: $sessions_after"
    echo "Exit code: $exit_code"

    # Verify no new session was created
    if [[ $sessions_after -eq $sessions_before ]] && [[ $exit_code -ne 0 ]]; then
        echo "✅ SUCCESS: No automatic session recreation"
        return 0
    else
        echo "❌ FAIL: Automatic session recreation detected or wrong exit code"
        echo "   Sessions before: $sessions_before"
        echo "   Sessions after: $sessions_after"
        echo "   Exit code: $exit_code (should be non-zero)"
        return 1
    fi
}

# Cleanup function
cleanup() {
    rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Server health check
if ! curl -fsS "$OPENCODE_URL/doc" >/dev/null 2>&1; then
    echo "❌ Server not accessible at $OPENCODE_URL"
    echo "   Start server: nix run . -- serve --port 4096"
    exit 1
fi

echo "✅ Server responding"
echo

# Run tests
echo "🔄 Running No-Fallback Strict Policy Tests"

if test_invalid_sid_strict_error && test_no_automatic_recreation; then
    echo
    echo "🟢 NO-FALLBACK TESTS: PASSING (GREEN) ✅"
    echo "   Fallback prevention implementation successful"
    echo "   Invalid SID now produces clear error instead of auto-recreation"
else
    echo
    echo "🔴 NO-FALLBACK TESTS: FAILING (RED) ❌"
    echo "   Current implementation still has fallback behavior"
    echo "   Implementation needed to make tests GREEN"
fi

echo
echo "🏁 No-Fallback Strict Policy Test Completed!"
echo "   These tests verify that invalid SID results in clear error"
echo "   instead of automatic session recreation (fallback prevention)"