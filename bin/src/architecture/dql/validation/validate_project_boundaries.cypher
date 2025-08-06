// プロジェクト境界違反検出クエリ
// 目的: プロジェクトが他プロジェクトの内部実装に直接依存していないか検証
//
// 違反パターン:
// - privateとマークされたコンポーネントへの外部依存
// - internal pathへの直接アクセス
// - 公開APIを経由しない依存

MATCH (source:Component)-[dep:DEPENDS_ON]->(target:Component)
WHERE source.project <> target.project  // 異なるプロジェクト間
  AND (
    target.visibility = 'private'
    OR target.path CONTAINS '/internal/'
    OR target.path CONTAINS '/impl/'
    OR (target.exported = false AND NOT EXISTS(dep.through_interface))
  )
WITH source, target, dep
RETURN 
    source.name as violating_component,
    source.project as source_project,
    'accesses' as violation,
    target.name as private_component,
    target.project as target_project,
    target.path as target_path,
    CASE
        WHEN target.visibility = 'private' THEN 'CRITICAL: Accessing private component'
        WHEN target.path CONTAINS '/internal/' THEN 'HIGH: Accessing internal implementation'
        WHEN NOT target.exported THEN 'MEDIUM: Using non-exported component'
        ELSE 'LOW: Potential boundary violation'
    END as violation_type,
    COALESCE(dep.reason, 'No reason specified') as dependency_reason,
    'Use public API or introduce proper abstraction' as recommendation
ORDER BY 
    CASE violation_type
        WHEN violation_type CONTAINS 'CRITICAL' THEN 1
        WHEN violation_type CONTAINS 'HIGH' THEN 2
        WHEN violation_type CONTAINS 'MEDIUM' THEN 3
        ELSE 4
    END,
    source.project;