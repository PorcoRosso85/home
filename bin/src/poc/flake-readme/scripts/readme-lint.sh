#!/usr/bin/env bash
# SSOT Lint: Ensure README.md doesn't duplicate readme.nix structured data
set -euo pipefail

echo "🔍 README.md SSOT Compliance Check"

# Extract structured data from readme.nix
README_NX_DESC=$(nix-instantiate --eval --strict readme.nix --attr description 2>/dev/null | tr -d '"')
README_NX_VERSION=$(nix-instantiate --eval --strict readme.nix --attr meta.version 2>/dev/null | tr -d '"')

# Rule 1: README.md should not duplicate the exact description from readme.nix
if grep -Fq "$README_NX_DESC" README.md; then
    echo "❌ FAIL: README.md contains exact duplicate of readme.nix description"
    echo "   Found: '$README_NX_DESC'"
    echo "   Fix: Use natural language variation instead of copying"
    exit 1
fi

# Rule 2: README.md should reference readme.nix for detailed specifications
if ! grep -q "readme.nix" README.md; then
    echo "❌ FAIL: README.md should reference readme.nix for detailed specs"
    echo "   Fix: Add reference like 'See readme.nix for detailed specifications'"
    exit 1
fi

# Rule 3: No hardcoded version numbers (should come from readme.nix)
if grep -Eq "version.*[0-9]+\.[0-9]+\.[0-9]+" README.md; then
    echo "⚠️  WARNING: README.md contains hardcoded version numbers"
    echo "   Consider: Dynamic versioning from readme.nix"
fi

# Rule 4: README.md should be primarily narrative/usage focused
STRUCTURED_PATTERNS="goal.*=\|nonGoal.*=\|output.*=\|meta.*="
if grep -Eq "$STRUCTURED_PATTERNS" README.md; then
    echo "❌ FAIL: README.md contains structured data patterns"
    echo "   Found structured patterns that belong in readme.nix"
    echo "   Fix: Move structured data to readme.nix, keep narrative in README.md"
    exit 1
fi

echo "✅ PASS: README.md follows SSOT lint rules"
echo "📋 Summary: README.md is narrative/usage focused, readme.nix is structured data"