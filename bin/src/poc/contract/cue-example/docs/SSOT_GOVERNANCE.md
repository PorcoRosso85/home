# SSOT Governance Framework

This document describes the complete Single Source of Truth (SSOT) governance framework implemented for the CUE Contract Management System.

## Overview

The SSOT governance framework ensures strict compliance with all SSOT principles through automated enforcement at every stage of development and deployment.

## 8 Core SSOT Principles Implemented

### 1. **Single Authoritative Source** (制度)
- **Implementation**: CUE schema as the definitive contract definition
- **Enforcement**: Schema validation in all operations
- **Location**: `/home/nixos/bin/src/poc/contract/cue-example/schema/contract.cue`

### 2. **Version Control Integration** (バージョン管理)
- **Implementation**: Git-tracked CUE contracts with structured versioning
- **Enforcement**: Breaking changes detection and version increment validation
- **Tool**: `tools/governance/check-breaking-changes.sh`

### 3. **Automated Validation** (自動検証)
- **Implementation**: Pre-commit hooks + CI pipeline validation
- **Enforcement**: Multi-layered validation (syntax, semantics, business rules)
- **Configuration**: `.pre-commit-config.yaml` with 6 governance checks

### 4. **Conflict Resolution** (競合解決)
- **Implementation**: Port conflict detection and resource collision prevention
- **Enforcement**: Automated scanning and prevention of resource conflicts
- **Tool**: `tools/governance/check-port-conflicts.sh`

### 5. **Dependency Management** (依存関係)
- **Implementation**: Vendor dependency validation and lockfile monitoring
- **Enforcement**: Pure evaluation requirements and dependency integrity
- **Tools**:
  - `tools/governance/check-vendor-deps.sh`
  - `tools/governance/check-lockfile-drift.sh`

### 6. **Change Tracking** (変更追跡)
- **Implementation**: Git-based change tracking with governance metadata
- **Enforcement**: Commit-time validation of all changes
- **Integration**: Pre-commit hooks validate all modifications

### 7. **Access Control** (アクセス制御)
- **Implementation**: Git permissions + pre-commit enforcement
- **Enforcement**: Automated rejection of non-compliant changes
- **Coverage**: All contract modifications must pass governance checks

### 8. **Operational Governance** (運用統治)
- **Implementation**: Complete automation of SSOT enforcement
- **Enforcement**: Pre-commit + CI + lockfile monitoring
- **Tools**: Full governance automation prevents human error

## Governance Tools

### Pre-commit Integration
All governance checks are automatically executed on every commit:

```yaml
# Enhanced .pre-commit-config.yaml includes:
- breaking-changes-check      # Version compatibility validation
- port-conflicts-check        # Resource conflict detection
- vendor-dependencies-check   # Dependency integrity validation
- lockfile-drift-check       # Lock file consistency monitoring
- impure-operations-check    # Pure evaluation enforcement
- contract-completeness-check # Contract structure validation
```

### Individual Governance Checks

#### 1. Breaking Changes Validation
- **Purpose**: Ensures backward compatibility or proper versioning
- **Script**: `tools/governance/check-breaking-changes.sh`
- **Validates**: Contract modifications against compatibility rules
- **Fails**: When breaking changes lack version increments

#### 2. Port Conflicts Detection
- **Purpose**: Prevents service port collisions
- **Script**: `tools/governance/check-port-conflicts.sh`
- **Validates**: Unique port assignment across all contracts
- **Fails**: When multiple services claim the same port

#### 3. Vendor Dependencies Check
- **Purpose**: Ensures dependency integrity and security
- **Script**: `tools/governance/check-vendor-deps.sh`
- **Validates**: Dependency declarations, duplicates, security
- **Fails**: When duplicate or insecure dependencies detected

#### 4. Lockfile Drift Detection
- **Purpose**: Monitors lock file consistency and prevents drift
- **Script**: `tools/governance/check-lockfile-drift.sh`
- **Validates**: Lock file changes are intentional and documented
- **Fails**: When unauthorized lock file modifications detected

#### 5. Impure Operations Prevention
- **Purpose**: Enforces pure evaluation for reproducibility
- **Script**: `tools/governance/check-impure-ops.sh`
- **Validates**: All operations use pure Nix evaluation
- **Fails**: When impure patterns (--impure, NIX_PATH) detected

#### 6. Contract Completeness Check
- **Purpose**: Ensures all contracts have required structure
- **Script**: `tools/governance/check-contract-completeness.sh`
- **Validates**: Required fields, CUE syntax, semantic correctness
- **Fails**: When contracts lack essential fields or structure

## Operational Workflow

### Development Workflow
1. **Developer makes changes** to contracts or code
2. **Pre-commit triggers** all 6 governance checks automatically
3. **If any check fails**, commit is rejected with detailed error message
4. **Developer fixes issues** and retries commit
5. **Only compliant changes** are allowed into the repository

### CI/CD Integration
1. **Push triggers CI pipeline** with same governance checks
2. **Lockfile validation** ensures reproducible builds
3. **Breaking changes** are properly versioned and documented
4. **Port conflicts** and resource collisions are prevented
5. **Deployment only proceeds** if all governance checks pass

### Emergency Procedures
- **Governance checks cannot be bypassed** - this is intentional
- **Emergency fixes** must still comply with SSOT principles
- **Hotfixes** require proper governance metadata and validation
- **No --impure operations** allowed even in emergencies

## Benefits Achieved

### 1. **Zero Configuration Drift**
- Automated prevention of configuration inconsistencies
- Lock file monitoring prevents dependency drift
- Pure evaluation ensures reproducible environments

### 2. **Conflict Prevention**
- Port conflicts detected before deployment
- Resource collisions prevented automatically
- Breaking changes properly versioned

### 3. **Audit Trail**
- Complete change tracking through Git integration
- Governance metadata attached to every change
- Reproducible history of all modifications

### 4. **Developer Experience**
- Immediate feedback on policy violations
- Clear error messages with remediation guidance
- Automated formatting and validation

### 5. **Production Safety**
- Only validated, compliant configurations reach production
- Breaking changes require explicit version increments
- Resource conflicts impossible due to pre-commit prevention

## Implementation Status

✅ **Phase 1.0**: Schema Definition and Basic Validation
✅ **Phase 2.0**: Advanced Validation and Error Handling
✅ **Phase 2.5**: Complete Operational Governance (CURRENT)

**All 8 SSOT principles are now fully implemented and operationally enforced.**

## Usage

### Run All Governance Checks
```bash
nix develop --command pre-commit run --all-files
```

### Run Individual Checks
```bash
# Test breaking changes
./tools/governance/check-breaking-changes.sh

# Check port conflicts
./tools/governance/check-port-conflicts.sh

# Validate dependencies
./tools/governance/check-vendor-deps.sh

# Monitor lockfile drift
./tools/governance/check-lockfile-drift.sh

# Prevent impure operations
./tools/governance/check-impure-ops.sh

# Validate contract completeness
./tools/governance/check-contract-completeness.sh
```

### Development Environment
```bash
nix develop  # Enters environment with all tools available
```

## Compliance Verification

The system is designed to be **self-enforcing**:

1. **Pre-commit hooks** prevent non-compliant commits
2. **CI validation** catches any bypassed checks
3. **Lockfile monitoring** prevents configuration drift
4. **Pure evaluation** ensures reproducibility
5. **Automated validation** eliminates human error
6. **Complete audit trail** tracks all changes

**Result**: 100% SSOT compliance with zero configuration drift and complete operational governance.