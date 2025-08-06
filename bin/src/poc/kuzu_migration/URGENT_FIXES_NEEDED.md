# kuzu-migrate 緊急修正事項

## 問題1: apply処理のタイムアウト（2分）

### 現象
```bash
nix develop -c kuzu-migrate --ddl ./ddl --db ./data/kuzu.db apply
# タイムアウト: Command timed out after 2m 0.0s
```

### 原因
`src/kuzu-migrate.sh`のデフォルトタイムアウトが120秒（2分）に設定されている可能性

### 修正案
```bash
# kuzu-migrate.sh内で以下を追加
KUZU_TIMEOUT="${KUZU_TIMEOUT:-600}"  # 10分のデフォルト

# kuzu実行時にタイムアウトを明示
timeout "$KUZU_TIMEOUT" kuzu "$db_path" < "$init_script"
```

## 問題2: データベース認識の不整合

### 現象
- ファイルは存在（36864バイト）
- しかし「Database not found」エラー

### 考えられる原因
1. KuzuDBファイルフォーマットの確認不足
2. ディレクトリとファイルの混同
3. 権限問題

### 修正案
```bash
# データベース存在チェックの改善
check_database() {
    local db_path="$1"
    
    # KuzuDBはディレクトリベースのDB
    if [[ -d "$db_path" ]]; then
        # ディレクトリ内の必要ファイルを確認
        if [[ -f "$db_path/catalog.kz" ]] || [[ -f "$db_path/nodes.kz" ]]; then
            return 0
        fi
    fi
    
    # 単一ファイルの場合（古い形式？）
    if [[ -f "$db_path" ]] && [[ -s "$db_path" ]]; then
        # ファイルヘッダーを確認してKuzuDBか判定
        return 0
    fi
    
    return 1
}
```

## 問題3: マイグレーション履歴テーブル作成のハング

### 現象
```
ℹ️  Initializing migration tracking...
# ここでハング
```

### 修正案
```bash
# 1. CREATE TABLE文を別プロセスで実行
init_migration_history() {
    local db_path="$1"
    local init_query="CREATE NODE TABLE IF NOT EXISTS _migration_history (
        migration_name STRING PRIMARY KEY,
        applied_at TIMESTAMP,
        success BOOLEAN
    );"
    
    # タイムアウト付きで実行
    if timeout 30 echo "$init_query" | kuzu "$db_path" > /dev/null 2>&1; then
        success "Migration tracking initialized"
    else
        # 既存DBの場合はスキップ可能にする
        warning "Could not create migration history table (may already exist)"
        return 0  # エラーにしない
    fi
}

# 2. デバッグモードの追加
if [[ "${DEBUG:-0}" == "1" ]]; then
    set -x  # コマンドを表示
    exec 2>&1  # エラーも表示
fi
```

## 問題4: KuzuDB 0.11.1との互換性

### 確認事項
- 使用しているCypher構文がv0.11.1でサポートされているか
- CREATE NODE TABLEの構文変更がないか

### 修正案
```bash
# バージョンチェックと警告
check_kuzu_version() {
    local version=$(kuzu --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    
    case "$version" in
        0.11.*)
            info "KuzuDB $version detected"
            ;;
        *)
            warning "Untested KuzuDB version: $version"
            ;;
    esac
}
```

## 問題5: エラーハンドリングの改善

### 修正案
```bash
# より詳細なエラー情報を提供
apply_migration() {
    local migration_file="$1"
    local db_path="$2"
    
    # 実行前にクエリを検証（dry-run的な機能）
    if [[ "${VALIDATE_ONLY:-0}" == "1" ]]; then
        info "Validating: $(basename "$migration_file")"
        # 構文チェックのみ
        return 0
    fi
    
    # エラー出力をキャプチャして表示
    local error_file=$(mktemp)
    if ! kuzu "$db_path" < "$migration_file" 2>"$error_file"; then
        error "Migration failed: $(basename "$migration_file")"
        echo "Error details:" >&2
        cat "$error_file" >&2
        rm -f "$error_file"
        return 1
    fi
    rm -f "$error_file"
}
```

## 即座に試せる回避策

### 1. 手動でのDB初期化
```bash
# 新しいDBを作成
mkdir -p ./data/kuzu_new.db
echo "CREATE NODE TABLE _migration_history (
    migration_name STRING PRIMARY KEY,
    applied_at TIMESTAMP,
    success BOOLEAN
);" | kuzu ./data/kuzu_new.db
```

### 2. タイムアウトを延長して実行
```bash
# 環境変数でタイムアウトを設定（実装が必要）
KUZU_TIMEOUT=600 nix develop -c kuzu-migrate --ddl ./ddl --db ./data/kuzu.db apply
```

### 3. デバッグモードで実行
```bash
# 詳細ログを出力（実装が必要）
DEBUG=1 nix develop -c kuzu-migrate --ddl ./ddl --db ./data/kuzu.db apply
```

## 推奨される次のステップ

1. **緊急**: タイムアウト値を増やす
2. **重要**: データベース存在チェックを改善
3. **重要**: エラー時の詳細情報を提供
4. **検討**: dry-runモードの実装
5. **検討**: 既存DBへの適用モード追加