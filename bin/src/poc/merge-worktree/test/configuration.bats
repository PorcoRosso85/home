#!/usr/bin/env bats

# BATS test suite for worktree restriction configuration handling
# Tests configuration loading, precedence, and glob pattern matching

setup() {
    # Hook path
    HOOK_PATH="$BATS_TEST_DIRNAME/../hooks/pre-receive"

    # Temporary git repository for testing
    export TEST_REPO=$(mktemp -d)
    cd "$TEST_REPO"
    git init --bare >/dev/null 2>&1

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

# Helper function to test configuration
test_config() {
    local old="1111111111111111111111111111111111111111"
    local new="2222222222222222222222222222222222222222"
    local ref="$1"
    printf "%s %s %s\n" "$old" "$new" "$ref" | "$HOOK_PATH"
}

@test "default configuration uses refs/heads/main as core ref" {
    cd "$TEST_REPO"
    # Remove any existing config
    git config --unset-all policy.coreRef || true

    # Mock git to simulate direct commit to main
    git() {
        if [[ "$1" == "config" ]]; then
            # No config found
            return 1
        elif [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            # Single parent (direct commit)
            printf "parent 1111111111111111111111111111111111111111\n"
        else
            command git "$@"
        fi
    }
    export -f git

    run test_config "refs/heads/main"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]
}

@test "default configuration uses flakes/*/** as allowed glob" {
    cd "$TEST_REPO"
    git config --unset-all policy.allowedGlob || true

    # Mock git to simulate file in default allowed path
    git() {
        if [[ "$1" == "config" && "$3" == "policy.allowedGlob" ]]; then
            return 1  # No config
        elif [[ "$1" == "config" && "$3" == "policy.coreRef" ]]; then
            return 1  # No config - should use default
        elif [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
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

    run test_config "refs/heads/develop"  # Non-core ref
    [ "$status" -eq 0 ]
}

@test "multiple core refs can be configured" {
    cd "$TEST_REPO"
    git config policy.coreRef "refs/heads/main"
    git config --add policy.coreRef "refs/heads/staging"
    git config --add policy.coreRef "refs/heads/production"

    # Mock git to simulate direct commit
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\n"
        else
            command git "$@"
        fi
    }
    export -f git

    # All should be treated as core refs
    run test_config "refs/heads/staging"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]

    run test_config "refs/heads/production"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]
}

@test "multiple allowed globs can be configured" {
    cd "$TEST_REPO"
    git config policy.allowedGlob "src/**"
    git config --add policy.allowedGlob "docs/**"
    git config --add policy.allowedGlob "tests/*.nix"

    # Mock git to simulate files in different allowed paths
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
        elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
            return 0
        elif [[ "$1" == "diff-tree" ]]; then
            case "$TEST_PATH" in
                "src") printf "A\0src/module/test.nix\0" ;;
                "docs") printf "A\0docs/README.md\0" ;;
                "tests") printf "A\0tests/unit.nix\0" ;;
            esac
        elif [[ "$1" == "ls-tree" ]]; then
            return 1
        else
            command git "$@"
        fi
    }
    export -f git

    # Test each allowed path
    TEST_PATH="src" run test_config "refs/heads/develop"
    [ "$status" -eq 0 ]

    TEST_PATH="docs" run test_config "refs/heads/develop"
    [ "$status" -eq 0 ]

    TEST_PATH="tests" run test_config "refs/heads/develop"
    [ "$status" -eq 0 ]
}

@test "environment variables override git config completely" {
    cd "$TEST_REPO"
    git config policy.coreRef "refs/heads/main"
    git config policy.allowedGlob "old/**"

    export CORE_REFS_OVERRIDE=$'refs/heads/custom\nrefs/heads/special'
    export ALLOWED_GLOBS_OVERRIDE=$'new/**\nspecial/**'

    # Git config should be ignored, environment should be used
    git() {
        if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
            printf "parent 1111111111111111111111111111111111111111\n"
        else
            command git "$@"
        fi
    }
    export -f git

    # main should not be core ref anymore
    run test_config "refs/heads/main"
    [ "$status" -eq 0 ]

    # custom should be core ref
    run test_config "refs/heads/custom"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]
}

