#!/usr/bin/env bash
set -euo pipefail

# README Graphシステムの初期化スクリプト
# 目的: KuzuDBのデータベースを初期化し、基本スキーマを作成

DB_PATH="./readme.db"
KUZU_CLI="kuzu_shell"

# 既存DBの確認
if [ -d "$DB_PATH" ]; then
    echo "警告: 既存のデータベース '$DB_PATH' が見つかりました"
    read -p "削除して再作成しますか? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$DB_PATH"
        echo "既存データベースを削除しました"
    else
        echo "初期化を中止しました"
        exit 0
    fi
fi

echo "=== README Graph データベース初期化 ==="
echo "データベースパス: $DB_PATH"

# スキーマ作成のCypherクエリ
cat << 'EOF' > /tmp/init_schema.cypher
// モジュールノードの作成
CREATE NODE TABLE Module(
    id STRING PRIMARY KEY,
    purpose STRING NOT NULL,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

// 責務ノードの作成
CREATE NODE TABLE Responsibility(
    id STRING PRIMARY KEY,
    name STRING NOT NULL,
    description STRING NOT NULL
);

// 制約ノードの作成
CREATE NODE TABLE Constraint(
    id STRING PRIMARY KEY,
    type STRING NOT NULL,
    rule STRING NOT NULL,
    severity STRING DEFAULT 'must'
);

// 価値提案ノードの作成
CREATE NODE TABLE ValueProposition(
    id STRING PRIMARY KEY,
    value STRING NOT NULL
);

// リレーションシップの定義
CREATE REL TABLE HAS_RESPONSIBILITY(FROM Module TO Responsibility);
CREATE REL TABLE HAS_CONSTRAINT(FROM Module TO Constraint);
CREATE REL TABLE PROVIDES_VALUE(FROM Module TO ValueProposition);
CREATE REL TABLE DEPENDS_ON(FROM Module TO Module);

// システムテーブル（メタデータ）
CREATE NODE TABLE SystemInfo(
    key STRING PRIMARY KEY,
    value STRING,
    updated_at TIMESTAMP DEFAULT now()
);

// 初期システム情報の挿入
CREATE (:SystemInfo {key: 'schema_version', value: '1.0.0'});
CREATE (:SystemInfo {key: 'initialized_at', value: cast(now() as STRING)});
EOF

# KuzuDBでスキーマを実行
echo "スキーマを作成中..."
echo "CREATE DATABASE '$DB_PATH';" | $KUZU_CLI
cat /tmp/init_schema.cypher | $KUZU_CLI "$DB_PATH"

# 結果確認
echo ""
echo "=== 作成されたテーブル ==="
echo "CALL show_tables() RETURN *;" | $KUZU_CLI "$DB_PATH"

echo ""
echo "=== システム情報 ==="
echo "MATCH (s:SystemInfo) RETURN s.key, s.value;" | $KUZU_CLI "$DB_PATH"

# 一時ファイルのクリーンアップ
rm -f /tmp/init_schema.cypher

echo ""
echo "✅ 初期化完了: $DB_PATH"
echo "次のステップ: ./add_module.sh でモジュールを追加"