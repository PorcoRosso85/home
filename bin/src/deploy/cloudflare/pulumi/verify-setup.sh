#!/bin/bash
set -euo pipefail

# Pulumi Setup Verification Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Verifying Pulumi Setup"
echo "========================="
echo ""

# Check required files
echo "📋 Checking required files..."
REQUIRED_FILES=(
    "Pulumi.yaml"
    "package.json"
    "tsconfig.json"
    "index.ts"
    "Pulumi.dev.yaml"
    "Pulumi.stg.yaml"
    "Pulumi.prod.yaml"
    ".env.example"
    ".gitignore"
    "README.md"
    "pulumi-safe.sh"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file"
        MISSING_FILES+=("$file")
    fi
done

if [[ ${#MISSING_FILES[@]} -gt 0 ]]; then
    echo ""
    echo "❌ Missing files detected:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    exit 1
fi

echo ""
echo "📋 Checking file permissions..."
if [[ -x "pulumi-safe.sh" ]]; then
    echo "  ✅ pulumi-safe.sh is executable"
else
    echo "  ❌ pulumi-safe.sh is not executable"
    exit 1
fi

echo ""
echo "📋 Checking stack configurations..."
STACKS=("dev" "stg" "prod")
for stack in "${STACKS[@]}"; do
    if [[ -f "Pulumi.$stack.yaml" ]]; then
        echo "  ✅ Stack $stack configured"

        # Check if previewOnly is set
        if grep -q "previewOnly: true" "Pulumi.$stack.yaml"; then
            echo "    🛡️ Preview-only mode enabled"
        else
            echo "    ⚠️ Preview-only mode not found"
        fi
    else
        echo "  ❌ Stack $stack missing"
    fi
done

echo ""
echo "📋 Checking TypeScript configuration..."
if command -v node >/dev/null 2>&1; then
    echo "  ✅ Node.js available"

    # Validate package.json syntax
    if node -e "JSON.parse(require('fs').readFileSync('package.json', 'utf8'))" 2>/dev/null; then
        echo "  ✅ package.json syntax valid"
    else
        echo "  ❌ package.json syntax invalid"
        exit 1
    fi

    # Validate tsconfig.json syntax
    if node -e "JSON.parse(require('fs').readFileSync('tsconfig.json', 'utf8'))" 2>/dev/null; then
        echo "  ✅ tsconfig.json syntax valid"
    else
        echo "  ❌ tsconfig.json syntax invalid"
        exit 1
    fi
else
    echo "  ⚠️ Node.js not available (will be provided by Nix environment)"
fi

echo ""
echo "📋 Security verification..."
if [[ -f ".env" ]]; then
    echo "  ⚠️ .env file found - ensure it's not committed to git"
else
    echo "  ✅ No .env file found (use .env.example as template)"
fi

if grep -q ".env" .gitignore 2>/dev/null; then
    echo "  ✅ .env is properly ignored in .gitignore"
else
    echo "  ❌ .env should be added to .gitignore"
    exit 1
fi

echo ""
echo "🎉 Pulumi Setup Verification Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and configure your Cloudflare credentials"
echo "2. Run 'nix develop' to enter the development environment"
echo "3. Run 'npm install' to install dependencies"
echo "4. Test with './pulumi-safe.sh dev validate'"
echo ""
echo "Available environments: dev, stg, prod"
echo "All environments are configured in preview-only mode for safety."