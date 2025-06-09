# Duck DB LocationURI追加スクリプト（デバッグ版）
# 使用方法: bash duck.add_locationuri.sh
# 説明: DuckLakeのLocationURIテーブルに追加データを挿入

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
    
    echo -e "${RED}データ追加に失敗しました${NC}"
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
echo "LocationURIデータ追加を開始します..."
echo ""

# まずDuck APIが動作しているか確認
echo "Duck APIの動作確認..."
test_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT 1 as test"}')

test_http_code=$(echo "$test_response" | tail -n1)
test_body=$(echo "$test_response" | sed '$d')

echo "HTTPステータス: $test_http_code"
echo "レスポンス内容:"
echo "$test_body"
echo ""

if [ "$test_http_code" != "200" ]; then
    echo -e "${RED}Duck APIが正しく応答していません${NC}"
    echo "Duck APIサーバーが起動していることを確認してください"
    exit 1
fi

# 現在のデータ数を確認
echo "現在のデータ数を確認中..."
count_response=$(curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT COUNT(*) as count FROM lake.LocationURI"}')

echo "デバッグ: COUNT応答:"
echo "$count_response"
echo ""

# レスポンスがエラーでないか確認
if echo "$count_response" | grep -q '"code"'; then
    echo -e "${RED}エラー: LocationURIテーブルが存在しないか、DuckLakeが初期化されていません${NC}"
    echo "まず duck.init.sh を実行してください"
    exit 1
fi

# jqでパース（エラーが発生した場合は0を使用）
current_count=$(echo "$count_response" | jq -r '.data[0].count // 0' 2>/dev/null || echo "0")

echo "現在のLocationURI数: $current_count 件"
echo ""

# スナップショット4: より多くのプロジェクトファイルを追加（+12件 = 合計21件）
echo "スナップショット4を作成中..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"

# アプリケーション層のファイル
execute_query "INSERT INTO lake.LocationURI (id) VALUES \
    ('file:///home/nixos/bin/src/kuzu/browse/application/hooks/useLocationUris.ts'), \
    ('file:///home/nixos/bin/src/kuzu/browse/application/hooks/locationUrisLogic.ts'), \
    ('file:///home/nixos/bin/src/kuzu/browse/application/hooks/useVersionStates.ts'), \
    ('file:///home/nixos/bin/src/kuzu/browse/application/usecase/loadLocationUrisFromDuck.ts')" \
    "アプリケーション層ファイル追加"

# インフラストラクチャ層のファイル
execute_query "INSERT INTO lake.LocationURI (id) VALUES \
    ('file:///home/nixos/bin/src/kuzu/browse/infrastructure/config/variables.ts'), \
    ('file:///home/nixos/bin/src/kuzu/browse/infrastructure/repository/duckApiClient.ts'), \
    ('file:///home/nixos/bin/src/kuzu/browse/infrastructure/repository/databaseConnection.ts'), \
    ('file:///home/nixos/bin/src/kuzu/browse/infrastructure/repository/queryExecutor.ts')" \
    "インフラストラクチャ層ファイル追加"

# インターフェース層のファイル
execute_query "INSERT INTO lake.LocationURI (id) VALUES \
    ('file:///home/nixos/bin/src/kuzu/browse/interface/App.tsx'), \
    ('file:///home/nixos/bin/src/kuzu/browse/interface/Page.tsx'), \
    ('file:///home/nixos/bin/src/kuzu/browse/interface/presentation/VersionStates.tsx'), \
    ('file:///home/nixos/bin/src/kuzu/browse/interface/presentation/TreeView.tsx')" \
    "インターフェース層ファイル追加"

execute_query "COMMIT" "トランザクションコミット（スナップショット4作成）"

# スナップショット5: Duckサーバー側のファイルも追加（+8件 = 合計29件）
echo ""
echo "スナップショット5を作成中..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"

execute_query "INSERT INTO lake.LocationURI (id) VALUES \
    ('file:///home/nixos/bin/src/duck/server.ts'), \
    ('file:///home/nixos/bin/src/duck/duck.init.sh'), \
    ('file:///home/nixos/bin/src/duck/infrastructure/variables.ts'), \
    ('file:///home/nixos/bin/src/duck/infrastructure/repository/duckdbRepository.ts'), \
    ('file:///home/nixos/bin/src/duck/application/usecase/executeQuery.ts'), \
    ('file:///home/nixos/bin/src/duck/application/usecase/manageDuckLake.ts'), \
    ('file:///home/nixos/bin/src/duck/domain/types.ts'), \
    ('file:///home/nixos/bin/src/CONVENTION.yaml')" \
    "Duckサーバー側ファイル追加"

execute_query "COMMIT" "トランザクションコミット（スナップショット5作成）"

# スナップショット6: テストとクエリファイル（+6件 = 合計35件）
echo ""
echo "スナップショット6を作成中..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"

execute_query "INSERT INTO lake.LocationURI (id) VALUES \
    ('file:///home/nixos/bin/src/kuzu/query/ddl/schema.cypher'), \
    ('file:///home/nixos/bin/src/kuzu/query/dql/list_uris_cumulative.cypher'), \
    ('file:///home/nixos/bin/src/kuzu/browse/public/dql/list_uris_cumulative.cypher'), \
    ('file:///home/nixos/bin/src/kuzu/browse/public/ddl/schema.cypher'), \
    ('file:///home/nixos/bin/src/kuzu/browse/public/export_data/copy_parquet.cypher'), \
    ('file:///home/nixos/bin/src/kuzu/browse/public/dql/import_parquet.cypher')" \
    "クエリファイル追加"

execute_query "COMMIT" "トランザクションコミット（スナップショット6作成）"

echo ""
echo -e "${GREEN}データ追加が完了しました！${NC}"
echo ""

# データ確認
echo "=== 追加後のデータ確認 ==="
echo ""

# 現在のLocationURI数
new_count_response=$(curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT COUNT(*) as count FROM lake.LocationURI"}')

new_count=$(echo "$new_count_response" | jq -r '.data[0].count // 0' 2>/dev/null || echo "0")

echo "追加前: $current_count 件"
echo "追加後: $new_count 件"
echo "追加数: $((new_count - current_count)) 件"
echo ""

# 最新のスナップショット確認
echo "=== 利用可能なスナップショット ==="
for v in 1 2 3 4 5 6 7 8; do
  result=$(curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT COUNT(*) as count FROM lake.LocationURI AT (VERSION => $v)" '{query: $q}')")
  
  count=$(echo "$result" | jq -r '.data[0].count // 0' 2>/dev/null || echo "0")
  if [ "$count" -gt 0 ]; then
    echo "Version $v: $count rows"
  fi
done

echo ""
echo "=== 最新のLocationURI一覧（最後の10件）==="
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT * FROM lake.LocationURI ORDER BY id DESC LIMIT 10" '{query: $q}')" | jq '.' 2>/dev/null || echo "パースエラー"

echo ""
echo "データ追加スクリプトが正常に完了しました。"
echo ""
echo "使用例:"
echo "  - バージョン一覧: curl -X POST http://localhost:8000/api/versions"
echo "  - スナップショット取得: curl -X POST http://localhost:8000/api/snapshot/6 --output LocationURI_v6.parquet"
