#!/usr/bin/env bash
#
# OpenCode .gitignore Verification Script
# Validates document protection and artifact exclusion
#

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FLAKE_README_PATH="/home/nixos/bin/src/poc/flake-readme"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# JSON output flag
JSON_OUTPUT=false
if [[ "${1:-}" == "--json" ]]; then
    JSON_OUTPUT=true
fi

# Results tracking
ERRORS=()
WARNINGS=()
SUCCESS_COUNT=0

log_info() {
    if [[ "$JSON_OUTPUT" == "false" ]]; then
        echo -e "${GREEN}✅ $1${NC}"
    fi
    ((SUCCESS_COUNT++))
}

log_warning() {
    if [[ "$JSON_OUTPUT" == "false" ]]; then
        echo -e "${YELLOW}⚠️  $1${NC}"
    fi
    WARNINGS+=("$1")
}

log_error() {
    if [[ "$JSON_OUTPUT" == "false" ]]; then
        echo -e "${RED}❌ $1${NC}"
    fi
    ERRORS+=("$1")
}

# Change to project root
cd "$PROJECT_ROOT"

if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo "🔍 OpenCode .gitignore Verification"
    echo "📁 Project: $PROJECT_ROOT"
    echo
fi

# Test 1: Verify readme.nix files are NOT ignored
if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo "📋 Test 1: Document Protection Verification"
fi

README_FILES=($(find . -name "readme.nix" -type f | sort))
PROTECTED_COUNT=0

for readme_file in "${README_FILES[@]}"; do
    if git check-ignore -q -- "$readme_file" 2>/dev/null; then
        log_error "readme.nix is ignored: $readme_file"
    else
        log_info "readme.nix protected: $readme_file"
        ((PROTECTED_COUNT++))
    fi
done

if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo "   Protected: $PROTECTED_COUNT/${#README_FILES[@]} files"
    echo
fi

# Test 2: Verify artifacts ARE ignored
if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo "🗑️  Test 2: Artifact Exclusion Verification"
fi

# Test artifact patterns
ARTIFACTS=("result" "result-test" "logs/test.log" "temp.tmp" "backup.bak" "target-files-test.txt")
IGNORED_COUNT=0

for artifact in "${ARTIFACTS[@]}"; do
    if git check-ignore -q -- "$artifact" 2>/dev/null; then
        log_info "Artifact ignored: $artifact"
        ((IGNORED_COUNT++))
    else
        log_warning "Artifact not ignored: $artifact"
    fi
done

if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo "   Ignored: $IGNORED_COUNT/${#ARTIFACTS[@]} patterns"
    echo
fi

# Test 3: flake-readme compatibility (optional - can be slow)
if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo "📚 Test 3: flake-readme Compatibility"
fi

if [[ "${SKIP_FLAKE_README:-}" == "true" ]]; then
    log_info "flake-readme check skipped (SKIP_FLAKE_README=true)"
elif [[ -d "$FLAKE_README_PATH" ]]; then
    # Use timeout to prevent hanging
    if readme_output=$(timeout 10 bash -c "cd '$FLAKE_README_PATH' && nix run .#readme-check -- --root '$PROJECT_ROOT'" 2>&1); then
        if echo "$readme_output" | grep -q "Documentation validation complete"; then
            log_info "flake-readme validation passed"
        else
            log_warning "flake-readme validation unclear"
        fi
    else
        log_warning "flake-readme validation timed out or failed (use SKIP_FLAKE_README=true to skip)"
    fi
else
    log_warning "flake-readme not found at $FLAKE_README_PATH"
fi

if [[ "$JSON_OUTPUT" == "false" ]]; then
    echo
fi

# Summary
ERROR_COUNT=${#ERRORS[@]}
WARNING_COUNT=${#WARNINGS[@]}

if [[ "$JSON_OUTPUT" == "true" ]]; then
    # JSON output
    cat << EOF
{
  "status": "$([ $ERROR_COUNT -eq 0 ] && echo "success" || echo "failure")",
  "summary": {
    "errors": $ERROR_COUNT,
    "warnings": $WARNING_COUNT,
    "successes": $SUCCESS_COUNT
  },
  "tests": {
    "document_protection": {
      "protected": $PROTECTED_COUNT,
      "total": ${#README_FILES[@]}
    },
    "artifact_exclusion": {
      "ignored": $IGNORED_COUNT,
      "total": ${#ARTIFACTS[@]}
    }
  },
  "errors": [$(printf '"%s",' "${ERRORS[@]}" | sed 's/,$//')],
  "warnings": [$(printf '"%s",' "${WARNINGS[@]}" | sed 's/,$//')],
  "timestamp": "$(date -Iseconds)"
}
EOF
else
    # Human-readable summary
    echo "📊 Verification Summary"
    echo "   ✅ Successes: $SUCCESS_COUNT"
    echo "   ⚠️  Warnings: $WARNING_COUNT"
    echo "   ❌ Errors: $ERROR_COUNT"
    echo

    if [[ $ERROR_COUNT -eq 0 ]]; then
        echo -e "${GREEN}🎉 All critical checks passed!${NC}"
        if [[ $WARNING_COUNT -gt 0 ]]; then
            echo -e "${YELLOW}⚠️  Some warnings detected - consider reviewing${NC}"
        fi
    else
        echo -e "${RED}💥 Critical errors detected - immediate action required${NC}"
    fi
fi

# Exit with appropriate code
exit $ERROR_COUNT