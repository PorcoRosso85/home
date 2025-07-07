# 階層概念の誤解を解くためのクリーンアップガイド

## 重要な前提

RGLシステムには固定的な「階層」概念は存在しません。あるのはグラフのエッジ関係とその深さ制限のみです。

## 誤解を招く可能性のあるファイル

### 高優先度（階層を前提とした実装）
- `domain/hierarchy_rules.py` - 階層ルールの定義
- `infrastructure/hierarchy_validator.py` - 階層検証ロジック  
- `infrastructure/hierarchy_udfs.py` - 階層関連のUDF
- `domain/requirement_hierarchy.py` - 要件階層ドメイン

### 中優先度（階層への言及がある）
- テストファイル全般（test_*.py）
- `domain/violation_definitions.py` - 階層違反の定義
- `application/scoring_service.py` - 階層違反のスコアリング

## 推奨される修正

1. **用語の変更**
   - "階層違反" → "グラフ深さ制限違反"
   - "hierarchy_level" → 削除（使用しない）
   - "ビジョン/タスク" → 単なる要件の例として扱う

2. **実装の変更**
   - 固定レベルチェック → グラフトラバーサルによる深さチェック
   - hierarchy_validator → graph_depth_validator

3. **テストの変更**
   - 階層前提のテスト → グラフ構造のテスト
   - レベル0-4の仮定 → 削除

## 注意事項

既存の`hierarchy_validator.py`などは、現在のシステムで使われている可能性があります。
削除や大幅な変更の前に、実際の使用状況を確認してください。