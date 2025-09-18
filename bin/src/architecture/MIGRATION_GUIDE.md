# KuzuDB マイグレーション実行ガイド

## 概要

このガイドでは、KuzuDBのネイティブなEXPORT/IMPORTコマンドを使用したマイグレーションの実行手順を説明します。`kuzu-migrate`ツール（`migration_tool.py`）は、これらのコマンドをラップして、バージョン管理とマイグレーション履歴の追跡を自動化します。

## 1. 実行前の確認事項

### 1.1 環境確認

```bash
# 現在のディレクトリ確認
pwd
# 出力例: /home/nixos/bin/src/architecture

# KuzuDBがインストールされているか確認
which kuzu || echo "KuzuDBがインストールされていません"

# Pythonの確認
python3 --version
```

### 1.2 データベースの状態確認

```bash
# 現在のバージョンを確認
python3 infrastructure/migration_tool.py list

# データベースサイズの確認（大きい場合は時間がかかる）
du -sh .
```

### 1.3 バックアップの確認

**重要**: マイグレーション前に必ず手動バックアップを作成してください。

```bash
# タイムスタンプ付きバックアップディレクトリ作成
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# データベースファイルをコピー
cp -r db/* "$BACKUP_DIR/" 2>/dev/null || echo "データベースファイルが見つかりません"
```

## 2. kuzu-migrateでの実行手順

### 2.1 現在のデータベースをエクスポート（新バージョン作成）

```bash
# バージョン名の決定（例: v4.1.0）
VERSION="v4.1.0"

# エクスポート実行
python3 infrastructure/migration_tool.py export --version "$VERSION" --format parquet

# CSVフォーマットでエクスポートする場合
python3 infrastructure/migration_tool.py export --version "$VERSION" --format csv
```

**注意**: 実際のエクスポートにはKuzuDBコンソールでの実行が必要です：

```bash
# KuzuDBコンソールを開く
kuzu .

# エクスポートコマンドを実行
kuzu> EXPORT DATABASE 'migrations/v4.1.0' (format="parquet");
```

### 2.2 スキーマ変更の適用

エクスポート後、必要に応じてスキーマを変更します：

```bash
# エクスポートされたスキーマファイルを編集
nano migrations/v4.1.0/schema.cypher

# 変更内容をCHANGELOGに記録
nano migrations/v4.1.0/CHANGELOG.md
```

### 2.3 新しいバージョンのインポート

```bash
# 別の環境または新しいデータベースでインポート
python3 infrastructure/migration_tool.py import --version "$VERSION"
```

**注意**: 実際のインポートにはKuzuDBコンソールでの実行が必要です：

```bash
# 新しいデータベースディレクトリを作成
mkdir -p new_db
cd new_db

# KuzuDBコンソールを開く
kuzu .

# インポートコマンドを実行
kuzu> IMPORT DATABASE '../migrations/v4.1.0';
```

### 2.4 バージョン間の差分確認

```bash
# 2つのバージョン間の差分を確認
python3 infrastructure/migration_tool.py diff v4.0.0 v4.1.0

# 詳細な差分表示
diff -u migrations/v4.0.0/schema.cypher migrations/v4.1.0/schema.cypher
```

## 3. 実行後の検証方法

### 3.1 スキーマの検証

```bash
# KuzuDBコンソールでスキーマを確認
kuzu .
kuzu> CALL table_info('*') RETURN *;
kuzu> CALL show_tables() RETURN *;
```

### 3.2 データ整合性の確認

```cypher
-- ノード数の確認
MATCH (n) RETURN labels(n)[0] as label, COUNT(*) as count;

-- エッジ数の確認
MATCH ()-[r]->() RETURN type(r) as type, COUNT(*) as count;

-- 特定のテーブルのサンプルデータ確認
MATCH (r:Requirement) RETURN r LIMIT 5;
```

### 3.3 パフォーマンステスト

```cypher
-- 基本的なクエリパフォーマンスを確認
PROFILE MATCH (r:Requirement)-[:depends_on]->(d:Requirement) RETURN COUNT(*);
```

### 3.4 アプリケーション接続テスト

