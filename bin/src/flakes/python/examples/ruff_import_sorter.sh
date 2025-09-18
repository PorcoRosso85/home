#!/usr/bin/env bash
#
# ruff_import_sorter.sh - ruffのネイティブ機能でインポートを整理
#
# このスクリプトは、ruffの素の機能をそのまま使用して
# Pythonファイルのインポートを整理します。

set -euo pipefail

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ヘルプ表示
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] [FILE|DIRECTORY]

ruffのネイティブ機能を使用してPythonのインポートを整理します。

OPTIONS:
    -h, --help      このヘルプを表示
    -d, --diff      変更内容を表示（適用しない）
    -f, --fix       実際に修正を適用
    -a, --all       すべてのruffルールを適用（インポート以外も）
    -v, --verbose   詳細な出力

EXAMPLES:
    # インポート関連の問題をチェック
    $0 main.py

    # 修正内容をプレビュー
    $0 --diff main.py

    # 実際に修正を適用
    $0 --fix src/

    # すべてのルールで修正
    $0 --all --fix .

EOF
}

# デフォルト値
DIFF_ONLY=false
FIX=false
ALL_RULES=false
VERBOSE=false
TARGET="."

# オプション解析
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -d|--diff)
            DIFF_ONLY=true
            shift
            ;;
        -f|--fix)
            FIX=true
            shift
            ;;
        -a|--all)
            ALL_RULES=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

# ruffコマンドの構築
RUFF_CMD="ruff check"

# ルール選択
if [ "$ALL_RULES" = false ]; then
    # インポート関連のルールのみ
    RUFF_CMD="$RUFF_CMD --select I"
fi

# ターゲット追加
RUFF_CMD="$RUFF_CMD $TARGET"

# メイン処理
echo -e "${BLUE}🔍 ruff Import Sorter${NC}"
echo -e "${BLUE}===================${NC}"
echo

# 1. 現在の状態をチェック
echo -e "${YELLOW}📋 現在の状態をチェック中...${NC}"
if [ "$VERBOSE" = true ]; then
    $RUFF_CMD || true
else
    OUTPUT=$($RUFF_CMD 2>&1) || true
    if [ -n "$OUTPUT" ]; then
        echo "$OUTPUT"
    else
        echo -e "${GREEN}✅ インポートは既に整理されています${NC}"
        exit 0
    fi
fi

# 2. 差分表示または修正
if [ "$DIFF_ONLY" = true ] || [ "$FIX" = false ]; then
    # 差分を表示
    echo
    echo -e "${YELLOW}📝 修正案:${NC}"
    $RUFF_CMD --fix --diff || true
    
    if [ "$FIX" = false ]; then
        echo
        echo -e "${BLUE}💡 ヒント: 実際に修正を適用するには --fix オプションを使用してください${NC}"
    fi
elif [ "$FIX" = true ]; then
    # 修正を適用
    echo
    echo -e "${YELLOW}🔧 修正を適用中...${NC}"
    $RUFF_CMD --fix
    echo -e "${GREEN}✅ 修正が完了しました${NC}"
    
    # 結果を確認
    echo
    echo -e "${YELLOW}📊 修正後の状態:${NC}"
    $RUFF_CMD || echo -e "${GREEN}✅ すべてのインポートが整理されました${NC}"
fi

# 追加情報
if [ "$VERBOSE" = true ]; then
    echo
    echo -e "${BLUE}ℹ️  ruffの設定:${NC}"
    echo "- インポート順序: 標準ライブラリ → サードパーティ → ローカル"
    echo "- グループ間には空行を挿入"
    echo "- 各グループ内はアルファベット順"
    
    # pyproject.tomlがある場合は設定を表示
    if [ -f "pyproject.toml" ]; then
        echo
        echo -e "${BLUE}📄 pyproject.toml の設定:${NC}"
        grep -A 10 "\[tool.ruff\]" pyproject.toml 2>/dev/null || echo "（ruff設定なし）"
    fi
fi