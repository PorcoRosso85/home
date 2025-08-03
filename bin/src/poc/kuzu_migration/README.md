# KuzuDB Migration CLI

プロジェクトのddlディレクトリを管理し、KuzuDBのマイグレーションを実行するスタンドアロンCLIツール。

## 概要

このツールは、各プロジェクトのddlディレクトリを指定して、その配下にマイグレーション構造を構築・管理します。

## アーキテクチャ

```
プロジェクト/
├── ddl/                    # プロジェクトが作成
│   ├── migrations/        # kuzu-migrateが管理
│   └── snapshots/         # kuzu-migrateが管理
└── src/                   # プロジェクト本体
```

## 主な機能

- 📁 **DDLディレクトリ管理**: 指定されたddlディレクトリ配下を完全管理
- 🔄 **Cypherネイティブ実行**: KuzuDBの標準形式で直接実行
- 📊 **マイグレーション履歴**: _migration_historyテーブルで追跡
- 📷 **スナップショット**: EXPORT/IMPORT DATABASEで完全バックアップ
- 🎯 **スタンドアロン**: 言語非依存のCLIツール

## インストール

### Nixで直接実行
```bash
# インストール不要で直接実行
nix run github:yourorg/kuzu-migrate -- --ddl ./ddl apply
```

### Flake統合
```nix
# flake.nix
inputs.kuzu-migrate.url = "github:yourorg/kuzu-migrate";

outputs = { self, kuzu-migrate, ... }: {
  apps = kuzu-migrate.lib.mkKuzuMigration { 
    ddlPath = "./ddl";
  };
};
```

## 使い方

### 1. 初期化
```bash
# ddlディレクトリを作成して初期化
mkdir ddl
kuzu-migrate --ddl ./ddl init
```

### 2. マイグレーション作成
```bash
# Cypherファイルを直接作成
echo "ALTER TABLE User ADD email STRING DEFAULT '';" > ddl/migrations/001_add_email.cypher
```

### 3. マイグレーション実行
```bash
# デフォルトはddl/ディレクトリ
kuzu-migrate apply

# または明示的に指定
kuzu-migrate --ddl ./custom/ddl apply
```

### 4. スナップショット作成
```bash
kuzu-migrate snapshot --version v1.0.0
```

## コマンド

| コマンド | 説明 |
|---------|------|
| `init` | ddlディレクトリ構造を初期化 |
| `apply` | 未適用のマイグレーションを実行 |
| `status` | 現在のマイグレーション状態を表示 |
| `snapshot` | 現在のスキーマをスナップショット |
| `rollback` | 指定したスナップショットに復元 |

## マイグレーション定義形式

### Cypherネイティブ形式（推奨）

```cypher
-- migrations/001_add_user_email.cypher
-- Migration ID: 001_add_user_email
-- Description: Add email field to User table
-- Author: dev-team
-- Date: 2024-07-01

ALTER TABLE User ADD email STRING DEFAULT '';
```

### スキーマ差分からの自動生成

```bash
# 現在のスキーマをエクスポート
kuzu-migrate export-schema ./snapshots/current

# 変更後のスキーマと比較して差分を生成
kuzu-migrate generate-migration ./snapshots/current ./snapshots/new
```

### サポートされる操作タイプ

| type | 説明 | パラメータ |
|------|------|-----------|
| add_column | カラム追加 | table, column, data_type, default |
| drop_column | カラム削除 | table, column, if_exists |
| rename_table | テーブル名変更 | table, new_name |
| rename_column | カラム名変更 | table, old_column, new_column |
| add_comment | コメント追加 | table, comment |
| create_table | テーブル作成 | query |
| custom | カスタムクエリ | query |

## 例

### 1. 単純なカラム追加

```cypher
-- migrations/002_add_status.cypher
ALTER TABLE User ADD status STRING DEFAULT 'active';
```

### 2. 複数操作の組み合わせ

```cypher
-- migrations/003_user_metadata.cypher
ALTER TABLE User ADD created_by STRING;
ALTER TABLE User ADD updated_at TIMESTAMP;
ALTER TABLE User COMMENT 'User table with audit fields';
```

### 3. テーブル作成

```cypher
-- migrations/004_create_products.cypher
CREATE NODE TABLE Product (
    id INT64,
    name STRING,
    price DOUBLE,
    PRIMARY KEY (id)
);
```

## ディレクトリ構成

