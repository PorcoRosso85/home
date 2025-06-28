# analyze-jsonl

分散されたディレクトリにあるJSONLファイルを集約してDuckDBでSQLクエリを実行するツール

## インストール

```bash
# uvを使用
cd /home/nixos/bin/src/poc/analyze_jsonl
export LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/
uv sync
```

## 使用例

### Python API

```python
# 環境変数設定が必要
import os
os.environ['LD_LIBRARY_PATH'] = '/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/'

from core import create_analyzer

# 単一ディレクトリの分析
analyzer = create_analyzer(['/logs/app1'])
analyzer.register_jsonl_files('/logs/app1', '*.jsonl', 'app1_logs')
result = analyzer.query("SELECT COUNT(*) as total FROM app1_logs")
if result['ok']:
    print(f"Total records: {result['data']['rows'][0][0]}")

# 複数ディレクトリの統合分析
analyzer = create_analyzer(['/logs/app1', '/logs/app2'])
analyzer.register_jsonl_files('/logs/app1', '*.jsonl', 'app1')
analyzer.register_jsonl_files('/logs/app2', '*.jsonl', 'app2')
analyzer.create_unified_view('all_logs')

# 統合ビューに対するクエリ
result = analyzer.query("""
    SELECT 
        source,
        COUNT(*) as count,
        MIN(timestamp) as first_log,
        MAX(timestamp) as last_log
    FROM all_logs
    GROUP BY source
""")
```

### テスト実行

```bash
# 全テスト実行
export LD_LIBRARY_PATH=/nix/store/l7d6vwajpfvgsd3j4cr25imd1mzb7d1d-gcc-14.3.0-lib/lib/
uv run pytest -v

# 個別ファイルのテスト
uv run pytest -v core.py
uv run pytest -v adapters.py
```

## アーキテクチャ

CONVENTION.yaml準拠のモジュール設計：

- `analyzer_types.py` - 型定義（TypedDict使用）
- `core.py` - ビジネスロジック（in-sourceテスト含む）
- `adapters.py` - 外部依存（DuckDB、ファイルシステム）
- `mod.py` - エクスポート用インターフェース
- `test_integration.py` - 統合テスト

## TDD開発

t-wada式TDDサイクルで開発：

1. **RED**: 失敗するテストを先に書く
2. **GREEN**: テストを通す最小限の実装
3. **REFACTOR**: テストを維持したままコード改善

## 設計原則

- エラーを値として扱う（`Union[Success, Error]`パターン）
- 純粋関数を優先
- 依存性の明示的な注入
- in-sourceテストによる仕様の明確化