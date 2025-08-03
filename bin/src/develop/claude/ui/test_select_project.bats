#!/usr/bin/env bats

# Test for project selection logic

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

# Extract selection functions for testing
setup_selection_functions() {
  cat > "$TEST_DIR/selection_functions.sh" << 'FUNCTIONS_EOF'
# Normalize path: expand tilde and make absolute
normalize_path() {
  local path="$1"
  path=$(eval echo "$path")
  [[ "$path" != /* ]] && path="$(pwd)/$path"
  echo "$path"
}

# Parse fzf output and determine selection mode
parse_selection() {
  local result="$1"
  
  # Empty result means cancellation
  if [[ -z "$result" ]]; then
    echo "cancelled"
    return 1
  fi
  
  # Parse query and selection
  local query=$(echo "$result" | head -1)
  local selected=$(echo "$result" | tail -n +2)
  
  # Check if both query and selected are empty (whitespace only input)
  if [[ -z "$query" && -z "$selected" ]]; then
    echo "cancelled"
    return 1
  fi
  
  # Determine mode
  if [[ -z "$selected" && -n "$query" ]]; then
    echo "new:$query"
  elif [[ -n "$selected" ]]; then
    echo "existing:$selected"
  else
    echo "cancelled"
    return 1
  fi
}

# Process selection and return target directory
process_selection() {
  local mode_and_path="$1"
  local mode="${mode_and_path%%:*}"
  local path="${mode_and_path#*:}"
  
  case "$mode" in
    "new")
      echo "$(normalize_path "$path")"
      ;;
    "existing")
      echo "$(dirname "$path")"
      ;;
    *)
      return 1
      ;;
  esac
}
FUNCTIONS_EOF
  source "$TEST_DIR/selection_functions.sh"
}

# Test successful existing project selection
@test "select existing project - returns directory path" {
  setup_selection_functions
  
  # Simulate fzf output for existing project selection
  fzf_output=$'
/home/user/project1/flake.nix'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "existing:/home/user/project1/flake.nix" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "/home/user/project1" ]
}

# Test new project creation - absolute path
@test "create new project - absolute path" {
  setup_selection_functions
  
  # Simulate fzf output for new project
  fzf_output=$'/home/user/new-project
'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "new:/home/user/new-project" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "/home/user/new-project" ]
}

# Test new project creation - relative path
@test "create new project - relative path" {
  setup_selection_functions
  cd "$TEST_DIR"
  
  # Simulate fzf output for new project with relative path
  fzf_output=$'my-new-project
'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "new:my-new-project" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "$TEST_DIR/my-new-project" ]
}

# Test new project creation - tilde path
@test "create new project - tilde path expansion" {
  setup_selection_functions
  export HOME="$TEST_DIR/home"
  mkdir -p "$HOME"
  
  # Simulate fzf output for new project with tilde
  fzf_output=$'~/my-project
'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "new:~/my-project" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "$HOME/my-project" ]
}

# Test cancellation - empty result
@test "cancellation - empty result" {
  setup_selection_functions
  
  # Simulate empty fzf output (user cancelled)
  fzf_output=""
  
  # Parse selection should fail
  run parse_selection "$fzf_output"
  [ "$status" -eq 1 ]
  [ "$output" = "cancelled" ]
}

# Test cancellation - only whitespace
@test "cancellation - whitespace only" {
  setup_selection_functions
  
  # Simulate fzf output with only whitespace
  fzf_output=$'
'
  
  # Parse selection should fail
  run parse_selection "$fzf_output"
  [ "$status" -eq 1 ]
  [ "$output" = "cancelled" ]
}

# Test selection with spaces in path
@test "select project with spaces in path" {
  setup_selection_functions
  
  # Simulate fzf output with spaces in path
  fzf_output=$'
/home/user/my project/flake.nix'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "existing:/home/user/my project/flake.nix" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "/home/user/my project" ]
}

# Test new project with trailing slash
@test "new project - trailing slash handling" {
  setup_selection_functions
  cd "$TEST_DIR"
  
  # Simulate fzf output with trailing slash
  fzf_output=$'new-project/
'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "new:new-project/" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "$TEST_DIR/new-project/" ]
}

# Test deeply nested project selection
@test "select deeply nested project" {
  setup_selection_functions
  
  # Simulate fzf output for deeply nested project
  fzf_output=$'
/home/user/projects/category/subcategory/my-app/flake.nix'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "existing:/home/user/projects/category/subcategory/my-app/flake.nix" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "/home/user/projects/category/subcategory/my-app" ]
}

# Test normalize_path function directly
@test "normalize_path - various path types" {
  setup_selection_functions
  cd "$TEST_DIR"
  export HOME="$TEST_DIR/home"
  mkdir -p "$HOME"
  
  # Test absolute path
  result=$(normalize_path "/absolute/path")
  [ "$result" = "/absolute/path" ]
  
  # Test relative path
  result=$(normalize_path "relative/path")
  [ "$result" = "$TEST_DIR/relative/path" ]
  
  # Test tilde expansion
  result=$(normalize_path "~/test")
  [ "$result" = "$HOME/test" ]
  
  # Test current directory
  result=$(normalize_path ".")
  [ "$result" = "$TEST_DIR/." ]
  
  # Test parent directory
  result=$(normalize_path "..")
  [ "$result" = "$TEST_DIR/.." ]
}

# Test edge case - query with newline but no selection
@test "new project - query with trailing newline" {
  setup_selection_functions
  
  # Simulate fzf output where user typed path and pressed enter
  # This has query but empty selection (common for new project)
  fzf_output=$'/path/to/new/project
'
  
  # Parse selection
  result=$(parse_selection "$fzf_output")
  [ "$?" -eq 0 ]
  [ "$result" = "new:/path/to/new/project" ]
  
  # Process selection
  target_dir=$(process_selection "$result")
  [ "$?" -eq 0 ]
  [ "$target_dir" = "/path/to/new/project" ]
}