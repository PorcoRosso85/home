# KuzuDB Migration Framework

ALTER TABLE機能を活用したシンプルで強力なマイグレーション管理システム。

## 🎉 重要な更新

KuzuDBが包括的なALTER TABLE機能をサポートしていることが判明し、マイグレーションが大幅に簡素化されました。

## 主な機能

- ✅ **ネイティブALTER TABLE**: テーブル再作成不要
- ✅ **瞬時のスキーマ変更**: 大規模データでも高速
- ✅ **マイグレーション履歴管理**: 適用済み変更の追跡
- ✅ **JSONベースの定義**: 読みやすく管理しやすい
- ✅ **部分的ロールバック**: 可能な範囲でのロールバック

## クイックスタート

### 1. インストール

```bash
# Nix環境
nix develop

# または直接
pip install kuzu
```

### 2. マイグレーション作成

```python
from migration_framework import MigrationBuilder

# カラム追加のマイグレーション
migration = MigrationBuilder.create_add_column_migration(
    table="User",
    column="email",
    data_type="STRING",
    default="",
    description="Add email to users"
)

# ファイルとして保存
MigrationBuilder.create_migration_file(migration)
```

### 3. マイグレーション実行

```python
from migration_framework import KuzuMigration

# マイグレーターを初期化
migrator = KuzuMigration("my_database.db", "migrations")
migrator.connect()
migrator.init_migration_tracking()

# すべてのマイグレーションを実行
migrator.run_migrations()

migrator.disconnect()
```

## マイグレーション定義形式

### JSON形式（推奨）

```json
{
  "id": "20240701_100000_add_user_email",
  "name": "Add email column to users",
  "operations": [
    {
      "type": "add_column",
      "table": "User",
      "column": "email",
      "data_type": "STRING",
      "default": ""
    }
  ]
}
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

```json
{
  "id": "20240701_add_status",
  "name": "Add status field",
  "operations": [
    {
      "type": "add_column",
      "table": "User",
      "column": "status",
      "data_type": "STRING",
      "default": "active"
    }
  ]
}
```

### 2. 複数操作の組み合わせ

```json
{
  "id": "20240701_user_metadata",
  "name": "Add user metadata fields",
  "operations": [
    {
      "type": "add_column",
      "table": "User",
      "column": "created_by",
      "data_type": "STRING"
    },
    {
      "type": "add_column",
      "table": "User",
      "column": "updated_at",
      "data_type": "TIMESTAMP"
    },
    {
      "type": "add_comment",
      "table": "User",
      "comment": "User table with audit fields"
    }
  ]
}
```

### 3. テーブル作成

```json
{
  "id": "20240701_create_products",
  "name": "Create products table",
  "operations": [
    {
      "type": "create_table",
      "query": "CREATE NODE TABLE Product (id INT64, name STRING, price DOUBLE, PRIMARY KEY (id))"
    }
  ]
}
```

## 従来形式のサポート（後方互換性）

```cypher
-- Migration: add_user_email
-- Created at: 2024-07-01 10:00:00

-- UP
ALTER TABLE User ADD email STRING DEFAULT '';

-- DOWN
ALTER TABLE User DROP email;
```

## ロールバック

⚠️ **注意**: 一部の操作は不可逆です（DROP COLUMNなど）

### ロールバックファイルの作成

```json
{
  "id": "20240701_add_status_rollback",
  "name": "Rollback: Remove status field",
  "operations": [
    {
      "type": "drop_column",
      "table": "User",
      "column": "status",
      "if_exists": true
    }
  ],
  "warning": "This will permanently delete all data in the status column"
}
```

### ロールバックの実行

```python
migrator.rollback_migration("20240701_add_status")
```

## ベストプラクティス

1. **バックアップ**: 重要な変更前は必ずバックアップ
   ```python
   backup_path = migrator.create_backup()
   ```

2. **段階的な変更**: 大きな変更は複数の小さなマイグレーションに分割

3. **テスト環境での検証**: 本番適用前に必ずテスト

4. **命名規則**: `YYYYMMDD_HHMMSS_description`形式を推奨

5. **ドキュメント化**: 各マイグレーションに明確な説明を記載

## 制限事項

1. **データ型変更**: 直接的な型変更は非サポート（新カラム追加→データ移行→旧カラム削除）
2. **ロールバック**: DROP操作は不可逆
3. **トランザクション**: 部分的なサポート

## パフォーマンス

| 操作 | データ量 | 実行時間 |
|------|---------|----------|
| ADD COLUMN | 100万行 | < 1秒 |
| DROP COLUMN | 100万行 | < 1秒 |
| RENAME TABLE | 任意 | 瞬時 |
| RENAME COLUMN | 任意 | 瞬時 |

## ALTER TABLE機能の発見

詳細は[ALTER_TABLE_DISCOVERY.md](ALTER_TABLE_DISCOVERY.md)を参照してください。

## トラブルシューティング

### エラー: "Property already exists"
- 原因: カラムが既に存在
- 解決: `ADD IF NOT EXISTS`を使用

### エラー: "Table does not exist"
- 原因: テーブルが存在しない
- 解決: CREATE TABLEマイグレーションを先に実行

### マイグレーションが重複適用される
- 原因: 履歴テーブルの不整合
- 解決: `_migration_history`テーブルを確認

## 今後の展開

1. **自動マイグレーション生成**: スキーマ差分からの自動生成
2. **並列実行**: 独立したマイグレーションの並列処理
3. **監視ダッシュボード**: マイグレーション状態の可視化
4. **クラウド統合**: S3/GCSへの自動バックアップ

## 貢献

PRを歓迎します！特に以下の領域：
- データ型変換のサポート
- より高度なロールバック戦略
- パフォーマンス最適化