# DuckDB統合初期化スクリプト - 複数テーブル対応版
# 使用方法: bash duck.init_multi_tables.sh [-y]
# 説明: LocationURI、RequirementEntity、CodeEntityの3テーブルを一括初期化
# 注意: 実行時に既存データは削除されます
# オプション: -y 確認をスキップ

set -e  # エラー時に停止

# コマンドライン引数の処理
SKIP_CONFIRM=false
if [ "$1" = "-y" ]; then
    SKIP_CONFIRM=true
fi

# 設定
BASE_URL="http://localhost:8000/query"
CONTENT_TYPE="Content-Type: application/json"

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
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

# クエリ実行関数
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
echo -e "${BLUE}=== DuckDB複数テーブル統合初期化 ===${NC}"
echo "対象テーブル: LocationURI, RequirementEntity, CodeEntity"
echo ""

if [ "$SKIP_CONFIRM" = false ]; then
    echo -e "${YELLOW}警告: 既存のDuckLakeデータはすべて削除されます！${NC}"
    echo -n "続行しますか？ (y/N): "
    read -r response

    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "初期化をキャンセルしました"
        exit 0
    fi
fi

# Duck APIが動作しているか確認
echo "Duck APIの動作確認..."
test_response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT 1 as test"}')

test_http_code=$(echo "$test_response" | tail -n1)

if [ "$test_http_code" != "200" ]; then
    echo -e "${RED}Duck APIが正しく応答していません${NC}"
    echo "Duck APIサーバーが起動していることを確認してください"
    exit 1
fi

# 既存のカタログをデタッチ
echo ""
echo "既存のカタログをクリーンアップ中..."
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "DETACH lake"}' > /dev/null 2>&1 || true

# DuckLake拡張のインストール
echo ""
echo "DuckLake拡張をセットアップ中..."
execute_query "INSTALL ducklake" "DuckLake拡張インストール"
execute_query "LOAD ducklake" "DuckLake拡張ロード"

# DuckLakeカタログのアタッチ（インメモリ）
echo ""
echo "DuckLakeカタログをアタッチ中..."
execute_query "ATTACH 'ducklake::memory:' AS lake" "DuckLakeカタログアタッチ（インメモリ）"

# ========== スナップショット1: 初期データ ==========
echo ""
echo -e "${BLUE}=== スナップショット1: 初期データ作成 ===${NC}"

# トランザクション開始
execute_query "BEGIN TRANSACTION" "トランザクション開始"

# 1. LocationURIテーブル作成と初期データ
execute_query "CREATE TABLE IF NOT EXISTS lake.LocationURI (id VARCHAR)" "LocationURIテーブル作成"
execute_query "INSERT INTO lake.LocationURI (id) VALUES 
    ('file:///home/nixos/bin/src/kuzu/browse'), 
    ('file:///home/nixos/bin/src/kuzu/browse/main.ts'), 
    ('file:///home/nixos/bin/src/duck/server.ts')" \
    "LocationURI初期データ挿入（3件）"

# 2. RequirementEntityテーブル作成と初期データ
execute_query "CREATE TABLE IF NOT EXISTS lake.RequirementEntity (
    id VARCHAR,
    title VARCHAR,
    description VARCHAR,
    priority VARCHAR,
    requirement_type VARCHAR
)" "RequirementEntityテーブル作成"

execute_query "INSERT INTO lake.RequirementEntity VALUES
    ('REQ-001', 'ユーザー認証機能', 'ログイン機能の実装', 'HIGH', 'FUNCTIONAL'),
    ('REQ-002', 'データ永続化', 'DuckDBへのデータ保存', 'HIGH', 'FUNCTIONAL')" \
    "RequirementEntity初期データ挿入（2件）"

