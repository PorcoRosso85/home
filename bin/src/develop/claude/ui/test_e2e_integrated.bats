#!/usr/bin/env bats
# End-to-end tests for claude-launcher
# These tests extract and test the complete flow from fzf selection to claude launch

setup() {
  # Create temporary directory for tests
  export TEST_DIR="$(mktemp -d)"
  export ORIGINAL_PWD="$(pwd)"
  cd "$TEST_DIR"
  
  # Set test mode
  export TEST_MODE=1
}

teardown() {
  # Clean up
  cd "$ORIGINAL_PWD"
  rm -rf "$TEST_DIR"
}

# Load all functions into current shell context
load_test_environment() {
  # Define helper functions
  debug_log() {
    if [[ -n "${DEBUG:-}" ]]; then
      echo "[DEBUG] $*" >&2
    fi
  }
  
  normalize_path() {
    local path="$1"
    path=$(eval echo "$path")
    [[ "$path" != /* ]] && path="$(pwd)/$path"
    echo "$path"
  }
  
  # Mock fzf based on environment variables
  fzf() {
    local input=""
    while IFS= read -r line; do
      input="${input}${line}"$'\n'
    done
    
    case "$FZF_MOCK_MODE" in
      "select_existing")
        echo "$FZF_MOCK_QUERY"
        echo "$FZF_MOCK_SELECTION"
        return 0
        ;;
      "new_project")
        echo "$FZF_MOCK_QUERY"
        return 0
        ;;
      "cancel")
        return 130
        ;;
      "empty")
        echo ""
        return 0
        ;;
      *)
        return 1
        ;;
    esac
  }
  
  # Mock claude-code
  claude-code() {
    echo "CLAUDE_MOCK: Launched with args: $*" > "$TEST_DIR/claude-launch.log"
    echo "CLAUDE_MOCK: Working directory: $(pwd)" >> "$TEST_DIR/claude-launch.log"
    echo "CLAUDE_MOCK: Environment NIXPKGS_ALLOW_UNFREE: ${NIXPKGS_ALLOW_UNFREE:-unset}" >> "$TEST_DIR/claude-launch.log"
    
    if [[ "$*" =~ "--continue" ]]; then
      return 1
    fi
    
    return 0
  }
  
  # Main launcher function (extracted from flake.nix)
  run_launcher() {
    debug_log "Starting claude launcher"
    
    # Find all flake.nix files
    files=$(find "$(pwd)" -name "flake.nix" -type f 2>/dev/null | grep -v "/.git/")
    debug_log "Found $(echo "$files" | wc -l) flake.nix files"
    
    # Run fzf selector
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
      
      NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
    elif [[ -n "$selected" ]]; then
      # Existing project mode
      target_dir=$(dirname "$selected")
      debug_log "Existing project mode: $target_dir"
      
      echo "Launching Claude in: $target_dir"
      cd "$target_dir"
      
      # Try with conversation history first
      NIXPKGS_ALLOW_UNFREE=1 claude-code --continue --dangerously-skip-permissions || {
        echo "No conversation history found. Starting new session..."
        NIXPKGS_ALLOW_UNFREE=1 claude-code --dangerously-skip-permissions
      }
    else
      echo "No selection made"
      return 1
    fi
  }
}

@test "e2e: select existing project" {
  load_test_environment
  
  # Create test projects
  mkdir -p "$TEST_DIR/project1"
  mkdir -p "$TEST_DIR/project2"
  echo 'description = "Test project 1";' > "$TEST_DIR/project1/flake.nix"
  echo 'description = "Test project 2";' > "$TEST_DIR/project2/flake.nix"
  
  # Setup mock to select project1
  export FZF_MOCK_MODE="select_existing"
  export FZF_MOCK_QUERY=""
  export FZF_MOCK_SELECTION="$TEST_DIR/project1/flake.nix"
  
  # Run the launcher
  run run_launcher
  
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

@test "e2e: create new project" {
  load_test_environment
  
  # Create a test project to show in list
  mkdir -p "$TEST_DIR/existing"
  echo 'description = "Existing project";' > "$TEST_DIR/existing/flake.nix"
  
  # Setup mock to create new project
  export FZF_MOCK_MODE="new_project"
  export FZF_MOCK_QUERY="$TEST_DIR/new-project"
  export FZF_MOCK_SELECTION=""
  
  # Run the launcher
  run run_launcher
  
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

@test "e2e: cancel selection" {
  load_test_environment
  
  # Create test projects
  mkdir -p "$TEST_DIR/project1"
  echo 'description = "Test project";' > "$TEST_DIR/project1/flake.nix"
  
  # Setup mock to simulate cancellation
  export FZF_MOCK_MODE="cancel"
  export FZF_MOCK_QUERY=""
  export FZF_MOCK_SELECTION=""
  
  # Run the launcher
  run run_launcher
  
  # Verify cancellation was handled
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No selection made" ]]
  
  # Verify claude-code was NOT called
  [ ! -f "$TEST_DIR/claude-launch.log" ]
}

@test "e2e: new project with relative path" {
  load_test_environment
  
  # Setup mock to create new project with relative path
  export FZF_MOCK_MODE="new_project"
  export FZF_MOCK_QUERY="my-new-project"
  export FZF_MOCK_SELECTION=""
  
  # Run the launcher from TEST_DIR
  cd "$TEST_DIR"
  run run_launcher
  
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

@test "e2e: new project with tilde path" {
  load_test_environment
  
  # Create a fake home directory for testing
  export HOME="$TEST_DIR/home"
  mkdir -p "$HOME"
  
  # Setup mock to create new project with tilde path
  export FZF_MOCK_MODE="new_project"
  export FZF_MOCK_QUERY="~/my-project"
  export FZF_MOCK_SELECTION=""
  
  # Run the launcher
  run run_launcher
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Creating new project at: $HOME/my-project" ]]
  
  # Verify directory was created in the correct location
  [ -d "$HOME/my-project" ]
}

@test "e2e: existing project with conversation history" {
  load_test_environment
  
  # Override mock to succeed with --continue
  claude-code() {
    echo "CLAUDE_MOCK: Launched with args: $*" > "$TEST_DIR/claude-launch.log"
    echo "CLAUDE_MOCK: Working directory: $(pwd)" >> "$TEST_DIR/claude-launch.log"
    return 0  # Always succeed
  }
  
  # Create test project
  mkdir -p "$TEST_DIR/project-with-history"
  echo 'description = "Project with history";' > "$TEST_DIR/project-with-history/flake.nix"
  
  # Setup mock to select project with history
  export FZF_MOCK_MODE="select_existing"
  export FZF_MOCK_QUERY=""
  export FZF_MOCK_SELECTION="$TEST_DIR/project-with-history/flake.nix"
  
  # Run the launcher
  run run_launcher
  
  # Verify the flow
  [ "$status" -eq 0 ]
  [[ "$output" =~ "Launching Claude in: $TEST_DIR/project-with-history" ]]
  [[ ! "$output" =~ "No conversation history found" ]]
  
  # Verify claude-code was called with --continue
  [ -f "$TEST_DIR/claude-launch.log" ]
  log_content=$(cat "$TEST_DIR/claude-launch.log")
  [[ "$log_content" =~ "--continue" ]]
}

@test "e2e: empty input handling" {
  load_test_environment
  
  # Setup mock to return empty result
  export FZF_MOCK_MODE="empty"
  export FZF_MOCK_QUERY=""
  export FZF_MOCK_SELECTION=""
  
  # Run the launcher
  run run_launcher
  
  # Verify empty input was handled
  [ "$status" -eq 1 ]
  [[ "$output" =~ "No selection made" ]]
}

@test "e2e: debug mode enabled" {
  load_test_environment
  
  # Enable debug mode
  export DEBUG=1
  
  # Create test project
  mkdir -p "$TEST_DIR/debug-test"
  echo 'description = "Debug test";' > "$TEST_DIR/debug-test/flake.nix"
  
  # Setup mock to select project
  export FZF_MOCK_MODE="select_existing"
  export FZF_MOCK_QUERY=""
  export FZF_MOCK_SELECTION="$TEST_DIR/debug-test/flake.nix"
  
  # Run the launcher
  run run_launcher
  
  # Verify debug output was produced
  [ "$status" -eq 0 ]
  [[ "$output" =~ "[DEBUG] Starting claude launcher" ]]
  [[ "$output" =~ "[DEBUG] Found" ]]
  [[ "$output" =~ "[DEBUG] Existing project mode:" ]]
}