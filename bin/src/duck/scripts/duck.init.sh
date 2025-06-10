#!/bin/bash
# DuckLake公式準拠初期化スクリプト
# 使用方法: bash duck.init.sh [-y] [--mode MODE] [--catalog-type TYPE] [--catalog-path PATH]
# 
# オプション:
#   -y                    確認をスキップ
#   --mode MODE          初期化モード (single|multi) デフォルト: single
#   --catalog-type TYPE   カタログタイプ (duckdb|postgres|mysql|sqlite) デフォルト: duckdb
#   --catalog-path PATH   カタログパス デフォルト: ./ducklake.ducklake
#   --data-path PATH      データファイルパス デフォルト: ./data_files

set -e

# 色付き出力
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト設定
SKIP_CONFIRM=false
MODE="single"
CATALOG_TYPE="duckdb"
CATALOG_PATH="./ducklake.ducklake"
DATA_PATH="./data_files"
BASE_URL="http://localhost:8000/query"
CONTENT_TYPE="Content-Type: application/json"

# 引数解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -y)
            SKIP_CONFIRM=true
            shift
            ;;
        --mode)
            MODE="$2"
            shift 2
            ;;
        --catalog-type)
            CATALOG_TYPE="$2"
            shift 2
            ;;
        --catalog-path)
            CATALOG_PATH="$2"
            shift 2
            ;;
        --data-path)
            DATA_PATH="$2"
            shift 2
            ;;
        *)
            echo "不明なオプション: $1"
            echo "使用方法: bash duck.init.sh [-y] [--mode MODE] [--catalog-type TYPE] [--catalog-path PATH] [--data-path PATH]"
            exit 1
            ;;
    esac
done

# エラーハンドリング
error_exit() {
    echo -e "${RED}エラー: $1${NC}" >&2
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
    if echo "$body" | grep -q '"code"'; then
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

# モード検証
if [ "$MODE" != "single" ] && [ "$MODE" != "multi" ]; then
    error_exit "サポートされていないモード: $MODE (single|multi のみ)"
fi

# メイン処理
echo -e "${BLUE}=== DuckLake公式準拠初期化 ===${NC}"
echo ""
echo "設定:"
echo "  モード: $MODE"
echo "  カタログタイプ: $CATALOG_TYPE"
echo "  カタログパス: $CATALOG_PATH"
echo "  データパス: $DATA_PATH"
echo ""

if [ "$SKIP_CONFIRM" = false ]; then
    echo -e "${YELLOW}警告: 既存のDuckLakeデータが存在する場合は削除されます！${NC}"
    echo -n "続行しますか？ (y/N): "
    read -r response

    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "初期化をキャンセルしました"
        exit 0
    fi
fi

# Duck APIが動作しているか確認
echo ""
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

# データディレクトリ作成
mkdir -p "$DATA_PATH"

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

# カタログタイプに応じた接続文字列を構築
case $CATALOG_TYPE in
    duckdb)
        ATTACH_QUERY="ATTACH 'ducklake:${CATALOG_PATH}' AS lake (DATA_PATH '${DATA_PATH}')"
        ;;
    postgres)
        # PostgreSQL接続の場合は環境変数から接続情報を取得
        PG_CONNECTION=${DUCKLAKE_CATALOG_CONNECTION:-"postgres:dbname=ducklake_catalog host=localhost"}
        ATTACH_QUERY="ATTACH 'ducklake:${PG_CONNECTION}' AS lake (DATA_PATH '${DATA_PATH}')"
        execute_query "INSTALL postgres" "PostgreSQL拡張インストール"
        ;;
    mysql)
        # MySQL接続の場合は環境変数から接続情報を取得
        MYSQL_CONNECTION=${DUCKLAKE_CATALOG_CONNECTION:-"mysql:db=ducklake_catalog host=localhost"}
        ATTACH_QUERY="ATTACH 'ducklake:${MYSQL_CONNECTION}' AS lake (DATA_PATH '${DATA_PATH}')"
        execute_query "INSTALL mysql" "MySQL拡張インストール"
        ;;
    sqlite)
        ATTACH_QUERY="ATTACH 'ducklake:sqlite:${CATALOG_PATH}' AS lake (DATA_PATH '${DATA_PATH}')"
        execute_query "INSTALL sqlite" "SQLite拡張インストール"
        ;;
    *)
        error_exit "サポートされていないカタログタイプ: $CATALOG_TYPE"
        ;;
