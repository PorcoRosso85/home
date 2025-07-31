# Meta-Test DDL Migration

## 概要

このディレクトリには、requirement/graphスキーマを拡張してメタテストシステムをサポートするためのDDLが含まれています。

## ベーススキーマ

requirement/graph v3.4.0の構造：
- **RequirementEntity**: 要件エンティティ（embedding付き）
- **LocationURI**: 階層的な場所表現
- **VersionState**: バージョン管理

## 拡張内容

### Phase 1: テスト基本構造
- **TestEntity**: テストケース/スイート
- **TestExecution**: テスト実行結果
- **VERIFIED_BY**: 要件とテストの関連

### Phase 2: ビジネス影響追跡
- **Incident**: インシデント記録
- **BusinessMetric**: ビジネス指標
- **PREVENTED_BY**: テストがインシデントを防いだ関連
- **IMPACTS**: 要件がビジネス指標に与える影響

### Phase 3: メタテスト指標
- **MetricResult**: 7つの指標の計算結果
- **LearningData**: ベイズ学習データ
- **HAS_METRIC**: 要件と指標結果の関連

### Phase 4: 改善追跡
- **Improvement**: 改善提案と結果
- **IMPROVES**: 改善が指標に与えた影響

## 価値連鎖の実現

```
TestEntity 
    ↓ VERIFIED_BY
RequirementEntity
    ↓ IMPACTS
BusinessMetric
    ↑ 相関分析
Incident (PREVENTED_BY TestExecution)
```

この構造により、「テストが要件を担保し、要件がビジネス価値に貢献する」という価値連鎖を定量的に追跡できます。

## 使用方法

```cypher
-- DDLの適用
:read migration_v1.0.0_meta_test.sql

-- テストと要件の関連付け
CREATE (t:TestEntity {id: 'test_payment_boundary'})
CREATE (r:RequirementEntity {id: 'req_payment_reliability'})
CREATE (t)-[:VERIFIED_BY {verification_type: 'boundary', coverage_score: 0.85}]->(r)

-- ビジネス影響の記録
CREATE (m:BusinessMetric {
    id: 'revenue_daily_20240131',
    metric_name: 'daily_revenue',
    value: 1000000,
    unit: 'JPY'
})
CREATE (r)-[:IMPACTS {impact_type: 'revenue', correlation_strength: 0.75}]->(m)
```

## POCでの検証ポイント

1. **データ投入**: 実際のテスト実行データを投入
2. **相関計算**: TestExecution → Incident/BusinessMetricの相関
3. **学習更新**: ベイズ更新による指標6,7の精度向上
4. **ROI算出**: テストの投資対効果を定量化