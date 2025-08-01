# Meta-Test Class-to-Functional Migration Plan

## Current State Summary

### Functional Implementations Status
- **Completed**: All 7 metric functional implementations exist
  - `existence_functional.py` ✅ (has test)
  - `reachability_functional.py` ✅ (has test)
  - `boundary_coverage_functional.py` ❌ (test missing)
  - `change_sensitivity_functional.py` ❌ (test missing)
  - `semantic_alignment_functional.py` ✅ (has test)
  - `runtime_correlation_functional.py` ✅ (has test)
  - `value_probability_functional.py` ❌ (test missing)

### Active Class Usage
- **20+ actively used classes** across the codebase
- **Critical dependencies**:
  - `MetricsCalculator` class used in all scripts and E2E tests
  - `BaseMetric` abstract class inherited by all metric implementations
  - All application layer depends on class-based implementations
  - Infrastructure services (`GraphAdapter`, `EmbeddingService`, `MetricsCollector`)

## Risk Assessment

### High Risk Areas
1. **Production Scripts** (scripts/ directory):
   - `init_metrics.py`, `calculate_all.py`, `daily_learning.py` all import class-based `MetricsCalculator`
   - Direct production impact if broken

2. **E2E Test Suite**:
   - 6+ E2E test files depending on current class structure
   - Business scenario tests actively used for validation

3. **Missing Test Coverage**:
   - 3 functional implementations without tests (43% coverage gap)
   - Risk of regression without test safety net

### Medium Risk Areas
1. **Import Dependencies**:
   - 50+ import statements need updating
   - Circular dependency risks during migration

2. **Type Safety**:
   - Current `BaseMetric` ABC provides type guarantees
   - Need to maintain type safety during transition

## Phased Migration Approach

### Phase 1: Test Coverage (60-90 minutes)
**Goal**: Achieve 100% test coverage for functional implementations

1. Create `test_boundary_coverage_functional.py`
2. Create `test_change_sensitivity_functional.py`
3. Create `test_value_probability_functional.py`
4. Run all tests to ensure functional implementations work correctly

**Success Criteria**: All functional implementations have passing tests

### Phase 2: Adapter Pattern Implementation (90-120 minutes)
**Goal**: Create backward-compatible adapters for gradual migration

1. Create `domain/metrics/adapters.py`:
   ```python
   # Adapter classes that wrap functional implementations
   class ExistenceMetricAdapter(BaseMetric):
       def calculate(self, input: MetricInput) -> MetricResult:
           return calculate_existence_metric(input, self.graph_adapter)
   ```

2. Update `metric_registry.py` to support both class and functional registration

3. Create `application/calculate_metrics_adapter.py`:
   - Wrapper for `MetricsCalculator` that uses functional implementations
   - Maintains same API for backward compatibility

**Success Criteria**: Both class and functional implementations can coexist

### Phase 3: Systematic Import Updates (60-90 minutes)
**Goal**: Update imports without breaking functionality

1. **Update application layer first**:
   - Start with `calculate_metrics.py` to use adapters
   - Update one file at a time, test after each change

2. **Update scripts**:
   - Use feature flags or environment variables for gradual rollout
   - Example: `USE_FUNCTIONAL_METRICS=true`

3. **Update E2E tests**:
   - Create parallel test files using functional approach
   - Run both old and new tests to ensure compatibility

**Success Criteria**: All imports updated, both implementations still work

### Phase 4: Remove Old Implementations (30-60 minutes)
**Goal**: Clean removal of class-based code

1. **Remove in order**:
   - Remove old metric classes (after confirming no usage)
   - Remove `BaseMetric` abstract class
   - Remove adapter layer
   - Clean up imports

2. **Final cleanup**:
   - Update documentation
   - Remove feature flags
   - Archive old implementation for reference

**Success Criteria**: Only functional implementations remain

## Rollback Strategy

### Per-Phase Rollback
1. **Phase 1**: No rollback needed (only adding tests)

2. **Phase 2**: 
   - Keep adapter code in separate branch
   - Can revert adapter introduction without affecting existing code

3. **Phase 3**:
   - Use git stash for each file change
   - Test immediately after each import update
   - Rollback individual files if issues arise

4. **Phase 4**:
   - Keep old implementations in `_deprecated/` folder initially
   - Full git history available for complete rollback

### Emergency Rollback
```bash
# Tag before migration
git tag pre-functional-migration

# Emergency rollback
git checkout pre-functional-migration
```

## Timeline Estimates

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Test Coverage | 60-90 min | 60-90 min |
| Phase 2: Adapter Pattern | 90-120 min | 150-210 min |
| Phase 3: Import Updates | 60-90 min | 210-300 min |
| Phase 4: Cleanup | 30-60 min | 240-360 min |
| **Total** | **240-360 min** | **4-6 hours** |

## Migration Checklist

### Pre-Migration
- [ ] Create git tag `pre-functional-migration`
- [ ] Ensure all current tests pass
- [ ] Document current API usage
- [ ] Set up feature flags

### During Migration
- [ ] Complete Phase 1 tests
- [ ] Implement Phase 2 adapters
- [ ] Update Phase 3 imports systematically
- [ ] Execute Phase 4 cleanup

### Post-Migration
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Performance benchmarks
- [ ] Archive old implementation

## Key Success Factors

1. **Incremental Changes**: Never break working code
2. **Test First**: Add tests before changing implementations
3. **Backward Compatibility**: Use adapters for smooth transition
4. **Clear Communication**: Update team on progress and any issues
5. **Rollback Ready**: Always have a way back at each step

## Next Steps

1. Review and approve this plan
2. Create feature branch `feature/functional-migration`
3. Begin with Phase 1 (test coverage)
4. Daily progress updates during migration