esac

# DuckLakeカタログのアタッチ
echo ""
echo "DuckLakeカタログをアタッチ中..."
execute_query "$ATTACH_QUERY" "DuckLakeカタログアタッチ"

# 初期データのセットアップ
echo ""
echo -e "${BLUE}=== 初期データ作成 ===${NC}"

if [ "$MODE" = "single" ]; then
    # シングルモード: LocationURIのみ
    echo "モード: シングル（LocationURIテーブルのみ）"
    
    # トランザクション開始
    execute_query "BEGIN TRANSACTION" "トランザクション開始"
    
    # LocationURIテーブル作成
    execute_query "CREATE TABLE IF NOT EXISTS lake.LocationURI (id VARCHAR)" "LocationURIテーブル作成"
    execute_query "INSERT INTO lake.LocationURI (id) VALUES 
        ('file:///home/nixos/bin/src/kuzu/browse'), 
        ('file:///home/nixos/bin/src/kuzu/browse/main.ts'), 
        ('file:///home/nixos/bin/src/duck/server.ts')" \
        "LocationURI初期データ挿入（3件）"
    
    # トランザクションコミット（スナップショット作成）
    execute_query "COMMIT" "トランザクションコミット"
    
else
    # マルチモード: 複数テーブルと複数スナップショット
    echo "モード: マルチ（3テーブル、2スナップショット）"
    
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
fi

# 確認
echo ""
echo -e "${GREEN}=== 初期化完了！===${NC}"
echo ""

# スナップショット情報を表示
echo "スナップショット情報:"
snapshot_result=$(curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT * FROM ducklake_snapshots('"'"'lake'"'"')"}')

if echo "$snapshot_result" | jq -e '.data | length > 0' > /dev/null 2>&1; then
    echo "$snapshot_result" | jq -r '.data[] | "  Version \(.snapshot_id): \(.snapshot_time)"'
else
    echo "  スナップショットが作成されていません"
fi

# テーブル情報
echo ""
echo "テーブル情報:"
table_result=$(curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "SELECT * FROM ducklake_table_info('"'"'lake'"'"')"}')

if echo "$table_result" | jq -e '.data | length > 0' > /dev/null 2>&1; then
    echo "$table_result" | jq -r '.data[] | "  \(.table_name): \(.row_count) rows"'
else
    echo "  テーブル情報が取得できません"
fi

# マルチモードの場合は詳細情報を表示
if [ "$MODE" = "multi" ]; then
    echo ""
    echo "各テーブルのデータ数:"
    for table in LocationURI RequirementEntity CodeEntity; do
        count_result=$(curl -s -X POST "$BASE_URL" \
            -H "$CONTENT_TYPE" \
            -d "$(jq -n --arg q "SELECT COUNT(*) as count FROM lake.$table" '{query: $q}')")
        
        count=$(echo "$count_result" | jq -r '.data[0].count // 0' 2>/dev/null || echo "0")
        echo "  $table: $count 件"
    done
fi

echo ""
echo "使用例:"
echo "  - クエリ実行: curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{\"query\": \"SELECT * FROM lake.LocationURI\"}'"
echo "  - スナップショット確認: curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{\"query\": \"SELECT * FROM ducklake_snapshots('\\''lake'\\'')\"}'"
echo "  - タイムトラベル: curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{\"query\": \"SELECT * FROM lake.LocationURI AT (VERSION => 1)\"}'"

if [ "$MODE" = "multi" ]; then
    echo "  - 変更履歴確認: curl -X POST http://localhost:8000/query -H 'Content-Type: application/json' -d '{\"query\": \"SELECT * FROM lake.ducklake_table_changes('\\''LocationURI'\\'', 1, 2)\"}'"
fi