# VSS/FTS初期化繰り返し問題の改善案

## 現状の問題点

1. **初期化コストの内訳**（TEST_PERFORMANCE_ANALYSIS.mdより）
   - VECTOR拡張のロード: ~0.5秒/回
   - Embeddingモデル初期化: ~2-3秒（初回）
   - E2Eテスト43個 × 初期化 = 100秒以上のオーバーヘッド

2. **根本原因**
   - 各テストが独立してSearchAdapterを初期化
   - subprocess起動によるPythonプロセス全体の再初期化
   - 共有リソース（VECTOR拡張、モデル）の再利用なし

## 改善案

### 1. セッションレベルFixture（短期・推奨）

```python
# conftest.py に追加
@pytest.fixture(scope="session")
def shared_vss_connection():
    """セッション全体で共有されるVSS接続"""
    import kuzu
    from vss_kuzu import create_vss
    
    # メモリ内DBで高速化
    conn = kuzu.Connection(":memory:")
    conn.execute("INSTALL vector;")
    conn.execute("LOAD EXTENSION vector;")
    
    vss = create_vss(db_path=":memory:", existing_connection=conn)
    yield vss, conn
    
    # セッション終了時にクリーンアップ
    conn.close()

@pytest.fixture
def search_adapter(shared_vss_connection):
    """各テスト用のSearchAdapter（共有接続を利用）"""
    vss, conn = shared_vss_connection
    # テストごとにデータはクリア
    conn.execute("MATCH (n) DETACH DELETE n")
    
    from application.search_adapter import SearchAdapter
    adapter = SearchAdapter(":memory:", repository_connection=conn)
    return adapter
```

**メリット**：
- 初期化は1回のみ（100秒→3秒）
- 実装が簡単
- テストの独立性は維持

**デメリット**：
- E2Eテスト（subprocess）には効果なし
- 並列実行時の競合に注意必要

### 2. プロセスプール（中期）

```python
# process_pool_runner.py
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

class VSSProcessPool:
    def __init__(self, num_workers=4):
        self.executor = ProcessPoolExecutor(
            max_workers=num_workers,
            initializer=self._init_worker
        )
    
    def _init_worker(self):
        """ワーカープロセスの初期化（1回のみ）"""
        global _vss_service
        from vss_kuzu import create_vss
        _vss_service = create_vss(db_path=":memory:")
    
    def run_test(self, test_func, *args):
        """事前初期化されたワーカーでテスト実行"""
        return self.executor.submit(test_func, *args)
```

**メリット**：
- E2Eテストも高速化可能
- 並列実行と相性良好

**デメリット**：
- 実装が複雑
- デバッグが困難

### 3. 軽量モックの活用（短期）

```python
# 開発時用の軽量モック
class LightweightVSSMock:
    def __init__(self):
        self.data = {}
    
    def index(self, documents):
        # 単純なハッシュベースの疑似類似度
        for doc in documents:
            self.data[doc["id"]] = doc
        return {"ok": True}
    
    def search(self, query, limit=10):
        # 単純な文字列マッチング
        results = []
        for id, doc in self.data.items():
            if query.lower() in doc["content"].lower():
                results.append({
                    "id": id,
                    "content": doc["content"],
                    "score": 0.8  # 固定スコア
                })
        return {"ok": True, "results": results[:limit]}

# pytest.ini で環境変数設定
# VSS_USE_MOCK=1 nix run .#test -- -m "not e2e"
```

**メリット**：
- 開発時のテストが超高速（0.01秒/テスト）
- 実装が簡単

**デメリット**：
- 実際のVSS動作と異なる
- E2E/統合テストには使えない

### 4. Docker/コンテナベース（長期）

```yaml
# docker-compose.test.yml
services:
  vss-server:
    image: vss-service:latest
    ports:
      - "8080:8080"
    environment:
      - PRELOAD_MODEL=true
      - CACHE_SIZE=1GB
  
  test-runner:
    depends_on:
      - vss-server
    environment:
      - VSS_ENDPOINT=http://vss-server:8080
```

**メリット**：
- 完全な分離とスケーラビリティ
- CI/CDパイプラインと統合しやすい

**デメリット**：
- インフラ変更が必要
- ローカル開発が複雑化

## 推奨実装順序

### Phase 1: 即座に実装可能（1日）
1. **セッションFixture導入**
   - conftest.py更新
   - 既存テストの修正は最小限
   - 期待効果: 単体/統合テストが5倍高速化

2. **テストマーカーの活用強化**
   ```bash
   # 開発時: VSSなしの高速テスト
   nix run .#test -- -m "not vss_required"
   ```

### Phase 2: 1週間で実装（アーキテクチャ小変更）
1. **接続プーリング実装**
   ```python
   class ConnectionPool:
       def __init__(self, size=5):
           self.connections = queue.Queue(maxsize=size)
           for _ in range(size):
               conn = self._create_connection()
               self.connections.put(conn)
   ```

2. **キャッシュレイヤー追加**
   - Embedding結果のLRUキャッシュ
   - よく使うクエリの結果キャッシュ

### Phase 3: 1ヶ月で実装（アーキテクチャ変更）
1. **E2E実行方式の見直し**
   - subprocess → Python関数呼び出し
   - CLIテストとビジネスロジックテストの分離

2. **サービス分離**
   - VSS/FTSを別プロセス/サービス化
   - gRPC/REST APIでの通信

## 具体的な次のステップ

1. **今すぐ実行可能**:
   ```bash
   # HOW_TO_TEST.mdに追加
   # 超高速開発モード（VSS/FTS除外）
   nix run .#test -- -m "not vss_required and not fts_required"
   ```

2. **conftest.py改善** (PR作成):
   - セッションスコープfixture追加
   - 環境変数でモック切り替え

3. **pytest-xdist設定最適化**:
   ```ini
   # pytest.ini更新
   [tool:pytest]
   addopts = 
       # loadgroup: VSSテストを同一ワーカーに
       --dist loadgroup
       # 事前にVSS初期化
       --setup-show
   ```

これらの改善により、開発時のテスト実行時間を**21分→3分**に短縮可能です。