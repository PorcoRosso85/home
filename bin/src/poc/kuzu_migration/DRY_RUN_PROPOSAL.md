# Dry-Run機能の提案

## 現状
kuzu-migrateには`--dry-run`オプションが未実装。

## 実装提案

### 1. 簡易的なdry-runスクリプト

```bash
#!/usr/bin/env bash
# kuzu-migrate-dryrun.sh

set -euo pipefail

# 設定読み込み
DDL_DIR="${1:-./ddl}"
DB_PATH="${2:-./data/kuzu.db}"

echo "=== DRY RUN MODE ==="
echo "Database: $DB_PATH"
echo "DDL Directory: $DDL_DIR"
echo

# 1. 現在の状態を確認
echo "Current migration status:"
kuzu-migrate --ddl "$DDL_DIR" --db "$DB_PATH" status | grep -E "(applied|pending)"
echo

# 2. 実行予定のマイグレーションを表示
echo "Migrations to be applied:"
pending_migrations=$(kuzu-migrate --ddl "$DDL_DIR" --db "$DB_PATH" status | grep "pending" | awk '{print $1}')

if [ -z "$pending_migrations" ]; then
    echo "No pending migrations."
    exit 0
fi

# 3. 各マイグレーションの内容を表示
for migration in $pending_migrations; do
    echo
    echo "--- $migration ---"
    # 最初の20行を表示（CREATE文などの重要部分）
    head -20 "$DDL_DIR/migrations/$migration"
    
    # ファイルが長い場合は省略表示
    line_count=$(wc -l < "$DDL_DIR/migrations/$migration")
    if [ "$line_count" -gt 20 ]; then
        echo "... ($(($line_count - 20)) more lines)"
    fi
done

echo
echo "=== END DRY RUN ==="
echo "To apply these migrations, run: kuzu-migrate apply"
```

### 2. kuzu-migrate本体への組み込み案

```bash
# src/kuzu-migrate.shへの追加案

apply_command() {
    local ddl_dir="$1"
    local db_path="$2"
    local dry_run=false
    
    # 引数解析
    shift 2
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                dry_run=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ "$dry_run" = true ]; then
        echo "=== DRY RUN MODE - No changes will be made ==="
        echo
    fi
    
    # マイグレーション検索（既存のコード）
    local pending_count=0
    for migration_file in "${migration_files[@]}"; do
        # ... 既存のチェックロジック ...
        
        if [ "$dry_run" = true ]; then
            echo "Would apply: $(basename "$migration_file")"
            echo "First 10 lines:"
            head -10 "$migration_file" | sed 's/^/  /'
            echo
        else
            # 実際の適用処理（既存のコード）
        fi
        
        ((pending_count++))
    done
    
    if [ "$dry_run" = true ]; then
        echo "Total migrations to apply: $pending_count"
        echo "Run without --dry-run to apply these migrations."
    fi
}
```

### 3. 高度なdry-run実装（将来案）

```bash
# 仮想環境でのシミュレーション
dry_run_advanced() {
    local ddl_dir="$1"
    local db_path="$2"
    
    # 1. メモリ内DBまたは一時DBを作成
    local temp_db="/tmp/kuzu_dryrun_$(date +%s).db"
    
    # 2. 現在のスキーマをコピー
    kuzu-migrate --db "$db_path" snapshot --version dryrun-temp
    kuzu "$temp_db" < "./ddl/snapshots/dryrun-temp/schema.cypher"
    
    # 3. マイグレーションを仮想環境で実行
    echo "Simulating migrations on temporary database..."
    if kuzu-migrate --ddl "$ddl_dir" --db "$temp_db" apply; then
        echo "✓ All migrations would succeed"
        
        # 4. 変更の要約を表示
        echo
        echo "Schema changes summary:"
        diff -u \
            <(kuzu-migrate --db "$db_path" snapshot --version before 2>/dev/null && cat ./ddl/snapshots/before/schema.cypher) \
            <(kuzu-migrate --db "$temp_db" snapshot --version after 2>/dev/null && cat ./ddl/snapshots/after/schema.cypher) \
            || true
    else
        echo "✗ Migration would fail"
    fi
    
    # 5. クリーンアップ
    rm -rf "$temp_db"
    rm -rf "./ddl/snapshots/dryrun-temp"
    rm -rf "./ddl/snapshots/before"
    rm -rf "./ddl/snapshots/after"
}
```

## 推奨実装順序

1. **Phase 1**: 簡易スクリプトとして別ファイルで提供
2. **Phase 2**: `--dry-run`フラグをapplyコマンドに追加
3. **Phase 3**: 仮想環境での完全なシミュレーション

## 期待される効果

- **安全性向上**: 実行前に変更内容を確認
- **レビュー促進**: チーム内での変更確認が容易に
- **エラー予防**: 構文エラーや論理エラーの事前発見
- **計画性向上**: 実行時間の見積もりが可能に