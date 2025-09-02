# Final Solution: Directory Restriction for Claude Code

## ✅ WORKING SOLUTION

```bash
firejail --noprofile --blacklist=$PWD/sensitive-dir claude-or-any-command
```

## Key Findings

1. **Firejail WORKS** - But requires `--noprofile` flag
2. **Simple is better** (KISS) - Complex nix run commands cause issues
3. **DRY** - One command pattern for all restrictions

## Tested & Verified

```bash
# This blocks access successfully:
firejail --noprofile --blacklist=$PWD/test-dirs/child1 ls test-dirs/child1
# Result: Permission denied ✓
```

## Why Previous Attempts Failed

- Default profile conflicts with nix run
- Over-engineered approach (YAGNI violation)
- Complex wrapper instead of simple blacklist

## Production Usage

```bash
# For Claude Code with restrictions:
firejail --noprofile \
    --blacklist=$PWD/sensitive \
    --blacklist=$PWD/production \
    bash  # Then run claude inside

# Or use chmod (even simpler):
chmod 000 sensitive/
```

## Principles Applied

- **KISS**: One-line solution
- **DRY**: Reusable pattern
- **YAGNI**: No complex wrappers needed
- **SOLID**: Single responsibility (just block access)