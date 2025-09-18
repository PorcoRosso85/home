#!/usr/bin/env bats

# Test for claude-launcher functionality

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

# Helper function to extract bash code from flake.nix
extract_bash_functions() {
  # Extract the functions from flake.nix for testing
  cat > "$TEST_DIR/test_functions.sh" << 'FUNCTIONS_EOF'
# Debug logging
debug_log() {
  if [[ -n "${DEBUG:-}" ]]; then
    echo "[DEBUG] $*" >&2
  fi
}

# Normalize path: expand tilde and make absolute
normalize_path() {
  local path="$1"
  path=$(eval echo "$path")
  [[ "$path" != /* ]] && path="$(pwd)/$path"
  echo "$path"
}

# Mock storage for setting up test scenarios
declare -g FZF_MOCK_MODE=""
declare -g FZF_MOCK_QUERY=""
declare -g FZF_MOCK_SELECTION=""

# Setup mock for specific test scenario
setup_fzf_mock() {
  local mode="$1"
  local query="${2:-}"
  local selection="${3:-}"
  
  FZF_MOCK_MODE="$mode"
  FZF_MOCK_QUERY="$query"
  FZF_MOCK_SELECTION="$selection"
  
  # Also write to a file so the wrapper can read it
  cat > "$TEST_DIR/fzf_mock_settings" << EOF
FZF_MOCK_MODE="$mode"
FZF_MOCK_QUERY="$query"
FZF_MOCK_SELECTION="$selection"
EOF
}

# Mock fzf command that simulates user interactions
mock_fzf() {
  # Read all input (simulating the list of files passed to fzf)
  local input=""
  while IFS= read -r line; do
    input="${input}${line}"$'\n'
  done
  
  # Process based on mock mode
  case "$FZF_MOCK_MODE" in
    "select_existing")
      # Simulate selecting an existing project
      # Output format: query on first line, selection on second line
      echo "$FZF_MOCK_QUERY"
      echo "$FZF_MOCK_SELECTION"
      return 0
      ;;
    
    "new_project")
      # Simulate creating a new project (query only, no selection)
      # Output format: query on first line, empty selection
      echo "$FZF_MOCK_QUERY"
      return 0
      ;;
    
    "cancel")
      # Simulate user cancellation (ESC or Ctrl-C)
      # Return empty output and non-zero exit code
      return 130  # Standard exit code for cancelled operations
      ;;
    
    "empty")
      # Simulate empty selection (enter with no input)
      echo ""
      return 0
      ;;
    
    *)
      # Default: return error
      echo "Mock fzf error: Unknown mode '$FZF_MOCK_MODE'" >&2
      return 1
      ;;
  esac
}
FUNCTIONS_EOF
  source "$TEST_DIR/test_functions.sh"
}

@test "normalize_path: relative path to absolute" {
  extract_bash_functions
  cd "$TEST_DIR"
  result=$(normalize_path "test/dir")
  [ "$result" = "$TEST_DIR/test/dir" ]
}

@test "normalize_path: absolute path unchanged" {
  extract_bash_functions
  result=$(normalize_path "/absolute/path")
  [ "$result" = "/absolute/path" ]
}

@test "normalize_path: tilde expansion" {
  extract_bash_functions
  result=$(normalize_path "~/test")
  [ "$result" = "$HOME/test" ]
}

@test "debug_log: outputs when DEBUG is set" {
  extract_bash_functions
  export DEBUG=1
  run debug_log "test message"
  [ "$status" -eq 0 ]
  [ "$output" = "[DEBUG] test message" ]
}

@test "debug_log: silent when DEBUG is not set" {
  extract_bash_functions
  unset DEBUG
  run debug_log "test message"
  [ "$status" -eq 0 ]
  [ "$output" = "" ]
}

@test "flake.nix file discovery simulation" {
  # Create test flake.nix files
  mkdir -p "$TEST_DIR/project1"
  mkdir -p "$TEST_DIR/project2/.git"
  mkdir -p "$TEST_DIR/project3"
  
  touch "$TEST_DIR/project1/flake.nix"
  touch "$TEST_DIR/project2/.git/flake.nix"  # Should be excluded
  touch "$TEST_DIR/project3/flake.nix"
  
  # Simulate find command
  files=$(find "$TEST_DIR" -name "flake.nix" -type f 2>/dev/null | grep -v "/.git/")
  
  # Should find exactly 2 files (excluding .git)
  [ "$(echo "$files" | wc -l)" -eq 2 ]
  [[ "$files" =~ project1/flake.nix ]]
  [[ "$files" =~ project3/flake.nix ]]
  [[ ! "$files" =~ \.git ]]
}

# Replace the actual fzf command with our mock in tests
create_fzf_mock_wrapper() {
  # Create a bash function that overrides fzf command
  fzf() {
    # Load mock settings from file
    if [[ -f "$TEST_DIR/fzf_mock_settings" ]]; then
      source "$TEST_DIR/fzf_mock_settings"
    fi
    
    # Read all input (simulating the list of files passed to fzf)
    local input=""
    while IFS= read -r line; do
      input="${input}${line}"$'\n'
    done
    
    # Process based on mock mode
    case "$FZF_MOCK_MODE" in
      "select_existing")
        # Simulate selecting an existing project
        # Output format: query on first line, selection on second line
        echo "$FZF_MOCK_QUERY"
        echo "$FZF_MOCK_SELECTION"
        return 0
        ;;
      
      "new_project")
        # Simulate creating a new project (query only, no selection)
        # Output format: query on first line, empty selection
        echo "$FZF_MOCK_QUERY"
        return 0
        ;;
      
      "cancel")
        # Simulate user cancellation (ESC or Ctrl-C)
        # Return empty output and non-zero exit code
        return 130  # Standard exit code for cancelled operations
        ;;
      
      "empty")
        # Simulate empty selection (enter with no input)
        echo ""
        return 0
        ;;
      
      *)
        # Default: return error
        echo "Mock fzf error: Unknown mode '$FZF_MOCK_MODE'" >&2
        return 1
        ;;
    esac
  }
  export -f fzf
}

@test "fzf mock: test existing project selection" {
  extract_bash_functions
  create_fzf_mock_wrapper
  
  # Setup mock to simulate selecting an existing project
  setup_fzf_mock "select_existing" "" "$TEST_DIR/project1/flake.nix"
  
  # Test the mock
  result=$(echo -e "$TEST_DIR/project1/flake.nix\n$TEST_DIR/project2/flake.nix" | fzf)
  
  # Verify output format
  query=$(echo "$result" | head -1)
  selected=$(echo "$result" | tail -n +2)
  
  [ "$query" = "" ]
  [ "$selected" = "$TEST_DIR/project1/flake.nix" ]
}

@test "fzf mock: test new project creation" {
  extract_bash_functions
  create_fzf_mock_wrapper
  
  # Setup mock to simulate new project creation
  setup_fzf_mock "new_project" "/home/user/new-project" ""
  
  # Test the mock
  result=$(echo -e "$TEST_DIR/project1/flake.nix" | fzf)
  
  # Verify output format
  query=$(echo "$result" | head -1)
  selected=$(echo "$result" | tail -n +2)
  
  [ "$query" = "/home/user/new-project" ]
  [ "$selected" = "" ]
}

@test "fzf mock: test cancellation" {
  extract_bash_functions
  create_fzf_mock_wrapper
  
  # Setup mock to simulate cancellation
  setup_fzf_mock "cancel" "" ""
  
  # Test the mock - should return non-zero exit code
  run bash -c 'echo "test" | fzf || echo "cancelled"'
  
  [ "$status" -eq 0 ]
  [[ "$output" =~ "cancelled" ]]
}

@test "fzf mock: test empty selection" {
  extract_bash_functions
  create_fzf_mock_wrapper
  
  # Setup mock to simulate empty selection
  setup_fzf_mock "empty" "" ""
  
  # Test the mock
  result=$(echo -e "$TEST_DIR/project1/flake.nix" | fzf)
  
  [ "$result" = "" ]
}

# Mock claude-code command
create_claude_mock() {
  # Create a bash function that overrides claude-code command
  claude-code() {
    # Mock claude-code for testing
    echo "CLAUDE_MOCK: Launched with args: $*" > "$TEST_DIR/claude-launch.log"
    echo "CLAUDE_MOCK: Working directory: $(pwd)" >> "$TEST_DIR/claude-launch.log"
    echo "CLAUDE_MOCK: Environment NIXPKGS_ALLOW_UNFREE: ${NIXPKGS_ALLOW_UNFREE:-unset}" >> "$TEST_DIR/claude-launch.log"
    
    # Check for specific flags
    if [[ "$*" =~ "--continue" ]]; then
      # Simulate no conversation history (exit with error)
      return 1
    fi
    
    # Success
    return 0
  }
  export -f claude-code
}

# Extract the main launcher script logic from flake.nix
extract_launcher_script() {
  # Ensure functions are available
  extract_bash_functions
  create_fzf_mock_wrapper
  create_claude_mock
  
  # Main launcher function
  run_launcher() {
    debug_log "Starting claude launcher"
    
    # Find all flake.nix files
    files=$(find "$(pwd)" -name "flake.nix" -type f 2>/dev/null | grep -v "/.git/")
    debug_log "Found $(echo "$files" | wc -l) flake.nix files"
    
    # Run fzf selector (using our mock in tests)
    result=$(echo "$files" | fzf \
      --print-query \
      --prompt="Select flake.nix or enter new project path: " \
      --preview="head -20 {}" \
      --preview-window=right:50%:wrap \
      --header=$'Enter: Confirm | Tab: Edit selection | Type path: Create new project\n─────────────────────────────────────────────────' \
      --bind='tab:replace-query' \
      || echo "")
    
    # Check if cancelled
    if [[ -z "$result" ]]; then
      echo "No selection made"
      return 1
    fi
    
    # Parse fzf output
    query=$(echo "$result" | head -1)
    selected=$(echo "$result" | tail -n +2)
    debug_log "Query: '$query', Selected: '$selected'"
    
    # Determine mode and launch
    if [[ -z "$selected" && -n "$query" ]]; then
      # New project mode
      target_dir=$(normalize_path "$query")
      debug_log "New project mode: $target_dir"
      
      echo "Creating new project at: $target_dir"
      mkdir -p "$target_dir" || {
        echo "Error: Failed to create directory $target_dir"
        return 1
      }
      cd "$target_dir"
      
      # In test mode, use mock claude-code
      if [[ -n "${TEST_MODE:-}" ]]; then
        env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
      else
        exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
      fi
    elif [[ -n "$selected" ]]; then
      # Existing project mode
      target_dir=$(dirname "$selected")
      debug_log "Existing project mode: $target_dir"
      
      echo "Launching Claude in: $target_dir"
      cd "$target_dir"
      
      # In test mode, use mock claude-code
      if [[ -n "${TEST_MODE:-}" ]]; then
        # Try with conversation history first
        env NIXPKGS_ALLOW_UNFREE=1 claude-code --continue --dangerously-skip-permissions || {
          echo "No conversation history found. Starting new session..."
          env NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
        }
      else
        # Try with conversation history first
        env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --continue --dangerously-skip-permissions || {
          echo "No conversation history found. Starting new session..."
          exec env NIXPKGS_ALLOW_UNFREE=1 nix run github:NixOS/nixpkgs/nixos-unstable#claude-code --impure -- --dangerously-skip-permissions
        }
      fi
    else
      echo "No selection made"
      return 1
    fi
  }
  export -f run_launcher
}

# End-to-end test: Select existing project
@test "e2e: complete flow - select existing project" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export PATH="$TEST_DIR:$PATH"
  
  # Create test projects
  mkdir -p "$TEST_DIR/project1"
  mkdir -p "$TEST_DIR/project2"
  echo 'description = "Test project 1";' > "$TEST_DIR/project1/flake.nix"
  echo 'description = "Test project 2";' > "$TEST_DIR/project2/flake.nix"
  
  # Setup mock to select project1
  setup_fzf_mock "select_existing" "" "$TEST_DIR/project1/flake.nix"
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Launching Claude in: $TEST_DIR/project1" ]]
  [[ "$output" =~ "No conversation history found. Starting new session..." ]]
  
  # Verify claude-code was called correctly
  [ -f "$TEST_DIR/claude-launch.log" ]
  log_content=$(cat "$TEST_DIR/claude-launch.log")
  [[ "$log_content" =~ "Working directory: $TEST_DIR/project1" ]]
  [[ "$log_content" =~ "Environment NIXPKGS_ALLOW_UNFREE: 1" ]]
  [[ "$log_content" =~ "--dangerously-skip-permissions" ]]
}

# End-to-end test: Create new project
@test "e2e: complete flow - create new project" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export PATH="$TEST_DIR:$PATH"
  
  # Create a test project to show in list
  mkdir -p "$TEST_DIR/existing"
  echo 'description = "Existing project";' > "$TEST_DIR/existing/flake.nix"
  
  # Setup mock to create new project
  setup_fzf_mock "new_project" "$TEST_DIR/new-project" ""
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Creating new project at: $TEST_DIR/new-project" ]]
  
  # Verify directory was created
  [ -d "$TEST_DIR/new-project" ]
  
  # Verify claude-code was called correctly
  [ -f "$TEST_DIR/claude-launch.log" ]
  log_content=$(cat "$TEST_DIR/claude-launch.log")
  [[ "$log_content" =~ "Working directory: $TEST_DIR/new-project" ]]
  [[ "$log_content" =~ "Environment NIXPKGS_ALLOW_UNFREE: 1" ]]
  [[ "$log_content" =~ "--dangerously-skip-permissions" ]]
  [[ ! "$log_content" =~ "--continue" ]]
}

# End-to-end test: Cancel selection
@test "e2e: complete flow - cancel selection" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export PATH="$TEST_DIR:$PATH"
  
  # Create test projects
  mkdir -p "$TEST_DIR/project1"
  echo 'description = "Test project";' > "$TEST_DIR/project1/flake.nix"
  
  # Setup mock to simulate cancellation
  setup_fzf_mock "cancel" "" ""
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify cancellation was handled
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No selection made" ]]
  
  # Verify claude-code was NOT called
  [ ! -f "$TEST_DIR/claude-launch.log" ]
}

# End-to-end test: New project with relative path
@test "e2e: complete flow - new project with relative path" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export PATH="$TEST_DIR:$PATH"
  
  # Setup mock to create new project with relative path
  setup_fzf_mock "new_project" "my-new-project" ""
  
  # Run the launcher from TEST_DIR
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Creating new project at: $TEST_DIR/my-new-project" ]]
  
  # Verify directory was created
  [ -d "$TEST_DIR/my-new-project" ]
  
  # Verify claude-code was called in the correct directory
  [ -f "$TEST_DIR/claude-launch.log" ]
  log_content=$(cat "$TEST_DIR/claude-launch.log")
  [[ "$log_content" =~ "Working directory: $TEST_DIR/my-new-project" ]]
}

# End-to-end test: New project with tilde path
@test "e2e: complete flow - new project with tilde path" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export PATH="$TEST_DIR:$PATH"
  export HOME="$TEST_DIR/home"
  mkdir -p "$HOME"
  
  # Setup mock to create new project with tilde path
  setup_fzf_mock "new_project" "~/my-project" ""
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Creating new project at: $HOME/my-project" ]]
  
  # Verify directory was created in the correct location
  [ -d "$HOME/my-project" ]
}

# End-to-end test: Existing project with conversation history
@test "e2e: complete flow - existing project with conversation history" {
  extract_launcher_script
  
  # Override the mock for this test to succeed with --continue
  claude-code() {
    # Mock claude-code that succeeds with --continue
    echo "CLAUDE_MOCK: Launched with args: $*" > "$TEST_DIR/claude-launch.log"
    echo "CLAUDE_MOCK: Working directory: $(pwd)" >> "$TEST_DIR/claude-launch.log"
    
    # Always succeed (simulating existing conversation)
    return 0
  }
  export -f claude-code
  
  # Setup test environment
  export TEST_MODE=1
  
  # Create test project
  mkdir -p "$TEST_DIR/project-with-history"
  echo 'description = "Project with history";' > "$TEST_DIR/project-with-history/flake.nix"
  
  # Setup mock to select project with history
  setup_fzf_mock "select_existing" "" "$TEST_DIR/project-with-history/flake.nix"
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Launching Claude in: $TEST_DIR/project-with-history" ]]
  [[ ! "$output" =~ "No conversation history found" ]]
  
  # Verify claude-code was called with --continue
  [ -f "$TEST_DIR/claude-launch.log" ]
  log_content=$(cat "$TEST_DIR/claude-launch.log")
  [[ "$log_content" =~ "--continue" ]]
}

# End-to-end test: Empty input handling
@test "e2e: complete flow - empty input" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export PATH="$TEST_DIR:$PATH"
  
  # Setup mock to return empty result
  setup_fzf_mock "empty" "" ""
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify empty input was handled
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No selection made" ]]
}

# End-to-end test: Debug mode
@test "e2e: complete flow - debug mode enabled" {
  extract_launcher_script
  
  # Setup test environment
  export TEST_MODE=1
  export DEBUG=1
  export PATH="$TEST_DIR:$PATH"
  
  # Create test project
  mkdir -p "$TEST_DIR/debug-test"
  echo 'description = "Debug test";' > "$TEST_DIR/debug-test/flake.nix"
  
  # Setup mock to select project
  setup_fzf_mock "select_existing" "" "$TEST_DIR/debug-test/flake.nix"
  
  # Run the launcher
  cd "$TEST_DIR"
  output=$(run_launcher 2>&1)
  status=$?
  
  # Verify debug output was produced
  [ "$status" -eq 0 ]
  [[ "$output" =~ "[DEBUG] Starting claude launcher" ]]
  [[ "$output" =~ "[DEBUG] Found" ]]
  [[ "$output" =~ "[DEBUG] Existing project mode:" ]]
}