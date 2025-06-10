# DuckLakeクリーンアップスクリプト
# 使用方法: bash duck.cleanup.sh [-y]
# 説明: DuckLakeのデータディレクトリとカタログファイルをクリーンアップ

set -e

# オプション解析
SKIP_CONFIRM=false
if [ "$1" = "-y" ]; then
    SKIP_CONFIRM=true
fi

# 設定
DATA_PATH="${DATA_FILES_PATH:-./data_files}"
CATALOG_PATH="${DUCKLAKE_CATALOG_PATH:-./ducklake.ducklake}"
if [[ "$DATA_PATH" != /* ]]; then
    DATA_PATH="$(pwd)/$DATA_PATH"
fi
if [[ "$CATALOG_PATH" != /* ]]; then
    CATALOG_PATH="$(pwd)/$CATALOG_PATH"
fi

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "DuckLakeクリーンアップを開始します..."
echo "データパス: $DATA_PATH"
echo "カタログパス: $CATALOG_PATH"
echo ""

# 確認
if [ "$SKIP_CONFIRM" = false ]; then
    echo -e "${YELLOW}警告: これによりすべてのDuckLakeデータが削除されます！${NC}"
    echo -n "続行しますか？ (y/N): "
    read -r response

    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo ""
        echo "クリーンアップをキャンセルしました"
        exit 0
    fi
fi
echo ""
echo "クリーンアップ中..."

# カタログをデタッチ
echo "カタログをデタッチ中..."
curl -s -X POST http://localhost:8000/query \
    -H 'Content-Type: application/json' \
    -d '{"query": "DETACH lake"}' > /dev/null 2>&1 || true

# データディレクトリを削除
if [ -d "$DATA_PATH" ]; then
    rm -rf "$DATA_PATH"
    echo -e "${GREEN}データディレクトリを削除しました${NC}"
else
    echo "データディレクトリが見つかりません"
fi

# カタログファイルを削除
if [ -f "$CATALOG_PATH" ]; then
    rm -f "$CATALOG_PATH"
    echo -e "${GREEN}カタログファイルを削除しました${NC}"
else
    echo "カタログファイルが見つかりません"
fi

echo ""
echo -e "${GREEN}クリーンアップが完了しました${NC}"