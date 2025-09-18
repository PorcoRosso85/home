# browseアプリ新エンドポイント対応確認
# 使用方法: bash test_browse_endpoint.sh

BASE_URL="http://localhost:8000"

echo "1. 旧エンドポイント（削除済み確認）"
echo "POST $BASE_URL/api/snapshot/2"
curl -s -X POST "$BASE_URL/api/snapshot/2"
echo ""
echo ""

echo "2. 新エンドポイント（LocationURI）"
echo "POST $BASE_URL/api/snapshot/2/LocationURI"
curl -s -I -X POST "$BASE_URL/api/snapshot/2/LocationURI" | grep -E "(HTTP/|Content-Length|X-DuckLake-Table)"

echo ""
echo "3. 他のテーブル（将来対応予定）"
echo "POST $BASE_URL/api/snapshot/2/RequirementEntity"
curl -s -I -X POST "$BASE_URL/api/snapshot/2/RequirementEntity" | grep -E "(HTTP/|Content-Length|X-DuckLake-Table)"
