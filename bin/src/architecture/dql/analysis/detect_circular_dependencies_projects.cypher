// プロジェクト間の循環依存検出クエリ
// 目的: プロジェクトレベルでの循環依存を検出し、アーキテクチャの問題を特定
//
// 循環依存の例:
// A → B → C → A のような依存関係チェーン

MATCH path = (p1:Project)-[:DEPENDS_ON*]->(p1)
WITH p1, path, [node IN nodes(path) | node.name] as cycle_nodes
WHERE SIZE(cycle_nodes) > 1  // 自己参照を除外
RETURN 
    p1.name as circular_project,
    p1.path as project_path,
    SIZE(cycle_nodes) - 1 as cycle_length,  // 最後は始点と同じなので-1
    cycle_nodes as dependency_cycle,
    CASE
        WHEN SIZE(cycle_nodes) - 1 = 2 THEN 'HIGH'    // 直接的な相互依存
        WHEN SIZE(cycle_nodes) - 1 = 3 THEN 'MEDIUM'  // 3つのプロジェクト間
        ELSE 'LOW'                                     // より長い循環
    END as severity,
    'Circular dependency detected. Consider introducing an abstraction or interface.' as recommendation
ORDER BY severity DESC, cycle_length;