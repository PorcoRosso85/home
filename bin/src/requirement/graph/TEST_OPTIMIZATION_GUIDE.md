# テスト高速化ガイド

## 実装済みの最適化

### 1. 並列実行環境（✅ 完了）
- `pytest-xdist`が導入済み（pyproject.toml）
- `pytest.ini`で並列実行設定を定義
- `--dist loadscope`でモジュール単位の並列化

### 2. サブプロセス最適化（✅ 完了）
- `conftest.py`に`run_system_optimized`関数を実装
- タイムアウト機能（デフォルト30秒）
- 確実なプロセスクリーンアップ
- プロセスハング問題の解決

### 3. テストマーカー（✅ 完了）
- `e2e`: E2Eテスト（サブプロセス使用）
- `slow`: 5秒以上かかるテスト
- `integration`: データベース統合テスト
- `unit`: ユニットテスト（高速）

### 4. インメモリDB対応（✅ 準備完了）
- `inmemory_db`フィクスチャを提供
- `:memory:`プレフィックスによる高速化
- 現在は移行待ち（既存テストはファイルベース）

## 使用方法

### 高速テスト実行スクリプト
```bash
# 全テストを並列実行
./run_tests_fast.sh all

# ユニットテストのみ（E2Eスキップ）
./run_tests_fast.sh unit

# E2Eテストのみ
./run_tests_fast.sh e2e

# 特定のテストファイル
./run_tests_fast.sh single test_performance_comparison.py
```

### Pytestコマンド直接実行
```bash
# 並列実行（自動ワーカー数）
nix run .#test -- -n auto

# E2Eテストをスキップ
nix run .#test -- -m "not e2e"

# 特定のテストクラス
nix run .#test -- test_graph_health.py::TestCircularDependencyPrevention
```

## パフォーマンス改善の期待値

1. **並列実行**: 2-4倍高速化（CPUコア数に依存）
2. **E2Eスキップ**: 50-70%時間短縮（開発時）
3. **インメモリDB**: 30-50%高速化（移行後）
4. **サブプロセス最適化**: タイムアウト回避

## 今後の改善提案

### 1. インメモリDB完全移行
現在のファイルベースDBをインメモリに移行：
```python
# Before (file-based)
@pytest.fixture
def temp_db(self):
    with tempfile.TemporaryDirectory() as db_dir:
        # ...

# After (in-memory)
@pytest.fixture 
def temp_db(self, inmemory_db):
    return inmemory_db
```

### 2. プロセスプール実装
頻繁なサブプロセス起動を回避：
```python
@pytest.fixture(scope="session")
def process_pool():
    pool = ProcessPoolExecutor(max_workers=4)
    yield pool
    pool.shutdown()
```

### 3. CI/CD最適化
- 開発時: `pytest -m "not e2e"`
- CI時: 全テスト実行
- マージ前: E2Eテストも含む

## トラブルシューティング

### テストがハングする場合
1. `conftest.py`の`run_system_optimized`を使用
2. タイムアウト値を調整（デフォルト30秒）
3. プロセスが残っていないか確認

### 並列実行でエラーが出る場合
1. `--dist loadscope`オプションを確認
2. テスト間の依存関係を排除
3. フィクスチャのスコープを確認

### パフォーマンスが改善しない場合
1. E2Eテストの割合を確認
2. CPUコア数と`-n`オプションの値を調整
3. インメモリDB移行を検討