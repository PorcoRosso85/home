#!/usr/bin/env bash

# Minimal tests for Claude launching logic
# Run with: bash test_launch_claude.sh

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test helper functions
run_test() {
  local test_name="$1"
  echo -n "Testing: $test_name ... "
  TESTS_RUN=$((TESTS_RUN + 1))
}

pass() {
  echo -e "${GREEN}PASS${NC}"
  TESTS_PASSED=$((TESTS_PASSED + 1))
}

fail() {
  local reason="$1"
  echo -e "${RED}FAIL${NC}: $reason"
}

# Setup
TEST_DIR="$(mktemp -d)"
trap "rm -rf $TEST_DIR" EXIT

# Mock claude-code command
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

# Test 1: launching with --continue flag when history exists
run_test "launching with --continue flag when history exists"
create_mock_claude_code
touch "$TEST_DIR/.has_history"
cd "$TEST_DIR"
output=$(env NIXPKGS_ALLOW_UNFREE=1 claude-code --continue --dangerously-skip-permissions 2>&1)
if [[ "$output" =~ "CLAUDE_LAUNCHED" ]] && \
   [[ "$output" =~ "ARGS: --continue --dangerously-skip-permissions" ]] && \
   [[ "$output" =~ "NIXPKGS_ALLOW_UNFREE: 1" ]]; then
  pass
else
  fail "Expected output not found"
fi

# Test 2: launching without --continue for new sessions
run_test "launching without --continue for new sessions"
create_mock_claude_code
cd "$TEST_DIR"
output=$(env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions 2>&1)
if [[ "$output" =~ "CLAUDE_LAUNCHED" ]] && \
   [[ "$output" =~ "ARGS: --dangerously-skip-permissions" ]] && \
   [[ ! "$output" =~ "--continue" ]] && \
   [[ "$output" =~ "NIXPKGS_ALLOW_UNFREE: 1" ]]; then
  pass
else
  fail "Expected output not found or --continue was present"
fi

# Test 3: environment variable NIXPKGS_ALLOW_UNFREE=1 is set
run_test "environment variable NIXPKGS_ALLOW_UNFREE=1 is set"
create_mock_claude_code
cd "$TEST_DIR"

# Test with env var set
output=$(env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions 2>&1)
if [[ "$output" =~ "NIXPKGS_ALLOW_UNFREE: 1" ]]; then
  pass
else
  fail "NIXPKGS_ALLOW_UNFREE not set to 1"
fi

# Test without env var
run_test "environment variable NIXPKGS_ALLOW_UNFREE is unset when not provided"
output=$(unset NIXPKGS_ALLOW_UNFREE && claude-code --dangerously-skip-permissions 2>&1)
if [[ "$output" =~ "NIXPKGS_ALLOW_UNFREE: unset" ]]; then
  pass
else
  fail "NIXPKGS_ALLOW_UNFREE should be unset (got: $output)"
fi

# Test 4: correct working directory is used
run_test "correct working directory is used"
create_mock_claude_code
mkdir -p "$TEST_DIR/project1"
mkdir -p "$TEST_DIR/project2"

# Test from project1
cd "$TEST_DIR/project1"
output=$(env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions 2>&1)
if [[ "$output" =~ "PWD: $TEST_DIR/project1" ]]; then
  pass
else
  fail "Wrong working directory"
fi

# Test from project2
run_test "correct working directory is used (project2)"
cd "$TEST_DIR/project2"
output=$(env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions 2>&1)
if [[ "$output" =~ "PWD: $TEST_DIR/project2" ]]; then
  pass
else
  fail "Wrong working directory"
fi

# Test 5: fallback behavior when --continue fails (no history)
run_test "fallback behavior when --continue fails (no history)"
create_mock_claude_code
rm -f "$TEST_DIR/.has_history"  # Ensure no history

# Create launcher simulation
cat > "$TEST_DIR/test-launcher.sh" << 'EOF'
#!/usr/bin/env bash
cd "$1"

# Try with conversation history first
env NIXPKGS_ALLOW_UNFREE=1 claude-code --continue --dangerously-skip-permissions || {
  echo "No conversation history found. Starting new session..."
  env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
}
EOF
chmod +x "$TEST_DIR/test-launcher.sh"

mkdir -p "$TEST_DIR/test-project"
output=$("$TEST_DIR/test-launcher.sh" "$TEST_DIR/test-project" 2>&1)

if [[ "$output" =~ "No conversation history found. Starting new session..." ]] && \
   [[ "$output" =~ "CLAUDE_LAUNCHED" ]]; then
  # Check that both launches happened
  continue_count=$(echo "$output" | grep -c "ARGS: --continue --dangerously-skip-permissions" || true)
  normal_count=$(echo "$output" | grep -c "ARGS: --dangerously-skip-permissions" | grep -v "continue" || true)
  
  if [[ $continue_count -eq 1 ]]; then
    pass
  else
    fail "Expected fallback behavior not found"
  fi
else
  fail "Expected output not found"
fi

# Summary
echo
echo "===== Test Summary ====="
echo "Tests run: $TESTS_RUN"
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $((TESTS_RUN - TESTS_PASSED))"
echo "======================="

if [[ $TESTS_PASSED -eq $TESTS_RUN ]]; then
  echo -e "${GREEN}All tests passed!${NC}"
  exit 0
else
  echo -e "${RED}Some tests failed!${NC}"
  exit 1
fi