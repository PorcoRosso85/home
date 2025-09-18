# アーキテクチャ管理のためのDQL設計

## 目的
アーキテクチャをgraph dbで管理するという責務に特化したDQLクエリ群を提供する。

## 主要なユースケース

### 1. プロジェクト責務分析
**目的**: 各プロジェクトの責務が明確に分離されているか確認

```cypher
// 責務の重複検出
MATCH (p1:Project)-[:HAS_RESPONSIBILITY]->(r:Responsibility)<-[:HAS_RESPONSIBILITY]-(p2:Project)
WHERE p1.id < p2.id
RETURN p1.name as project1, p2.name as project2, r.name as shared_responsibility
```

### 2. 依存関係の健全性
**目的**: 循環依存や過度な結合を検出

```cypher
// 依存の深さ分析
MATCH path = (p:Project)-[:DEPENDS_ON*]->(dep:Project)
WITH p, dep, length(path) as depth
WHERE depth > 3
RETURN p.name, dep.name, depth
ORDER BY depth DESC
```

### 3. レイヤー違反検出
**目的**: アーキテクチャレイヤーの原則違反を発見

```cypher
// 下位レイヤーが上位レイヤーに依存
MATCH (lower:Component)-[:DEPENDS_ON]->(upper:Component)
WHERE lower.layer = 'infrastructure' AND upper.layer = 'application'
RETURN lower.name as violator, upper.name as violation_target
```

### 4. 変更影響分析
**目的**: あるコンポーネントの変更が与える影響範囲を把握

```cypher
// 影響を受けるコンポーネント一覧
MATCH (changed:Component {id: $component_id})<-[:DEPENDS_ON*]-(affected:Component)
RETURN DISTINCT affected.id, affected.name, affected.project
ORDER BY affected.critical_level DESC
```

### 5. 技術的負債の可視化
**目的**: アーキテクチャ上の問題箇所を特定

```cypher
// 高結合度コンポーネント
MATCH (c:Component)
OPTIONAL MATCH (c)-[:DEPENDS_ON]->(dep:Component)
OPTIONAL MATCH (c)<-[:DEPENDS_ON]-(dependent:Component)
WITH c, COUNT(DISTINCT dep) as outgoing, COUNT(DISTINCT dependent) as incoming
WHERE outgoing + incoming > 10
RETURN c.name, c.project, outgoing, incoming, outgoing + incoming as total_coupling
ORDER BY total_coupling DESC
```

## アーキテクチャ固有のDQL分類

### analysis/architecture/
- `detect_responsibility_overlap.cypher` - 責務の重複検出
- `analyze_layer_dependencies.cypher` - レイヤー間依存分析
- `find_architectural_smells.cypher` - アーキテクチャの臭い検出

### validation/architecture/
- `validate_layer_constraints.cypher` - レイヤー制約違反チェック
- `validate_project_boundaries.cypher` - プロジェクト境界違反チェック
- `validate_dependency_rules.cypher` - 依存ルール違反チェック

### reporting/architecture/
- `project_responsibility_matrix.cypher` - プロジェクト責務マトリクス
- `dependency_graph_export.cypher` - 依存グラフエクスポート
- `architecture_health_report.cypher` - アーキテクチャ健全性レポート

## 実装の方向性

1. **プロジェクト構造の可視化**
   - flake.nixから責務を抽出
   - 依存関係を自動検出
   - レイヤー構造を推論

2. **継続的なアーキテクチャ検証**
   - CI/CDでの自動チェック
   - 違反の早期発見
   - 改善提案の生成

3. **意思決定支援**
   - 新機能の配置場所提案
   - リファクタリング優先順位
   - 技術的負債の定量化