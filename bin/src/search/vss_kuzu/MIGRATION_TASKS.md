# VSS_KUZU 移行タスク

## 概要
requirement/graphから移行要請されたテストの受け入れタスクです。
これらは独立して並行作業可能です。

## タスク一覧

### Task 1: 類似度計算の検証テスト
**ファイル**: `tests/test_similarity_calculation.py`（新規作成）
**元ファイル参考**: requirement/graph/test_vss_issue.py

**実装すべきテスト**:
```python
def test_similarity_score_not_zero_for_similar_texts():
    """類似テキストの類似度スコアが0.0にならないことを確認"""
    # 日本語テキストでのテスト必須
    
def test_exact_match_returns_high_similarity():
    """完全一致テキストが高い類似度を返すことを確認"""
    
def test_semantic_similarity_works_correctly():
    """意味的に類似したテキストが適切にランク付けされることを確認"""
```

**完了条件**:
- [ ] 類似度が適切に計算される
- [ ] 日本語テキストで正常動作
- [ ] エッジケースのカバー

### Task 2: 接続管理の検証テスト
**ファイル**: `tests/test_connection_handling.py`（新規作成）
**元ファイル参考**: requirement/graph/test_vss_with_connection.py

**実装すべきテスト**:
```python
def test_persistent_database_connection():
    """永続的データベースでの接続が正常に管理されることを確認"""
    
def test_multiple_connections_work_independently():
    """複数の接続が独立して動作することを確認"""
    
def test_connection_cleanup_on_close():
    """close()メソッドでリソースが適切に解放されることを確認"""
```

**完了条件**:
- [ ] 接続のライフサイクル管理
- [ ] リソースリークがない
- [ ] 並行アクセスの安全性

### Task 3: エラーハンドリングの強化
**ファイル**: `tests/test_error_handling.py`（既存ファイルに追加または新規）

**実装すべきテスト**:
```python
def test_vector_extension_missing_error():
    """VECTOR拡張が無い場合の明確なエラーメッセージ"""
    
def test_invalid_parameters_rejected():
    """不正なパラメータが適切に拒否される"""
    
def test_resource_exhaustion_handling():
    """リソース不足時のgraceful degradation"""
```

**完了条件**:
- [ ] すべてのエラーケースで明確なメッセージ
- [ ] エラー時もシステムが安定
- [ ] 回復可能なエラーは回復する

### Task 4: SearchAdapter互換機能の実装【重要】
**ファイル**: `tests/test_search_adapter_compatibility.py`（新規作成）
**元ファイル参考**: requirement/graph/test_search_adapter.py

**実装すべきテスト**:
```python
def test_add_to_index_functionality():
    """add_to_indexに相当する機能が正常動作"""
    # requirement形式のドキュメント追加
    
def test_search_similar_functionality():
    """search_similarに相当する機能の完全テスト"""
    # k件の類似文書取得
    # スコアの妥当性確認
    
def test_empty_index_search():
    """空のインデックスでの検索が適切に処理される"""
```

**完了条件**:
- [ ] requirement/graphのSearchAdapterが依存する機能をカバー
- [ ] 同じ入力で同じ出力が得られる
- [ ] エッジケースも網羅

## 作業の進め方

1. **並行作業可能**: 各タスクは独立しているため、複数人で同時作業可能
2. **既存テストの活用**: test_unified_api.pyを参考に、同じスタイルで実装
3. **規約準拠**: 
   - print文禁止（構造化ログを使用）
   - テストファイルは対象コードと同じディレクトリに配置
   - 関数名で仕様を表現

## 受け入れ基準

各タスク完了時:
1. `nix run .#test`が通る
2. 新規テストがすべてPASS
3. 既存テストに影響なし
4. カバレッジが低下しない

## 質問・相談

不明点があれば requirement/graph/MIGRATION_REQUEST.md を参照してください。