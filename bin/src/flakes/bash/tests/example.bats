#!/usr/bin/env bats

# Sample tests for Bash development environment
# These tests verify that all development tools are available and working

@test "bash command is available" {
    run which bash
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}

@test "bash version is reasonable" {
    run bash --version
    [ "$status" -eq 0 ]
    [[ "$output" =~ "GNU bash" ]]
}

@test "shellcheck command is available" {
    run which shellcheck
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}

@test "shellcheck can analyze simple script" {
    # Create a temporary script with a minor issue
    temp_script=$(mktemp)
    echo '#!/bin/bash' > "$temp_script"
    echo 'echo $USER' >> "$temp_script"  # Missing quotes around $USER
    
    run shellcheck "$temp_script"
    [ "$status" -eq 1 ]  # Should find the quoting issue
    [[ "$output" =~ "SC2086" ]]  # Specific shellcheck rule for unquoted variables
    
    rm "$temp_script"
}

@test "shfmt command is available" {
    run which shfmt
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}

@test "shfmt can format simple script" {
    # Create a poorly formatted script
    temp_script=$(mktemp)
    echo '#!/bin/bash' > "$temp_script"
    echo 'if [ true ];then' >> "$temp_script"  # Poor formatting
    echo 'echo "hello"' >> "$temp_script"
    echo 'fi' >> "$temp_script"
    
    run shfmt "$temp_script"
    [ "$status" -eq 0 ]
    # Check that the output contains properly formatted if statement
    [[ "$output" =~ "; then" ]]  # Should have proper spacing after condition
    
    rm "$temp_script"
}

@test "bats command is available" {
    run which bats
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}

@test "bash-language-server is available" {
    run which bash-language-server
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}

@test "sample bash script execution" {
    # Test that we can run a simple bash script
    temp_script=$(mktemp)
    echo '#!/bin/bash' > "$temp_script"
    echo 'echo "Hello from Bash development environment"' >> "$temp_script"
    chmod +x "$temp_script"
    
    run bash "$temp_script"
    [ "$status" -eq 0 ]
    [ "$output" = "Hello from Bash development environment" ]
    
    rm "$temp_script"
}

@test "environment variables are accessible" {
    run bash -c 'echo $HOME'
    [ "$status" -eq 0 ]
    [ "$output" != "" ]
}