```python
# Python接続テスト
import kuzu

db = kuzu.Database(".")
conn = kuzu.Connection(db)

# テストクエリ実行
result = conn.execute("MATCH (n) RETURN COUNT(*)")
print(f"ノード総数: {result.get_next()[0]}")
```

## 4. 問題発生時の対処法

### 4.1 エクスポート失敗時

**症状**: `EXPORT DATABASE`コマンドがエラーで終了する

**対処法**:
1. ディスク容量を確認
   ```bash
   df -h .
   ```
2. 書き込み権限を確認
   ```bash
   ls -la migrations/
   ```
3. 部分エクスポートを試行（スキーマのみ）
   ```cypher
   EXPORT DATABASE 'migrations/v4.1.0' (schema_only=true);
   ```

### 4.2 インポート失敗時

**症状**: `IMPORT DATABASE`コマンドがエラーで終了する

**対処法**:
1. エクスポートファイルの完全性確認
   ```bash
   ls -la migrations/v4.1.0/
   # 必須ファイル: schema.cypher, copy.cypher, データファイル
   ```
2. 空のデータベースから開始
   ```bash
   rm -rf db/*  # 注意: バックアップ確認後のみ実行
   ```
3. 段階的インポート
   ```bash
   # まずスキーマのみ
   kuzu> SOURCE 'migrations/v4.1.0/schema.cypher';
   # その後データ
   kuzu> SOURCE 'migrations/v4.1.0/copy.cypher';
   ```

### 4.3 ロールバック手順

```bash
# 以前のバージョンに戻す
python3 infrastructure/migration_tool.py rollback v4.0.0

# または手動でバックアップから復元
rm -rf db/*
cp -r "$BACKUP_DIR"/* db/
```

### 4.4 データ不整合の修復

**症状**: インポート後にデータが欠落または重複

**対処法**:
1. 制約違反の確認
   ```cypher
   -- ユニーク制約違反をチェック
   MATCH (n:Requirement)
   WITH n.id as id, COUNT(*) as cnt
   WHERE cnt > 1
   RETURN id, cnt;
   ```

2. 参照整合性の確認
   ```cypher
   -- 存在しない参照をチェック
   MATCH (r:Requirement)-[:depends_on]->(d)
   WHERE NOT EXISTS(d.id)
   RETURN r.id;
   ```

3. データクリーンアップ
   ```cypher
   -- 重複データの削除（慎重に実行）
   MATCH (n:Requirement)
   WITH n.id as id, COLLECT(n) as nodes
   WHERE SIZE(nodes) > 1
   FOREACH (n IN nodes[1..] | DELETE n);
   ```

### 4.5 トラブルシューティングチェックリスト

- [ ] バックアップは作成済みか？
- [ ] ディスク容量は十分か？（エクスポートサイズの2倍以上推奨）
- [ ] KuzuDBのバージョンは互換性があるか？
- [ ] ファイルシステムの権限は適切か？
- [ ] メモリは十分か？（大規模データベースの場合）
- [ ] ネットワークドライブを使用していないか？（ローカルディスク推奨）

## 5. ベストプラクティス

1. **定期的なエクスポート**: 重要な変更前には必ずエクスポートを作成
2. **バージョン命名規則**: セマンティックバージョニング（v<major>.<minor>.<patch>）を使用
3. **CHANGELOG記録**: すべての変更を詳細に記録
4. **テスト環境での検証**: 本番環境適用前に必ずテスト環境で検証
5. **自動化スクリプト**: 頻繁な作業は自動化スクリプトを作成

## 6. 参考情報

- [KuzuDB公式ドキュメント - Migrate your database](https://kuzudb.com/docs/data-import/migrate)
- `infrastructure/migration_tool.py` - マイグレーションツールのソースコード
- `migrations/` - マイグレーション履歴ディレクトリ

---

**注意**: このガイドは`infrastructure/migration_tool.py`をベースにしていますが、実際のEXPORT/IMPORTコマンドはKuzuDBコンソールで直接実行する必要があります。ツールは管理とバージョニングを支援するラッパーとして機能します。