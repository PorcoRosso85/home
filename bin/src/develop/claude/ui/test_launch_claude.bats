#!/usr/bin/env bats

# Minimal tests for Claude launching logic

setup() {
  # Create temporary directory for tests
  export TEST_DIR="$(mktemp -d)"
  export ORIGINAL_PWD="$(pwd)"
  cd "$TEST_DIR"
}

teardown() {
  # Clean up
  cd "$ORIGINAL_PWD"
  rm -rf "$TEST_DIR"
}

# Helper to create mock claude-code
create_mock_claude_code() {
  cat > "$TEST_DIR/claude-code" << EOF
#!/usr/bin/env bash
echo "CLAUDE_LAUNCHED"
echo "ARGS: \$*"
echo "PWD: \$(pwd)"
echo "NIXPKGS_ALLOW_UNFREE: \${NIXPKGS_ALLOW_UNFREE:-unset}"

# Check for --continue flag
if [[ "\$*" =~ "--continue" ]]; then
  if [[ -f "$TEST_DIR/.has_history" ]]; then
    exit 0  # Success with history
  else
    exit 1  # No history found
  fi
fi
exit 0
EOF
  chmod +x "$TEST_DIR/claude-code"
  export PATH="$TEST_DIR:$PATH"
}

@test "launching with --continue flag when history exists" {
  create_mock_claude_code
  touch "$TEST_DIR/.has_history"
  
  cd "$TEST_DIR"
  run env NIXPKGS_ALLOW_UNFREE=1 claude-code --continue --dangerously-skip-permissions
  
  [ "$status" -eq 0 ]
  [[ "${output}" =~ "CLAUDE_LAUNCHED" ]]
  [[ "${output}" =~ "ARGS: --continue --dangerously-skip-permissions" ]]
  [[ "${output}" =~ "NIXPKGS_ALLOW_UNFREE: 1" ]]
}

@test "launching without --continue for new sessions" {
  create_mock_claude_code
  
  cd "$TEST_DIR"
  run env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
  
  [ "$status" -eq 0 ]
  [[ "${output}" =~ "CLAUDE_LAUNCHED" ]]
  [[ "${output}" =~ "ARGS: --dangerously-skip-permissions" ]]
  [[ ! "${output}" =~ "--continue" ]]
  [[ "${output}" =~ "NIXPKGS_ALLOW_UNFREE: 1" ]]
}

@test "environment variable NIXPKGS_ALLOW_UNFREE=1 is set" {
  create_mock_claude_code
  
  cd "$TEST_DIR"
  run env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
  
  [ "$status" -eq 0 ]
  [[ "${output}" =~ "NIXPKGS_ALLOW_UNFREE: 1" ]]
  
  # Test without setting the variable
  run claude-code --dangerously-skip-permissions
  
  [ "$status" -eq 0 ]
  [[ "${output}" =~ "NIXPKGS_ALLOW_UNFREE: unset" ]]
}

@test "correct working directory is used" {
  create_mock_claude_code
  
  mkdir -p "$TEST_DIR/project1"
  mkdir -p "$TEST_DIR/project2"
  
  # Test launching from project1
  cd "$TEST_DIR/project1"
  run env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
  
  [ "$status" -eq 0 ]
  [[ "${output}" =~ "PWD: $TEST_DIR/project1" ]]
  
  # Test launching from project2
  cd "$TEST_DIR/project2"
  run env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
  
  [ "$status" -eq 0 ]
  [[ "${output}" =~ "PWD: $TEST_DIR/project2" ]]
}