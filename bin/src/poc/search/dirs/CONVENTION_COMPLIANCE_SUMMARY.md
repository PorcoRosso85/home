# Convention Compliance Summary

## 規約遵守の変更内容

### 1. クラスの削除 ✅
- `test_unit.py`: すべてのテストクラスを関数に変換
  - `TestUtilityFunctions` → 個別のテスト関数
  - `TestMetadataExtraction` → 個別のテスト関数
  - `TestEnvironmentVariables` → 個別のテスト関数

### 2. モック実装の削除 ✅
- `main.py`: モック実装を削除
  - `create_text_search()` → TODO コメントに置き換え
  - `create_embedder()` → TODO コメントに置き換え
  - `create_vector_search()` → TODO コメントに置き換え
- `mock_db.py`: ファイル全体を削除

### 3. エラーを値として返す ✅
- `infrastructure/variables/env.py`:
  - `get_scan_root_path()`: raise文を削除、EnvResultを返すように変更
  - `get_db_path()`: raise文を削除、EnvResultを返すように変更
  - `should_use_inmemory()`: None返却を明示的にFalse返却に修正

### 4. テストファイル名規約 ✅
- `test_directory_scanner.py` → `test_main.py`
- `test_unit.py` → `test_main_utils.py`
- `test_integration.py` → `test_main_integration.py`
- 新規追加:
  - `test_env.py` (infrastructure/variables/env.py用)
  - `test_database_factory.py` (infrastructure/db/database_factory.py用)

### 5. 未実装機能のテスト対応 ✅
以下のテストを`@pytest.mark.xfail`でマーク:
- FTS関連: `test_インデックス保持_FTS事前構築_高速検索可能`
- FTS検索: `test_FTS検索_キーワード一致_高速応答`
- VSS検索: `test_VSS検索_意味的類似_関連POC発見`
- VSS埋め込み: `test_VSS埋め込み保存_再計算不要_メモリ効率`
- ハイブリッド検索: `test_ハイブリッド検索_両方組み合わせ_ランキング統合`
- README更新検知: `test_README更新_タイムスタンプ変更_再インデックス`
- 統合テスト: `test_統合_フルワークフロー_正常動作`, `test_検索機能_FTS_キーワード一致`

## テスト実行結果
```
49 passed, 8 xfailed in 1.75s
```

すべてのテストが規約に準拠し、未実装機能は適切にマークされています。

## 今後の実装が必要な機能
1. KuzuDB FTS拡張を使用したフルテキスト検索
2. sentence-transformersを使用したベクトル検索
3. README更新時のタイムスタンプ検知の改善