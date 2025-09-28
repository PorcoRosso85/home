# Phase Guard Operation System

## Overview

The Phase Guard Operation System provides comprehensive management for phase lifecycle, ensuring safe progression through development phases with proper completion verification and deletion safety mechanisms.

## System Architecture

```
Phase Guard System
├── Receipt Management (docs/.receipts/)
├── Status Tracking (docs/PHASES_STATUS.json)
├── Deletion Safety (PHASE_DELETION_RULES.md)
├── Inspection Engine (PHASE_GUARD_SPEC.md)
└── Operation Workflows (this document)
```

## Core Components

### 1. Receipt System (`docs/.receipts/`)

**Purpose**: Immutable completion records for each phase

**Structure**:
```
docs/.receipts/
├── 1.1.done           # Phase 1.1 completion receipt
├── 1.2.done           # Phase 1.2 completion receipt (future)
├── backups/           # Deleted phase file backups
└── templates/         # Receipt templates for new phases
```

**Receipt Format**: Structured JSON containing:
- Phase metadata (title, version)
- Completion timestamp and approver
- Implementation gates verification
- Acceptance criteria confirmation
- Deliverables list
- Verification results

### 2. Status Management (`docs/PHASES_STATUS.json`)

**Purpose**: Central registry of all phase states and progression

**Features**:
- Real-time phase status tracking
- Version and commit hash recording
- Completion date logging
- Cross-reference with receipt files
- Guard rule definitions

### 3. Safety Mechanisms

**Deletion Prevention**:
- Multi-factor verification before phase file deletion
- Automatic backup creation
- Cross-reference consistency checks
- Dependency analysis

**Error Recovery**:
- Automated backup restoration
- Status rollback procedures
- Emergency recovery protocols
- Audit trail maintenance

## Operational Workflows

### Phase Initiation Workflow

1. **Phase Planning**
   ```bash
   # Create phase instruction file
   cp docs/phases/template.md docs/phases/1.X-Phase-Name.md

   # Initialize status tracking
   jq '.phases."1.X" = {
     "title": "Phase Name",
     "status": "pending",
     "completion_date": null,
     "version": null,
     "commit_hash": null,
     "receipt_file": null,
     "notes": "Phase description"
   }' docs/PHASES_STATUS.json > tmp && mv tmp docs/PHASES_STATUS.json
   ```

2. **Work Commencement**
   ```bash
   # Update status to in_progress
   jq '.phases."1.X".status = "in_progress"' docs/PHASES_STATUS.json > tmp && mv tmp docs/PHASES_STATUS.json

   # Begin implementation following phase instructions
   ```

### Phase Completion Workflow

1. **Pre-Completion Verification**
   ```bash
   # Verify all implementation checklist items
   # Confirm acceptance criteria are met
   # Test rollback procedures
   # Validate deliverables
   ```

2. **Receipt Generation**
   ```bash
   # Copy receipt template
   cp docs/.receipts/template.json docs/.receipts/1.X.done

   # Fill in completion data
   # - Current timestamp
   # - Git commit hash
   # - Approver signature
   # - All gate statuses (must be true)
   # - Deliverables list
   # - Verification results
   ```

3. **Status Update**
   ```bash
   # Mark phase as completed
   jq '.phases."1.X" = {
     "status": "completed",
     "completion_date": "2024-09-28T05:47:00Z",
     "version": "1.X.0",
     "commit_hash": "actual-commit-hash",
     "receipt_file": "docs/.receipts/1.X.done"
   }' docs/PHASES_STATUS.json > tmp && mv tmp docs/PHASES_STATUS.json
   ```

4. **Validation Check**
   ```bash
   # Run phase guard validation
   ./scripts/phase-guard.sh validate 1.X

   # Ensure all checks pass before proceeding
   ```

### Phase Deletion Workflow

1. **Pre-Deletion Validation**
   ```bash
   # Run comprehensive validation
   ./scripts/phase-guard.sh prepare-delete 1.X

   # Verify all safety conditions are met:
   # - Receipt file exists and is valid
   # - Status shows completed
   # - All gates are true
   # - No dependent work exists
   ```

