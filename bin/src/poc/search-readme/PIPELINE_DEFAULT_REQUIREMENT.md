# Pipeline Default Mode Requirement

## Current Status
❌ **FAILING**: Legacy mode is currently the default

## Problem
The current implementation defaults to `MODE="legacy"` on line 47 of `flake.nix`, which conflicts with the strict policy requirement identified in the review.

## Evidence

### Current Behavior (Legacy Default)
```bash
$ nix run . -- "test query"
# Result: "No results found in either README or code search" (exit 81)
# Behavior: Tries README search first, then falls back to code search
```

### Expected Behavior (Pipeline Default)  
```bash
$ nix run . -- -m pipeline "test query"
# Result: "No README files matched the responsibility filter" (exit 80)
# Behavior: Fails immediately if no README candidates found (strict policy)
```

## Required Change

**File**: `/home/nixos/bin/src/poc/search-readme/flake.nix`
**Line**: 47
**Current**: `MODE="legacy"`
**Required**: `MODE="pipeline"`

## Verification

The test `test-pipeline-default.sh` validates this requirement:
- ✅ **Currently failing** as expected (detects legacy default)
- 🎯 **Will pass** once the change is applied
- 📊 **Test logic**: Compares default behavior output vs explicit pipeline mode output

## Impact

This change enforces the strict policy by default:
- No fallback behavior in default mode
- Immediate exit 80 if no README candidates
- Immediate exit 81 if no code results in filtered directories
- Suitable for CI/CD and automated workflows requiring predictable behavior

## Rollback

If needed, users can still access legacy behavior explicitly:
```bash
nix run . -- -m legacy "query"
```