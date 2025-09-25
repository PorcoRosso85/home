#!/usr/bin/env bash
# SSOT Verification: Comprehensive check for readme.nix ↔ README.md consistency
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🎯 SSOT Verification Suite"
echo "=================================="

# Initialize counters
ERRORS=0
WARNINGS=0

log_error() {
    echo "❌ ERROR: $1"
    ((ERRORS++))
}

log_warning() {
    echo "⚠️  WARNING: $1"
    ((WARNINGS++))
}

log_success() {
    echo "✅ $1"
}

# Verify readme.nix exists and is valid
if [[ ! -f "readme.nix" ]]; then
    log_error "readme.nix not found"
    exit 1
fi

# Test readme.nix can be evaluated
if ! nix-instantiate --eval readme.nix --attr description >/dev/null 2>&1; then
    log_error "readme.nix cannot be evaluated (syntax error)"
    exit 1
fi

log_success "readme.nix structure valid"

# Extract key data from readme.nix
README_NX_DESC=$(nix-instantiate --eval --strict readme.nix --attr description 2>/dev/null | tr -d '"')
README_NX_VERSION=$(nix-instantiate --eval --strict readme.nix --attr meta.version 2>/dev/null | tr -d '"')

# Verify README.md exists
if [[ ! -f "README.md" ]]; then
    log_error "README.md not found"
    exit 1
fi

# Rule 1: No exact duplication of structured data
if grep -Fq "$README_NX_DESC" README.md; then
    log_error "README.md contains exact duplicate of readme.nix description"
    echo "         Found: '$README_NX_DESC'"
    echo "         Fix: Use natural language variation instead of copying"
fi

# Rule 2: README.md should reference readme.nix for specifications
if ! grep -qi "readme\.nix" README.md; then
    log_warning "README.md should reference readme.nix for detailed specifications"
    echo "           Suggestion: Add 'See readme.nix for technical specifications'"
fi

# Rule 3: Check for hardcoded versions that should come from readme.nix
if grep -Eq "version.*[0-9]+\.[0-9]+\.[0-9]+" README.md && ! grep -q "$README_NX_VERSION" README.md; then
    log_warning "README.md may contain hardcoded version numbers"
    echo "           Current readme.nix version: $README_NX_VERSION"
fi

# Rule 4: No structured data patterns in README.md
STRUCTURED_PATTERNS="(goal|nonGoal|output|meta).*="
if grep -Eq "$STRUCTURED_PATTERNS" README.md; then
    log_error "README.md contains structured data patterns"
    echo "         These belong in readme.nix, not README.md"
    echo "         Keep README.md focused on narrative and usage"
fi

# Rule 5: Verify SSOT principle compliance
SSOT_INDICATORS=("# Configuration" "## Schema" "### Fields")
for indicator in "${SSOT_INDICATORS[@]}"; do
    if grep -Fq "$indicator" README.md; then
        log_warning "README.md contains structured documentation: '$indicator'"
        echo "           Consider: Move structured docs to readme.nix or separate schema docs"
    fi
done

echo "=================================="
echo "📊 SSOT Verification Summary"
echo "   Errors: $ERRORS"
echo "   Warnings: $WARNINGS"

if [[ $ERRORS -gt 0 ]]; then
    echo "❌ SSOT verification FAILED"
    echo "   Fix errors above to ensure readme.nix ↔ README.md consistency"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo "⚠️  SSOT verification PASSED with warnings"
    echo "   Consider addressing warnings for better SSOT compliance"
    exit 0
else
    echo "✅ SSOT verification PASSED"
    echo "   Perfect readme.nix ↔ README.md separation maintained"
    exit 0
fi