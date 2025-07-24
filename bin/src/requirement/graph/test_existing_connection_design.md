# existing_connection Test Design Document

## Overview
This document outlines the test strategy for the `existing_connection` parameter functionality in the requirement/graph module.

## Current State Analysis

### Implementation Summary
- **SearchAdapter**: Accepts `repository_connection` parameter and passes it to VSS/FTS adapters
- **VSSSearchAdapter**: Receives connection, enables VECTOR extension, passes to `create_vss()`
- **FTSSearchAdapter**: Receives connection, passes to `create_fts()`
- **kuzu_repository**: Creates single connection, exposes via `"connection"` key

### Testing Gap
- No existing tests for `existing_connection` functionality
- All current tests create new database instances
- Integration tests use subprocess calls with isolated databases

## Test Strategy

### 1. Unit Tests (`test_existing_connection.py`)

#### Test Cases
1. **Connection Sharing Verification**
   - Verify SearchAdapter uses provided connection
   - Ensure VSS/FTS services receive the same connection
   - Check that no new connections are created

2. **Extension Initialization**
   - Test VECTOR extension enablement on existing connection
   - Handle cases where extension is already loaded
   - Verify error handling for extension failures

3. **Service Initialization**
   - Test VSS service initialization with existing connection
   - Test FTS service initialization with existing connection
   - Verify both services can coexist on same connection

4. **Error Scenarios**
   - Invalid connection object
   - Closed connection
   - Connection without required permissions

### 2. Integration Tests (updates to existing tests)

#### Test Approach
Following the established pattern of subprocess-based integration tests:

1. **Modify test_search_integration.py**
   - Add test that verifies connection reuse behavior
   - Use process monitoring to ensure single connection

2. **Performance Validation**
   - Compare initialization time with/without existing_connection
   - Verify memory usage doesn't increase with reused connections

### 3. Testing Philosophy Compliance

- **No Mocks**: Use real KuzuDB connections with in-memory databases
- **Observable Behavior**: Test through public APIs and measurable outputs
- **Value-Driven**: Focus on the value of connection reuse (performance, consistency)

## Implementation Plan

### Phase 2: Unit Tests
1. Create `test_existing_connection.py` with real database tests
2. Test connection sharing mechanics
3. Verify extension initialization behavior
4. Test error handling with real scenarios

### Phase 3: Integration Tests
1. Enhance existing integration tests to validate connection reuse
2. Add performance benchmarks
3. Ensure backward compatibility

### Phase 4: Documentation
1. Update SearchAdapter README with connection sharing examples
2. Document performance benefits
3. Add troubleshooting guide for connection issues

## Success Criteria

1. All tests pass with `nix run .#test`
2. No regression in existing functionality
3. Measurable performance improvement with connection reuse
4. Clear documentation for users