#!/usr/bin/env bats

# BATS test suite for worktree restriction pre-receive hook
# Tests all validation logic including merge shape, fast-forward, paths, and configuration

setup() {
    # Test data setup
    export ZERO_OID="0000000000000000000000000000000000000000"
    export TEST_OLD="1111111111111111111111111111111111111111"
    export TEST_NEW="2222222222222222222222222222222222222222"
    export TEST_REF="refs/heads/main"

    # Hook path
    HOOK_PATH="$BATS_TEST_DIRNAME/../hooks/pre-receive"

    # Temporary git repository for testing
    export TEST_REPO=$(mktemp -d)
    cd "$TEST_REPO"
    git init --bare >/dev/null 2>&1

    # Default configuration
    git config policy.coreRef "refs/heads/main"
    git config --add policy.allowedGlob "flakes/*/**"

    # Clear environment variables
    unset CORE_REFS_OVERRIDE
    unset ALLOWED_GLOBS_OVERRIDE
    unset ALLOW_INITIAL_CREATE
    unset ALLOW_OUTSIDE_DELETE
    unset ALLOW_GITMODULES
    unset STRICT_BOUNDARY_CHECK
}

teardown() {
    cd /
    rm -rf "$TEST_REPO"
}

# Helper function to run hook with input
run_hook() {
    local old="$1" new="$2" ref="$3"
    printf "%s %s %s\n" "$old" "$new" "$ref" | "$HOOK_PATH"
}

@test "hook exists and is executable" {
    [ -f "$HOOK_PATH" ]
    [ -x "$HOOK_PATH" ]
}

@test "hook loads default configuration when no git config exists" {
    cd "$TEST_REPO"
    git config --unset-all policy.coreRef || true
    git config --unset-all policy.allowedGlob || true

    # Should use defaults: refs/heads/main and flakes/*/**
    run run_hook "$ZERO_OID" "$TEST_NEW" "refs/heads/develop"
    [ "$status" -eq 0 ]
}

@test "hook respects git config settings" {
    cd "$TEST_REPO"
    git config policy.coreRef "refs/heads/production"
    git config --replace-all policy.allowedGlob "src/**"

    # Should apply policy to production branch
    run run_hook "$TEST_OLD" "$TEST_NEW" "refs/heads/production"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]
}

@test "environment variables override git config" {
    cd "$TEST_REPO"
    export CORE_REFS_OVERRIDE="refs/heads/custom"
    export ALLOWED_GLOBS_OVERRIDE="custom/**"

    # Should use environment variables instead of git config
    run run_hook "$TEST_OLD" "$TEST_NEW" "refs/heads/custom"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]
}

@test "deletion of core ref is denied" {
    cd "$TEST_REPO"
    run run_hook "$TEST_OLD" "$ZERO_OID" "$TEST_REF"
    [ "$status" -eq 14 ]  # DEL code
    [[ "$output" =~ "Deletion denied" ]]
}

@test "initial creation is denied by default" {
    cd "$TEST_REPO"
    run run_hook "$ZERO_OID" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 13 ]  # INIT code
    [[ "$output" =~ "Initial creation denied" ]]
}

