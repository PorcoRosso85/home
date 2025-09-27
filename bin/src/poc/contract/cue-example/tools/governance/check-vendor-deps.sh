#!/usr/bin/env bash
# Vendor dependencies validation for SSOT governance
# Ensures all dependencies are properly declared and managed

set -euo pipefail

echo "📦 Checking vendor dependencies..."

# Check flake inputs for dependency declarations
if [[ ! -f "flake.nix" ]]; then
    echo "❌ flake.nix not found"
    exit 1
fi

echo "Validating flake inputs..."

# Extract inputs from flake.nix
if ! grep -q "inputs" flake.nix; then
    echo "⚠️  No inputs section found in flake.nix"
fi

# Check for version pinning
unpinned_inputs=$(grep -A 20 "inputs.*{" flake.nix | grep -E "url.*github:|url.*gitlab:" | grep -v "rev\|ref" || true)

if [[ -n "$unpinned_inputs" ]]; then
    echo "⚠️  Unpinned dependencies detected:"
    echo "$unpinned_inputs" | sed 's/^/    /'
    echo "    Consider pinning to specific revisions for reproducibility"
fi

# Check for duplicate dependencies
echo "Checking for duplicate dependencies..."

# Extract only input declarations from flake.nix
declared_deps=$(awk '/inputs[[:space:]]*=/{flag=1; next} /^[[:space:]]*}[[:space:]]*;?$/{flag=0} flag && /^[[:space:]]*[a-zA-Z0-9_-]+[[:space:]]*=/{print $1}' flake.nix | tr -d ' ' || true)

declare -A dep_count
for dep in $declared_deps; do
    if [[ -n "$dep" ]]; then
        if [[ -n "${dep_count[$dep]:-}" ]]; then
            ((dep_count[$dep]++))
        else
            dep_count[$dep]=1
        fi
    fi
done

duplicates_found=false
for dep in "${!dep_count[@]}"; do
    if [[ ${dep_count[$dep]} -gt 1 ]]; then
        echo "❌ Duplicate dependency: $dep (appears ${dep_count[$dep]} times)"
        duplicates_found=true
    fi
done

# Check for transitive dependency conflicts
echo "Checking transitive dependencies..."

if command -v nix >/dev/null 2>&1; then
    # Check if flake can be evaluated
    if ! nix flake check --no-build 2>/dev/null; then
        echo "❌ Flake evaluation failed - potential dependency conflicts"
        echo "Run 'nix flake check' for detailed error information"
        exit 1
    fi

    # Check for security advisories (if available)
    if command -v nix-audit >/dev/null 2>&1; then
        echo "Running security audit..."
        nix-audit || echo "⚠️  Security audit tool not available or found issues"
    fi
fi

# Check for proper dependency organization
echo "Validating dependency organization..."

# Check if development dependencies are separate from runtime dependencies
if ! grep -q "devShells\|devShell" flake.nix; then
    echo "⚠️  No development shell configuration found"
    echo "    Consider separating development and runtime dependencies"
fi

# Validate dependency sources
suspicious_sources=$(grep -E "url.*http://|url.*git\+ssh:" flake.nix || true)

if [[ -n "$suspicious_sources" ]]; then
    echo "⚠️  Potentially insecure dependency sources detected:"
    echo "$suspicious_sources" | sed 's/^/    /'
    echo "    Prefer HTTPS URLs for security"
fi

if [[ "$duplicates_found" == "true" ]]; then
    echo ""
    echo "❌ Vendor dependency validation failed!"
    echo "Resolve duplicate dependencies to maintain SSOT compliance."
    exit 1
fi

echo "✅ Vendor dependencies validation passed"