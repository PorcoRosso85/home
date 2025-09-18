# 根本的な問題解決策

## 解決可能な根本問題

### 1. データベース初期化の改善

**現在の問題**：
- KuzuDBがファイル形式かディレクトリ形式か不明確
- 初期化処理でのハング

**根本的解決策**：
```bash
# データベース初期化を明示的に分離
init_database() {
    local db_path="$1"
    
    # KuzuDBの形式を自動判定
    if [[ ! -e "$db_path" ]]; then
        # 新規作成の場合
        echo "Creating new KuzuDB at: $db_path"
        mkdir -p "$(dirname "$db_path")"
        
        # KuzuDB CLIで空のDBを作成
        echo "CREATE NODE TABLE IF NOT EXISTS _dummy();" | timeout 10 kuzu "$db_path"
        if [[ $? -eq 0 ]]; then
            # 作成成功後、ダミーテーブルを削除
            echo "DROP TABLE _dummy;" | kuzu "$db_path"
        fi
    fi
}
```

### 2. 非同期実行とプログレス表示

**現在の問題**：
- 長時間の処理で応答がない
- ユーザーが進捗を確認できない

**根本的解決策**：
```bash
# プログレスバー付き実行
apply_with_progress() {
    local migration_file="$1"
    local db_path="$2"
    
    # バックグラウンドで実行
    (
        kuzu "$db_path" < "$migration_file" 2>&1
        echo $? > /tmp/kuzu_exit_code
    ) &
    
    local pid=$!
    local spinner=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local i=0
    
    # プログレス表示
    while kill -0 $pid 2>/dev/null; do
        printf "\r${spinner[$i]} Applying migration... "
        i=$(( (i + 1) % ${#spinner[@]} ))
        sleep 0.1
    done
    
    wait $pid
    local exit_code=$(cat /tmp/kuzu_exit_code)
    rm -f /tmp/kuzu_exit_code
    
    return $exit_code
}
```

### 3. Python実装への段階的移行

**現在の問題**：
- Bash実装の限界（エラーハンドリング、並行処理）
- デバッグの困難さ

**根本的解決策**：
```python
# kuzu_migrate.py - コア機能をPythonで再実装
import kuzu
import asyncio
from pathlib import Path
from typing import Optional
import click

class KuzuMigrator:
    def __init__(self, db_path: Path, ddl_path: Path):
        self.db_path = db_path
        self.ddl_path = ddl_path
        self.conn: Optional[kuzu.Connection] = None
    
    def connect(self):
        """データベースへの接続を確立"""
        try:
            # ファイルでもディレクトリでも対応
            self.db = kuzu.Database(str(self.db_path))
            self.conn = kuzu.Connection(self.db)
        except Exception as e:
            # より詳細なエラー情報
            raise ConnectionError(f"Failed to connect: {e}")
    
    async def apply_migration_async(self, migration_file: Path):
        """非同期でマイグレーションを適用"""
        query = migration_file.read_text()
        
        # タイムアウト付き実行
        try:
            await asyncio.wait_for(
                self._execute_query(query),
                timeout=300.0  # 5分
            )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Migration {migration_file.name} timed out")
    
    def check_database_format(self):
        """データベース形式を自動判定"""
        if self.db_path.is_dir():
            return "directory"
        elif self.db_path.is_file():
            return "file"
        else:
            return "not_exists"
```

### 4. 互換性レイヤーの実装

**現在の問題**：
- KuzuDBバージョン間の差異
- 将来的な破壊的変更への対応

**根本的解決策**：
```python
# version_compat.py
class KuzuVersionAdapter:
    def __init__(self, version: str):
        self.version = version
        self.major, self.minor, self.patch = map(int, version.split('.'))
    
    def get_create_table_syntax(self) -> str:
        """バージョンに応じた構文を返す"""
        if self.major == 0 and self.minor <= 11:
            # v0.11.x以前の構文
            return "CREATE NODE TABLE"
        else:
            # 新しい構文（仮）
            return "CREATE TABLE"
    
    def adapt_query(self, query: str) -> str:
        """クエリをバージョンに合わせて変換"""
        # バージョン固有の変換ルールを適用
        return query
```

### 5. dry-runの完全実装

**現在の問題**：
- 実行前に結果を予測できない
- リスクの高い操作

**根本的解決策**：
```python
def dry_run(self, migrations: List[Path]) -> DryRunResult:
    """実際には実行せずに結果を予測"""
    results = []
    
    # トランザクション内でシミュレート
    with self.conn.begin() as tx:
        for migration in migrations:
            try:
                # 実行はするがロールバック
                self.conn.execute(migration.read_text())
                results.append({
                    'file': migration.name,
                    'status': 'would_succeed',
                    'changes': self._analyze_changes()
                })
            except Exception as e:
                results.append({
                    'file': migration.name,
                    'status': 'would_fail',
                    'error': str(e)
                })
        
        # 最後にロールバック
        tx.rollback()
    
    return DryRunResult(results)
```

## 実装優先順位

1. **即座に実装可能**（Bashパッチ）
   - ✅ タイムアウト追加
   - ✅ データベース形式の柔軟な認識
   - プログレス表示

2. **短期的改善**（Python部分実装）
   - エラーハンドリングの改善
   - 非同期実行
   - dry-run機能

3. **長期的移行**（完全なPython実装）
   - 互換性レイヤー
   - プラグインシステム
   - Web UI

## 結論

根本的な問題は**すべて解決可能**です。段階的なアプローチで：
1. まず緊急の問題をBashパッチで解決
2. 次にコア機能をPythonで再実装
3. 最終的に完全なPythonベースのツールへ移行

これにより、現在の問題を解決しつつ、将来的な拡張性も確保できます。