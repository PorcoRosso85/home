# テスト削除・移行候補リスト

## 黄金律：「リファクタリングの壁」違反テスト

### 1. パフォーマンステスト（削除推奨）

| ファイル | テスト名 | 違反理由 | 対応 |
|---------|---------|---------|------|
| test_duplicate_detection.py | test_performance_with_many_requirements | パフォーマンスは実装詳細 | 削除 |
| test_existing_connection.py | test_initialization_performance | 初期化速度は実装詳細 | 削除 |
| test_existing_connection.py | test_detailed_performance_comparison | 接続共有の速度は実装詳細 | 削除済み |

### 2. モックを使用したアプリケーション層テスト（統合テストへ移行）

| ファイル | テスト名 | 違反理由 | 対応 |
|---------|---------|---------|------|
| test_search_template.py | test_search_template_with_mock_adapter | モックによる実装のコピー | 統合テストへ |
| test_search_template_integration.py | test_search_template_integration | モックによる実装のコピー | 実DBを使う統合テストへ |
| test_existing_connection.py | MockLog使用 | システムレベルのモック | 削除検討 |

### 3. 実装詳細をテストしているもの

| ファイル | テスト名 | 違反理由 | 対応 |
|---------|---------|---------|------|
| test_duplicate_detection.py | エンベディング生成の確認部分 | 内部実装の詳細 | 該当行削除 |

## 規約準拠の良いテスト例

### 公開APIの振る舞いをテスト
- test_output_contract.py - 出力形式の契約を検証
- test_requirement_management.py - ユースケースレベルの統合テスト
- test_hybrid_search_spec.py - 検索仕様の検証

### 推奨アクション

1. **即削除（Phase 3）**:
   - test_performance_with_many_requirements
   - test_initialization_performance

2. **統合テストへ移行（Phase 2）**:
   - test_search_template_with_mock_adapter → 実DBを使った統合テストへ
   - test_search_template_integration → 実際のSearchAdapterを使用

3. **保持（価値あるテスト）**:
   - test_search_template_validation - 入力検証は公開API
   - test_output_contract.py - 出力契約の保証
   - test_requirement_management.py - ユースケースレベル