#!/usr/bin/env bash
# Breaking changes validation for SSOT governance
# Ensures contract changes follow proper versioning and compatibility rules

set -euo pipefail

echo "🔄 Checking for breaking changes..."

# Check if CUE breaking changes validator exists
if [[ ! -f "tools/breaking-changes.cue" ]]; then
    echo "❌ Breaking changes validator not found at tools/breaking-changes.cue"
    exit 1
fi

# Validate all contracts against breaking changes rules
echo "Validating contracts for breaking changes..."

# Find all contract files
contract_files=$(find contracts/ -name "contract.cue" 2>/dev/null || true)

if [[ -z "$contract_files" ]]; then
    echo "⚠️  No contract files found in contracts/ directory"
    exit 0
fi

validation_failed=false

for contract in $contract_files; do
    echo "Checking: $contract"

    # Use CUE to validate against breaking changes rules
    if ! cue vet "$contract" tools/breaking-changes.cue 2>/dev/null; then
        echo "❌ Breaking changes detected in: $contract"
        echo "Details:"
        cue vet "$contract" tools/breaking-changes.cue || true
        validation_failed=true
    else
        echo "✅ No breaking changes in: $contract"
    fi
done

# Check for version updates in modified contracts
if git rev-parse --git-dir >/dev/null 2>&1; then
    modified_contracts=$(git diff --name-only HEAD~1 2>/dev/null | grep "contract\.cue$" || true)

    for contract in $modified_contracts; do
        if [[ -f "$contract" ]]; then
            # Check if version was incremented
            if ! grep -q "version.*[0-9]\+\.[0-9]\+\.[0-9]\+" "$contract"; then
                echo "⚠️  Modified contract $contract should include version number"
            fi
        fi
    done
fi

if [[ "$validation_failed" == "true" ]]; then
    echo ""
    echo "❌ Breaking changes validation failed!"
    echo "Ensure all contract modifications maintain backward compatibility"
    echo "or properly increment version numbers for breaking changes."
    exit 1
fi

echo "✅ Breaking changes validation passed"