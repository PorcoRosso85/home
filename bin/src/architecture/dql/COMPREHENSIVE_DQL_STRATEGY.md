# 包括的DQL戦略 - /normalize規約遵守への道

## 目的
診断・予測・監視の3本柱を徹底することで、`/normalize`の規約（責務分離・正規化・重複排除）を守れるアーキテクチャを実現する。

## 1. 診断ツール群（現状の問題発見）

### 1.1 責務の健全性診断
```cypher
// 責務の重複診断
MATCH (r:Responsibility)<-[:HAS_RESPONSIBILITY]-(p:Project)
WITH r, COLLECT(p) as projects
WHERE SIZE(projects) > 1
RETURN r.name as duplicated_responsibility, 
       [p IN projects | p.name] as projects_with_duplication
```

### 1.2 結合度診断
```cypher
// 高結合度コンポーネントの発見
MATCH (c:Component)
OPTIONAL MATCH (c)-[:DEPENDS_ON]->(out)
OPTIONAL MATCH (c)<-[:DEPENDS_ON]-(in)
WITH c, COUNT(DISTINCT out) + COUNT(DISTINCT in) as coupling_score
WHERE coupling_score > 5
RETURN c.name, c.project, coupling_score
ORDER BY coupling_score DESC
```

### 1.3 正規化違反診断
```cypher
// 同じ機能の重複実装を検出
MATCH (c1:Component), (c2:Component)
WHERE c1.id < c2.id 
  AND c1.functionality = c2.functionality
  AND c1.project <> c2.project
RETURN c1.name, c1.project, c2.name, c2.project, 
       c1.functionality as duplicated_functionality
```

## 2. 予測ツール群（変更影響の把握）

### 2.1 変更影響予測
```cypher
// コンポーネント変更時の影響範囲
MATCH path = (changed:Component {id: $component_id})<-[:DEPENDS_ON*]-(affected)
RETURN affected.name, affected.project, 
       length(path) as distance,
       CASE 
         WHEN length(path) = 1 THEN 'DIRECT'
         WHEN length(path) = 2 THEN 'INDIRECT'
         ELSE 'TRANSITIVE'
       END as impact_type
ORDER BY distance
```

### 2.2 新機能配置提案
```cypher
// 責務に基づく適切な配置場所の提案
MATCH (r:Responsibility {name: $new_responsibility})
OPTIONAL MATCH (r)-[:SIMILAR_TO]-(similar:Responsibility)<-[:HAS_RESPONSIBILITY]-(p:Project)
RETURN p.name as suggested_project, 
       COUNT(similar) as similarity_score,
       p.current_load as current_responsibilities
ORDER BY similarity_score DESC, current_load ASC
LIMIT 3
```

### 2.3 リファクタリング影響予測
```cypher
// 責務移動時の影響分析
MATCH (source:Project)-[hr:HAS_RESPONSIBILITY]->(r:Responsibility)
WHERE source.id = $source_project_id AND r.id = $responsibility_id
MATCH (r)<-[:DEPENDS_ON_RESPONSIBILITY]-(dependent:Component)
RETURN dependent.name, dependent.project,
       CASE 
         WHEN dependent.project = source.name THEN 'INTERNAL'
         ELSE 'EXTERNAL'
       END as dependency_type
```

## 3. 監視ツール群（継続的な健全性チェック）

### 3.1 アーキテクチャ健全性スコア
```cypher
// プロジェクト単位の健全性スコア算出
MATCH (p:Project)
OPTIONAL MATCH (p)-[:HAS_RESPONSIBILITY]->(r:Responsibility)
OPTIONAL MATCH (p)-[:CONTAINS]->(c:Component)
OPTIONAL MATCH (c)-[:DEPENDS_ON]->(external:Component)
WHERE external.project <> p.name
WITH p, 
     COUNT(DISTINCT r) as responsibility_count,
     COUNT(DISTINCT c) as component_count,
     COUNT(DISTINCT external) as external_dependencies
RETURN p.name,
       CASE
         WHEN responsibility_count = 0 THEN 0
         WHEN responsibility_count > 5 THEN 50
         ELSE 100
       END as responsibility_score,
       CASE
         WHEN external_dependencies > component_count THEN 0
         ELSE 100 - (external_dependencies * 100.0 / GREATEST(component_count, 1))
       END as independence_score
```

