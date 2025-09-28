# Phase Guard Inspection Specification

## Overview

The Phase Guard Inspection System is a comprehensive validation framework that ensures proper phase completion and deletion safety. This specification defines the enhanced inspection rules and implementation requirements.

## Core Inspection Scenarios

### Scenario 1: Missing Phase File with Valid Completion

**Trigger**: `docs/phases/{phase}.md` file does not exist

**Required Validations**:

1. **Receipt File Validation**
   - `docs/.receipts/{phase}.done` must exist
   - File must contain valid JSON structure
   - All required fields must be present and non-null
   - Schema validation against expected format

2. **Status File Validation**
   - `docs/PHASES_STATUS.json` must exist and be readable
   - Phase entry must exist with status `"completed"`
   - Completion date must be present and valid ISO 8601 format
   - Version field must be present and follow semantic versioning

3. **Gate Completion Verification**
   - All implementation checklist items must be `true`
   - All acceptance criteria must be `true`
   - All rollback tests must be `true`
   - All verification gates must be `true`

4. **Cross-Reference Consistency**
   - Commit hash in receipt matches status file
   - Completion dates are consistent (within reasonable tolerance)
   - Version numbers match between receipt and status
   - Approver information is consistent

### Scenario 2: Phase File Exists - Completion Check

**Trigger**: `docs/phases/{phase}.md` file exists

**Required Validations**:

1. **Work Status Assessment**
   - Check if phase is actively being worked on
   - Verify implementation progress against checklist
   - Assess completion readiness

2. **Premature Deletion Prevention**
   - Ensure phase file is not deleted before completion
   - Validate that all work items are addressed
   - Check for any pending dependencies

## Phase 1.1 Specific Inspection Rules

### File Presence Matrix

| Condition | Phase File | Receipt File | Status | Action |
|-----------|------------|--------------|---------|---------|
| **Valid Completion** | ❌ Missing | ✅ Valid | `completed` | ✅ Allow (normal state) |
| **Work in Progress** | ✅ Present | ❌ Missing | `in_progress` | ✅ Allow (working state) |
| **Invalid Deletion** | ❌ Missing | ❌ Missing | `in_progress` | ❌ Error: Accidental deletion |
| **Incomplete Receipt** | ❌ Missing | ⚠️ Invalid | `completed` | ❌ Error: Invalid completion |

### Required Gate Validations

When `docs/phases/1.1-Lite-pSEO.md` is missing, verify these specific gates:

```json
{
  "implementation_checklist": {
    "locales_defined": true,
    "meta_helpers_defined": true,
    "build_sitemap_implemented": true,
    "build_hreflang_implemented": true,
    "ci_build_step_added": true
  },
  "acceptance_criteria": {
    "sitemap_xml_generated": true,
    "sitemap_urls_valid": true,
    "sitemap_lastmod_valid": true,
    "hreflang_tags_verified": true
  }
}
```

### Mandatory File Verification

1. **Receipt Structure Validation**
   ```bash
   # Must exist and be valid JSON
   test -f docs/.receipts/1.1.done
   jq . docs/.receipts/1.1.done > /dev/null
   ```

2. **Status Consistency Check**
   ```bash
   # Phase 1.1 must be marked completed
   jq -r '.phases."1.1".status' docs/PHASES_STATUS.json | grep -q "completed"
   ```

3. **Gate Completion Verification**
   ```bash
   # All implementation gates must be true
   jq -r '.gates.implementation_checklist | to_entries[] | .value' docs/.receipts/1.1.done | grep -q false && exit 1
   ```

## Implementation Requirements

### Guard Script Interface

The phase guard system must provide these commands:

```bash
# Validate specific phase
./scripts/phase-guard.sh validate 1.1

# Check all phases
./scripts/phase-guard.sh check-all

# Prepare phase for deletion
./scripts/phase-guard.sh prepare-delete 1.1

# Emergency validation
./scripts/phase-guard.sh emergency-check
```

### Return Codes

- `0`: All validations passed
- `1`: Validation failed - invalid state detected
- `2`: Missing required files
- `3`: Inconsistent data between files
- `4`: Premature deletion attempt
- `5`: Emergency state - manual intervention required

### Output Format

```json
{
  "phase": "1.1",
  "validation_timestamp": "2024-09-28T05:47:00Z",
  "status": "valid|invalid|warning",
  "checks": {
    "receipt_exists": true,
    "receipt_valid_json": true,
    "status_consistent": true,
    "gates_completed": true,
    "cross_reference_valid": true
  },
  "errors": [],
  "warnings": [],
  "recommendations": []
}
```

## Advanced Validation Rules

### Temporal Consistency

- Completion dates must be chronologically ordered
- Phase 1.1 cannot be completed before Phase 1.0
- Completion date cannot be in the future
- Receipt timestamp should align with git commit timestamp

### Dependency Validation

- Phase 1.1 completion must not break Phase 1.2 prerequisites
- Ensure all referenced files and deliverables exist
- Validate that deleted phase files don't break documentation links

### Integrity Checks

- Receipt file hash validation to prevent tampering
- Commit hash existence verification in git history
- Approver signature validation against authorized list

## Error Handling

### Validation Failures

1. **Missing Receipt File**
   - Error: "Phase file deleted without proper completion receipt"
   - Action: Restore phase file from backup or create emergency receipt
   - Escalation: Require manual approval for continuation

2. **Invalid Gate Status**
   - Error: "Completion gates not satisfied for phase deletion"
   - Action: Restore phase file and resume work
   - Escalation: Review completion criteria and re-validate

3. **Inconsistent Data**
   - Error: "Receipt and status files contain conflicting information"
   - Action: Investigate data corruption or manual tampering
   - Escalation: Require data integrity review and correction

### Recovery Procedures

1. **Automatic Recovery**
   - Restore from `docs/.receipts/backups/` if available
   - Reset phase status to previous valid state
   - Log recovery action for audit trail

2. **Manual Intervention**
   - Generate validation report for human review
   - Provide specific recommendations for resolution
   - Require explicit approval for non-standard operations

## Integration Points

### Git Hooks

- Pre-commit: Validate phase state before commit
- Pre-push: Ensure no invalid phase deletions in push
- Post-merge: Verify phase consistency after merge

### CI/CD Pipeline

- Build stage: Run full phase guard validation
- Deploy stage: Verify phase completeness for deployment
- Post-deploy: Confirm phase status consistency

### Development Workflow

- Phase start: Initialize tracking in status file
- Phase progress: Update completion percentages
- Phase completion: Generate receipt and validate all gates
- Phase deletion: Execute full guard validation before deletion

## Testing Requirements

### Unit Tests

- JSON schema validation for receipt files
- Status file consistency checking
- Gate completion verification logic
- Cross-reference validation algorithms

### Integration Tests

- End-to-end phase completion workflow
- Invalid deletion prevention scenarios
- Recovery procedure validation
- Multi-phase dependency testing

### Scenario Tests

- Simulate accidental phase file deletion
- Test with corrupted receipt files
- Validate with inconsistent status data
- Emergency recovery procedures
