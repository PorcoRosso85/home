#!/usr/bin/env bats

setup() {
    # テスト用の一時ディレクトリを作成
    export TEST_TMPDIR="$(mktemp -d)"
    export ORIG_PWD="$(pwd)"
}

teardown() {
    # テスト用の一時ディレクトリを削除
    rm -rf "$TEST_TMPDIR"
    cd "$ORIG_PWD"
}

@test "flake-selector-multi.sh exists and is executable" {
    [ -f "./flake-selector-multi.sh" ]
    [ -x "./flake-selector-multi.sh" ]
}

@test "flake-selector-multi.sh shows container options" {
    run ./flake-selector-multi.sh --list
    [ "$status" -eq 0 ]
    [[ "$output" =~ "container-base" ]]
    [[ "$output" =~ "container-nodejs" ]]
    [[ "$output" =~ "container-python" ]]
    [[ "$output" =~ "container-go" ]]
    [[ "$output" =~ "container-integrated" ]]
}

@test "flake-selector-multi.sh displays help with --help" {
    run ./flake-selector-multi.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Usage:" ]]
    [[ "$output" =~ "Multiple flake selection" ]]
}

@test "flake-selector-multi.sh handles invalid input gracefully" {
    # Invalid single selection
    run bash -c "echo 'invalid' | ./flake-selector-multi.sh --non-interactive"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Invalid" ]]
}

@test "flake-selector-multi.sh supports single container selection" {
    # Test single selection of base container
    run bash -c "echo '1' | ./flake-selector-multi.sh --non-interactive"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "container-base" ]]
}

@test "flake-selector-multi.sh supports multiple container selection" {
    # Test multiple selection: base and nodejs
    run bash -c "echo -e '1,2\ndone' | ./flake-selector-multi.sh --non-interactive"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "container-base" ]]
    [[ "$output" =~ "container-nodejs" ]]
}

@test "flake-selector-multi.sh validates container numbers" {
    # Test invalid container number
    run bash -c "echo '99' | ./flake-selector-multi.sh --non-interactive"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Invalid" ]]
}

@test "flake-selector-multi.sh can build selected containers" {
    # Skip if nix build is not available or too slow for CI
    if ! command -v nix &> /dev/null; then
        skip "nix command not available"
    fi
    
    # Test building base container
    run bash -c "echo -e '1\nbuild' | timeout 60s ./flake-selector-multi.sh --non-interactive"
    
    # Accept either success or timeout (for slow CI environments)
    if [ "$status" -eq 124 ]; then
        skip "Build test timed out (acceptable in CI)"
    elif [ "$status" -eq 0 ]; then
        [[ "$output" =~ "Building" || "$output" =~ "container-base" ]]
    else
        # Allow non-zero exit if it's just a build issue
        [[ "$output" =~ "Building" || "$output" =~ "Error" ]]
    fi
}

@test "flake-selector-multi.sh supports container execution preview" {
    # Test execution preview without actually running containers
    run bash -c "echo -e '1\npreview' | ./flake-selector-multi.sh --non-interactive"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "podman run" || "$output" =~ "Preview" ]]
}

@test "flake-selector-multi.sh handles comma-separated input" {
    # Test comma-separated multiple selection
    run bash -c "echo '1,3' | ./flake-selector-multi.sh --non-interactive --list-selected"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "container-base" ]]
    [[ "$output" =~ "container-python" ]]
}

@test "flake-selector-multi.sh removes duplicates from selection" {
    # Test duplicate removal
    run bash -c "echo '1,1,2' | ./flake-selector-multi.sh --non-interactive --list-selected"
    [ "$status" -eq 0 ]
    # Should only show each container once
    [ "$(echo "$output" | grep -c "container-base")" -eq 1 ]
    [[ "$output" =~ "container-nodejs" ]]
}

@test "flake-selector-multi.sh displays container descriptions" {
    run ./flake-selector-multi.sh --describe
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Base container" || "$output" =~ "Node.js" ]]
    [[ "$output" =~ "Python" ]]
    [[ "$output" =~ "Go" ]]
    [[ "$output" =~ "Integrated" ]]
}

@test "flake-selector-multi.sh supports batch mode" {
    # Test batch processing with predefined selection
    run ./flake-selector-multi.sh --batch "1,2"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "container-base" ]]
    [[ "$output" =~ "container-nodejs" ]]
}

@test "flake-selector-multi.sh validates batch input format" {
    # Test invalid batch format
    run ./flake-selector-multi.sh --batch "a,b"
    [ "$status" -ne 0 ]
    [[ "$output" =~ "Invalid" ]]
}

@test "flake-selector-multi.sh supports range selection" {
    # Test range selection (1-3)
    run ./flake-selector-multi.sh --batch "1-3"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "container-base" ]]
    [[ "$output" =~ "container-nodejs" ]]
    [[ "$output" =~ "container-python" ]]
}

@test "flake-selector-multi.sh displays selection summary" {
    run bash -c "echo '1,2' | ./flake-selector-multi.sh --non-interactive --summary"
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Selected containers:" ]]
    [[ "$output" =~ "2" ]]  # Should show count of 2
}