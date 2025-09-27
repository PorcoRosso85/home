# Contract Separation Architecture

## Current State Analysis

### Problems Identified
1. **Mixed Validation Scope**: Production and example contracts validated together
2. **Intentional Failures**: Examples with duplicates/unresolved deps fail validation
3. **Poor Separation**: No clear distinction between operational vs educational content

### Current Structure
```
contracts/
├── example/contract.cue          # Single example
├── examples/                     # Educational examples
│   ├── normal/                   # Working examples
│   ├── duplicate/                # Duplicate name examples
│   └── unresolved/               # Unresolved dependency examples
└── test-contracts/               # Additional test fixtures
```

## Proposed Architecture

### Directory Structure
```
contracts/
├── production/                   # STRICT validation (zero tolerance)
│   ├── api/contract.cue
│   ├── database/contract.cue
│   └── cache/contract.cue
├── examples/                     # EDUCATIONAL validation (lenient)
│   ├── basic/                    # Working examples
│   ├── anti-patterns/            # Error demonstrations
│   │   ├── duplicates/           # Duplicate name examples
│   │   └── unresolved-deps/      # Missing dependency examples
│   └── README.md                 # Learning guide
└── test/                         # TEST validation (disabled)
    ├── fixtures/                 # Test data
    └── scenarios/                # Test scenarios
```

### Validation Levels

#### 1. Production Validation (contracts/production/)
- **Full aggregate validation**
- **Zero duplicate tolerance**
- **Complete dependency resolution required**
- **Port conflict detection**
- **Secrets scanning**

#### 2. Example Validation (contracts/examples/)
- **Per-subdirectory validation**
- **Duplicate checking within subdirectory only**
- **Dependency resolution warnings (not errors)**
- **Educational error messages**

#### 3. Test Validation (contracts/test/)
- **Syntax checking only**
- **No aggregate validation**
- **No cross-references**

### Implementation Strategy

#### Phase 1: Structure Migration
1. Create production/ directory
2. Move viable contracts from examples/normal/
3. Reorganize examples by learning purpose
4. Update flake.nix discovery logic

#### Phase 2: Conditional Validation
1. Modify tools/aggregate.cue for directory-aware validation
2. Create separate validation schemas per directory type
3. Update Nix checks to run appropriate validation per directory

#### Phase 3: Documentation Integration
1. Create learning paths in examples/README.md
2. Add validation explanations for each anti-pattern
3. Document production contract requirements

## Benefits

### Immediate
- **Production validation succeeds** (no example interference)
- **Examples remain educational** (errors are features, not bugs)
- **Clear operational boundaries**

### Long-term
- **Scalable governance** (different rules for different purposes)
- **Educational value preserved** (anti-patterns safely demonstrated)
- **Production safety** (strict validation where it matters)

## Decision Rationale

**Why not complete separation?**
- Maintains unified tooling and schemas
- Examples stay relevant to production patterns
- Single flake manages all contract types

**Why conditional validation?**
- Preserves educational value of error examples
- Allows production-grade validation where needed
- Flexible governance without tool fragmentation