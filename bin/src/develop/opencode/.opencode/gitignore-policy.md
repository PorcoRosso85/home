# OpenCode .gitignore Policy

## Implementation Summary
- **Target**: Nix build artifacts, temporary files, and development databases
- **Strategy**: Ignore-only (no `git rm --cached` used to avoid disruption)
- **Validation**: Maintains flake-readme missingReadmes=0 status

## Safety Measures

### 1. Backup Strategy
- Original tracked files preserved (not removed from Git history)
- .gitignore patterns prevent future tracking of matching files
- Reversible by modifying/removing .gitignore entries

### 2. Pattern Coverage
- `/result*` - Nix build outputs
- `*.bak`, `*.backup`, `*.tmp` - Temporary files
- `target-files*.txt` - Build process artifacts
- `.opencode/*.db*` - Development databases (keeps config/readme)

### 3. Alternative Approaches

#### Option A: Selective Removal (if needed)
```bash
# If specific files need immediate removal:
git rm --cached specific-file.txt
git commit -m "Remove specific tracked artifact"
```

#### Option B: .gitignore Adjustment
```bash
# Add more specific patterns if needed:
echo "additional-pattern" >> .gitignore
git add .gitignore
git commit -m "Refine .gitignore patterns"
```

#### Option C: Emergency Rollback
```bash
# Complete rollback if issues arise:
git checkout HEAD~1 -- .gitignore
git commit -m "Rollback .gitignore changes"
```

## Verification Commands
- Check ignored status: `git status --ignored`
- Test pattern matching: `git check-ignore target-file.txt`
- Validate flake-readme: `cd /home/nixos/bin/src/poc/flake-readme && nix run .#readme-check -- --root /home/nixos/bin/src/develop/opencode`

## Rationale
This ignore-only approach prioritizes stability over immediate cleanup, ensuring:
1. No disruption to existing workflows
2. Gradual artifact exclusion as new files are created
3. Full compatibility with flake-readme requirements
4. Easy reversal if adjustments needed