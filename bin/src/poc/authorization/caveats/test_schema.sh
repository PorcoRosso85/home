#!/usr/bin/env bash
# Test: SpiceDBスキーマが正しく定義され、基本的な権限モデルが機能すること

set -euo pipefail

echo "Testing SpiceDB schema..."

# Test 1: schema.zamlファイルが存在すること
if [ ! -f "schema.zaml" ]; then
    echo "❌ FAIL: schema.zaml file does not exist"
    exit 1
fi
echo "✅ PASS: schema.zaml file exists"

# Test 2: スキーマが有効であること（SpiceDBでバリデーション）
echo "Starting temporary SpiceDB instance for validation..."
# Start SpiceDB in the background with a temporary datastore
spicedb serve --grpc-preshared-key "test-key" \
    --datastore-engine memory \
    --grpc-addr :50051 \
    --http-addr :8080 \
    --http-enabled \
    --dispatch-cluster-enabled=false &

SPICEDB_PID=$!
sleep 2  # Wait for SpiceDB to start

# Function to cleanup SpiceDB on exit
cleanup() {
    kill $SPICEDB_PID 2>/dev/null || true
}
trap cleanup EXIT

# Test schema validation using curl API
SCHEMA_CONTENT=$(cat schema.zaml | jq -Rs .)
SCHEMA_REQUEST="{\"schema\": $SCHEMA_CONTENT}"

echo "Sending schema to SpiceDB..."
RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d "$SCHEMA_REQUEST" \
    http://localhost:8080/v1/schema/write)

echo "Response: $RESPONSE"

if ! echo "$RESPONSE" | grep -q "writtenAt"; then
    echo "❌ FAIL: Schema validation failed"
    exit 1
fi
echo "✅ PASS: Schema is valid"

# Test 3: 基本的な権限チェックが動作すること
# Write test relationships
cat > test_relationships.zaml << 'EOF'
document:doc1#viewer@user:alice
document:doc1#owner@user:bob
EOF

# Create relationships using API
RELATIONSHIP1='{"operation":"OPERATION_CREATE","relationship":{"resource":{"objectType":"document","objectId":"doc1"},"relation":"viewer","subject":{"object":{"objectType":"user","objectId":"alice"}}}}'
RELATIONSHIP2='{"operation":"OPERATION_CREATE","relationship":{"resource":{"objectType":"document","objectId":"doc1"},"relation":"owner","subject":{"object":{"objectType":"user","objectId":"bob"}}}}'

echo "Creating relationships..."
REL_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d "{\"updates\":[$RELATIONSHIP1,$RELATIONSHIP2]}" \
    http://localhost:8080/v1/relationships/write)

echo "Relationship response: $REL_RESPONSE"

if ! echo "$REL_RESPONSE" | grep -q "writtenAt"; then
    echo "❌ FAIL: Failed to create test relationships"
    exit 1
fi

# Test permission check: owner should have view permission
CHECK_REQUEST='{"resource":{"objectType":"document","objectId":"doc1"},"permission":"view","subject":{"object":{"objectType":"user","objectId":"bob"}}}'
if ! curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d "$CHECK_REQUEST" \
    http://localhost:8080/v1/permissions/check | grep -q '"permissionship":"PERMISSIONSHIP_HAS_PERMISSION"'; then
    echo "❌ FAIL: Owner should have view permission"
    exit 1
fi
echo "✅ PASS: Owner has view permission"

# Test permission check: viewer should have view permission
CHECK_REQUEST2='{"resource":{"objectType":"document","objectId":"doc1"},"permission":"view","subject":{"object":{"objectType":"user","objectId":"alice"}}}'
if ! curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d "$CHECK_REQUEST2" \
    http://localhost:8080/v1/permissions/check | grep -q '"permissionship":"PERMISSIONSHIP_HAS_PERMISSION"'; then
    echo "❌ FAIL: Viewer should have view permission"
    exit 1
fi
echo "✅ PASS: Viewer has view permission"

# Test permission check: non-authorized user should NOT have view permission
CHECK_REQUEST3='{"resource":{"objectType":"document","objectId":"doc1"},"permission":"view","subject":{"object":{"objectType":"user","objectId":"charlie"}}}'
if curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer test-key" \
    -d "$CHECK_REQUEST3" \
    http://localhost:8080/v1/permissions/check | grep -q '"permissionship":"PERMISSIONSHIP_HAS_PERMISSION"'; then
    echo "❌ FAIL: Non-authorized user should NOT have view permission"
    exit 1
fi
echo "✅ PASS: Non-authorized user does not have view permission"

# Clean up
rm -f test_relationships.zaml

echo "🎉 All schema tests passed!"