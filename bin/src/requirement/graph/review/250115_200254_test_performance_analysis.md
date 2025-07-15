# 統合テストのパフォーマンス分析と改善提案

**作成日:** 2025年01月15日
**分析者:** Claude

## 1. 現状分析

### テストファイルの規模と実行負荷

| ファイル名 | 行数 | 負荷レベル | 主な要因 |
|-----------|------|-----------|---------|
| test_requirement_management.py | 309 | 最重 | subprocess起動、tempfile DB作成 |
| test_search_integration.py | 213 | 重 | Search service初期化、embedding計算 |
| test_duplicate_detection.py | 199 | 中 | 複数の類似度計算 |
| test_hybrid_search_spec.py | 191 | 中 | ハイブリッド検索 |
| test_output_contract.py | 157 | 軽 | 単純な入出力検証 |

### 重い処理の詳細分析

#### 1. test_requirement_management.py（最重）
```python
def run_system(input_data, db_path=None):
    result = subprocess.run(
        [python_cmd, "-m", "requirement.graph"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
        cwd=project_root
    )
```

**問題点:**
- 各テストケースで新規Pythonプロセスを起動
- 毎回tempfileでDBを作成・削除
- スキーマ適用処理が各テストで実行
- プロセス間通信のオーバーヘッド

#### 2. test_search_integration.py（重）
**問題点:**
- Search serviceの初期化（言語モデルのロード）
- ベクトル化処理（256次元embedding生成）
- 複数要件での重複検出計算

#### 3. test_duplicate_detection.py（中程度）
**問題点:**
- 複数の類似度計算（VSS）
- Search serviceの繰り返し初期化

## 2. パフォーマンスへの影響

### 開発者体験への影響
- **TDDサイクルの遅延**: 1回のテスト実行に数秒〜数十秒
- **フィードバックループの劣化**: 即座な確認ができない
- **開発効率の低下**: テスト実行を避ける傾向

### CI/CDへの影響
- **ビルド時間の増大**: 全テスト実行に数分
- **リソース消費**: CPU/メモリの過剰使用
- **並列実行の制限**: プロセス起動による競合

## 3. 改善提案

### 短期的改善（すぐに実装可能）

#### 1. テストの分類とマーキング
```python
# 重いテストにマークを付ける
@pytest.mark.slow
def test_full_integration_with_subprocess():
    pass

# 実行時の使い分け
# 開発時: pytest -m "not slow"
# CI時: pytest
```

#### 2. セッションスコープのfixture活用
```python
@pytest.fixture(scope="session")
def shared_db():
    """セッション全体で共有するDB"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        # スキーマ適用は1回のみ
        apply_schema(db_path)
        yield db_path
```

#### 3. 並列実行の導入
```bash
# pytest-xdistを使用
pytest -n auto  # CPU数に応じて自動並列化
```

### 中期的改善（設計変更を伴う）

#### 1. インプロセステストモードの追加
```python
# 直接関数を呼び出すテストモード
def test_requirement_creation_inprocess():
    # subprocessを使わずに直接実行
    from requirement.graph.application import process_request
    result = process_request({...})
```

#### 2. Search serviceのモック化
```python
@pytest.fixture
def mock_search_service():
    """軽量なモックサービス"""
    return MockSearchService(
        # 事前計算したembeddingを使用
        precomputed_embeddings={...}
    )
```

#### 3. インメモリDBの活用
```python
# KuzuDBのインメモリモード（可能な場合）
repository = create_repository(":memory:")
```

### 長期的改善（アーキテクチャ変更）

#### 1. テスト専用の軽量エントリポイント
```python
# requirement.graph.test_runner
# プロセス起動オーバーヘッドを削減
```

#### 2. 段階的な統合テスト
- **Unit層**: 純粋関数のテスト（最速）
- **Integration層**: DB接続を含むテスト
- **E2E層**: 完全な統合テスト（最遅）

## 4. 実装優先順位

1. **即実施**: テストのマーキング（@pytest.mark.slow）
2. **1週間以内**: セッションfixture導入
3. **1ヶ月以内**: 並列実行環境の整備
4. **3ヶ月以内**: インプロセステストモードの実装

## 5. 期待される効果

### 定量的効果
- **開発時テスト**: 10秒 → 2秒（80%削減）
- **CI全体実行**: 5分 → 1分（80%削減）
- **TDDサイクル**: 即座なフィードバック

### 定性的効果
- **開発者満足度向上**: ストレスフリーなTDD
- **品質向上**: テスト実行頻度の増加
- **生産性向上**: 待ち時間の削減

## 6. リスクと対策

### リスク
- **テストの独立性低下**: 共有リソースによる相互影響
- **デバッグの困難化**: 並列実行時のエラー特定

### 対策
- **適切な初期化/クリーンアップ**: 各テストの独立性確保
- **ログ出力の強化**: 並列実行時も追跡可能に

## 7. 結論

現在の統合テストは、特に`test_requirement_management.py`において、プロセス起動のオーバーヘッドが大きな問題となっている。短期的にはテストのマーキングとfixture改善で対応し、中長期的にはアーキテクチャレベルでの最適化を行うことで、開発効率とテスト品質の両立を図ることができる。