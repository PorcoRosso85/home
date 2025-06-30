# 不整合性検出システム TDD Red 仕様書

## 概要

多角度からの要件定義における不整合性を自動検出するためのTDD Red（失敗するテスト）を定義しました。
これらのテストは現在存在しない機能をテストするため、すべて失敗します。

## テストファイル

`test_inconsistency_detection.py` に以下の不整合性検出テストを実装：

### 1. 意味的矛盾検出テスト (SemanticValidator)

**配置場所**: `application/semantic_validator.py`

**テスト内容**:
- 同じ性能要件に対する異なる制約値の検出
  - PM視点: APIレスポンス500ms以内
  - Engineer視点: APIレスポンス200ms以内
  - → 矛盾を検出し、conflictとして報告

- 相反するセキュリティポリシーの検出
  - Executive視点: 利便性重視（認証ステップ最小化）
  - Engineer視点: セキュリティ重視（MFA必須）
  - → ポリシーの矛盾を検出

### 2. リソース競合検出テスト (ResourceConflictDetector)

**配置場所**: `application/resource_conflict_detector.py`

**テスト内容**:
- データベース接続プールの競合
  - Service A: 80接続必要
  - Service B: 60接続必要
  - システム制約: 最大100接続
  - → 40接続のオーバーアロケーションを検出

### 3. 優先度整合性テスト (PriorityConsistencyChecker)

**配置場所**: `application/priority_consistency_checker.py`

**テスト内容**:
- 依存関係と優先度の逆転検出
  - 高優先度要件（Priority: 250）が低優先度要件（Priority: 100）に依存
  - → 優先度逆転を検出し警告

### 4. 要件完全性テスト (RequirementCompletenessAnalyzer)

**配置場所**: `application/requirement_completeness_analyzer.py`

**テスト内容**:
- 必須カテゴリの欠落検出
  - セキュリティ要件の欠落を検出
  - カバレッジ率を計算

- 重複要件の検出
  - 異なるIDだが実質的に同じ内容の要件を検出
  - 類似度スコアで判定

### 5. 統合検証テスト (IntegratedConsistencyValidator)

**配置場所**: `application/integrated_consistency_validator.py`

**テスト内容**:
- すべての不整合性を統合的に検出
- 全体的な健全性スコアを算出

## 実装ガイド

これらのテストを通過させるには、以下の実装が必要：

1. **SemanticValidator**
   - Metadataフィールドの解析
   - 同一対象への異なる制約の検出ロジック
   - ポリシー矛盾の検出アルゴリズム

2. **ResourceConflictDetector**
   - リソース要求の集計
   - システム制約との照合
   - オーバーアロケーションの計算

3. **PriorityConsistencyChecker**
   - 依存グラフの構築
   - 優先度の伝播解析
   - 逆転パターンの検出

4. **RequirementCompletenessAnalyzer**
   - カテゴリ分類器
   - テキスト類似度計算（重複検出）
   - カバレッジ分析

5. **IntegratedConsistencyValidator**
   - 各バリデーターの統合
   - レポート生成
   - 健全性スコアリング

## 期待される効果

これらのバリデーターが実装されることで：

- PM、Executive、Engineerが同時に要件を追加しても、矛盾や競合を自動検出
- リソースの過剰要求を事前に防止
- 優先度の論理的整合性を保証
- 要件の網羅性を確保
- 重複作業の防止

これにより、多角度からの要件定義における不整合性を自動排除できるシステムが実現します。