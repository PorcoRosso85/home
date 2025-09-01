#!/usr/bin/env bash
set -euo pipefail

# クエリスクリプト
# 目的: グラフDBの現在の状態を確認（READMEの読み取りに相当）

DB_PATH="./readme.db"
KUZU_CLI="kuzu_shell"

# 使用方法
usage() {
    cat << EOF
使用方法: $0 [オプション]

オプション:
  -i ID       特定モジュールの詳細表示
  -l          全モジュールのリスト表示
  -d          依存関係グラフの表示
  -s          システム統計の表示
  -r RAW      生のCypherクエリ実行
  -h          このヘルプを表示

例:
  $0 -l                     # 全モジュール一覧
  $0 -i auth-service        # 特定モジュールの詳細
  $0 -d                     # 依存関係の可視化
  $0 -r "MATCH (n) RETURN n LIMIT 5"  # カスタムクエリ
EOF
    exit 0
}

# データベース存在確認
if [ ! -d "$DB_PATH" ]; then
    echo "エラー: データベースが存在しません。先に ./init.sh を実行してください"
    exit 1
fi

# モジュール詳細表示
show_module_detail() {
    local module_id="$1"
    
    echo "=== モジュール: $module_id ==="
    
    # 基本情報
    echo ""
    echo "【目的】"
    echo "MATCH (m:Module {id: '$module_id'}) RETURN m.purpose as Purpose;" | \
        $KUZU_CLI "$DB_PATH" | tail -n +3 | head -n -1
    
    # 責務
    echo ""
    echo "【責務】"
    cat << EOF | $KUZU_CLI "$DB_PATH" | tail -n +3 | head -n -1
MATCH (m:Module {id: '$module_id'})-[:HAS_RESPONSIBILITY]->(r:Responsibility)
RETURN r.name as Name, r.description as Description
ORDER BY r.name;
EOF
    
    # 価値提案
    echo ""
    echo "【価値提案】"
    cat << EOF | $KUZU_CLI "$DB_PATH" | tail -n +3 | head -n -1
MATCH (m:Module {id: '$module_id'})-[:PROVIDES_VALUE]->(v:ValueProposition)
RETURN v.value as Value;
EOF
    
    # 制約
    echo ""
    echo "【制約】"
    cat << EOF | $KUZU_CLI "$DB_PATH" | tail -n +3 | head -n -1
MATCH (m:Module {id: '$module_id'})-[:HAS_CONSTRAINT]->(c:Constraint)
RETURN c.type as Type, c.severity as Severity, c.rule as Rule
ORDER BY c.severity DESC, c.type;
EOF
    
    # 依存関係
    echo ""
    echo "【依存先】"
    cat << EOF | $KUZU_CLI "$DB_PATH" | tail -n +3 | head -n -1
MATCH (m:Module {id: '$module_id'})-[:DEPENDS_ON]->(d:Module)
RETURN d.id as DependsOn, d.purpose as Purpose;
EOF
    
    echo ""
    echo "【被依存】"
    cat << EOF | $KUZU_CLI "$DB_PATH" | tail -n +3 | head -n -1
MATCH (m:Module {id: '$module_id'})<-[:DEPENDS_ON]-(d:Module)
RETURN d.id as DependedBy, d.purpose as Purpose;
EOF
}

# 全モジュールリスト
show_all_modules() {
    echo "=== 全モジュール一覧 ==="
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m:Module)
RETURN m.id as ID, m.purpose as Purpose
ORDER BY m.id;
EOF
}

# 依存関係グラフ
show_dependencies() {
    echo "=== 依存関係グラフ ==="
    echo ""
    echo "【依存関係】"
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m1:Module)-[:DEPENDS_ON]->(m2:Module)
RETURN m1.id as From, '--->' as Arrow, m2.id as To
ORDER BY m1.id, m2.id;
EOF
    
    echo ""
    echo "【孤立モジュール（依存なし・被依存なし）】"
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m:Module)
WHERE NOT EXISTS { MATCH (m)-[:DEPENDS_ON]->() }
  AND NOT EXISTS { MATCH (m)<-[:DEPENDS_ON]-() }
RETURN m.id as IsolatedModule, m.purpose as Purpose;
EOF
    
    echo ""
    echo "【循環依存チェック】"
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH path = (m:Module)-[:DEPENDS_ON*2..]->(m)
RETURN DISTINCT m.id as CircularDependency
LIMIT 10;
EOF
}

# システム統計
show_statistics() {
    echo "=== システム統計 ==="
    
    echo ""
    echo "【ノード数】"
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (m:Module) WITH count(m) as modules
MATCH (r:Responsibility) WITH modules, count(r) as responsibilities
MATCH (c:Constraint) WITH modules, responsibilities, count(c) as constraints
MATCH (v:ValueProposition) WITH modules, responsibilities, constraints, count(v) as values
RETURN 
    modules as Modules,
    responsibilities as Responsibilities,
    constraints as Constraints,
    values as ValuePropositions;
EOF
    
    echo ""
    echo "【リレーションシップ数】"
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH ()-[r:DEPENDS_ON]->() WITH count(r) as deps
MATCH ()-[r:HAS_RESPONSIBILITY]->() WITH deps, count(r) as resps
MATCH ()-[r:HAS_CONSTRAINT]->() WITH deps, resps, count(r) as consts
MATCH ()-[r:PROVIDES_VALUE]->() WITH deps, resps, consts, count(r) as vals
RETURN
    deps as Dependencies,
    resps as Responsibilities,
    consts as Constraints,
    vals as Values;
EOF
    
    echo ""
    echo "【システム情報】"
    cat << EOF | $KUZU_CLI "$DB_PATH"
MATCH (s:SystemInfo)
RETURN s.key as Key, s.value as Value
ORDER BY s.key;
EOF
}

# メイン処理
if [ $# -eq 0 ]; then
    show_all_modules
    exit 0
fi

while getopts "i:ldsr:h" opt; do
    case $opt in
        i)
            show_module_detail "$OPTARG"
            ;;
        l)
            show_all_modules
            ;;
        d)
            show_dependencies
            ;;
        s)
            show_statistics
            ;;
        r)
            echo "=== カスタムクエリ実行 ==="
            echo "$OPTARG" | $KUZU_CLI "$DB_PATH"
            ;;
        h)
            usage
            ;;
        *)
            usage
            ;;
    esac
done