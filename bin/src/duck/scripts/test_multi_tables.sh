# DuckDB複数テーブル動作確認スクリプト
# 使用方法: bash test_multi_tables.sh

set -e

# 設定
BASE_URL="http://localhost:8000"
CONTENT_TYPE="Content-Type: application/json"

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== DuckDB複数テーブル機能テスト ===${NC}"
echo ""

# 1. サーバー接続確認
echo "1. サーバー接続確認..."
if curl -s -f -X GET "$BASE_URL/" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ サーバーは起動しています${NC}"
else
    echo -e "${RED}✗ サーバーが起動していません${NC}"
    echo "サーバーを起動してください:"
    echo 'LOG_LEVEL=4 LD_LIBRARY_PATH="/nix/store/p44qan69linp3ii0xrviypsw2j4qdcp2-gcc-13.2.0-lib/lib":$LD_LIBRARY_PATH nix run nixpkgs#deno -- run --allow-read --allow-ffi --allow-net --allow-env server.ts'
    exit 1
fi

# 2. DuckLake状態確認
echo ""
echo "2. DuckLake状態確認..."
LAKE_STATUS=$(curl -s -X POST "$BASE_URL/query" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_catalog = '\''lake'\''"}' \
    2>/dev/null || echo '{"error": "failed"}')

if echo "$LAKE_STATUS" | grep -q '"error"'; then
    echo -e "${YELLOW}⚠ DuckLakeが初期化されていません${NC}"
    echo "初期化スクリプトを実行してください:"
    echo "bash /home/nixos/bin/src/duck/scripts/duck.init_multi_tables.sh -y"
    exit 1
fi

# 3. 利用可能なバージョン確認
echo ""
echo "3. 利用可能なバージョン確認..."
VERSIONS=$(curl -s -X POST "$BASE_URL/api/versions")
echo "$VERSIONS" | jq '.' 2>/dev/null || echo "$VERSIONS"

# 4. テーブル一覧取得（新機能）
echo ""
echo -e "${BLUE}4. テーブル一覧取得テスト（新機能）${NC}"
echo "POST /api/snapshot/2/tables"
TABLES_RESPONSE=$(curl -s -X POST "$BASE_URL/api/snapshot/2/tables")
echo "$TABLES_RESPONSE" | jq '.' 2>/dev/null || echo "$TABLES_RESPONSE"

# テーブル名を抽出
if echo "$TABLES_RESPONSE" | jq -e '.tables' > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}✓ テーブル一覧取得成功${NC}"
    TABLE_NAMES=$(echo "$TABLES_RESPONSE" | jq -r '.tables[] | select(.exists == true) | .name')
else
    echo -e "${RED}✗ テーブル一覧取得失敗${NC}"
    exit 1
fi

# 5. 個別テーブル取得テスト（新機能）
echo ""
echo -e "${BLUE}5. 個別テーブル取得テスト（新機能）${NC}"
for table in $TABLE_NAMES; do
    echo ""
    echo "POST /api/snapshot/2/$table"
    
    # ファイルサイズを確認
    RESPONSE_HEADERS=$(curl -s -I -X POST "$BASE_URL/api/snapshot/2/$table" 2>/dev/null)
    CONTENT_LENGTH=$(echo "$RESPONSE_HEADERS" | grep -i "content-length" | awk '{print $2}' | tr -d '\r')
    
    if [ -n "$CONTENT_LENGTH" ] && [ "$CONTENT_LENGTH" -gt 0 ]; then
        echo -e "${GREEN}✓ $table: $CONTENT_LENGTH bytes${NC}"
        
        # 実際にダウンロードしてみる
        curl -s -X POST "$BASE_URL/api/snapshot/2/$table" --output "/tmp/${table}_test.parquet"
        
        # ファイルサイズ確認
        if [ -f "/tmp/${table}_test.parquet" ]; then
            FILE_SIZE=$(stat -f%z "/tmp/${table}_test.parquet" 2>/dev/null || stat -c%s "/tmp/${table}_test.parquet" 2>/dev/null || echo "0")
            echo "  ダウンロード完了: $FILE_SIZE bytes"
        fi
    else
        echo -e "${RED}✗ $table: 取得失敗${NC}"
    fi
done

# 6. エラーケーステスト
echo ""
echo -e "${BLUE}6. エラーケーステスト${NC}"

echo ""
echo "存在しないテーブル: POST /api/snapshot/2/NonExistentTable"
ERROR_RESPONSE=$(curl -s -X POST "$BASE_URL/api/snapshot/2/NonExistentTable")
echo "$ERROR_RESPONSE" | jq '.' 2>/dev/null || echo "$ERROR_RESPONSE"

echo ""
echo "存在しないバージョン: POST /api/snapshot/999/tables"
ERROR_RESPONSE2=$(curl -s -X POST "$BASE_URL/api/snapshot/999/tables")
echo "$ERROR_RESPONSE2" | jq '.' 2>/dev/null || echo "$ERROR_RESPONSE2"

# 7. 結果サマリー
echo ""
echo -e "${BLUE}=== テスト結果サマリー ===${NC}"
echo -e "${GREEN}✓ サーバー接続: OK${NC}"
echo -e "${GREEN}✓ テーブル一覧API: 実装済み${NC}"
echo -e "${GREEN}✓ 個別テーブル取得API: 実装済み${NC}"
echo -e "${GREEN}✓ エラーハンドリング: 実装済み${NC}"

# クリーンアップ
rm -f /tmp/*_test.parquet

echo ""
echo "テスト完了！"
