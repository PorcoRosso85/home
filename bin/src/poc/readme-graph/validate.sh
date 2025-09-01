#!/usr/bin/env bash
set -euo pipefail

# 検証スクリプト
# 目的: モジュール定義の制約チェックと整合性検証

DB_PATH="./readme.db"
KUZU_CLI="kuzu_shell"

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 使用方法
usage() {
    cat << EOF
使用方法: $0 [オプション]

オプション:
  -a          全検証を実行
  -c          循環依存チェック
  -o          孤立モジュールチェック
  -m          必須制約チェック
  -i MODULE   特定モジュールの検証
  -h          このヘルプを表示

例:
  $0 -a                     # 全検証実行
  $0 -c                     # 循環依存のみチェック
  $0 -i auth-service        # 特定モジュールの検証
EOF
    exit 0
}

# データベース存在確認
if [ ! -d "$DB_PATH" ]; then
    echo "エラー: データベースが存在しません。先に ./init.sh を実行してください"
    exit 1
fi

# 結果出力
print_result() {
    local status="$1"
    local message="$2"
    
    if [ "$status" = "OK" ]; then
        echo -e "${GREEN}✓${NC} $message"
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
    else
        echo -e "${RED}✗${NC} $message"
    fi
}

# 循環依存チェック
check_circular_deps() {
    echo "=== 循環依存チェック ==="
    
    RESULT=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -v "^-" | grep -v "^$" | tail -n +2
MATCH path = (m:Module)-[:DEPENDS_ON*2..]->(m)
RETURN DISTINCT m.id as module
LIMIT 10;
EOF
)
    
    if [ -z "$RESULT" ]; then
        print_result "OK" "循環依存なし"
        return 0
    else
        print_result "ERROR" "循環依存を検出:"
        echo "$RESULT" | while read -r line; do
            echo "  - $line"
        done
        return 1
    fi
}

# 孤立モジュールチェック
check_orphan_modules() {
    echo "=== 孤立モジュールチェック ==="
    
    RESULT=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -v "^-" | grep -v "^$" | tail -n +3
MATCH (m:Module)
WHERE NOT EXISTS { MATCH (m)-[:DEPENDS_ON]->() }
  AND NOT EXISTS { MATCH (m)<-[:DEPENDS_ON]-() }
RETURN m.id as module, m.purpose as purpose;
EOF
)
    
    if [ -z "$RESULT" ]; then
        print_result "OK" "全モジュールが依存関係に含まれています"
    else
        COUNT=$(echo "$RESULT" | wc -l)
        print_result "WARN" "$COUNT 個の孤立モジュール:"
        echo "$RESULT" | while IFS='|' read -r module purpose; do
            echo "  - $module: $purpose"
        done
    fi
}

# 必須制約チェック
check_must_constraints() {
    echo "=== 必須制約チェック ==="
    
    RESULT=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -v "^-" | grep -v "^$" | tail -n +3
MATCH (m:Module)-[:HAS_CONSTRAINT]->(c:Constraint)
WHERE c.severity = 'must'
RETURN m.id as module, c.type as type, c.rule as rule
ORDER BY m.id, c.type;
EOF
)
    
    if [ -z "$RESULT" ]; then
        print_result "WARN" "必須制約が定義されていません"
    else
        COUNT=$(echo "$RESULT" | wc -l)
        print_result "OK" "$COUNT 個の必須制約が定義されています:"
        echo "$RESULT" | while IFS='|' read -r module type rule; do
            echo "  [$module] $type: $rule"
        done
    fi
}

# モジュール単体検証
validate_module() {
    local module_id="$1"
    
    echo "=== モジュール検証: $module_id ==="
    
    # モジュール存在確認
    EXISTS=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -c "$module_id" || true
MATCH (m:Module {id: '$module_id'})
RETURN m.id;
EOF
)
    
    if [ "$EXISTS" -eq 0 ]; then
        print_result "ERROR" "モジュール '$module_id' が存在しません"
        return 1
    fi
    
    # 目的の確認
    PURPOSE=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -v "^-" | grep -v "^$" | tail -n +3
MATCH (m:Module {id: '$module_id'})
RETURN m.purpose;
EOF
)
    
    if [ -z "$PURPOSE" ]; then
        print_result "ERROR" "目的が未定義"
    else
        print_result "OK" "目的: $PURPOSE"
    fi
    
    # 責務の確認
    RESP_COUNT=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -c "." || echo "0"
MATCH (m:Module {id: '$module_id'})-[:HAS_RESPONSIBILITY]->(r)
RETURN count(r);
EOF
)
    
    if [ "$RESP_COUNT" -eq 0 ]; then
        print_result "WARN" "責務が未定義"
    else
        print_result "OK" "$RESP_COUNT 個の責務が定義済み"
    fi
    
    # 価値提案の確認
    VALUE_COUNT=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -c "." || echo "0"
MATCH (m:Module {id: '$module_id'})-[:PROVIDES_VALUE]->(v)
RETURN count(v);
EOF
)
    
    if [ "$VALUE_COUNT" -eq 0 ]; then
        print_result "WARN" "価値提案が未定義"
    else
        print_result "OK" "$VALUE_COUNT 個の価値提案が定義済み"
    fi
    
    # 依存関係の確認
    DEP_COUNT=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -c "." || echo "0"
MATCH (m:Module {id: '$module_id'})-[:DEPENDS_ON]->(d)
RETURN count(d);
EOF
)
    
    echo "  依存先: $DEP_COUNT モジュール"
    
    # 循環依存の個別チェック
    CIRCULAR=$(cat << EOF | $KUZU_CLI "$DB_PATH" 2>/dev/null | grep -c "$module_id" || echo "0"
MATCH path = (m:Module {id: '$module_id'})-[:DEPENDS_ON*2..]->(m)
RETURN m.id;
EOF
)
    
    if [ "$CIRCULAR" -gt 0 ]; then
        print_result "ERROR" "このモジュールは循環依存に含まれています"
    fi
}

# 全検証実行
run_all_validations() {
    echo "=== 全検証実行 ==="
    echo ""
    
    ERROR_COUNT=0
    WARN_COUNT=0
    
    check_circular_deps || ((ERROR_COUNT++))
    echo ""
    
    check_orphan_modules
    echo ""
    
    check_must_constraints
    echo ""
    
    # サマリー
    echo "=== 検証結果サマリー ==="
    if [ "$ERROR_COUNT" -eq 0 ]; then
        print_result "OK" "エラーなし"
    else
        print_result "ERROR" "$ERROR_COUNT 個のエラーが見つかりました"
    fi
}

# メイン処理
if [ $# -eq 0 ]; then
    run_all_validations
    exit 0
fi

while getopts "acomhi:" opt; do
    case $opt in
        a)
            run_all_validations
            ;;
        c)
            check_circular_deps
            ;;
        o)
            check_orphan_modules
            ;;
        m)
            check_must_constraints
            ;;
        i)
            validate_module "$OPTARG"
            ;;
        h)
            usage
            ;;
        *)
            usage
            ;;
    esac
done