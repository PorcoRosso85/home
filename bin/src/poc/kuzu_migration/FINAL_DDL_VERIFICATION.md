# 最終DDL確認とスナップショット戦略

## 問題意識
マイグレーションファイルは差分の積み上げであり、現在のスキーマの全体像が見えにくい。

## 解決策：snapshotコマンドの活用

### 1. 最終DDLの確認

```bash
# 現在のデータベースの完全なスキーマを取得
kuzu-migrate snapshot --version current-schema

# 生成されたschema.cypherを確認
cat ./ddl/snapshots/current-schema/schema.cypher
```

これにより、マイグレーション積算後の**最終的なDDL**が確認できます。

### 2. スキーマのみのエクスポート（データなし）

KuzuDBの公式機能を使用して、スキーマのみを確認：

```cypher
-- KuzuDB CLIで直接実行
EXPORT DATABASE './ddl/schema-only' (schema_only=true);
```

### 3. 差分の可視化

```bash
# マイグレーション履歴の確認
kuzu-migrate status

# 適用済みマイグレーション:
# ✓ 000_initial.cypher
# ✓ 001_add_users.cypher
# ✓ 002_add_indexes.cypher

# 最終スキーマと比較
diff ./ddl/migrations/000_initial.cypher ./ddl/snapshots/current-schema/schema.cypher
```

## スナップショットベースの新しい運用

### 1. 定期的なスキーマ正規化

```bash
# 四半期ごとに実施
# 1. 現在のスキーマをスナップショット
kuzu-migrate snapshot --version v2.0.0-baseline

# 2. 古いマイグレーションファイルをアーカイブ
mkdir -p ./ddl/archive/pre-v2.0.0
mv ./ddl/migrations/*.cypher ./ddl/archive/pre-v2.0.0/

# 3. 新しいベースラインを作成
cp ./ddl/snapshots/v2.0.0-baseline/schema.cypher ./ddl/migrations/000_v2_baseline.cypher

# 4. マイグレーション履歴をリセット（オプション）
```

### 2. CI/CDでの最終DDL確認

```yaml
# .github/workflows/migration-check.yml
steps:
  - name: Apply migrations to test DB
    run: kuzu-migrate --db test.db apply
    
  - name: Export final schema
    run: kuzu-migrate --db test.db snapshot --version ci-check
    
  - name: Validate schema
    run: |
      # スキーマの妥当性チェック
      grep "CREATE NODE TABLE" ./ddl/snapshots/ci-check/schema.cypher
      # 必須テーブルの存在確認など
```

### 3. 開発環境での活用

```bash
#!/bin/bash
# show-current-schema.sh

echo "=== 現在のデータベーススキーマ ==="
echo

# 一時的なスナップショット作成
TEMP_SNAPSHOT="temp-$(date +%s)"
kuzu-migrate snapshot --version "$TEMP_SNAPSHOT"

# スキーマ表示
cat "./ddl/snapshots/$TEMP_SNAPSHOT/schema.cypher"

# 一時ファイル削除
rm -rf "./ddl/snapshots/$TEMP_SNAPSHOT"
```

## メリット

1. **可視性**: 現在のスキーマ全体が一目で確認可能
2. **監査**: 特定時点のスキーマを記録として保存
3. **簡潔性**: 差分の積み重ねではなく、最終形を確認
4. **移行**: 新規環境へのセットアップが簡単

## 推奨される運用フロー

1. **開発時**: マイグレーションファイルで差分管理
2. **レビュー時**: snapshotで最終DDLを確認
3. **リリース時**: バージョン付きsnapshotを作成
4. **定期的**: 古いマイグレーションを統合してベースライン更新

これにより、差分管理の利点を保ちつつ、最終的なスキーマの可視性も確保できます。