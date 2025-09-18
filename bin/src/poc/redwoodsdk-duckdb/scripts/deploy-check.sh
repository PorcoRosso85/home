#!/bin/bash

# Pre-deployment validation script
set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ERRORS=0
WARNINGS=0

# Function to print colored output
print_color() {
    local color=$1
    shift
    echo -e "${color}$*${NC}"
}

# Function to check and report
check() {
    local name=$1
    local command=$2
    local critical=${3:-true}
    
    echo -n "  Checking $name... "
    
    if eval "$command" &> /dev/null; then
        print_color $GREEN "✅"
        return 0
    else
        if [ "$critical" = true ]; then
            print_color $RED "❌"
            ((ERRORS++))
        else
            print_color $YELLOW "⚠️"
            ((WARNINGS++))
        fi
        return 1
    fi
}

# Banner
print_color $BLUE "╔════════════════════════════════════════════╗"
print_color $BLUE "║   🔍 Pre-Deployment Validation             ║"
print_color $BLUE "╚════════════════════════════════════════════╝"
echo ""

cd "$PROJECT_ROOT"

# 1. Environment Checks
print_color $YELLOW "📋 Environment Checks:"
check "Node.js version" "node --version"
check "NPM/PNPM available" "command -v npm || command -v pnpm"
check "Wrangler installed" "command -v wrangler"
check "Prisma installed" "command -v prisma"
echo ""

# 2. Configuration Checks
print_color $YELLOW "⚙️  Configuration Checks:"
check "wrangler.jsonc exists" "test -f wrangler.jsonc"
check "package.json exists" "test -f package.json"
check "Database ID configured" "grep -v 'REPLACE_WITH_DATABASE_ID' wrangler.jsonc"
check "Prisma schema valid" "npx prisma validate"
echo ""

# 3. Build Checks
print_color $YELLOW "🔨 Build Checks:"
check "TypeScript compilation" "npm run types" true
check "Dependencies installed" "test -d node_modules"
check "Prisma client generated" "test -d generated/prisma"
echo ""

# 4. Test Checks
print_color $YELLOW "🧪 Test Checks:"
if [ -f "vitest.config.ts" ]; then
    check "Unit tests pass" "npm run test:unit -- --run" false
    check "Integration tests configured" "test -d tests/integration" false
else
    print_color $YELLOW "  ⚠️  No test configuration found"
    ((WARNINGS++))
fi
echo ""

# 5. Security Checks
print_color $YELLOW "🔐 Security Checks:"
check "No hardcoded secrets in code" "! grep -r 'api[_-]key.*=.*['\"]' src/ --include='*.ts' --include='*.tsx'" true
check "No .env in git" "! git ls-files | grep -E '^\.env$'" true
check "Security headers configured" "grep -q 'x-content-type-options' src/app/headers.ts" false
echo ""

# 6. Database Checks
print_color $YELLOW "🗄️  Database Checks:"
check "Migrations directory exists" "test -d migrations"
check "D1 database configured" "grep -q 'd1_databases' wrangler.jsonc"

# Try to list D1 databases (might fail without auth)
if npx wrangler d1 list &> /dev/null; then
    DB_NAME=$(grep 'database_name' wrangler.jsonc | head -1 | cut -d'"' -f4)
    check "D1 database exists" "npx wrangler d1 list | grep -q '$DB_NAME'" false
fi
echo ""

# 7. Performance Checks
print_color $YELLOW "⚡ Performance Checks:"
check "Bundle size reasonable" "[ $(find dist -name '*.js' 2>/dev/null | xargs du -cb 2>/dev/null | grep total | cut -f1) -lt 5242880 ]" false
check "No console.log in production" "! grep -r 'console\.log' src/ --include='*.ts' --include='*.tsx' | grep -v '// eslint-disable'" false
echo ""

# 8. Documentation Checks
print_color $YELLOW "📚 Documentation Checks:"
check "README exists" "test -f README.md" false
check "Deployment docs exist" "test -f docs/PRODUCTION_DEPLOY.md" false
check "API documentation" "test -f docs/API.md" false
echo ""

# 9. Git Checks
print_color $YELLOW "📦 Git Checks:"
check "Git repository initialized" "test -d .git"
check "No uncommitted changes" "[ -z \"$(git status --porcelain)\" ]" false
check ".gitignore configured" "test -f .gitignore"
echo ""

# 10. Final Validation
print_color $YELLOW "🎯 Running final validation..."

# Check if we can actually build
BUILD_SUCCESS=false
if npm run build &> /tmp/build.log; then
    print_color $GREEN "  ✅ Build successful"
    BUILD_SUCCESS=true
else
    print_color $RED "  ❌ Build failed (see /tmp/build.log for details)"
    ((ERRORS++))
fi

echo ""

# Summary
print_color $BLUE "╔════════════════════════════════════════════╗"
print_color $BLUE "║   📊 Validation Summary                    ║"
print_color $BLUE "╚════════════════════════════════════════════╝"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    print_color $GREEN "🎉 All checks passed! Ready to deploy."
    echo ""
    print_color $GREEN "Deploy with: npm run deploy:safe"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    print_color $YELLOW "✅ No critical errors found."
    print_color $YELLOW "⚠️  $WARNINGS warning(s) detected."
    echo ""
    print_color $YELLOW "Review warnings before deploying."
    print_color $NC "Deploy with: npm run deploy:safe"
    exit 0
else
    print_color $RED "❌ $ERRORS critical error(s) found."
    print_color $YELLOW "⚠️  $WARNINGS warning(s) detected."
    echo ""
    print_color $RED "Fix errors before deploying."
    
    # Show common fixes
    echo ""
    print_color $YELLOW "Common fixes:"
    print_color $NC "  • Missing database ID: Run 'npm run init'"
    print_color $NC "  • Build errors: Check TypeScript errors with 'npm run types'"
    print_color $NC "  • Test failures: Run 'npm test' to see details"
    print_color $NC "  • Uncommitted changes: Commit or stash your changes"
    
    exit 1
fi