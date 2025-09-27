#!/usr/bin/env bash
# Contract completeness validation for SSOT governance
# Ensures all contracts have required fields and proper structure

set -euo pipefail

echo "📋 Checking contract completeness..."

# Find all contract files
contract_files=$(find contracts/ -name "contract.cue" 2>/dev/null || true)

if [[ -z "$contract_files" ]]; then
    echo "⚠️  No contract files found in contracts/ directory"
    exit 0
fi

# Required fields for complete contracts
REQUIRED_FIELDS=(
    "name"
    "version"
    "description"
    "interface"
    "dependencies"
)

# Optional but recommended fields
RECOMMENDED_FIELDS=(
    "metadata"
    "ports"
    "env"
    "volumes"
    "healthcheck"
)

validation_failed=false

echo "Validating contract completeness..."

for contract in $contract_files; do
    echo "Checking: $contract"

    # Check required fields
    missing_required=()
    for field in "${REQUIRED_FIELDS[@]}"; do
        if ! grep -q "$field:" "$contract"; then
            missing_required+=("$field")
        fi
    done

    # Check recommended fields
    missing_recommended=()
    for field in "${RECOMMENDED_FIELDS[@]}"; do
        if ! grep -q "$field:" "$contract"; then
            missing_recommended+=("$field")
        fi
    done

    # Report findings
    if [[ ${#missing_required[@]} -gt 0 ]]; then
        echo "❌ Missing required fields in $contract:"
        printf '    • %s\n' "${missing_required[@]}"
        validation_failed=true
    fi

    if [[ ${#missing_recommended[@]} -gt 0 ]]; then
        echo "⚠️  Missing recommended fields in $contract:"
        printf '    • %s\n' "${missing_recommended[@]}"
    fi

    # Validate CUE syntax
    if ! cue vet "$contract" >/dev/null 2>&1; then
        echo "❌ CUE validation failed for: $contract"
        echo "Details:"
        cue vet "$contract" || true
        validation_failed=true
    fi

    # Check for proper versioning
    if grep -q "version:" "$contract"; then
        version=$(grep "version:" "$contract" | head -1 | sed 's/.*version:[[:space:]]*//' | sed 's/[\"'"'"']//g')
        if ! echo "$version" | grep -qE "^[0-9]+\.[0-9]+\.[0-9]+"; then
            echo "⚠️  Version in $contract should follow semantic versioning (x.y.z)"
        fi
    fi

    # Check for interface completeness
    if grep -q "interface:" "$contract"; then
        # Verify interface has essential components
        interface_section=$(sed -n '/interface:/,/^[[:space:]]*[a-zA-Z]/p' "$contract" | head -n -1)

        if ! echo "$interface_section" | grep -q "inputs\|outputs\|methods"; then
            echo "⚠️  Interface in $contract should define inputs, outputs, or methods"
        fi
    fi

    if [[ "$validation_failed" == "false" ]]; then
        echo "✅ Contract completeness check passed for: $contract"
    fi
done

# Check for contract consistency across environment
echo ""
echo "Checking contract consistency..."

# Verify contracts don't conflict with each other
if [[ $(echo "$contract_files" | wc -l) -gt 1 ]]; then
    # Check for name conflicts
    names=$(grep -h "name:" $contract_files | sed 's/.*name:[[:space:]]*//' | sed 's/[\"'"'"']//g' | sort)
    duplicates=$(echo "$names" | uniq -d)

    if [[ -n "$duplicates" ]]; then
        echo "❌ Duplicate contract names detected:"
        echo "$duplicates" | sed 's/^/    /'
        validation_failed=true
    fi
fi

if [[ "$validation_failed" == "true" ]]; then
    echo ""
    echo "❌ Contract completeness validation failed!"
    echo "Ensure all contracts have required fields and proper structure."
    echo "This is essential for SSOT compliance and system integrity."
    exit 1
fi

echo "✅ All contracts are complete and properly structured"