2. **Safety Backup Creation**
   ```bash
   # Create timestamped backup
   mkdir -p docs/.receipts/backups/
   cp docs/phases/1.X-Phase-Name.md docs/.receipts/backups/1.X-Phase-Name.md.$(date +%Y%m%d_%H%M%S)
   ```

3. **Deletion Execution**
   ```bash
   # Only after all validations pass
   rm docs/phases/1.X-Phase-Name.md

   # Update status with deletion timestamp
   jq '.phases."1.X".deleted_date = "2024-09-28T05:47:00Z"' docs/PHASES_STATUS.json > tmp && mv tmp docs/PHASES_STATUS.json
   ```

## Phase 1.1 Specific Operations

### Current State Assessment

**Phase File**: `docs/phases/1.1-Lite-pSEO.md` (exists)
**Status**: `in_progress`
**Receipt**: Template created at `docs/.receipts/1.1.done`

### Completion Checklist for Phase 1.1

**Implementation Requirements**:
- [ ] `packages/i18n/locales.ts` - Language definitions
- [ ] `packages/i18n/meta.ts` - Title/description helpers
- [ ] `scripts/build-sitemap.ts` - Sitemap generation
- [ ] `scripts/build-hreflang.ts` - Hreflang generation
- [ ] CI integration for build step

**Acceptance Criteria**:
- [ ] `public/sitemap.xml` generated with valid URLs
- [ ] Sitemap contains proper lastmod timestamps
- [ ] Hreflang tags verified on major pages
- [ ] Manual or E2E testing completed

**Before Deletion**:
1. Update `docs/.receipts/1.1.done` with actual completion data
2. Update `docs/PHASES_STATUS.json` phase 1.1 status to "completed"
3. Run validation: `./scripts/phase-guard.sh validate 1.1`
4. Create backup: Copy phase file to `docs/.receipts/backups/`
5. Delete: `rm docs/phases/1.1-Lite-pSEO.md`

### Phase 1.1 Validation Commands

```bash
# Check if Phase 1.1 can be safely deleted
./scripts/phase-guard.sh validate 1.1

# Expected checks:
# - Receipt file exists and contains valid JSON
# - All implementation gates are true
# - All acceptance criteria are true
# - Status file shows phase as completed
# - Commit hash is valid and exists in git history
# - Approver signature is present
```

## Guard Script Implementation

### Required Scripts

1. **`scripts/phase-guard.sh`** - Main validation script
2. **`scripts/phase-backup.sh`** - Backup management
3. **`scripts/phase-status.sh`** - Status management utilities
4. **`scripts/phase-validate.sh`** - Deep validation checks

### Validation Logic Flow

```bash
#!/bin/bash
# scripts/phase-guard.sh

validate_phase() {
    local phase=$1
    local phase_file="docs/phases/${phase}-*.md"
    local receipt_file="docs/.receipts/${phase}.done"
    local status_file="docs/PHASES_STATUS.json"

    # Check if phase file exists
    if [[ -f $phase_file ]]; then
        echo "Phase $phase is in progress"
        return 0
    fi

    # Phase file missing - validate completion
    if [[ ! -f $receipt_file ]]; then
        echo "ERROR: Phase file deleted without receipt"
        return 1
    fi

    # Validate receipt JSON
    if ! jq . "$receipt_file" >/dev/null 2>&1; then
        echo "ERROR: Invalid receipt JSON format"
        return 1
    fi

    # Check phase status
    local status=$(jq -r ".phases.\"$phase\".status" "$status_file")
    if [[ "$status" != "completed" ]]; then
        echo "ERROR: Phase status is '$status', expected 'completed'"
        return 1
    fi

    # Validate all gates are true
    local gates_valid=$(jq -r '.gates | to_entries[] | .value | to_entries[]? | .value' "$receipt_file" | grep -v true | wc -l)
    if [[ $gates_valid -gt 0 ]]; then
        echo "ERROR: Not all completion gates are satisfied"
        return 1
    fi

    echo "Phase $phase validation passed"
    return 0
}
```

## Integration with Development Workflow

### Git Integration

**Pre-commit Hook**:
```bash
#!/bin/bash
# .git/hooks/pre-commit
./scripts/phase-guard.sh check-all || {
    echo "Phase guard validation failed"
    exit 1
}
```

