# Implementation Options Evaluation

## Current Validation Pipeline Analysis

### Current Flow
1. **Discovery**: `find contracts -name "contract.cue"` → `index.json`
2. **Data Injection**: Process each contract → `tools/contracts-data.cue`
3. **Validation**: `cue export ./tools/aggregate.cue ./tools/contracts-data.cue`

### Current Issues
- **Single validation scope**: All contracts validated with same rules
- **No directory awareness**: Can't apply different rules per directory type
- **Brittle error handling**: Fails on first validation error

## Implementation Options

### Option 1: Multiple Validation Pipelines ⭐

**Approach**: Create separate validation checks for each directory type

#### Structure
```nix
checks = {
  # Production contracts - strict validation
  contractsProduction = pkgs.runCommand "contracts-production" {
    contracts = findContracts "contracts/production";
    validationRules = "strict";
  } /* validation script */;

  # Example contracts - educational validation
  contractsExamples = pkgs.runCommand "contracts-examples" {
    contracts = findContracts "contracts/examples";
    validationRules = "educational";
  } /* validation script */;

  # Test contracts - syntax only
  contractsTest = pkgs.runCommand "contracts-test" {
    contracts = findContracts "contracts/test";
    validationRules = "syntax-only";
  } /* validation script */;
};
```

#### Pros
- **Clean separation**: Each pipeline has clear purpose
- **Easy debugging**: Failures isolated to specific contract types
- **Independent evolution**: Can modify validation per type without affecting others
- **Parallel execution**: Nix naturally parallelizes different checks

#### Cons
- **Code duplication**: Similar validation logic repeated
- **Maintenance overhead**: Multiple pipelines to maintain

#### Implementation Complexity: **Medium**

### Option 2: Directory-Aware Single Pipeline

**Approach**: Enhance current pipeline with directory-based logic

#### Structure
```bash
# Enhanced discovery with directory classification
for contract_file in $(jq -r '.[]' tools/index.json); do
  directory_type=$(classify_directory "$contract_file")
  apply_validation_rules "$directory_type" "$contract_file"
done
```

#### Pros
- **Unified pipeline**: Single validation system
- **Less code duplication**: Shared validation infrastructure
- **Consistent data format**: Single contracts-data.cue

#### Cons
- **Complex logic**: Directory classification and rule application
- **Harder debugging**: Failures mixed across contract types
- **Single point of failure**: Pipeline breaks if any directory fails

#### Implementation Complexity: **High**

### Option 3: Configurable Validation Rules

**Approach**: Make validation rules data-driven and configurable

#### Structure
```cue
// tools/validation-config.cue
validationConfig: {
  "production": {
    duplicateCheck: "error"
    dependencyCheck: "error"
    portCheck: "error"
  }
  "examples": {
    duplicateCheck: "warn"
    dependencyCheck: "warn"
    portCheck: "skip"
  }
  "test": {
    duplicateCheck: "skip"
    dependencyCheck: "skip"
    portCheck: "skip"
  }
}
```

#### Pros
- **Maximum flexibility**: Easy to adjust validation per directory
- **Data-driven**: Rules are configuration, not code
- **Extensible**: Easy to add new directory types and rules

#### Cons
- **Over-engineering**: May be too complex for current needs
- **Configuration sprawl**: Rules spread across multiple files
- **Learning curve**: Team needs to understand rule system

#### Implementation Complexity: **High**

## Decision Matrix

| Criteria | Option 1 (Multiple) | Option 2 (Single) | Option 3 (Config) |
|----------|---------------------|-------------------|-------------------|
| **Simplicity** | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Maintainability** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Debugging** | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **Flexibility** | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **Implementation Time** | ⭐⭐⭐ | ⭐ | ⭐ |

## Recommended Decision: Option 1 (Multiple Pipelines)

### Rationale
1. **Immediate value**: Solves current validation failures quickly
2. **Clear boundaries**: Production vs examples vs test separation
3. **Parallel benefits**: Nix naturally parallelizes different checks
4. **Incremental migration**: Can implement one pipeline at a time
5. **Future flexibility**: Can always merge or enhance later

### Implementation Strategy
1. **Phase 1**: Create production pipeline (strict validation)
2. **Phase 2**: Create example pipeline (educational validation)
3. **Phase 3**: Create test pipeline (syntax-only validation)
4. **Phase 4**: Refactor shared validation utilities

### Migration Path
```
Current: all contracts → single validation → success/failure
Target:  production contracts → strict validation → success/failure
         example contracts → educational validation → success/failure
         test contracts → syntax validation → success/failure
```

## Next Steps
1. Create directory structure migration plan
2. Implement production validation pipeline first
3. Migrate working contracts to production directory
4. Test validation isolation