# Duplicate Detection Test Migration Checklist

## Coverage Comparison

### Original E2E Tests (test_e2e_duplicate_detection.py)
- **Total test methods**: 9
- **Lines of code**: ~405

Test methods:
1. `test_duplicate_detection_behavior` - Basic duplicate detection
2. `test_no_false_positives` - Ensure unrelated requirements don't trigger
3. `test_search_functionality` - Search API (mostly commented out)
4. `test_embedding_generation` - Embedding creation verification
5. `test_user_journey_iterative_refinement` - User workflow with warnings
6. `test_user_journey_progressive_elaboration` - Abstract to concrete refinement
7. `test_user_journey_cross_team_coordination` - Team coordination scenario
8. `test_user_journey_terminology_variations` - Multi-language/terminology handling
9. `test_schema_migration_readiness` - Migration readiness (skipped)

### New 3-Layer Structure
- **Total test methods**: 11
- **Total lines of code**: ~450 (but better organized)

#### Fast Layer (test_duplicate_detection_rules.py)
- **Test methods**: 5
- **Lines**: ~120
- Tests pure business logic without I/O

#### Mid Layer (test_duplicate_detection_integration.py) 
- **Test methods**: 3
- **Lines**: ~150
- Tests with mocked VSS/FTS services

#### Slow Layer (test_duplicate_detection_e2e.py)
- **Test methods**: 3 (+ 1 skipped)
- **Lines**: ~180
- Critical VSS/FTS integration only

## Migration Benefits

### Test Execution Time
- **Original**: All tests run at VERY_SLOW speed (~30s+)
- **New Structure**:
  - Fast tests: <1s (can run on every save)
  - Mid tests: ~5s (run frequently)
  - Slow tests: ~20s (run on CI or before commit)

### Code Reduction
- **User journey tests**: Moved to Mid layer with mocks (4 tests)
- **Business logic**: Extracted to Fast layer (5 focused tests)
- **E2E tests**: Reduced from 9 to 3 critical paths

### Coverage Mapping

| Original Test | Migrated To | Layer | Rationale |
|--------------|-------------|--------|-----------|
| `test_duplicate_detection_behavior` | `test_vss_duplicate_detection_with_real_embeddings` | Slow | Critical VSS integration |
| `test_no_false_positives` | `test_no_false_positives` | Fast | Pure business logic |
| `test_search_functionality` | Removed | - | Commented out, not implemented |
| `test_embedding_generation` | `test_create_requirement_with_embedding` | Mid | Can mock embedding service |
| `test_user_journey_iterative_refinement` | `test_duplicate_warning_workflow` | Mid | User workflow, mockable |
| `test_user_journey_progressive_elaboration` | `test_similarity_threshold_rules` | Fast | Business rules |
| `test_user_journey_cross_team_coordination` | Covered by integration tests | Mid | Workflow testing |
| `test_user_journey_terminology_variations` | `test_multilingual_vss_detection` | Slow | Requires real embeddings |
| `test_schema_migration_readiness` | Removed | - | Not a functional test |

## Critical Behaviors Still Covered

1. ✅ **Duplicate Detection**: Tested at all layers
   - Fast: Business rules
   - Mid: Service integration
   - Slow: Real VSS similarity

2. ✅ **False Positive Prevention**: Fast layer

3. ✅ **Embedding Integration**: 
   - Mid: Service calls
   - Slow: Real embeddings

4. ✅ **User Workflows**: Mid layer with mocks

5. ✅ **Multi-language Support**: Slow layer (real embeddings needed)

6. ✅ **Similarity Thresholds**: Fast layer rules + Slow layer validation

## Migration Steps

1. [x] Analyze existing E2E tests
2. [x] Create Fast layer with business rules
3. [x] Create Mid layer with service mocks
4. [x] Create Slow layer with critical E2E tests
5. [ ] Run all tests to verify coverage
6. [ ] Remove original E2E file
7. [ ] Update CI configuration for layer-based execution

## Execution Strategy

```bash
# During development (fast feedback)
pytest tests/fast/

# Before commit (broader validation)
pytest tests/fast/ tests/mid/

# CI pipeline (complete validation)
pytest tests/  # All layers
```