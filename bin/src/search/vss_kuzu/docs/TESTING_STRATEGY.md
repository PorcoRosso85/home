# VSS KuzuDB Testing Strategy

## Overview

This document describes the testing strategy for vss_kuzu package, following the testing conventions.

## Test Layers (Following DDD)

### 1. Domain Layer Tests ✅
- **Status**: All tests passing
- **Files**: `test_domain.py`
- **Focus**: Pure business logic without external dependencies
- **Test types**: Unit tests for vector similarity calculations

### 2. Application Layer Tests ⚠️
- **Status**: Requires VECTOR extension
- **Files**: `test_application.py`, `test_legacy_api.py`
- **Focus**: Integration tests for use cases
- **Requirement**: KuzuDB with VECTOR extension installed

### 3. Infrastructure Layer Tests ⚠️
- **Status**: Requires VECTOR extension
- **Files**: `test_infrastructure.py`, `test_initialization.py`
- **Focus**: Real database interactions
- **Requirement**: KuzuDB with VECTOR extension installed

## Running Tests

### Domain Layer Only (No Dependencies)
```bash
nix run .#test -- test_domain.py -v
```

### All Tests (Requires VECTOR Extension)
```bash
# First install VECTOR extension
nix run .#install-vector -- --db-path ./test_db --create-if-missing

# Then run all tests
nix run .#test
```

## Test Environment Setup

Since VECTOR extension is a core requirement for VSS functionality:

1. **Local Development**
   - Install VECTOR extension using the provided script
   - Tests will fail without it (by design)

2. **CI Environment**
   - Must install VECTOR extension before running tests
   - Add installation step to CI pipeline

3. **Mock Testing**
   - Not recommended for infrastructure layer
   - Violates the "Refactoring Wall" principle
   - Real database tests provide better confidence

## Test Philosophy Compliance

Following the "Refactoring Wall" principle:
- Domain tests: Can be written without seeing implementation ✅
- Application/Infrastructure tests: Test observable behavior ✅
- No private method testing ✅
- No implementation detail testing ✅

## Error Handling in Tests

Per error handling conventions:
- VECTOR extension absence causes RuntimeError (critical failure) ✅
- No fallback to alternative implementations ✅
- Errors are explicit and informative ✅