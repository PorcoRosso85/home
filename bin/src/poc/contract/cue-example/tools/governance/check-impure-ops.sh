#!/usr/bin/env bash
# Impure operations prevention for SSOT governance
# Ensures all Nix operations use pure evaluation mode

set -euo pipefail

echo "🚫 Checking for impure operations..."

# Files to check for impure patterns (exclude governance scripts)
FILES_TO_CHECK=(
    "flake.nix"
    "*.nix"
    "*.sh"
    "Makefile"
    "justfile"
    ".github/workflows/*.yml"
    ".github/workflows/*.yaml"
)

# Directories to exclude from scanning
EXCLUDE_PATTERNS=(
    "tools/governance"
    ".git"
    "result"
    "result-*"
)

IMPURE_PATTERNS=(
    "--impure"
    "NIX_PATH="
    "\$NIX_PATH"
    "nix-env"
    "nix-channel"
    "--option sandbox false"
    "--option restrict-eval false"
    "import <nixpkgs>"
    "builtins.getEnv"
    "builtins.currentTime"
    "builtins.currentSystem"
)

# Check for impure patterns in relevant files
echo "Scanning for impure patterns..."
found_violations=false

# Build exclude arguments for find
EXCLUDE_ARGS=()
for exclude in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS+=("-path" "./$exclude" "-prune" "-o")
done

for pattern in "${IMPURE_PATTERNS[@]}"; do
    # Use find with -name patterns for glob patterns
    for file_pattern in "${FILES_TO_CHECK[@]}"; do
        if [[ "$file_pattern" == *.* ]]; then
            # Handle glob patterns with exclusions
            matches=$(find . "${EXCLUDE_ARGS[@]}" -name "$file_pattern" -type f -print | xargs grep -l "$pattern" 2>/dev/null || true)
            if [[ -n "$matches" ]]; then
                echo "❌ Impure pattern '$pattern' found in:"
                echo "$matches" | sed 's/^/  /'
                found_violations=true
            fi
        else
            # Handle specific files
            if [[ -f "$file_pattern" ]] && grep -q "$pattern" "$file_pattern" 2>/dev/null; then
                echo "❌ Impure pattern '$pattern' found in: $file_pattern"
                found_violations=true
            fi
        fi
    done
done

# Check for documentation of pure evaluation requirements
if [[ -f "README.md" ]]; then
    if ! grep -q -i "pure.*eval\|--pure\|impure.*prohibited" README.md; then
        echo "⚠️  README.md should document pure evaluation requirements"
    fi
fi

# Check flake.nix for proper pure evaluation setup
if [[ -f "flake.nix" ]]; then
    if ! grep -q "systems.*flake-utils\|nixpkgs.lib.genAttrs" flake.nix; then
        echo "⚠️  flake.nix should use proper system abstraction for pure evaluation"
    fi
fi

if [[ "$found_violations" == "true" ]]; then
    echo ""
    echo "❌ Impure operations detected!"
    echo "All operations must use pure evaluation mode for SSOT compliance."
    echo "Replace impure patterns with pure alternatives:"
    echo "  • Use 'nix develop' instead of 'nix-env'"
    echo "  • Use flake inputs instead of NIX_PATH"
    echo "  • Avoid --impure flag"
    echo "  • Use deterministic alternatives to builtins.getEnv"
    exit 1
fi

echo "✅ No impure operations detected"