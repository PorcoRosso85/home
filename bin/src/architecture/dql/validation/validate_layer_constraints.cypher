// レイヤー制約違反検出クエリ
// 目的: アーキテクチャレイヤーの依存ルール違反を検出
//
// レイヤー階層（上位→下位）:
// 1. presentation (UI/CLI)
// 2. application (ビジネスロジック)
// 3. domain (ドメインモデル)
// 4. infrastructure (永続化/外部サービス)
//
// ルール: 下位レイヤーは上位レイヤーに依存してはいけない

WITH {
    'presentation': 1,
    'application': 2,
    'domain': 3,
    'infrastructure': 4
} as layer_order

MATCH (source:Component)-[dep:DEPENDS_ON]->(target:Component)
WHERE layer_order[source.layer] > layer_order[target.layer]
WITH source, target, dep,
     source.layer as source_layer,
     target.layer as target_layer
RETURN 
    source.name as violating_component,
    source.project as source_project,
    source_layer,
    '→' as arrow,
    target.name as illegal_dependency,
    target.project as target_project,
    target_layer,
    CASE
        WHEN source_layer = 'infrastructure' AND target_layer = 'presentation' THEN 'CRITICAL'
        WHEN source_layer = 'domain' AND target_layer IN ['presentation', 'application'] THEN 'HIGH'
        ELSE 'MEDIUM'
    END as severity,
    dep.reason as dependency_reason
ORDER BY severity DESC, source.project, source.name;