**Pre-push Hook**:
```bash
#!/bin/bash
# .git/hooks/pre-push
# Prevent pushing incomplete phase deletions
for deleted_phase in $(git diff --name-only --diff-filter=D HEAD~1 | grep "docs/phases/"); do
    phase_num=$(basename "$deleted_phase" | cut -d'-' -f1)
    ./scripts/phase-guard.sh validate "$phase_num" || {
        echo "Cannot push: Phase $phase_num deletion is invalid"
        exit 1
    }
done
```

### CI/CD Integration

**Build Pipeline Check**:
```yaml
# .github/workflows/phase-guard.yml
name: Phase Guard Validation
on: [push, pull_request]
jobs:
  validate-phases:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate Phase Consistency
        run: ./scripts/phase-guard.sh check-all
      - name: Verify Receipt Integrity
        run: ./scripts/phase-validate.sh receipts
```

## Monitoring and Alerting

### Health Checks

- **Daily**: Automated phase consistency validation
- **On Commit**: Real-time validation during development
- **On Deploy**: Pre-deployment phase status verification

### Alert Conditions

- Phase file deleted without proper receipt
- Inconsistent data between receipt and status files
- Invalid completion gates in receipt files
- Missing backup files for deleted phases
- Unauthorized modifications to receipt files

## Maintenance Procedures

### Weekly Maintenance

1. **Backup Verification**
   ```bash
   # Verify all deleted phases have backups
   ./scripts/phase-backup.sh verify-all
   ```

2. **Receipt Integrity Check**
   ```bash
   # Validate all receipt files
   ./scripts/phase-validate.sh receipts
   ```

3. **Status Consistency Audit**
   ```bash
   # Check status file consistency
   ./scripts/phase-status.sh audit
   ```

### Monthly Maintenance

1. **Archive Old Backups**
   ```bash
   # Archive backups older than 90 days
   find docs/.receipts/backups/ -name "*.md.*" -mtime +90 -exec mv {} archive/ \;
   ```

2. **Generate Compliance Report**
   ```bash
   # Generate phase completion audit report
   ./scripts/phase-guard.sh audit-report > reports/phase-completion-$(date +%Y%m).md
   ```

## Troubleshooting Guide

### Common Issues

1. **"Phase file deleted without receipt"**
   - **Cause**: Accidental deletion or incomplete work
   - **Solution**: Restore from backup, complete missing work
   - **Prevention**: Use phase guard scripts for all deletions

2. **"Invalid receipt JSON format"**
   - **Cause**: Manual editing corruption or malformed JSON
   - **Solution**: Validate and fix JSON syntax
   - **Prevention**: Use automated receipt generation tools

3. **"Inconsistent phase status"**
   - **Cause**: Manual status file editing without receipt update
   - **Solution**: Synchronize receipt and status data
   - **Prevention**: Use automated status update scripts

### Recovery Procedures

1. **Emergency Phase Restoration**
   ```bash
   # Restore accidentally deleted phase
   cp docs/.receipts/backups/1.X-Phase-Name.md.TIMESTAMP docs/phases/1.X-Phase-Name.md
   jq '.phases."1.X".status = "in_progress"' docs/PHASES_STATUS.json > tmp && mv tmp docs/PHASES_STATUS.json
   ```

2. **Receipt File Recovery**
   ```bash
   # Recreate receipt from status file data
   ./scripts/phase-status.sh export-receipt 1.X > docs/.receipts/1.X.done
   ```

## Future Enhancements

### Planned Features

- **Automated Receipt Generation**: Scripts to auto-generate receipts from git history and validation results
- **Phase Dependency Management**: Automatic validation of phase prerequisites and dependencies
- **Integration Testing**: Automated testing of phase deliverables before completion
- **Metrics Dashboard**: Web interface for phase completion tracking and metrics
- **Notification System**: Automated alerts for phase milestones and issues

### Extensibility

The phase guard system is designed to be extensible for future phases and projects:

- **Plugin Architecture**: Support for custom validation plugins
- **Template System**: Customizable receipt and status templates
- **Multi-Project Support**: Extend to manage phases across multiple projects
- **API Integration**: REST API for external tools integration
