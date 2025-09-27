#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Testing contract aggregation checks..."

# Test setup: Create test contract files
mkdir -p test-contracts/duplicate1 test-contracts/duplicate2 test-contracts/unresolved

# Test Case 1: Duplicate namespace/name
cat > test-contracts/duplicate1/contract.cue << 'EOF'
package duplicate1
import "example.corp/contract-system/schema"

TestContract1: schema.Contract & {
    namespace: "corp.example"
    name:      "api-service"  // Same as existing
    role:      "service"
    provides:  []
    dependsOn: []
}
EOF

cat > test-contracts/duplicate2/contract.cue << 'EOF'
package duplicate2
import "example.corp/contract-system/schema"

TestContract2: schema.Contract & {
    namespace: "corp.example"
    name:      "api-service"  // Duplicate name
    role:      "lib"
    provides:  []
    dependsOn: []
}
EOF

# Test Case 2: Unresolved dependency
cat > test-contracts/unresolved/contract.cue << 'EOF'
package unresolved
import "example.corp/contract-system/schema"

TestContract3: schema.Contract & {
    namespace: "corp.example"
    name:      "dependent-service"
    role:      "service"
    provides:  []
    dependsOn: [{
        kind:   "db"
        target: "corp.example/nonexistent-db"  // Does not exist
    }]
}
EOF

# Create index.json with test contracts
cat > tools/test-index.json << EOF
[
    "/home/nixos/bin/src/poc/contract/cue-example/contracts/example/contract.cue",
    "/home/nixos/bin/src/poc/contract/cue-example/test-contracts/duplicate1/contract.cue",
    "/home/nixos/bin/src/poc/contract/cue-example/test-contracts/duplicate2/contract.cue",
    "/home/nixos/bin/src/poc/contract/cue-example/test-contracts/unresolved/contract.cue"
]
EOF

echo "Test 1: Testing duplicate namespace/name detection..."
if cue export tools/aggregate.cue -E tools/test-index.json 2>&1 | grep -q "aggregate: duplicate namespace/name"; then
    echo "✅ Duplicate detection works"
else
    echo "❌ Duplicate detection failed"
    exit 1
fi

echo "Test 2: Testing unresolved dependency detection..."
if cue export tools/aggregate.cue -E tools/test-index.json 2>&1 | grep -q "deps: missing provider"; then
    echo "✅ Dependency resolution works"
else
    echo "❌ Dependency resolution failed"
    exit 1
fi

echo "Test 3: Testing standardized error messages..."
OUTPUT=$(cue export tools/aggregate.cue -E tools/test-index.json 2>&1 || true)
if echo "$OUTPUT" | grep -E "^[a-z]+: .+$"; then
    echo "✅ Standardized message format"
else
    echo "❌ Message format not standardized"
    echo "Actual output: $OUTPUT"
    exit 1
fi

echo "Test 4: Testing non-zero exit code..."
if ! cue export tools/aggregate.cue -E tools/test-index.json >/dev/null 2>&1; then
    echo "✅ Non-zero exit code on errors"
else
    echo "❌ Should exit with non-zero code"
    exit 1
fi

# Cleanup
rm -rf test-contracts tools/test-index.json

echo "✅ All aggregation tests passed!"