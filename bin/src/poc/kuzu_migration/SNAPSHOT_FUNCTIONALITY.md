# Snapshot Functionality

## 目的と価値

`kuzu-migrate snapshot`コマンドは、KuzuDBデータベースの完全なバックアップを作成します。このスナップショットには以下が含まれます：

- データベーススキーマ（DDL）
- テーブルデータ
- マイグレーション履歴
- メタデータ

**主な価値**：
- **ポイントインタイムリカバリ**: 特定時点のデータベース状態を保存・復元
- **バージョン管理**: リリース前の状態保存とロールバック機能
- **監査証跡**: データベース変更履歴の記録
- **環境間移行**: 開発→テスト→本番環境への安全な移行

## 使用方法

### タイムスタンプ版（自動命名）

```bash
kuzu-migrate --ddl ./ddl --db ./data/kuzu.db snapshot
```

出力例：
```
Creating snapshot: snapshot_20250805_143025
Database exported successfully!
Snapshot completed successfully!
To restore from this snapshot:
  kuzu-migrate rollback --snapshot snapshot_20250805_143025
```

### バージョン指定版（明示的命名）

```bash
kuzu-migrate --ddl ./ddl --db ./data/kuzu.db snapshot --version v1.0.0
```

出力例：
```
Creating snapshot: v1.0.0
Database exported successfully!
Snapshot completed successfully!
To restore from this snapshot:
  kuzu-migrate rollback --snapshot v1.0.0
```

**バージョン形式要件**：
- 形式: `vX.Y.Z`（セマンティックバージョニング）
- 例: `v1.0.0`, `v2.3.1`, `v10.0.0`

## 生成されるファイル構造

```
ddl/
└── snapshots/
    └── v1.0.0/                    # または snapshot_20250805_143025/
        ├── schema.cypher          # データベーススキーマ定義
        ├── snapshot_metadata.json # スナップショットメタデータ
        └── [テーブルデータ]/      # KuzuDBエクスポートデータ
```

## メタデータの内容

`snapshot_metadata.json`の構造：

```json
{
  "snapshot_name": "v1.0.0",
  "created_at": "2025-08-05T14:30:25Z",
  "database_path": "/home/user/data/kuzu.db",
  "last_migration": "001_create_test_table.cypher",
  "kuzu_version": "0.6.0"
}
```

**フィールド説明**：
- `snapshot_name`: スナップショット識別子
- `created_at`: 作成日時（ISO 8601形式）
- `database_path`: 元データベースのパス
- `last_migration`: 最後に適用されたマイグレーション
- `kuzu_version`: 使用したKuzuDBのバージョン

## 復元方法

### 特定スナップショットへのロールバック

```bash
kuzu-migrate --ddl ./ddl --db ./data/kuzu.db rollback --snapshot v1.0.0
```

### 復元プロセス

1. 現在のデータベースをバックアップ
2. データベースを初期化
3. スナップショットのスキーマを適用
4. データをインポート
5. マイグレーション履歴を更新

## エラーハンドリング

### 一般的なエラー

1. **スナップショット重複**
   ```
   Error: Snapshot already exists: v1.0.0
   Choose a different version or use timestamp-based naming
   ```

2. **無効なバージョン形式**
   ```
   Error: Invalid version format: 1.0.0
   Version should be in format vX.Y.Z (e.g., v1.0.0)
   ```

3. **データベース未作成**
   ```
   Error: Database not found at ./data/kuzu.db
   Run 'kuzu-migrate apply' first to create the database
   ```

4. **DDLディレクトリ未初期化**
   ```
   Error: DDL directory not found at ./ddl
   Run 'kuzu-migrate init' first to initialize the project
   ```

## ベストプラクティス

1. **定期的なスナップショット**: 重要な変更前後に作成
2. **意味のあるバージョン番号**: リリースやマイルストーンに対応
3. **スナップショットの保管**: 外部ストレージへの定期バックアップ
4. **テスト環境での検証**: 本番環境への適用前に復元テスト実施