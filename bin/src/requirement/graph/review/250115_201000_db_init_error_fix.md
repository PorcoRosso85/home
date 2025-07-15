# DB初期化エラーの原因と修正

**作成日:** 2025年01月15日 20:10:00
**解決者:** Claude

## 1. エラーの症状

以下のテストファイルがすべてDB初期化エラーで失敗：
- test_duplicate_detection.py
- test_append_only_versioning.py
- test_version_management.py
- test_destructive_operations_prevention.py
- test_requirement_management.py
- test_search_integration.py
- test_hybrid_search_spec.py

## 2. 原因

`infrastructure/apply_ddl_schema.py`のスキーマファイルパスが間違っていた：

```python
# 誤り（修正前）
schema_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "ddl",  # これは ../ddl/ を指している
    "migrations",
    "3.4.0_search_integration.cypher"
)

# 正しい（修正後）
schema_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",  # 追加: requirement/graph/ ディレクトリに戻る
    "ddl",
    "migrations",
    "3.4.0_search_integration.cypher"
)
```

### ディレクトリ構造
```
requirement/graph/
├── infrastructure/
│   └── apply_ddl_schema.py  # ここから
├── ddl/
│   └── migrations/          # ここを参照すべき
│       └── 3.4.0_search_integration.cypher
```

## 3. 修正内容

`apply_ddl_schema.py`の37-44行目を修正：
- `".."` を2つに変更して正しいパスを指すように修正

## 4. 影響範囲

この修正により、以下のすべてのテストが正常に動作するはず：
- DB初期化を行うすべての統合テスト
- `run_system({"type": "schema", "action": "apply"})` を使用するテスト

## 5. 今後の対策

1. **パスの検証**: スキーマファイルの存在確認は既に実装されている
2. **エラーメッセージの改善**: ファイルが見つからない場合の詳細なパス情報を出力
3. **相対パスの削減**: 可能であれば環境変数や定数でパスを管理

## 6. 確認方法

```bash
# 修正が正しいか確認
python -m requirement.graph <<< '{"type": "schema", "action": "apply"}'
```

成功すれば `{"status": "success", "message": "Schema applied"}` が返る。