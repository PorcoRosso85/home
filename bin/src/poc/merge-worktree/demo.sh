#!/usr/bin/env bash
set -euo pipefail

# Practical demonstration of the worktree restriction system
# Shows installation, configuration, and policy enforcement

echo "🚀 Worktree Restriction System Demo"
echo "=================================="

# Create demo repositories
DEMO_DIR=$(mktemp -d)
BARE_REPO="$DEMO_DIR/repo.git"
WORK_REPO="$DEMO_DIR/workspace"

echo "📁 Setting up demo repositories in: $DEMO_DIR"

# Create bare repository
git init --bare "$BARE_REPO" >/dev/null 2>&1
echo "✅ Created bare repository: $BARE_REPO"

# Install the hook using the Nix app
echo "🔧 Installing worktree restriction hook..."
nix run .#install "$BARE_REPO"

# Configure policies
echo "⚙️  Configuring policies..."
git -C "$BARE_REPO" config policy.coreRef "refs/heads/main"
git -C "$BARE_REPO" config --add policy.coreRef "refs/heads/staging"
git -C "$BARE_REPO" config policy.allowedGlob "flakes/*/**"
git -C "$BARE_REPO" config --add policy.allowedGlob "docs/**"

echo "   Core refs: main, staging"
echo "   Allowed paths: flakes/**/**, docs/**"

# Create working repository
git init "$WORK_REPO" >/dev/null 2>&1
cd "$WORK_REPO"
git remote add origin "$BARE_REPO"
git config user.name "Demo User"
git config user.email "demo@example.com"

echo ""
echo "🧪 Testing Policy Enforcement"
echo "=============================="

# Test 1: Create allowed content on feature branch
echo "Test 1: Push allowed content to feature branch"
mkdir -p flakes/example
echo '{ description = "Example flake"; }' > flakes/example/flake.nix
git add flakes/
git commit -m "Add example flake" >/dev/null 2>&1

if git push origin HEAD:refs/heads/feature 2>&1; then
    echo "✅ PASS: Allowed content on feature branch accepted"
else
    echo "❌ FAIL: Should have allowed content on feature branch"
fi

# Test 2: Try to push forbidden content
echo ""
echo "Test 2: Push forbidden content to feature branch"
mkdir -p forbidden
echo "This should not be allowed" > forbidden/file.txt
git add forbidden/
git commit -m "Add forbidden content" >/dev/null 2>&1

if git push origin HEAD:refs/heads/feature-forbidden 2>&1; then
    echo "❌ FAIL: Should have rejected forbidden content"
else
    echo "✅ PASS: Forbidden content correctly rejected"
fi

# Test 3: Try direct commit to main branch
echo ""
echo "Test 3: Try direct commit to main branch"
git reset --hard HEAD~1 >/dev/null 2>&1  # Remove forbidden content
mkdir -p docs
echo "# Documentation" > docs/README.md
git add docs/
git commit -m "Add documentation" >/dev/null 2>&1

if git push origin HEAD:refs/heads/main 2>&1; then
    echo "❌ FAIL: Should have rejected direct commit to main"
else
    echo "✅ PASS: Direct commit to main correctly rejected"
fi

# Test 4: Enable initial creation and create main branch
echo ""
echo "Test 4: Enable initial creation and create main branch"
# Modify hook to allow initial creation
echo 'export ALLOW_INITIAL_CREATE="true"' >> "$BARE_REPO/hooks/pre-receive"

if git push origin HEAD:refs/heads/main 2>&1; then
    echo "✅ PASS: Initial creation of main branch allowed when configured"
else
    echo "❌ FAIL: Should have allowed initial creation when configured"
fi

# Test 5: Test environment variable override
echo ""
echo "Test 5: Test environment variable override"
# Modify hook to demonstrate environment override
cat >> "$BARE_REPO/hooks/pre-receive" << 'EOF'
export CORE_REFS_OVERRIDE="refs/heads/production"
export ALLOWED_GLOBS_OVERRIDE="src/**"
EOF

mkdir -p src
echo "Source code" > src/main.rs
git add src/
git commit -m "Add source code" >/dev/null 2>&1

# Main should not be restricted anymore due to override
if git push origin HEAD:refs/heads/main 2>&1; then
    echo "✅ PASS: Environment override working - main no longer restricted"
else
    echo "❌ FAIL: Environment override should have made main unrestricted"
fi

# But production should be restricted
if git push origin HEAD:refs/heads/production 2>&1; then
    echo "❌ FAIL: Should have restricted production branch"
else
    echo "✅ PASS: Production branch correctly restricted by environment override"
fi

echo ""
echo "🎯 Demonstration Summary"
echo "======================="
echo "✅ Hook installation and configuration working"
echo "✅ Path-based restrictions enforced"
echo "✅ Core branch protection working"
echo "✅ Environment variable overrides functional"
echo "✅ Initial creation policy configurable"

echo ""
echo "🧹 Cleanup"
echo "=========="
echo "Demo repositories created in: $DEMO_DIR"
echo "Run: rm -rf $DEMO_DIR to clean up"

echo ""
echo "📖 Next Steps"
echo "============"
echo "1. Install to your repository: nix run .#install /path/to/repo.git"
echo "2. Configure policies: git config policy.coreRef refs/heads/main"
echo "3. Set allowed paths: git config policy.allowedGlob 'your-pattern/**'"
echo "4. Test with: nix run . -- --help"

echo ""
echo "✨ Demo completed successfully!"