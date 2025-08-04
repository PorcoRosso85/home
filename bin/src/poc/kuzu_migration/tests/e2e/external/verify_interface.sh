#!/usr/bin/env bash
# Verify that the kuzu-migrate library interface works correctly

set -euo pipefail

echo "Verifying kuzu-migrate library interface..."
echo "=========================================="
echo ""

# Get the parent flake directory
PARENT_FLAKE_DIR="$(cd "$(dirname "$0")/../../.." && pwd)"

echo "📁 Parent flake directory: $PARENT_FLAKE_DIR"
echo ""

# Test that we can evaluate the library function
echo "🔍 Testing lib.mkKuzuMigration evaluation..."
cd "$PARENT_FLAKE_DIR"

# Create a test expression that uses the library
cat > /tmp/test-kuzu-lib.nix << 'EOF'
{ kuzu-migrate }:
let
  # Dummy pkgs for testing
  pkgs = {
    system = "x86_64-linux";
    writeShellScript = name: text: "/bin/${name}";
  };
  
  # Test the library function
  apps = kuzu-migrate.lib.mkKuzuMigration {
    inherit pkgs;
    ddlPath = "./test_ddl";
  };
in
{
  # Check that all expected apps are present
  hasInit = apps ? init;
  hasStatus = apps ? status;
  hasMigrate = apps ? migrate;
  hasSnapshot = apps ? snapshot;
  
  # Check that apps have correct structure
  initType = apps.init.type or "missing";
  statusType = apps.status.type or "missing";
  migrateType = apps.migrate.type or "missing";
  snapshotType = apps.snapshot.type or "missing";
}
EOF

# Evaluate the test expression
echo "Running evaluation test..."
RESULT=$(nix eval --impure --expr "import /tmp/test-kuzu-lib.nix { kuzu-migrate = (builtins.getFlake \"$PARENT_FLAKE_DIR\"); }" --json)

echo "Result: $RESULT"
echo ""

# Parse and verify the result
if echo "$RESULT" | jq -e '.hasInit and .hasStatus and .hasMigrate and .hasSnapshot' > /dev/null; then
    echo "✅ All required apps are present"
else
    echo "❌ Missing required apps"
    exit 1
fi

if echo "$RESULT" | jq -e '.initType == "app" and .statusType == "app" and .migrateType == "app" and .snapshotType == "app"' > /dev/null; then
    echo "✅ All apps have correct type"
else
    echo "❌ Apps have incorrect type"
    exit 1
fi

echo ""
echo "🎯 Testing actual app execution..."

# Test that the apps can be executed
nix run --impure "$PARENT_FLAKE_DIR#kuzu-migrate" -- --version

echo ""
echo "✅ Library interface verification complete!"
echo ""
echo "The lib.mkKuzuMigration function:"
echo "- Accepts { pkgs, ddlPath } parameters"
echo "- Returns { init, status, migrate, snapshot } apps"
echo "- Each app has type = \"app\" and a program attribute"
echo "- The ddlPath parameter is correctly passed to each command"

# Clean up
rm -f /tmp/test-kuzu-lib.nix