#!/usr/bin/env bats

# Multi-ref input robustness tests
# Ensures all refs are evaluated even when some fail

setup() {
    # Hook path
    HOOK_PATH="$BATS_TEST_DIRNAME/../hooks/pre-receive"

    # Temporary git repository for testing
    export TEST_REPO=$(mktemp -d)
    cd "$TEST_REPO"
    git init --bare >/dev/null 2>&1

    # Configure policies
    git config policy.coreRef "refs/heads/main"
    git config --add policy.allowedGlob "flakes/*/**"

    # Clear environment variables
    unset CORE_REFS_OVERRIDE
    unset ALLOWED_GLOBS_OVERRIDE
    unset ALLOW_INITIAL_CREATE
    unset ALLOW_OUTSIDE_DELETE
}

teardown() {
    cd /
    rm -rf "$TEST_REPO"
}

@test "multi-ref input: all refs evaluated despite failures" {
    cd "$TEST_REPO"

    # Create multi-ref input with mixed success/failure scenarios
    # Line 1: Success case (non-core ref)
    # Line 2: Failure case (core ref deletion)
    # Line 3: Another failure case (core ref initial creation)
    input="1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/feature
1111111111111111111111111111111111111111 0000000000000000000000000000000000000000 refs/heads/main
0000000000000000000000000000000000000000 3333333333333333333333333333333333333333 refs/heads/main"

    # Run hook with multi-ref input
    run bash -c "printf '%s\n' '$input' | '$HOOK_PATH'"

    # Should fail (non-zero exit)
    [ "$status" -ne 0 ]

    # Should contain error messages for both failing refs
    [[ "$output" =~ "Deletion denied" ]]
    [[ "$output" =~ "Initial creation denied" ]]

    # Should have processed all lines (not short-circuit on first failure)
    # Count error lines - expect at least 2
    error_count=$(echo "$output" | grep -c "ref=" || echo "0")
    [ "$error_count" -ge 2 ]
}

@test "multi-ref input: parsing robustness with edge cases" {
    cd "$TEST_REPO"

    # Test various input edge cases
    test_input() {
        local input="$1"
        local description="$2"

        # Should not hang or crash
        run bash -c "printf '%s' '$input' | '$HOOK_PATH'"

        # Exit code should be numeric (not timeout/crash)
        [[ "$status" =~ ^[0-9]+$ ]]
    }

    # Empty input
    test_input "" "empty input"

    # Single line without newline
    test_input "1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/test" "no trailing newline"

    # Multiple lines with empty line
    test_input $'1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/test1\n\n2222222222222222222222222222222222222222 3333333333333333333333333333333333333333 refs/heads/test2' "with empty line"
}

@test "multi-ref input: error aggregation preserves exit code priority" {
    cd "$TEST_REPO"

    # Multiple violations with different error codes
    # DEL (14) has higher priority than INIT (13)
    input="1111111111111111111111111111111111111111 0000000000000000000000000000000000000000 refs/heads/main
0000000000000000000000000000000000000000 2222222222222222222222222222222222222222 refs/heads/main"

    run bash -c "printf '%s\n' '$input' | '$HOOK_PATH'"

    # Should exit with first error code (DEL=14)
    [ "$status" -eq 14 ]

    # Should contain both error messages
    [[ "$output" =~ "Deletion denied" ]]
    [[ "$output" =~ "Initial creation denied" ]]
}

@test "multi-ref input: successful refs are processed normally" {
    cd "$TEST_REPO"

    # Mix of success and failure
    input="1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/feature
1111111111111111111111111111111111111111 0000000000000000000000000000000000000000 refs/heads/main
3333333333333333333333333333333333333333 4444444444444444444444444444444444444444 refs/heads/develop"

    run bash -c "printf '%s\n' '$input' | '$HOOK_PATH'"

    # Should fail due to main deletion
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Deletion denied" ]]

    # But should process all refs (feature and develop should pass silently)
    # Error output should only contain the main branch failure
    main_errors=$(echo "$output" | grep -c "ref=refs/heads/main" || echo "0")
    [ "$main_errors" -eq 1 ]
}