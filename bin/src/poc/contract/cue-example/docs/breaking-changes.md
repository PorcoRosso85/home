# Breaking Change Detection - Phase 2.1 Implementation

## Overview

The breaking change detection system implements SSOT (Single Source of Truth) governance by preventing incompatible changes to production contracts without explicit intent.

## Architecture

### Components

1. **Baseline Infrastructure** (`baseline/`)
   - `production.json`: Snapshot of current production contracts
   - Serves as reference point for compatibility checks
   - Updated only when breaking changes are intentional

2. **Breaking Changes Check** (`checks.breakingChanges`)
   - Automated validation in `nix flake check`
   - Compares current contracts against baseline
   - Blocks builds when breaking changes detected

3. **Detection Schema** (`tools/breaking-changes.cue`)
   - CUE schema definitions for breaking change analysis
   - Defines critical compatibility fields
   - Supports future extensibility

## What Constitutes Breaking Changes

### Service Capability Reduction
- **Detection**: Removal of entries from `provides` array
- **Impact**: Downstream services lose expected capabilities
- **Example**: API service removing an endpoint

### Service Removal
- **Detection**: Service present in baseline but missing in current
- **Impact**: Complete service unavailability
- **Example**: Database service being deleted

### Future Extensibility
The framework supports additional breaking change types:
- Required field removals
- Type constraint narrowing
- Enum value reductions
- Dependency version range restrictions

## Implementation Details

### Baseline Creation
```bash
# Export current production contracts
cue export contracts/production/api/contract.cue > baseline/api.json
cue export contracts/production/database/contract.cue > baseline/database.json
cue export contracts/production/cache/contract.cue > baseline/cache.json

# Combine into unified baseline
jq -s '.[0] * .[1] * .[2]' baseline/api.json baseline/cache.json baseline/database.json > baseline/production.json
```

### Check Execution
The check runs automatically during:
- `nix flake check`
- Pre-commit hooks
- CI/CD pipelines

### Error Handling
When breaking changes are detected:
```
🚫 BREAKING CHANGES DETECTED!
The following breaking changes were found:
  - Service ApiService capability changes

Breaking changes violate SSOT governance rules.
Either revert the changes or update the baseline intentionally.
```

## Usage

### Normal Development
Breaking change detection runs automatically. No action required for compatible changes.

### Intentional Breaking Changes
1. **Review Impact**: Understand downstream effects
2. **Update Baseline**: Regenerate baseline after careful consideration
3. **Coordinate**: Notify dependent teams/services
4. **Deploy**: Ensure proper rollout strategy

### Baseline Update Process
```bash
# Only after careful review and coordination
nix develop --command bash -c "
  cue export contracts/production/api/contract.cue > baseline/api.json &&
  cue export contracts/production/database/contract.cue > baseline/database.json &&
  cue export contracts/production/cache/contract.cue > baseline/cache.json &&
  jq -s '.[0] * .[1] * .[2]' baseline/api.json baseline/cache.json baseline/database.json > baseline/production.json
"
```

## Benefits

### Governance
- **Prevents Accidental Breaking Changes**: Catches incompatible modifications before deployment
- **Enforces Review Process**: Breaking changes require explicit baseline updates
- **Maintains Contract Stability**: Protects downstream consumers

### Development Workflow
- **Early Detection**: Issues caught at build time, not runtime
- **Clear Feedback**: Specific error messages about what changed
- **Automated Checks**: No manual intervention for compatible changes

### SSOT Compliance
- **Version Control**: Baseline changes are tracked in Git
- **Audit Trail**: Clear history of intentional breaking changes
- **Reproducible Builds**: Consistent results across environments

## Testing Results

### Validation Test Results
✅ **Compatible Changes**: Check passes when no breaking changes present
✅ **Breaking Change Detection**: Successfully detected removed API capability
✅ **Error Reporting**: Clear error messages with specific change details
✅ **Restoration**: Check passes again when breaking change is reverted

### Test Scenario
- **Baseline**: API service with `user-api` HTTP capability
- **Breaking Change**: Removed all capabilities (`provides: []`)
- **Detection**: Correctly identified capability reduction
- **Result**: Build failed with descriptive error message

## Integration

The breaking change detection integrates seamlessly with:
- Nix flake checks
- Pre-commit hooks
- CI/CD pipelines
- Development workflow

This ensures breaking changes are caught early and require explicit acknowledgment before proceeding.