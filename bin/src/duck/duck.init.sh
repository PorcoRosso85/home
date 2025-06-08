# Duck DB初期化スクリプト（修正版）
# 使用方法: ./duck.init.sh
# 説明: DDLとテストデータを投入し、エラー時はロールバック

set -e  # エラー時に停止

# 設定
BASE_URL="http://localhost:8000/query"
CONTENT_TYPE="Content-Type: application/json"

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# エラーハンドリング
error_exit() {
    echo -e "${RED}エラー: $1${NC}" >&2
    echo -e "${YELLOW}ロールバック中...${NC}"
    
    # ロールバック実行
    curl -s -X POST "$BASE_URL" \
        -H "$CONTENT_TYPE" \
        -d '{"query": "ROLLBACK"}' > /dev/null 2>&1
    
    echo -e "${RED}初期化に失敗しました${NC}"
    exit 1
}

# クエリ実行関数（jqを使用してJSONを生成）
execute_query() {
    local query="$1"
    local description="$2"
    
    echo -n "実行中: $description... "
    
    # jqを使って適切にエスケープされたJSONを生成
    json_data=$(jq -n --arg q "$query" '{query: $q}')
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
        -H "$CONTENT_TYPE" \
        -d "$json_data")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" != "200" ]; then
        echo -e "${RED}失敗${NC}"
        echo "HTTPステータス: $http_code"
        echo "レスポンス: $body"
        error_exit "$description に失敗しました"
    fi
    
    # エラーチェック
    if echo "$body" | grep -q '"success":false'; then
        echo -e "${RED}失敗${NC}"
        echo "レスポンス: $body"
        error_exit "$description でエラーが発生しました"
    fi
    
    echo -e "${GREEN}成功${NC}"
}

# jqの存在確認
if ! command -v jq &> /dev/null; then
    echo -e "${RED}エラー: jqがインストールされていません${NC}"
    echo "以下のコマンドでインストールしてください："
    echo "  nix-shell -p jq"
    exit 1
fi

# メイン処理
echo "Duck DB初期化を開始します..."
echo ""

# トランザクション開始
echo "トランザクションを開始..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"

# 3. DDL実行（VersionStateテーブル作成）
execute_query "CREATE TABLE IF NOT EXISTS VersionState (id VARCHAR PRIMARY KEY, timestamp VARCHAR, description VARCHAR, change_reason VARCHAR, progress_percentage FLOAT)" "VersionStateテーブル作成"

# 4. LocationURIテーブル作成
execute_query "CREATE TABLE IF NOT EXISTS LocationURI (id VARCHAR PRIMARY KEY)" "LocationURIテーブル作成"

# 5. リレーションテーブル作成
execute_query "CREATE TABLE IF NOT EXISTS TRACKS_STATE_OF_LOCATED_ENTITY (src VARCHAR, dst VARCHAR, PRIMARY KEY (src, dst))" "リレーションテーブル作成"

# 6. テストデータ挿入（VersionState）
execute_query "INSERT INTO VersionState (id, timestamp, description, change_reason, progress_percentage) VALUES ('v0.1.0', '2024-01-01T00:00:00Z', 'kuzu-browse project v0.1.0 - Initial version management system', '初期開発: グラフデータベースブラウザアプリケーション', 0.0)" "VersionStateデータ挿入"

# 7. LocationURI挿入
execute_query "INSERT INTO LocationURI (id) VALUES ('file:///home/nixos/bin/src/kuzu/browse'), ('file:///home/nixos/bin/src/kuzu/browse/main.ts'), ('file:///home/nixos/bin/src/kuzu/browse/deno.json')" "LocationURIデータ挿入"

# 8. リレーション作成
execute_query "INSERT INTO TRACKS_STATE_OF_LOCATED_ENTITY (src, dst) VALUES ('v0.1.0', 'file:///home/nixos/bin/src/kuzu/browse'), ('v0.1.0', 'file:///home/nixos/bin/src/kuzu/browse/main.ts'), ('v0.1.0', 'file:///home/nixos/bin/src/kuzu/browse/deno.json')" "リレーションデータ挿入"

# トランザクションコミット
echo ""
echo "すべての操作が成功しました。コミット中..."
execute_query "COMMIT" "トランザクションコミット"

echo ""
echo -e "${GREEN}初期化が完了しました！${NC}"
echo ""

# 9. データ確認
echo "データ確認中..."
echo ""

# JOINでデータ確認
echo "=== バージョンとLocationURIの関連 ==="
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT v.id as version_id, v.description, l.id as location_id FROM VersionState v JOIN TRACKS_STATE_OF_LOCATED_ENTITY t ON v.id = t.src JOIN LocationURI l ON t.dst = l.id LIMIT 5" '{query: $q}')" | jq '.'

echo ""

# 10. 全データ統計（BigInt対策のためCAST追加）
echo "=== データ統計 ==="
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT 'versions' as type, CAST(COUNT(*) AS INTEGER) as count FROM VersionState UNION ALL SELECT 'locations' as type, CAST(COUNT(*) AS INTEGER) as count FROM LocationURI UNION ALL SELECT 'relations' as type, CAST(COUNT(*) AS INTEGER) as count FROM TRACKS_STATE_OF_LOCATED_ENTITY" '{query: $q}')" | jq '.'

echo ""
echo "初期化スクリプトが正常に完了しました。"