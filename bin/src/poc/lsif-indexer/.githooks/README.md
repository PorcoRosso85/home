# Git Hooks

## Pre-commit Hook

The `pre-commit` hook runs `./scripts/scan-nil-leftovers.sh` to prevent committing deprecated nil LSP references.

## Enable Git Hooks

To enable these hooks for this repository:

```bash
git config core.hooksPath .githooks
```

## Hook Functionality

- **pre-commit**: Scans for nil LSP leftovers
- Blocks commits if nil LSP references are found
- Ensures clean commits without deprecated LSP references