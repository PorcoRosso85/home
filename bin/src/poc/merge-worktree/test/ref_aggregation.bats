#!/usr/bin/env bats

# Single ref multiple violation aggregation tests
# Ensures all validators run and report violations for a single ref

setup() {
    # Hook path
    HOOK_PATH="$BATS_TEST_DIRNAME/../hooks/pre-receive"

    # Temporary git repository for testing
    export TEST_REPO=$(mktemp -d)
    cd "$TEST_REPO"
    git init --bare >/dev/null 2>&1

    # Configure policies for multiple violations
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

@test "single ref: multiple violations aggregated (merge shape + forbidden path)" {
    cd "$TEST_REPO"

    # Mock git commands to simulate:
    # 1. Non-merge commit (fails check_merge_shape)
    # 2. File in forbidden path (fails check_paths)
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Single parent (fails merge shape check)
            printf "parent 1111111111111111111111111111111111111111\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0  # Fast-forward OK
        elif [[ "$1" == "diff-tree" ]]; then
            # File in forbidden path (fails path check)
            printf "A\0forbidden/file.txt\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1  # Not a submodule
        else
            command git "$@"
        fi
    }
    export -f git

    run bash -c "echo '1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/main' | '$HOOK_PATH'"

    # Should fail
    [ "$status" -ne 0 ]

    # Should contain BOTH violation messages:
    # 1. Merge commit violation (DIRECT code 10)
    # 2. Forbidden path violation (PATH code 11)
    [[ "$output" =~ "Merge commit" ]]
    [[ "$output" =~ "Forbidden path" ]]

    # Should have exactly 2 error lines for same ref
    error_count=$(echo "$output" | grep -c "ref=refs/heads/main" || echo "0")
    [ "$error_count" -eq 2 ]
}

@test "single ref: aggregation preserves first error code priority" {
    cd "$TEST_REPO"

    # Simulate scenario with DIRECT (10) and PATH (11) violations
    # Should exit with first violation code (10)
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            printf "A\0forbidden/file.txt\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1
        else
            command git "$@"
        fi
    }
    export -f git

    run bash -c "echo '1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/main' | '$HOOK_PATH'"

    # Should exit with first error code (DIRECT = 10)
    [ "$status" -eq 10 ]

    # But should contain both messages
    [[ "$output" =~ "Merge commit" ]]
    [[ "$output" =~ "Forbidden path" ]]
}

@test "single ref: fast-forward + path violations aggregated" {
    cd "$TEST_REPO"

    # Mock git to simulate:
    # 1. Non-fast-forward (fails check_ff)
    # 2. Forbidden path (fails check_paths)
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Two parents (passes merge shape)
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 1  # Not ancestor (fails fast-forward)
        elif [[ "$1" == "diff-tree" ]]; then
            printf "A\0forbidden/file.txt\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1
        else
            command git "$@"
        fi
    }
    export -f git

    run bash -c "echo '1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/main' | '$HOOK_PATH'"

    # Should fail
    [ "$status" -ne 0 ]

    # Should contain BOTH violation messages:
    # 1. Fast-forward violation (FF code 12)
    # 2. Forbidden path violation (PATH code 11)
    [[ "$output" =~ "Non-fast-forward denied" ]]
    [[ "$output" =~ "Forbidden path" ]]

    # Error count verification
    error_count=$(echo "$output" | grep -c "ref=refs/heads/main" || echo "0")
    [ "$error_count" -eq 2 ]
}

@test "single ref: successful validation produces no errors" {
    cd "$TEST_REPO"

    # Mock successful scenario (non-core ref)
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            printf "A\0flakes/test/file.nix\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1
        else
            command git "$@"
        fi
    }
    export -f git

    run bash -c "echo '1111111111111111111111111111111111111111 2222222222222222222222222222222222222222 refs/heads/feature' | '$HOOK_PATH'"

    # Should succeed
    [ "$status" -eq 0 ]

    # Should have no error output
    [ -z "$output" ]
}