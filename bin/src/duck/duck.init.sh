# Duck DB初期化スクリプト（DuckLake版）
# 使用方法: bash duck.init.sh [-y]
# 説明: DuckLakeを使用してLocationURIテーブルを管理
# 注意: 実行時に既存データは削除されます
# オプション: -y 確認をスキップ
# 
# DuckLakeの制限事項:
# - PRIMARY KEY/UNIQUE制約はサポートされていない
# - DELETE操作で内部Parquetファイルエラーが発生する場合がある

set -e  # エラー時に停止

# コマンドライン引数の処理
SKIP_CONFIRM=false
if [ "$1" = "-y" ]; then
    SKIP_CONFIRM=true
fi

# 設定
BASE_URL="http://localhost:8000/query"
CONTENT_TYPE="Content-Type: application/json"
# 絶対パスに変換
if [[ "$DATA_FILES_PATH" == /* ]]; then
    # 既に絶対パス
    DATA_PATH="$DATA_FILES_PATH"
else
    # 相対パスの場合は絶対パスに変換
    DATA_PATH="$(pwd)/${DATA_FILES_PATH:-data_files}"
fi

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
echo "DuckLake初期化を開始します..."
echo "データパス: $DATA_PATH"

if [ "$SKIP_CONFIRM" = false ]; then
    echo ""
    echo -e "${YELLOW}警告: 既存のDuckLakeデータはすべて削除されます！${NC}"
    echo -n "続行しますか？ (y/N): "
    read -r response

    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "初期化をキャンセルしました"
        exit 0
    fi
fi

# 既存のカタログをデタッチ
echo ""
echo "既存のカタログをクリーンアップ中..."
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d '{"query": "DETACH lake"}' > /dev/null 2>&1 || true

# データディレクトリをクリーンアップ
echo "データディレクトリをクリーンアップ中..."
if [ -d "$DATA_PATH" ]; then
    rm -rf "$DATA_PATH"
    echo -e "${YELLOW}既存のデータディレクトリを削除しました${NC}"
fi

# データディレクトリの作成
echo "データディレクトリを作成中..."
mkdir -p "$DATA_PATH"
echo -e "${GREEN}データディレクトリ作成完了${NC}"

echo ""

# 1. DuckLake拡張のインストール
echo "DuckLake拡張をインストール中..."
execute_query "INSTALL ducklake" "DuckLake拡張インストール"
execute_query "LOAD ducklake" "DuckLake拡張ロード"

# 2. DuckLakeカタログをアタッチ後は何も変更しない箇所を確認

# 3. DuckLakeカタログのアタッチ（修正版）
echo ""
echo "DuckLakeカタログをアタッチ中..."
echo "使用するパス: $DATA_PATH"
# インメモリモードでのテスト（ファイル永続化の問題を回避）
# execute_query "ATTACH 'ducklake::' AS lake (DATA_PATH '$DATA_PATH')" "DuckLakeカタログアタッチ"
execute_query "ATTACH 'ducklake::memory:' AS lake" "DuckLakeカタログアタッチ（インメモリ）"

# 4. トランザクション開始
echo ""
echo "トランザクションを開始..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"

# 5. LocationURIテーブル作成（DuckLake内）
execute_query "CREATE TABLE IF NOT EXISTS lake.LocationURI (id VARCHAR)" "LocationURIテーブル作成"

# 6. 初期データ挿入（スナップショット1が作成される - 3件）
echo ""
echo "初期データを挿入中（スナップショット1）..."
execute_query "INSERT INTO lake.LocationURI (id) VALUES ('file:///home/nixos/bin/src/kuzu/browse'), ('file:///home/nixos/bin/src/kuzu/browse/main.ts'), ('file:///home/nixos/bin/src/kuzu/browse/deno.json')" "初期LocationURIデータ挿入"

# トランザクションコミット
execute_query "COMMIT" "トランザクションコミット（スナップショット1作成）"

# 7. 追加データ挿入（スナップショット2 - 合計6件）
echo ""
echo "追加データを挿入中（スナップショット2）..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"
execute_query "INSERT INTO lake.LocationURI (id) VALUES ('file:///home/nixos/bin/src/kuzu/browse/application'), ('file:///home/nixos/bin/src/kuzu/browse/domain'), ('file:///home/nixos/bin/src/kuzu/browse/infrastructure')" "追加LocationURIデータ挿入"
execute_query "COMMIT" "トランザクションコミット（スナップショット2作成）"

# 8. 更新操作（スナップショット3 - 合計9件）
echo ""
echo "追加データを挿入中（スナップショット3）..."
execute_query "BEGIN TRANSACTION" "トランザクション開始"
# DELETE操作は避けて、新しいデータの追加のみ行う
execute_query "INSERT INTO lake.LocationURI (id) VALUES ('file:///home/nixos/bin/src/kuzu/browse/index.tsx'), ('file:///home/nixos/bin/src/kuzu/browse/interface'), ('file:///home/nixos/bin/src/kuzu/browse/CONVENTION.md')" "新しいファイル追加"
execute_query "COMMIT" "トランザクションコミット（スナップショット3作成）"

echo ""
echo -e "${GREEN}初期化が完了しました！${NC}"
echo ""

# 9. データ確認
echo "データ確認中..."
echo ""

# 現在のLocationURI一覧
echo "=== 現在のLocationURI一覧 (バージョン3: 9件) ==="
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT * FROM lake.LocationURI ORDER BY id" '{query: $q}')" | jq '.'

echo ""

# スナップショット一覧
echo "=== 利用可能なスナップショット ==="
# 簡易的に1-5のバージョンを確認
for v in 1 2 3 4 5; do
  result=$(curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT COUNT(*) as count FROM lake.LocationURI AT (VERSION => $v)" '{query: $q}')")
  
  count=$(echo "$result" | jq -r '.data[0].count // 0')
  if [ "$count" -gt 0 ]; then
    echo "Version $v: $count rows"
  fi
done

echo ""

# バージョン2のデータ確認
echo "=== バージョン2のLocationURI (6件) ==="
curl -s -X POST "$BASE_URL" \
    -H "$CONTENT_TYPE" \
    -d "$(jq -n --arg q "SELECT * FROM lake.LocationURI AT (VERSION => 2) ORDER BY id" '{query: $q}')" | jq '.'

echo ""
echo "初期化スクリプトが正常に完了しました。"
echo ""
echo "作成されたスナップショット:"
echo "  - バージョン1: 3件（初期データ）"
echo "  - バージョン2: 6件（+3件追加）"
echo "  - バージョン3: 9件（+3件追加）"
echo ""
echo "使用例:"
echo "  - バージョン一覧: curl -X POST http://localhost:8000/api/versions"
echo "  - スナップショット取得: curl -X POST http://localhost:8000/api/snapshot/2 --output LocationURI_v2.parquet"