#!/usr/bin/env bats

# Integration tests for worktree restriction system
# Uses real git repositories for authentic testing

setup() {
    # Create test repositories
    export TEST_BARE=$(mktemp -d)
    export TEST_WORK=$(mktemp -d)

    # Initialize bare repository
    cd "$TEST_BARE"
    git init --bare >/dev/null 2>&1

    # Set up hook
    HOOK_SOURCE="$BATS_TEST_DIRNAME/../hooks/pre-receive"
    cp "$HOOK_SOURCE" "$TEST_BARE/hooks/pre-receive"
    chmod +x "$TEST_BARE/hooks/pre-receive"

    # Configure policies
    git config policy.coreRef "refs/heads/main"
    git config --add policy.allowedGlob "flakes/*/**"
    git config --add policy.allowedGlob "allowed/**"

    # Initialize working repository
    cd "$TEST_WORK"
    git init >/dev/null 2>&1
    git remote add origin "$TEST_BARE"

    # Set up git user for commits
    git config user.name "Test User"
    git config user.email "test@example.com"

    # Create initial commit on a non-core branch first with allowed path
    mkdir -p flakes/init
    echo "{ }" > flakes/init/flake.nix
    git add flakes/
    git commit -m "Initial commit" >/dev/null 2>&1
    git push origin HEAD:refs/heads/develop >/dev/null 2>&1
}

teardown() {
    cd /
    rm -rf "$TEST_BARE" "$TEST_WORK"
}

@test "hook installation works" {
    [ -f "$TEST_BARE/hooks/pre-receive" ]
    [ -x "$TEST_BARE/hooks/pre-receive" ]
}

@test "push to non-core branch succeeds" {
    cd "$TEST_WORK"
    echo "feature work" > feature.txt
    git add feature.txt
    git commit -m "Add feature" >/dev/null 2>&1

    # Push to non-core branch should succeed
    run git push origin HEAD:refs/heads/feature
    [ "$status" -eq 0 ]
}

@test "push to allowed path succeeds on non-core branch" {
    cd "$TEST_WORK"
    mkdir -p flakes/test
    echo "{ }" > flakes/test/flake.nix
    git add flakes/
    git commit -m "Add flake" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/feature-flakes
    [ "$status" -eq 0 ]
}

@test "push to forbidden path fails on any branch" {
    cd "$TEST_WORK"
    mkdir -p forbidden
    echo "content" > forbidden/file.txt
    git add forbidden/
    git commit -m "Add forbidden file" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/feature-forbidden
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Forbidden path" ]]
}

@test "direct commit to core branch fails" {
    cd "$TEST_WORK"

    # First establish main branch with allowed content
    mkdir -p flakes/init
    echo "{ }" > flakes/init/flake.nix
    git add flakes/
    git commit -m "Initial main commit" >/dev/null 2>&1

    # This should fail due to merge-only policy
    run git push origin HEAD:refs/heads/main
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Merge commit" ]]
}

@test "initial creation of core branch fails by default" {
    cd "$TEST_WORK"
    git checkout --orphan new-main >/dev/null 2>&1
    echo "new main" > main.txt
    git add main.txt
    git commit -m "New main branch" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/main
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Initial creation denied" ]]
}

@test "initial creation allowed when configured" {
    cd "$TEST_BARE"
    # Configure to allow initial creation
    echo 'export ALLOW_INITIAL_CREATE="true"' >> hooks/pre-receive

    cd "$TEST_WORK"
    git checkout --orphan allowed-main >/dev/null 2>&1
    mkdir -p flakes/start
    echo "{ }" > flakes/start/flake.nix
    git add flakes/
    git commit -m "Start main branch" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/main
    [ "$status" -eq 0 ]
}

@test "deletion of core branch fails" {
    cd "$TEST_WORK"

    # First create main branch
    cd "$TEST_BARE"
    echo 'export ALLOW_INITIAL_CREATE="true"' >> hooks/pre-receive

    cd "$TEST_WORK"
    git checkout --orphan temp-main >/dev/null 2>&1
    mkdir -p flakes/temp
    echo "{ }" > flakes/temp/flake.nix
    git add flakes/
    git commit -m "Temp main" >/dev/null 2>&1
    git push origin HEAD:refs/heads/main >/dev/null 2>&1

    # Now try to delete it
    run git push origin :refs/heads/main
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Deletion denied" ]]
}

@test "environment variable configuration override works" {
    cd "$TEST_BARE"
    # Override configuration via environment
    cat >> hooks/pre-receive << 'EOF'
export CORE_REFS_OVERRIDE="refs/heads/custom"
export ALLOWED_GLOBS_OVERRIDE="custom/**"
EOF

    cd "$TEST_WORK"
    mkdir -p custom
    echo "content" > custom/file.txt
    git add custom/
    git commit -m "Custom content" >/dev/null 2>&1

    # Push to main should succeed (not a core ref anymore)
    run git push origin HEAD:refs/heads/main
    [ "$status" -eq 0 ]

    # But custom should be restricted (even though it's a direct commit,
    # since we haven't implemented merge checking for non-existent branches)
    mkdir -p flakes/other
    echo "{ }" > flakes/other/flake.nix
    git add flakes/
    git commit -m "Non-custom content" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/custom
    # This should fail due to wrong path (flakes not in custom/**)
    [ "$status" -ne 0 ]
}

@test "hook respects git config policies" {
    cd "$TEST_BARE"
    # Change policy
    git config --replace-all policy.allowedGlob "docs/**"
    git config --add policy.allowedGlob "src/**"

    cd "$TEST_WORK"
    mkdir -p docs
    echo "documentation" > docs/README.md
    git add docs/
    git commit -m "Add docs" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/feature-docs
    [ "$status" -eq 0 ]

    # But flakes should now be forbidden
    mkdir -p flakes/test
    echo "{ }" > flakes/test/flake.nix
    git add flakes/
    git commit -m "Add flake" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/feature-flakes-forbidden
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Forbidden path" ]]
}

@test "multiple violations are reported" {
    cd "$TEST_WORK"

    # Create a commit that violates multiple rules
    mkdir -p forbidden/deep
    echo "bad content" > forbidden/deep/file.txt
    mkdir -p another-forbidden
    echo "more bad content" > another-forbidden/file.txt
    git add forbidden/ another-forbidden/
    git commit -m "Multiple violations" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/feature-multi-violations
    [ "$status" -ne 0 ]
    # Should report multiple forbidden paths
    [[ "$output" =~ "Forbidden path" ]]
}

@test "complex glob patterns work" {
    cd "$TEST_BARE"
    git config --replace-all policy.allowedGlob "*.md"
    git config --add policy.allowedGlob "src/*/test_*.sh"

    cd "$TEST_WORK"

    # Test simple pattern
    echo "readme content" > README.md
    git add README.md
    git commit -m "Add README" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/readme-test
    [ "$status" -eq 0 ]

    # Test more complex pattern
    mkdir -p src/module
    echo "#!/bin/bash" > src/module/test_unit.sh
    git add src/
    git commit -m "Add test script" >/dev/null 2>&1

    run git push origin HEAD:refs/heads/test-script
    [ "$status" -eq 0 ]
}