### kuzu-migrateが管理する構造
```
ddl/
├── migrations/              # Cypherマイグレーションファイル
│   ├── 000_initial.cypher  # 初期スキーマ
│   └── NNN_description.cypher  # 番号_説明.cypher形式
└── snapshots/              # EXPORT DATABASEの出力
    └── v1.0.0/            # バージョンごとのスナップショット
        ├── schema.cypher
        ├── macro.cypher
        └── data/
```

### 責任分界
- **プロジェクト**: ddl/ディレクトリの作成のみ
- **kuzu-migrate**: migrations/とsnapshots/の完全管理

## ロールバック

⚠️ **注意**: 一部の操作は不可逆です（DROP COLUMNなど）

### スナップショットベースの完全ロールバック

```python
# マイグレーション前にスナップショット作成
migrator.create_snapshot("pre_migration_v2.0.0")

# 変更実行
migrator.run_migrations()

# 問題発生時は完全復元
migrator.restore_snapshot("pre_migration_v2.0.0")
```

### 個別マイグレーションのロールバック

```cypher
-- migrations/002_add_status_rollback.cypher
-- Rollback for: 002_add_status
ALTER TABLE User DROP status IF EXISTS;
```

## 環境変数

| 変数名 | 説明 | デフォルト |
|--------|------|----------|
| `KUZU_DDL_DIR` | DDLディレクトリパス | `./ddl` |
| `KUZU_DB_PATH` | データベースファイルパス | `./data/kuzu.db` |

## エラーメッセージ

ツールはDon Normanのデザイン原則に従い、明確な指示を提供します：

```
❌ ERROR: ddl/ directory not found

This tool manages database migrations in a 'ddl' directory.
Please create it:

    mkdir ddl
    kuzu-migrate --ddl ./ddl init

Learn more: https://github.com/yourorg/kuzu-migrate#getting-started
```

## よくあるエラーと対処

### マイグレーション失敗時
```
❌ Migration 002_add_email.cypher failed:

    Error: Column 'email' already exists on table 'User'
    
    To fix:
    1. Check existing columns: 
       kuzu ./data/kuzu.db -c "CALL table_info('User')"
    
    2. Skip this migration:
       touch ddl/migrations/.applied/002_add_email.cypher
```

## 実装

シンプルなシェルスクリプトとして実装され、KuzuDB CLIのラッパーとして動作します。

```bash
#!/bin/bash
# kuzu-migrate

DDL_DIR="${1:-${KUZU_DDL_DIR:-./ddl}}"
DB_PATH="${KUZU_DB_PATH:-./data/kuzu.db}"

# 必須ディレクトリチェック
if [ ! -d "$DDL_DIR" ]; then
    echo "❌ ERROR: ddl/ directory not found"
    exit 1
fi

# マイグレーション実行
for migration in "$DDL_DIR/migrations"/*.cypher; do
    kuzu "$DB_PATH" < "$migration"
done
```

## 関連ドキュメント

- [MIGRATION_DIRECTORY_CONTRACT.md](MIGRATION_DIRECTORY_CONTRACT.md) - ディレクトリ構成契約
- [TODO.md](TODO.md) - 実装タスク一覧
- [ALTER_TABLE_DISCOVERY.md](ALTER_TABLE_DISCOVERY.md) - KuzuDBのALTER TABLE機能

## 継承プロジェクト

このツールは以下のプロジェクトで使用される予定です：

- `bin/src/flakes/python` - Pythonプロジェクトテンプレート
- `bin/src/persistence/kuzu_py` - KuzuDB Pythonバインディング
- `bin/src/telemetry/log_py` - テレメトリログシステム

各プロジェクトは自身のflake.nixでこのツールをinputとして宣言し、`lib.mkKuzuMigration`を使用してマイグレーションコマンドを統合します。

## トラブルシューティング

### KuzuDB CLIが見つからない
```
❌ ERROR: KuzuDB CLI not found

The 'kuzu' command is required but not installed.
Please install KuzuDB:

    nix-env -iA nixpkgs.kuzu
    # or
    brew install kuzu
    # or visit https://kuzudb.com/download/
```

### DDLディレクトリが存在しない
```
❌ ERROR: ddl/ directory not found

This tool manages database migrations in a 'ddl' directory.
Please create it:

    mkdir ddl
    kuzu-migrate --ddl ./ddl init
```

## ライセンス

MIT License