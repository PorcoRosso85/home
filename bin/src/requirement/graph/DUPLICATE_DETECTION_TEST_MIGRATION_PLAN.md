# Duplicate Detection Test Migration Plan

## Coverage Comparison Report

### Original E2E Test Scenarios
From `test_e2e_guardrail_workflow.py`:
1. **Duplicate Requirement ID Test** (lines 344-360)
   - Scenario: Insert requirement with duplicate ID
   - Expected: Failure with "duplicated primary key" error
   - Execution Time: ~500ms (includes DB setup)

### Proposed Test Layer Migration

#### Fast Layer (Unit Tests) - Target: <100ms per test
Location: `tests/fast/test_duplicate_detection_rules.py`

| Test Scenario | Description | Original E2E Coverage |
|--------------|-------------|----------------------|
| `test_duplicate_id_validation` | Validate ID format without DB | Partial - validation logic |
| `test_duplicate_detection_logic` | Pure logic for duplicate checking | New - extracted from DB logic |
| `test_id_normalization` | Test ID normalization rules | New - prevent case variants |
| `test_id_pattern_matching` | Validate ID patterns (REQ-*, SEC-*) | New - business rule |

#### Mid Layer (Integration Tests) - Target: <1s per test  
Location: `tests/mid/test_duplicate_detection_integration.py`

| Test Scenario | Description | Original E2E Coverage |
|--------------|-------------|----------------------|
| `test_duplicate_id_insert` | Test duplicate ID with in-memory DB | Full - maps to E2E test |
| `test_case_insensitive_duplicates` | Test REQ-001 vs req-001 | New - enhanced coverage |
| `test_concurrent_duplicate_check` | Test race conditions | New - robustness |
| `test_soft_delete_duplicates` | Test deleted ID reuse | New - lifecycle testing |

#### Slow Layer (E2E Tests) - Target: <5s per test
Location: `tests/slow/test_duplicate_detection_e2e.py`

| Test Scenario | Description | Original E2E Coverage |
|--------------|-------------|----------------------|
| `test_full_workflow_duplicate_prevention` | Complete workflow with real DB | Full - existing test |
| `test_multi_user_duplicate_scenarios` | Concurrent user duplicate attempts | New - production scenario |

## Performance Comparison

### Old Approach (All E2E)
- Single E2E test: ~500ms
- Feedback loop: Save → Run E2E → Result = ~2-3s
- Test isolation: Poor (shared DB state)
- Debugging: Difficult (full stack involved)

### New Approach (Layered)
- Fast tests: 4 tests × 50ms = 200ms
- Mid tests: 4 tests × 500ms = 2s  
- Slow tests: 2 tests × 2s = 4s
- **Total**: 6.2s (but typically only run Fast during development)

### Development Feedback Improvements
1. **Inner Loop** (Save → Fast Test): 200ms vs 2-3s (10-15x faster)
2. **Test Isolation**: Each layer independent
3. **Debugging**: Precise layer identifies issue location
4. **Coverage**: 10 test scenarios vs 1 (10x coverage)

## Implementation Priority

1. **Phase 1**: Implement Fast layer tests (immediate development feedback)
2. **Phase 2**: Implement Mid layer with in-memory DB
3. **Phase 3**: Refactor existing E2E test to Slow layer pattern
4. **Phase 4**: Add new E2E scenarios for production edge cases

## Summary

The test migration would transform a single 500ms E2E test into a comprehensive suite of 10 tests across three layers. While total execution time increases to 6.2s, the development experience improves dramatically with 200ms Fast tests providing immediate feedback. The layered approach provides 10x better coverage, precise debugging, and maintains the full E2E validation while adding robust unit and integration testing.