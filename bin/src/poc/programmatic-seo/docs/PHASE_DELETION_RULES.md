# Phase Deletion Timing and Safety Rules

## Overview

This document defines the strict rules and safety mechanisms for deleting phase instruction files (`docs/phases/*.md`) to prevent accidental loss of work and ensure proper completion verification.

## Deletion Timing Rules

### Pre-Deletion Requirements

A phase instruction file (e.g., `docs/phases/1.1-Lite-pSEO.md`) may ONLY be deleted when ALL of the following conditions are met:

1. **Receipt File Existence**: Valid receipt file exists at `docs/.receipts/{phase}.done`
2. **Status Completion**: Phase status in `docs/PHASES_STATUS.json` is marked as `"completed"`
3. **Gates Verification**: All gates in the receipt file show `true` status
4. **Commit Reference**: Valid commit hash recorded in both receipt and status files
5. **Approver Signature**: Designated approver has signed off in the receipt file

### Deletion Sequence

When all pre-deletion requirements are met:

1. **Double Verification**: Re-check all requirements using the phase guard inspection system
2. **Backup Creation**: Create backup of phase file with timestamp in `docs/.receipts/backups/`
3. **Dependency Check**: Verify no subsequent phases reference the current phase file
4. **Deletion Execution**: Remove the phase instruction file
5. **Status Update**: Update `docs/PHASES_STATUS.json` with deletion timestamp

## Safety Mechanisms

### Anti-Accidental Deletion

- **Guard Scripts**: Automated scripts must verify all conditions before allowing deletion
- **Manual Confirmation**: Two-factor confirmation required for deletion operations
- **Backup Retention**: Deleted phase files are backed up for 90 days minimum
- **Audit Trail**: All deletion operations are logged with timestamp and operator

### Error Prevention

- **Receipt Immutability**: Receipt files cannot be modified once created
- **Status Lock**: Completed phases cannot have their status changed without explicit override
- **Cross-Reference Validation**: Deletion scripts must verify consistency between receipt and status files
- **Dependency Analysis**: Check for any references to the phase in other files before deletion

### Recovery Procedures

- **Backup Restoration**: Process to restore accidentally deleted phase files from backup
- **Status Rollback**: Procedure to revert phase status if deletion was premature
- **Emergency Recovery**: Emergency procedures for critical phase instruction recovery

## Phase 1.1 Specific Rules

For `docs/phases/1.1-Lite-pSEO.md` deletion:

### Required Completion Evidence

- `docs/.receipts/1.1.done` must exist with valid JSON structure
- All implementation checklist items must be `true`:
  - `locales_defined`
  - `meta_helpers_defined`
  - `build_sitemap_implemented`
  - `build_hreflang_implemented`
  - `ci_build_step_added`
- All acceptance criteria must be `true`:
  - `sitemap_xml_generated`
  - `sitemap_urls_valid`
  - `sitemap_lastmod_valid`
  - `hreflang_tags_verified`

### Pre-Deletion Checklist

- [ ] Receipt file exists and is valid JSON
- [ ] All gates show `true` status
- [ ] Commit hash is recorded and valid
- [ ] Approver signature is present
- [ ] No pending work items remain
- [ ] Phase 1.2 acknowledges 1.1 completion (if 1.2 is started)
- [ ] Backup created successfully
- [ ] Dependencies verified

## Guard Script Requirements

The phase guard inspection system must implement the following checks:

### Missing Phase File Scenario

When `docs/phases/1.1-Lite-pSEO.md` is missing, verify:

1. `docs/.receipts/1.1.done` exists and contains valid completion data
2. `docs/PHASES_STATUS.json` shows phase 1.1 as `"completed"`
3. Completion date is recorded and reasonable
4. All required gates are marked as completed
5. Backup file exists in `docs/.receipts/backups/`

### Invalid Deletion Detection

Alert if phase file is missing but:

- Receipt file is incomplete or invalid
- Status shows phase as incomplete
- Required gates are not all `true`
- No valid approver signature
- Missing backup file

## Compliance Enforcement

- **Pre-Commit Hooks**: Git hooks to prevent commits that delete phase files without proper receipts
- **CI/CD Validation**: Build pipeline checks for proper phase completion before deployment
- **Review Requirements**: Pull requests deleting phase files require additional review
- **Audit Logging**: All phase deletion operations are logged for compliance

## Emergency Procedures

### Accidental Deletion Recovery

1. Check `docs/.receipts/backups/` for recent backup
2. Restore from backup with original timestamp
3. Verify receipt and status files are still valid
4. Update audit log with recovery action

### Invalid Receipt Detection

If receipt file is found to be invalid after phase deletion:

1. Immediately restore phase file from backup
2. Mark phase status as `"requires_review"`
3. Investigate receipt validation failure
4. Re-complete phase verification process

## References

- Receipt file format: `docs/.receipts/1.1.done`
- Status management: `docs/PHASES_STATUS.json`
- Phase guard inspection: `docs/PHASE_GUARD_SPEC.md`
