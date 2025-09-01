#!/usr/bin/env bash
set -euo pipefail

# モジュール追加スクリプト
# 目的: READMEに相当するモジュール定義をグラフDBに追加

DB_PATH="./readme.db"
KUZU_CLI="kuzu_shell"

# 使用方法の表示
usage() {
    cat << EOF
使用方法: $0 -i <ID> -p <PURPOSE> [オプション]

必須パラメータ:
  -i ID          モジュールID (例: auth-service)
  -p PURPOSE     モジュールの目的

オプション:
  -r RESP        責務を追加 (複数回指定可能)
                 形式: "名前:説明"
  -v VALUE       価値提案を追加 (複数回指定可能)
  -c CONSTRAINT  制約を追加 (複数回指定可能)
                 形式: "タイプ:ルール:重要度"
  -d DEPENDENCY  依存モジュールID (複数回指定可能)
  -h             このヘルプを表示

例:
  $0 -i auth-service -p "ユーザー認証機能を提供" \\
     -r "authentication:ユーザーの認証処理" \\
     -r "authorization:権限の確認" \\
     -v "セキュアな認証" \\
     -c "security:bcryptでパスワードをハッシュ化:must"
EOF
    exit 1
}

# データベース存在確認
if [ ! -d "$DB_PATH" ]; then
    echo "エラー: データベースが存在しません。先に ./init.sh を実行してください"
    exit 1
fi

# パラメータ初期化
MODULE_ID=""
PURPOSE=""
RESPONSIBILITIES=()
VALUES=()
CONSTRAINTS=()
DEPENDENCIES=()

# パラメータ解析
while getopts "i:p:r:v:c:d:h" opt; do
    case $opt in
        i) MODULE_ID="$OPTARG" ;;
        p) PURPOSE="$OPTARG" ;;
        r) RESPONSIBILITIES+=("$OPTARG") ;;
        v) VALUES+=("$OPTARG") ;;
        c) CONSTRAINTS+=("$OPTARG") ;;
        d) DEPENDENCIES+=("$OPTARG") ;;
        h) usage ;;
        *) usage ;;
    esac
done

# 必須パラメータチェック
if [ -z "$MODULE_ID" ] || [ -z "$PURPOSE" ]; then
    echo "エラー: IDと目的は必須です"
    usage
fi

echo "=== モジュール追加: $MODULE_ID ==="

# Cypherクエリ生成
CYPHER_FILE="/tmp/add_module_$$.cypher"

# モジュール作成
cat << EOF > "$CYPHER_FILE"
// 既存モジュールの確認
MATCH (m:Module {id: '$MODULE_ID'})
RETURN count(m) as existing_count;
EOF

EXISTING=$(echo "$(cat "$CYPHER_FILE")" | $KUZU_CLI "$DB_PATH" | grep -o '[0-9]' | head -1)

if [ "$EXISTING" = "1" ]; then
    echo "警告: モジュール '$MODULE_ID' は既に存在します"
    read -p "上書きしますか? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "追加を中止しました"
        exit 0
    fi
    # 既存の関連データを削除
    cat << EOF > "$CYPHER_FILE"
// 既存の関連を削除
MATCH (m:Module {id: '$MODULE_ID'})-[r]-(n)
DELETE r;
MATCH (m:Module {id: '$MODULE_ID'})
DELETE m;
EOF
    cat "$CYPHER_FILE" | $KUZU_CLI "$DB_PATH"
fi

# モジュール作成クエリ
cat << EOF > "$CYPHER_FILE"
// モジュールノードを作成
CREATE (m:Module {
    id: '$MODULE_ID',
    purpose: '$PURPOSE'
});
EOF

# 責務の追加
for resp in "${RESPONSIBILITIES[@]}"; do
    IFS=':' read -r name desc <<< "$resp"
    cat << EOF >> "$CYPHER_FILE"

// 責務を追加: $name
MATCH (m:Module {id: '$MODULE_ID'})
CREATE (r:Responsibility {
    id: '${MODULE_ID}_resp_${name}',
    name: '$name',
    description: '$desc'
})
CREATE (m)-[:HAS_RESPONSIBILITY]->(r);
EOF
done

# 価値提案の追加
for value in "${VALUES[@]}"; do
    cat << EOF >> "$CYPHER_FILE"

// 価値提案を追加: $value
MATCH (m:Module {id: '$MODULE_ID'})
CREATE (v:ValueProposition {
    id: '${MODULE_ID}_value_${RANDOM}',
    value: '$value'
})
CREATE (m)-[:PROVIDES_VALUE]->(v);
EOF
done

# 制約の追加
for constraint in "${CONSTRAINTS[@]}"; do
    IFS=':' read -r type rule severity <<< "$constraint"
    severity=${severity:-must}
    cat << EOF >> "$CYPHER_FILE"

// 制約を追加: $type
MATCH (m:Module {id: '$MODULE_ID'})
CREATE (c:Constraint {
    id: '${MODULE_ID}_constraint_${RANDOM}',
    type: '$type',
    rule: '$rule',
    severity: '$severity'
})
CREATE (m)-[:HAS_CONSTRAINT]->(c);
EOF
done

# 依存関係の追加
for dep in "${DEPENDENCIES[@]}"; do
    cat << EOF >> "$CYPHER_FILE"

// 依存関係を追加: $dep
MATCH (m:Module {id: '$MODULE_ID'})
MATCH (d:Module {id: '$dep'})
CREATE (m)-[:DEPENDS_ON]->(d);
EOF
done

# クエリ実行
echo "モジュールを追加中..."
cat "$CYPHER_FILE" | $KUZU_CLI "$DB_PATH"

# 結果確認
echo ""
echo "=== 追加されたモジュール ==="
cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m:Module {id: '$MODULE_ID'})
RETURN m.id as ID, m.purpose as Purpose;
EOF

echo ""
echo "=== 責務 ==="
cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m:Module {id: '$MODULE_ID'})-[:HAS_RESPONSIBILITY]->(r:Responsibility)
RETURN r.name as Name, r.description as Description;
EOF

echo ""
echo "=== 価値提案 ==="
cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m:Module {id: '$MODULE_ID'})-[:PROVIDES_VALUE]->(v:ValueProposition)
RETURN v.value as Value;
EOF

# クリーンアップ
rm -f "$CYPHER_FILE"

echo ""
echo "✅ モジュール '$MODULE_ID' を追加しました"
echo "確認: ./query.sh -i $MODULE_ID"