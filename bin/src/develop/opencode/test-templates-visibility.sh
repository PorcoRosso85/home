#!/usr/bin/env bash
set -euo pipefail

# Test: templates.multi-agent is visible in nix flake show
echo "Testing templates visibility..."

# Get flake show output
FLAKE_SHOW=$(nix flake show --no-warn-dirty 2>/dev/null)

echo "=== Current templates section ==="
echo "$FLAKE_SHOW" | grep -A 10 "templates" || echo "No templates section found"
echo "================================"

# Required templates that must be visible
REQUIRED_TEMPLATES=(
    "opencode-client"
    "multi-agent"
)

MISSING_TEMPLATES=()

for template in "${REQUIRED_TEMPLATES[@]}"; do
    if ! echo "$FLAKE_SHOW" | grep "templates" -A 10 | grep -q "$template"; then
        MISSING_TEMPLATES+=("$template")
    fi
done

if [ ${#MISSING_TEMPLATES[@]} -gt 0 ]; then
    echo "❌ FAIL: Missing templates in flake show: ${MISSING_TEMPLATES[*]}"
    echo "Expected: Both opencode-client and multi-agent templates visible"
    echo "Actual: Templates missing from nix flake show output"
    exit 1
else
    echo "✅ PASS: All required templates found in flake show"
fi

# Additional check: multi-agent description should mention key features
if echo "$FLAKE_SHOW" | grep -A 2 "multi-agent" | grep -q "session\|message\|orchestrator"; then
    echo "✅ PASS: multi-agent template description includes key features"
else
    echo "❌ FAIL: multi-agent template description lacks key features (session/message/orchestrator)"
    exit 1
fi