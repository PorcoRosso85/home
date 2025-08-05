# 安全なマイグレーション戦略

## 現状
kuzu-migrateには現在dry-runオプションが実装されていません。

## 安全にマイグレーションする方法

### 1. テスト環境での事前検証

```bash
# 本番データベースのコピーを作成
cp -r ./data/kuzu.db ./data/kuzu_test.db

# テスト環境でマイグレーション実行
kuzu-migrate --db ./data/kuzu_test.db apply

# 結果を確認
kuzu-migrate --db ./data/kuzu_test.db status
```

### 2. スナップショットによるバックアップ

```bash
# マイグレーション前にスナップショット作成
kuzu-migrate snapshot --version pre-migration-v1.0.0

# マイグレーション実行
kuzu-migrate apply

# 問題があれば（rollback未実装のため手動で）
rm -rf ./data/kuzu.db
kuzu ./data/kuzu.db < ./ddl/snapshots/pre-migration-v1.0.0/schema.cypher
# データのインポートも必要
```

### 3. 段階的マイグレーション

```bash
# 1つずつマイグレーションを適用
# 例: 001_create_users.cypherのみ適用したい場合

# 他のマイグレーションを一時的に移動
mkdir -p ./ddl/migrations_pending
mv ./ddl/migrations/002_*.cypher ./ddl/migrations_pending/

# 1つだけ適用
kuzu-migrate apply

# 確認
kuzu-migrate status

# 次のマイグレーションを戻す
mv ./ddl/migrations_pending/002_*.cypher ./ddl/migrations/
```

### 4. マイグレーションの事前レビュー

```bash
# 実行されるマイグレーションを確認
ls -la ./ddl/migrations/

# 各マイグレーションの内容を確認
cat ./ddl/migrations/*.cypher

# 手動でクエリの妥当性を検証
kuzu ./data/kuzu_test.db
kuzu> -- マイグレーションの内容をコピペして実行
```

### 5. dry-runの簡易実装案

以下のようなラッパースクリプトを作成：

```bash
#!/usr/bin/env bash
# kuzu-migrate-dryrun.sh

echo "=== DRY RUN MODE ==="
echo "以下のマイグレーションが実行される予定です："
echo

# 未適用のマイグレーションを表示
kuzu-migrate status | grep "pending" | while read -r line; do
    migration=$(echo "$line" | awk '{print $1}')
    echo "--- $migration ---"
    cat "./ddl/migrations/$migration"
    echo
done

echo "実際に適用するには: kuzu-migrate apply"
```

## 推奨される安全対策

1. **常にバックアップ**: `snapshot`コマンドでバックアップを取る
2. **テスト環境で検証**: 本番適用前に必ずテスト環境で確認
3. **小さな変更から**: 大きな変更は複数のマイグレーションに分割
4. **レビュープロセス**: マイグレーションファイルのコードレビュー
5. **監視**: 適用後の動作確認とパフォーマンス監視

## 将来的な改善案

### dry-runオプションの実装

```bash
# 理想的な使い方
kuzu-migrate apply --dry-run

# 出力例
DRY RUN MODE - No changes will be made
Would apply: 001_create_users.cypher
Would apply: 002_add_indexes.cypher
Total migrations to apply: 2
```

実装時は以下を表示：
- 適用予定のマイグレーション一覧
- 各マイグレーションの内容（最初の数行）
- 影響を受けるテーブル/インデックス
- 推定実行時間（可能であれば）