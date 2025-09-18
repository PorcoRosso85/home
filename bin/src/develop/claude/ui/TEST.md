# Claude Launcher Test Suite Documentation

## Overview

The Claude launcher project includes comprehensive end-to-end tests that verify all functionality of the interactive flake.nix selector and Claude Code launcher. The test suite ensures that the launcher behaves correctly in all user scenarios.

## Running Tests

### Quick Test Run
```bash
# Run all tests
nix run .#test

# Or use flake check (runs tests as part of checks)
nix flake check
```

### Development Testing
```bash
# Enter development shell with testing tools
nix develop

# Run tests directly with bats
bats test_e2e_integrated.bats

# Run specific test
bats test_e2e_integrated.bats -f "create new project"

# Run with debug output
DEBUG=1 bats test_e2e_integrated.bats
```

## What is Tested

The test suite provides complete coverage of the launcher's functionality:

### 1. **Project Selection Flow**
- Selecting existing projects from the fzf list
- Handling multiple flake.nix files in subdirectories
- Excluding .git directories from search results

### 2. **New Project Creation**
- Creating new projects with absolute paths
- Creating new projects with relative paths
- Creating new projects with tilde (~) expansion
- Directory creation and error handling

### 3. **User Interaction Scenarios**
- Cancellation handling (ESC/Ctrl-C)
- Empty input handling
- Query vs selection differentiation

### 4. **Claude Code Integration**
- Launching with correct working directory
- Setting NIXPKGS_ALLOW_UNFREE=1 environment variable
- Passing --dangerously-skip-permissions flag
- Attempting --continue for existing conversations
- Fallback to new session when no history exists

### 5. **Path Normalization**
- Relative to absolute path conversion
- Tilde expansion
- Proper working directory changes

### 6. **Debug Mode**
- Debug logging when DEBUG environment variable is set
- Proper stderr output for debug messages

### 7. **Edge Cases**
- Empty fzf results
- Failed directory creation
- Missing conversation history

## Test Architecture

### Mock System

The tests use a sophisticated mocking system to simulate user interactions:

1. **FZF Mock**: Simulates user selections without requiring actual fzf interaction
   - `select_existing`: User selects an existing project
   - `new_project`: User types a new project path
   - `cancel`: User cancels (ESC/Ctrl-C)
   - `empty`: User presses enter with no selection

2. **Claude Code Mock**: Captures launch parameters and verifies correct invocation
   - Logs working directory
   - Logs command-line arguments
   - Logs environment variables
   - Simulates --continue success/failure

### Test Environment

Each test runs in an isolated temporary directory to ensure:
- No interference between tests
- Clean state for each test
- Safe cleanup after completion

## Adding New Tests

To add new tests, follow this pattern:

```bash
@test "e2e: description of test scenario" {
  load_test_environment
  
  # Setup test environment (create files, directories)
  mkdir -p "$TEST_DIR/test-project"
  echo 'description = "Test";' > "$TEST_DIR/test-project/flake.nix"
  
  # Configure mock behavior
  export FZF_MOCK_MODE="select_existing"
  export FZF_MOCK_QUERY=""
  export FZF_MOCK_SELECTION="$TEST_DIR/test-project/flake.nix"
  
  # Run the launcher
  run run_launcher
  
  # Verify behavior
  [ "$status" -eq 0 ]
  [[ "$output" =~ "expected output" ]]
  
  # Verify side effects
  [ -f "$TEST_DIR/expected-file" ]
}
```

## Test Coverage for Refactoring

The test suite provides complete protection for refactoring by:

1. **Behavior Verification**: Tests verify observable behavior, not implementation details
2. **End-to-End Testing**: Tests exercise the complete flow from user input to Claude launch
3. **Mock Isolation**: Implementation can be changed without modifying tests
4. **Comprehensive Scenarios**: All user paths through the application are tested

This means you can safely:
- Refactor the bash script structure
- Change internal function implementations  
- Modify the fzf integration approach
- Update path handling logic

As long as the tests pass, the user-facing behavior remains correct.

## Continuous Integration

The tests are integrated into the Nix flake checks, ensuring:
- Tests run automatically with `nix flake check`
- Build failures if tests don't pass
- Consistent test environment across machines