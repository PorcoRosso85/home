# 変更履歴

## テストファイル名の変更

### 変更理由
「without_snapshot」という名前は、過去の実装詳細（スナップショット機能）への参照を含んでおり、将来的に見たときに意味が不明瞭になるため。

### 変更内容
- `test_version_tracking_without_snapshot.py` → `test_requirement_versioning.py`
- クラス名も `TestVersionTrackingWithoutSnapshot` → `TestRequirementVersioning` に変更
- 「スナップショットID廃止」テストを「APIレスポンス」テストに名称変更

### 更新されたファイル
1. `test_requirement_versioning.py` - メインの仕様テスト
2. `TEST_SPECIFICATION.md` - テスト仕様書
3. `test_version_service.py` - 削除（旧設計）
4. `test_jsonl_repository.py` - update()をsave()に修正
5. `test_kuzu_repository.py` - スキーマをイミュータブル設計に更新

## 設計原則の明確化

テストファイルは将来にわたって理解可能な名前と内容を持つべきです：
- 実装の詳細ではなく、機能や設計思想を表す名前
- 過去の技術的決定への参照を避ける
- 「テストは仕様そのもの」の原則を守る