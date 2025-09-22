# Rollback Procedures for Ignore-Only Policy Implementation

## Emergency Rollback

### Immediate Git Rollback
```bash
# Return to safe state immediately
cd /home/nixos/bin/src/poc/flake-readme
git checkout pre-ignore-only-backup
git branch rollback-emergency-$(date +%Y%m%d%H%M)
```

### Alternative: Reset to Backup Branch
```bash
# If current branch is corrupted
git reset --hard backup-pre-ignore-only-20250923
```

## Flake Input Pin Instructions for Users

### Emergency Flake Lock
If users experience issues with the new ignore-only policy:

```bash
# Pin to last known good version
nix flake lock --override-input flake-readme github:username/flake-readme/pre-ignore-only-backup

# Or use specific commit
nix flake lock --override-input flake-readme github:username/flake-readme/[commit-hash]
```

### Local Flake Override
```nix
{
  inputs = {
    flake-readme = {
      url = "github:username/flake-readme/pre-ignore-only-backup";
      # Or specific commit: url = "github:username/flake-readme/[commit-hash]";
    };
  };
}
```

## Recovery Procedures if Implementation Fails

### 1. Immediate Assessment
```bash
# Check what failed
cd /home/nixos/bin/src/poc/flake-readme
nix flake check 2>&1 | tee failure-log.txt
```

### 2. Partial Rollback (Per-file basis)
```bash
# Rollback specific files if only some components failed
git checkout pre-ignore-only-backup -- lib/core-docs.nix
git checkout pre-ignore-only-backup -- lib/flake-module.nix
```

### 3. Complete Implementation Rollback
```bash
# Full rollback to pre-implementation state
git reset --hard pre-ignore-only-backup
git clean -fd  # Remove untracked files
```

### 4. Verification After Rollback
```bash
# Verify system works after rollback
nix flake check
nix build .#readme-config
./verify-rollback.sh
```

## Testing Rollback Procedures

### Pre-Implementation Test
```bash
# Create test scenario
git stash  # Save current work
git checkout pre-ignore-only-backup
echo "Testing rollback from this point"
git checkout fix  # Return to implementation branch
git stash pop  # Restore work
```

### Post-Implementation Test
```bash
# Test rollback after implementation
cp -r /home/nixos/bin/src/poc/flake-readme /tmp/flake-readme-test
cd /tmp/flake-readme-test
# Follow rollback procedures above
# Verify functionality
```

## Safety Checklists

### Pre-Implementation Safety Checks
- [ ] Backup branch created: `backup-pre-ignore-only-$(date +%Y%m%d)`
- [ ] Backup tag created: `pre-ignore-only-backup`
- [ ] Current changes committed or stashed
- [ ] Rollback script tested
- [ ] Recovery procedures documented
- [ ] Emergency contact plan ready

### Post-Implementation Verification Steps
- [ ] `nix flake check` passes
- [ ] All tests pass (run test suite)
- [ ] Core functionality verified
- [ ] Documentation updated
- [ ] Rollback procedures still accessible
- [ ] Backup integrity verified

## Emergency Contacts and Resources

### Key Files to Monitor
- `lib/core-docs.nix` - Core documentation logic
- `lib/flake-module.nix` - Main flake module interface
- `CHANGELOG.md` - Version tracking
- Test files - Validation mechanisms

### Rollback Decision Matrix
| Scenario | Action | Priority |
|----------|--------|----------|
| Build fails | Immediate rollback | HIGH |
| Tests fail | Investigate first, rollback if critical | MEDIUM |
| Documentation issues | Fix forward unless blocking | LOW |
| Performance regression | Rollback and investigate | HIGH |

## Recovery Timeline
- **0-5 minutes**: Execute emergency rollback
- **5-15 minutes**: Verify rollback success
- **15-30 minutes**: Assess damage and plan forward
- **30+ minutes**: Implement fix or permanent rollback

## Version Recovery
```bash
# List all available recovery points
git tag --list | grep backup
git branch --list | grep backup

# Show what changed since backup
git diff pre-ignore-only-backup..HEAD --name-only
```

## Communication Plan
1. Document the issue in failure-log.txt
2. Execute appropriate rollback procedure
3. Verify system stability
4. Plan remediation or permanent rollback
5. Update team on status and next steps