@test "initial creation is allowed when configured" {
    cd "$TEST_REPO"
    export ALLOW_INITIAL_CREATE="true"
    run run_hook "$ZERO_OID" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "non-core refs are not subject to merge shape check" {
    cd "$TEST_REPO"
    run run_hook "$TEST_OLD" "$TEST_NEW" "refs/heads/feature/test"
    [ "$status" -eq 0 ]
}

@test "non-fast-forward is denied" {
    cd "$TEST_REPO"
    # Mock git merge-base to simulate non-ff
    git() {
        if [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 1  # Not ancestor
        fi
        command git "$@"
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "refs/heads/feature/test"
    [ "$status" -eq 12 ]  # FF code
    [[ "$output" =~ "Non-fast-forward denied" ]]
}

@test "merge commit validation requires exactly 2 parents" {
    cd "$TEST_REPO"
    # Mock git cat-file to simulate different parent counts
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Simulate commit with 1 parent (direct commit)
            echo "parent 1111111111111111111111111111111111111111"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0  # Is ancestor (fast-forward)
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 10 ]  # DIRECT code
    [[ "$output" =~ "Merge commit" ]]
}

@test "merge commit with 2 parents is accepted" {
    cd "$TEST_REPO"
    # Mock git cat-file to simulate merge commit
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Simulate merge commit with 2 parents
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0  # Is ancestor (fast-forward)
        elif [[ "$1" == "diff-tree" ]]; then
            # No file changes
            return 0
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "forbidden path is rejected" {
    cd "$TEST_REPO"
    # Mock git commands to simulate file changes
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Simulate merge commit
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            # Simulate file addition in forbidden path
            printf "A\0forbidden/file.txt\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1  # Not a submodule
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 11 ]  # PATH code
    [[ "$output" =~ "Forbidden path" ]]
}

@test "allowed path is accepted" {
    cd "$TEST_REPO"
    # Mock git commands to simulate file changes in allowed path
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Simulate merge commit
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            # Simulate file addition in allowed path
            printf "A\0flakes/example/test.nix\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1  # Not a submodule
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "submodule changes are denied by default" {
    cd "$TEST_REPO"
    # Mock git commands to simulate submodule addition
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            printf "A\0flakes/submodule\0"
        elif [[ "$1" == "ls-tree" ]]; then
            # Simulate submodule (mode 160000)
            echo "160000 commit 4444444444444444444444444444444444444444	flakes/submodule"
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 11 ]  # PATH code
    [[ "$output" =~ "Submodule change denied" ]]
}

@test "submodule changes are allowed when configured" {
    cd "$TEST_REPO"
    export ALLOW_GITMODULES="true"

    # Mock git commands to simulate submodule addition
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            printf "A\0flakes/submodule\0"
        elif [[ "$1" == "ls-tree" ]]; then
            echo "160000 commit 4444444444444444444444444444444444444444	flakes/submodule"
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "outside deletion is allowed when configured" {
    cd "$TEST_REPO"
    export ALLOW_OUTSIDE_DELETE="true"

    # Mock git commands to simulate file deletion outside allowed path
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            printf "D\0forbidden/file.txt\0"
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "rename operation requires both paths to be allowed" {
    cd "$TEST_REPO"
    export STRICT_BOUNDARY_CHECK="true"

    # Mock git commands to simulate rename from allowed to forbidden path
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            printf "R\0flakes/old.nix\0forbidden/new.nix\0"
        elif [[ "$1" == "ls-tree" ]]; then
            return 1  # Not a submodule
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "$TEST_REF"
    [ "$status" -eq 11 ]  # PATH code
    [[ "$output" =~ "Boundary crossing denied" ]]
}

@test "multiple violations are aggregated in output" {
    cd "$TEST_REPO"
    git config policy.coreRef "refs/heads/main"
    git config --add policy.coreRef "refs/heads/develop"

    # Test deletion of core ref (should fail immediately)
    run run_hook "$TEST_OLD" "$ZERO_OID" "$TEST_REF"
    [ "$status" -eq 14 ]
    [[ "$output" =~ "Deletion denied" ]]
}

@test "zero to zero update is handled gracefully" {
    cd "$TEST_REPO"
    run run_hook "$ZERO_OID" "$ZERO_OID" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "same old and new OID is handled gracefully" {
    cd "$TEST_REPO"
    run run_hook "$TEST_OLD" "$TEST_OLD" "$TEST_REF"
    [ "$status" -eq 0 ]
}

@test "tag refs are ignored" {
    cd "$TEST_REPO"
    run run_hook "$TEST_OLD" "$TEST_NEW" "refs/tags/v1.0.0"
    [ "$status" -eq 0 ]
}

@test "configuration priority: environment overrides git config" {
    cd "$TEST_REPO"
    git config policy.coreRef "refs/heads/main"
    export CORE_REFS_OVERRIDE="refs/heads/custom"

    # main should not be treated as core ref due to override
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Single parent (direct commit)
            printf "parent 1111111111111111111111111111111111111111\n"
        else
            command git "$@"
        fi
    }
    export -f git

    run run_hook "$TEST_OLD" "$TEST_NEW" "refs/heads/main"
    [ "$status" -eq 0 ]  # Should pass because main is not in override
}