### 3.2 正規化遵守率
```cypher
// 正規化の遵守状況を監視
MATCH (p:Project)-[:CONTAINS]->(c:Component)
OPTIONAL MATCH (c)-[dup:DUPLICATES]->(other:Component)
WITH p, COUNT(c) as total_components, COUNT(dup) as duplicate_count
RETURN p.name,
       total_components,
       duplicate_count,
       CASE
         WHEN total_components = 0 THEN 100
         ELSE 100 - (duplicate_count * 100.0 / total_components)
       END as normalization_compliance_rate
ORDER BY normalization_compliance_rate ASC
```

### 3.3 責務分離遵守率
```cypher
// 単一責任原則の遵守状況
MATCH (c:Component)-[:IMPLEMENTS]->(r:Responsibility)
WITH c, COUNT(DISTINCT r) as responsibility_count
RETURN c.project,
       AVG(CASE 
         WHEN responsibility_count = 1 THEN 100
         WHEN responsibility_count = 2 THEN 80
         ELSE 50
       END) as single_responsibility_score
ORDER BY single_responsibility_score ASC
```

## 4. /normalize規約遵守への統合

### 4.1 総合ダッシュボードクエリ
```cypher
// /normalize規約の総合遵守状況
MATCH (p:Project)
// 責務分離スコア
OPTIONAL MATCH (p)-[:CONTAINS]->(c:Component)-[:IMPLEMENTS]->(r:Responsibility)
WITH p, c, COUNT(DISTINCT r) as resp_per_component
WITH p, AVG(CASE WHEN resp_per_component <= 1 THEN 100 ELSE 50 END) as separation_score
// 正規化スコア
MATCH (p)-[:CONTAINS]->(comp:Component)
OPTIONAL MATCH (comp)-[:DUPLICATES]->(dup)
WITH p, separation_score, 
     100 - (COUNT(dup) * 100.0 / GREATEST(COUNT(comp), 1)) as normalization_score
// 重複排除スコア
MATCH (p)-[:HAS_RESPONSIBILITY]->(resp:Responsibility)
OPTIONAL MATCH (resp)<-[:HAS_RESPONSIBILITY]-(other:Project)
WHERE other <> p
WITH p, separation_score, normalization_score,
     100 - (COUNT(DISTINCT other) * 20) as deduplication_score
RETURN p.name as project,
       separation_score as 責務分離,
       normalization_score as 正規化,
       deduplication_score as 重複排除,
       (separation_score + normalization_score + deduplication_score) / 3 as 総合スコア
ORDER BY 総合スコア ASC
```

## 5. 実装優先順位

### Phase 1（即効性の高いもの）
1. 責務重複診断（1.1）
2. 変更影響予測（2.1）
3. アーキテクチャ健全性スコア（3.1）

### Phase 2（継続的改善）
1. 高結合度診断（1.2）
2. 新機能配置提案（2.2）
3. 正規化遵守率（3.2）

### Phase 3（高度な分析）
1. 正規化違反診断（1.3）
2. リファクタリング影響予測（2.3）
3. 総合ダッシュボード（4.1）

## 期待される効果

1. **即座の問題発見**: 診断ツールで現状の問題を可視化
2. **安全な変更**: 予測ツールで影響を事前に把握
3. **継続的改善**: 監視ツールで改善状況を追跡
4. **規約の自然な遵守**: データに基づく意思決定で/normalize規約が自然に守られる

これらのDQLを徹底的に実装・活用することで、アーキテクチャの健全性が保たれ、結果として/normalize規約が守られる状態を実現します。