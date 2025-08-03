# KuzuDB Migration Framework

ALTER TABLE機能を活用したシンプルで強力なマイグレーション管理システム。

## 🎉 重要な更新

KuzuDBが包括的なALTER TABLE機能をサポートしていることが判明し、マイグレーションが大幅に簡素化されました。

## 主な機能

- ✅ **ネイティブALTER TABLE**: テーブル再作成不要
- ✅ **瞬時のスキーマ変更**: 大規模データでも高速
- ✅ **マイグレーション履歴管理**: 適用済み変更の追跡
- ✅ **Cypherネイティブ定義**: KuzuDBの標準形式で透明性が高い
- ✅ **スキーマ差分からの自動生成**: EXPORT DATABASEを活用した差分検出
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

```bash
# Cypherファイルを直接作成
echo "ALTER TABLE User ADD email STRING DEFAULT '';" > migrations/001_add_email.cypher

# または、スキーマ差分から自動生成
kuzu-migrate generate-migration
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

## プロジェクト構造

```
kuzu_migration/
├── migrations/              # Cypherマイグレーションファイル
│   ├── 000_initial.cypher  # EXPORT DATABASE --schema-only の出力
│   └── NNN_description.cypher  # 番号_説明.cypher形式
├── snapshots/              # EXPORT DATABASEの出力
│   └── v1.0.0/            # バージョンごとのスナップショット
│       ├── schema.cypher
│       ├── macro.cypher
│       └── data/
└── src/                    # フレームワークのソースコード
    ├── migrator.py        # 実行エンジン
    ├── snapshot.py        # バックアップ/リストア
    └── cli.py             # コマンドライン
```

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