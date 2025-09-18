# FTS_KUZU 移行タスク

## 概要
requirement/graphから移行要請されたテストの受け入れタスクです。
主にSearchAdapterのFTS部分のテストを引き受けます。

## タスク一覧

### Task 1: FTS初期化とエラーハンドリング
**ファイル**: `tests/test_initialization.py`（新規作成）
**元ファイル参考**: requirement/graph/test_search_adapter.py（FTS部分）

**実装すべきテスト**:
```python
def test_fts_initialization_with_various_configs():
    """様々な設定でのFTS初期化が成功することを確認"""
    
def test_fts_initialization_error_cases():
    """初期化失敗時の適切なエラーハンドリング"""
    
def test_fts_module_availability_check():
    """FTSモジュールの利用可能性チェックが正確"""
```

**完了条件**:
- [ ] 各種設定での初期化成功
- [ ] エラー時の明確なメッセージ
- [ ] 初期化の冪等性

### Task 2: 検索クエリの検証
**ファイル**: `tests/test_search_queries.py`（新規作成）

**実装すべきテスト**:
```python
def test_japanese_text_search():
    """日本語テキストの全文検索が正常動作"""
    
def test_special_characters_handling():
    """特殊文字を含むクエリの適切な処理"""
    
def test_empty_and_null_queries():
    """空クエリやnullの適切な処理"""
```

**完了条件**:
- [ ] 日本語検索の正常動作
- [ ] エッジケースの処理
- [ ] SQLインジェクション対策

### Task 3: インデックス管理
**ファイル**: `tests/test_index_management.py`（新規作成）

**実装すべきテスト**:
```python
def test_incremental_indexing():
    """インクリメンタルなインデックス追加"""
    
def test_large_document_indexing():
    """大量ドキュメントのインデックス作成"""
    
def test_index_consistency():
    """インデックスの一貫性保証"""
```

**完了条件**:
- [ ] インデックス操作の信頼性
- [ ] パフォーマンスの確認
- [ ] 同時実行時の安全性

### Task 4: SearchAdapter互換機能の実装【重要】
**ファイル**: `tests/test_search_adapter_compatibility.py`（新規作成）
**元ファイル参考**: requirement/graph/test_search_adapter.py

**実装すべきテスト**:
```python
def test_add_to_index_functionality():
    """add_to_indexに相当する機能が正常動作"""
    # requirement形式（id, title, description）のドキュメント追加
    
def test_search_hybrid_functionality():
    """search_hybridに相当する機能のテスト"""
    # キーワード検索の精度
    # 結果のランキング
    
def test_special_characters_in_search():
    """特殊文字を含む検索クエリの処理"""
    # SQLインジェクション対策の確認
```

**完了条件**:
- [ ] requirement/graphのSearchAdapterが依存するFTS機能をカバー
- [ ] キーワード検索の精度保証
- [ ] セキュリティ面の考慮

## 既存テストとの統合

1. **test_unified_api.py**: プロトコル準拠は既に検証済み
2. **新規テスト**: 実装詳細とエラーケースに焦点

## 作業の優先順位

1. Task 1（初期化）- 基盤となる部分
2. Task 2（検索）- ユーザー影響が大きい
3. Task 3（インデックス）- 性能関連

## 並行作業の調整

- vss_kuzuチームとは独立して作業可能
- requirement/graphチームへの依存なし
- 完了後、requirement/graphに通知

## 完了確認

```bash
# 各タスク完了時
nix run .#test

# 全タスク完了時
nix run .#test -- --cov --cov-report=html
```

カバレッジレポートで新規テストの網羅性を確認してください。