# 3. CodeEntityテーブル作成と初期データ
execute_query "CREATE TABLE IF NOT EXISTS lake.CodeEntity (
    persistent_id VARCHAR,
    name VARCHAR,
    type VARCHAR,
    signature VARCHAR,
    complexity INT,
    start_position INT,
    end_position INT
)" "CodeEntityテーブル作成"

execute_query "INSERT INTO lake.CodeEntity VALUES
    ('FUNC-001', 'createServer', 'function', 'async function createServer(dataPath: string)', 5, 100, 200),
    ('FUNC-002', 'executeQuery', 'function', 'function executeQuery(query: string)', 3, 50, 80)" \
    "CodeEntity初期データ挿入（2件）"

# トランザクションコミット
execute_query "COMMIT" "トランザクションコミット（スナップショット1完了）"

# ========== スナップショット2: 追加データ ==========
echo ""
echo -e "${BLUE}=== スナップショット2: 追加データ作成 ===${NC}"

# トランザクション開始
execute_query "BEGIN TRANSACTION" "トランザクション開始"

# LocationURI追加データ
execute_query "INSERT INTO lake.LocationURI (id) VALUES 
    ('file:///home/nixos/bin/src/kuzu/browse/application'), 
    ('file:///home/nixos/bin/src/kuzu/browse/domain')" \
    "LocationURI追加データ挿入（+2件）"

# RequirementEntity追加データ
execute_query "INSERT INTO lake.RequirementEntity VALUES
    ('REQ-003', 'RESTful API設計', 'HTTP標準準拠', 'MEDIUM', 'NON_FUNCTIONAL')" \
    "RequirementEntity追加データ挿入（+1件）"

# CodeEntity追加データ
execute_query "INSERT INTO lake.CodeEntity VALUES
    ('CLASS-001', 'DuckDBRepository', 'class', 'export class DuckDBRepository', 8, 300, 500)" \
    "CodeEntity追加データ挿入（+1件）"

# トランザクションコミット
execute_query "COMMIT" "トランザクションコミット（スナップショット2完了）"

# ========== データ確認 ==========
echo ""
echo -e "${GREEN}=== 初期化完了！データ確認 ===${NC}"
echo ""

# 各テーブルの現在のデータ数
echo "=== 現在のデータ数（スナップショット2） ==="
for table in LocationURI RequirementEntity CodeEntity; do
    count_result=$(curl -s -X POST "$BASE_URL" \
        -H "$CONTENT_TYPE" \
        -d "$(jq -n --arg q "SELECT COUNT(*) as count FROM lake.$table" '{query: $q}')")
    
    count=$(echo "$count_result" | jq -r '.data[0].count // 0' 2>/dev/null || echo "0")
    echo "$table: $count 件"
done

echo ""
echo "=== 各テーブルのスナップショット履歴 ==="
for table in LocationURI RequirementEntity CodeEntity; do
    echo ""
    echo "[$table]"
    for v in 1 2; do
        result=$(curl -s -X POST "$BASE_URL" \
            -H "$CONTENT_TYPE" \
            -d "$(jq -n --arg q "SELECT COUNT(*) as count FROM lake.$table AT (VERSION => $v)" '{query: $q}')")
        
        count=$(echo "$result" | jq -r '.data[0].count // 0' 2>/dev/null || echo "0")
        if [ "$count" -gt 0 ]; then
            echo "  Version $v: $count rows"
        fi
    done
done

echo ""
echo -e "${GREEN}統合初期化スクリプトが正常に完了しました。${NC}"
echo ""
echo "作成されたスナップショット:"
echo "  - スナップショット1: LocationURI(3), RequirementEntity(2), CodeEntity(2)"
echo "  - スナップショット2: LocationURI(5), RequirementEntity(3), CodeEntity(3)"
echo ""
echo "使用例:"
echo "  - テーブル一覧: curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{\"query\": \"SHOW ALL TABLES\"}'"
echo "  - スナップショット取得: curl -X POST http://localhost:8000/api/snapshot/2 --output snapshot_v2.parquet"
