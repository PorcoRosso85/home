#!/usr/bin/env bats

# Help text clarity and completeness tests
# Ensures important information is clearly documented

@test "help text includes error code table" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should include error codes table
    [[ "$output" =~ "ERROR CODES" ]]
    [[ "$output" =~ "10" ]]  # DIRECT
    [[ "$output" =~ "11" ]]  # PATH
    [[ "$output" =~ "12" ]]  # FF
    [[ "$output" =~ "13" ]]  # INIT
    [[ "$output" =~ "14" ]]  # DEL
}

@test "help text clarifies tag handling policy" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should explicitly mention tags are ignored
    [[ "$output" =~ "tag" ]]
    [[ "$output" =~ "ignore" ]]
}

@test "help text clarifies bash case pattern semantics" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should clarify bash case patterns (not globstar)
    [[ "$output" =~ "bash case pattern" ]]

    # Should clarify no globstar requirement
    [[ "$output" =~ "WITHOUT shopt" ]]
    [[ "$output" =~ "NOT standard globstar" ]]
}

@test "help text shows configuration priority clearly" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should show ENV > Config > Default priority
    [[ "$output" =~ "Priority:" ]]
    [[ "$output" =~ "ENV variables" ]]
}

@test "help text includes submodule policy" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should mention submodule default denial
    [[ "$output" =~ "Submodule" ]]
    [[ "$output" =~ "denied by default" ]]
}

@test "help text includes boundary crossing policy" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should mention boundary crossing policy
    [[ "$output" =~ "Boundary crossing" ]]
    [[ "$output" =~ "disabled by default" ]]
}

@test "help text mentions core branch protection" {
    run nix run .#help
    [ "$status" -eq 0 ]

    # Should clarify merge-only policy
    [[ "$output" =~ "merge-only" ]]
    [[ "$output" =~ "core branch" ]]
}