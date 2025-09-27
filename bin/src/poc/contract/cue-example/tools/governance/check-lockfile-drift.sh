#!/usr/bin/env bash
# Lock file drift detection for SSOT governance
# Ensures flake.lock is consistent and not modified without proper governance

set -euo pipefail

echo "🔒 Checking for lock file drift..."

# Check if flake.lock exists
if [[ ! -f "flake.lock" ]]; then
    echo "❌ flake.lock not found"
    exit 1
fi

# Check if flake.lock is tracked by git (allow global ignore)
if ! git ls-files --error-unmatch flake.lock >/dev/null 2>&1; then
    if git check-ignore flake.lock >/dev/null 2>&1; then
        echo "ℹ️  flake.lock is globally ignored - checking for local changes only"
    else
        echo "❌ flake.lock is not tracked by git"
        exit 1
    fi
fi

# Check for uncommitted changes to flake.lock
if git diff --quiet flake.lock && git diff --cached --quiet flake.lock; then
    echo "✅ No lock file drift detected"
else
    echo "⚠️  Lock file changes detected:"
    echo "Staged changes:"
    git diff --cached --name-only flake.lock || true
    echo "Working tree changes:"
    git diff --name-only flake.lock || true

    # Check if this is intentional (commit message contains lock update keyword)
    if git log -1 --pretty=%B | grep -E "(update.*lock|lock.*update|bump.*deps|dependency.*update)" >/dev/null 2>&1; then
        echo "✅ Lock file update appears intentional (based on commit message)"
    else
        echo "❌ Lock file drift detected without proper governance"
        echo "If this is intentional, include 'update lock' or 'dependency update' in commit message"
        exit 1
    fi
fi

# Validate lock file integrity
if ! nix flake metadata --json >/dev/null 2>&1; then
    echo "❌ flake.lock appears corrupted or invalid"
    exit 1
fi

echo "✅ Lock file drift check passed"