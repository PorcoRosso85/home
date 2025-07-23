# VSS KuzuDB Testing Strategy

## Overview

This document describes the testing strategy for vss_kuzu package, emphasizing the function-first architecture and automatic test environment handling.

## Test Layers (Following DDD)

### 1. Domain Layer Tests ✅
- **Status**: All tests passing
- **Files**: `test_domain.py`
- **Focus**: Pure business logic without external dependencies
- **Test types**: Unit tests for vector similarity calculations and value objects

### 2. Application Layer Tests ✅
- **Status**: All tests passing (with automatic wrapper)
- **Files**: `test_application.py`, `test_unified_api.py`
- **Focus**: Function behavior and use case orchestration
- **Note**: Automatically uses subprocess wrapper when VECTOR extension unavailable

### 3. Infrastructure Layer Tests ✅
- **Status**: All tests passing (with automatic wrapper)
- **Files**: `test_infrastructure.py`, `test_initialization.py`
- **Focus**: Repository patterns and database interactions
- **Note**: Tests real KuzuDB behavior via wrapper when needed

### 4. End-to-End Tests ✅
- **Status**: All tests passing
- **Files**: `test_e2e.py`
- **Focus**: Full workflow validation from API to database
- **Note**: Uses wrapper for missing VECTOR extension

## Running Tests

### Quick Start (No Setup Required)
```bash
# Run all tests - wrapper handles missing VECTOR extension
nix run .#test
```

### Specific Test Categories
```bash
# Domain tests only (pure logic)
nix run .#test -- test_domain.py -v

# Application tests (with automatic wrapper)
nix run .#test -- test_application.py -v

# Infrastructure tests (with automatic wrapper)
nix run .#test -- test_infrastructure.py -v

# End-to-end tests
nix run .#test -- test_e2e.py -v
```

## Test Environment Handling

The test suite automatically adapts to the environment:

### 1. Development Environment (No VECTOR Extension)
- **Automatic Detection**: Tests detect missing VECTOR extension
- **Subprocess Wrapper**: `vector_subprocess_wrapper.py` activates automatically
- **Full Test Coverage**: All tests pass without manual setup
- **Performance**: Slightly slower due to subprocess overhead

### 2. Production-Like Environment (With VECTOR Extension)
```bash
# Install VECTOR extension for production-like testing
nix run .#install-vector -- --db-path ./test_db --create-if-missing

# Run tests with native extension
nix run .#test
```

### 3. CI/CD Environment
- **Option 1**: Run tests with wrapper (recommended for speed)
- **Option 2**: Install VECTOR extension for production validation
- **Both approaches**: Provide full test coverage

## Test Philosophy Compliance

Following the "Refactoring Wall" principle:
- **Domain tests**: Pure logic tests without implementation details ✅
- **Application tests**: Focus on function behavior and contracts ✅
- **Infrastructure tests**: Test repository patterns, not KuzuDB internals ✅
- **No private method testing**: Only public API tested ✅
- **Behavior-focused**: Tests describe what, not how ✅

## Function-First Testing Approach

The new architecture enables better testing:
1. **Pure Functions**: Easy to test in isolation
2. **Explicit Dependencies**: Repository passed as parameter
3. **Clear Contracts**: Type hints guide test expectations
4. **Composable Tests**: Functions can be tested individually or composed

## Error Handling Strategy

### Production Behavior
- VECTOR extension absence causes `RuntimeError` (critical failure) ✅
- No silent fallbacks or degraded modes ✅
- Clear error messages for troubleshooting ✅

### Test Environment Behavior
- Automatic wrapper activation for missing extension ✅
- Tests continue to validate behavior ✅
- Production error paths still testable ✅

## Wrapper Implementation Details

The `vector_subprocess_wrapper.py`:
- Spawns a subprocess with VECTOR extension mock
- Handles all VECTOR extension operations
- Transparent to test code
- Only active during tests, never in production