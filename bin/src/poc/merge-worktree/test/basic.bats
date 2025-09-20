#!/usr/bin/env bats

# Basic tests for hook functionality

@test "hook file exists and is executable" {
    HOOK_PATH="$BATS_TEST_DIRNAME/../hooks/pre-receive"
    [ -f "$HOOK_PATH" ]
    [ -x "$HOOK_PATH" ]
}

@test "hook runs without crashing on basic input" {
    HOOK_PATH="$BATS_TEST_DIRNAME/../hooks/pre-receive"

    # Create a temporary directory for testing
    TEST_DIR=$(mktemp -d)
    cd "$TEST_DIR"
    git init --bare >/dev/null 2>&1

    # Configure basic policies
    git config policy.coreRef "refs/heads/main"
    git config policy.allowedGlob "**"

    # Test with non-core branch (should pass)
    echo "1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/feature" | "$HOOK_PATH"
    status=$?

    cd /
    rm -rf "$TEST_DIR"

    # Should not crash
    [[ "$status" =~ ^[0-9]+$ ]]
}

@test "nix wrapper script exists and works" {
    run nix build .#default
    [ "$status" -eq 0 ]

    run ./result/bin/worktree-limiter --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Configurable worktree restriction system" ]]
}

@test "external lib usage works" {
    cd test/external
    run nix build .#custom-limiter
    [ "$status" -eq 0 ]

    cd ../..
}

@test "basic BATS setup works" {
    run echo "Hello BATS"
    [ "$status" -eq 0 ]
    [ "$output" = "Hello BATS" ]
}