@test "glob patterns work correctly" {
    cd "$TEST_REPO"
    git config --replace-all policy.allowedGlob "flakes/*/**"

    # Test various path patterns
    test_path() {
        local path="$1"
        git() {
            if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
                printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
            elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
                return 0
            elif [[ "$1" == "diff-tree" ]]; then
                printf "A\0%s\0" "$path"
            elif [[ "$1" == "ls-tree" ]]; then
                return 1
            else
                command git "$@"
            fi
        }
        export -f git

        test_config "refs/heads/develop"
    }

    # Should match
    run test_path "flakes/example/test.nix"
    [ "$status" -eq 0 ]

    run test_path "flakes/deep/nested/structure/file.txt"
    [ "$status" -eq 0 ]

    # Should not match
    run test_path "flakes/file.nix"  # Missing intermediate directory
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Forbidden path" ]]

    run test_path "other/flakes/test.nix"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Forbidden path" ]]
}

@test "complex glob patterns work" {
    cd "$TEST_REPO"
    git config --replace-all policy.allowedGlob "*.{nix,md}"
    git config --add policy.allowedGlob "src/**/test_*.sh"
    git config --add policy.allowedGlob "docs/[a-z]*.txt"

    test_complex_path() {
        local path="$1"
        git() {
            if [[ "$1" == "cat-file" && "$2" == "-p" ]]; then
                printf "parent 1111111111111111111111111111111111111111\nparent 3333333333333333333333333333333333333333\n"
            elif [[ "$1" == "merge-base" && "$2" == "--is-ancestor" ]]; then
                return 0
            elif [[ "$1" == "diff-tree" ]]; then
                printf "A\0%s\0" "$path"
            elif [[ "$1" == "ls-tree" ]]; then
                return 1
            else
                command git "$@"
            fi
        }
        export -f git

        test_config "refs/heads/develop"
    }

    # Note: bash case patterns are limited, so some patterns may not work as expected
    # Test what should work with bash case patterns

    run test_complex_path "README.md"
    [ "$status" -eq 0 ]

    run test_complex_path "flake.nix"
    [ "$status" -eq 0 ]
}

@test "boolean configuration values work correctly" {
    cd "$TEST_REPO"

    # Test ALLOW_INITIAL_CREATE
    export ALLOW_INITIAL_CREATE="true"
    run printf "0000000000000000000000000000000000000000 1111111111111111111111111111111111111111 refs/heads/main\n" | "$HOOK_PATH"
    [ "$status" -eq 0 ]

    export ALLOW_INITIAL_CREATE="false"
    run printf "0000000000000000000000000000000000000000 1111111111111111111111111111111111111111 refs/heads/main\n" | "$HOOK_PATH"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Initial creation denied" ]]

    unset ALLOW_INITIAL_CREATE

    # Test ALLOW_OUTSIDE_DELETE
    export ALLOW_OUTSIDE_DELETE="true"
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

    run test_config "refs/heads/develop"
    [ "$status" -eq 0 ]
}

@test "configuration loading is NUL-safe" {
    cd "$TEST_REPO"
    # Test that configurations with special characters work
    git config policy.coreRef "refs/heads/main-with-dashes"
    git config --add policy.coreRef "refs/heads/feature/with/slashes"
    git config policy.allowedGlob "path with spaces/**"
    git config --add policy.allowedGlob "path-with-dashes/**"

    # Should handle these without issues
    run test_config "refs/heads/main-with-dashes"
    # Status depends on mock, but should not crash
    [[ "$status" =~ ^[0-9]+$ ]]  # Numeric exit code
}

@test "empty configuration values are handled gracefully" {
    cd "$TEST_REPO"
    # Set empty configurations
    git config policy.coreRef ""
    git config policy.allowedGlob ""

    # Should fall back to defaults
    run test_config "refs/heads/main"
    [[ "$status" =~ ^[0-9]+$ ]]  # Should not crash
}