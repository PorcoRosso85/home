// プロジェクト責務マトリクスレポート
// 目的: 各プロジェクトがどの責務を担っているかを一覧表示
// 出力: プロジェクト×責務のマトリクス形式で、責務の分散状況を可視化

// すべてのプロジェクトと責務を取得
MATCH (p:Project)
OPTIONAL MATCH (p)-[:HAS_RESPONSIBILITY]->(r:Responsibility)
WITH p, COLLECT(DISTINCT r) as responsibilities

// 各プロジェクトの依存関係も集計
OPTIONAL MATCH (p)-[:DEPENDS_ON]->(dep:Project)
WITH p, responsibilities, COUNT(DISTINCT dep) as dependency_count

// 責務の分類
WITH p, responsibilities, dependency_count,
     [r IN responsibilities WHERE r.type = 'core'] as core_responsibilities,
     [r IN responsibilities WHERE r.type = 'support'] as support_responsibilities,
     [r IN responsibilities WHERE r.type = 'shared'] as shared_responsibilities

RETURN 
    p.name as project_name,
    p.path as project_path,
    p.description as project_description,
    SIZE(core_responsibilities) as core_responsibility_count,
    SIZE(support_responsibilities) as support_responsibility_count,
    SIZE(shared_responsibilities) as shared_responsibility_count,
    SIZE(responsibilities) as total_responsibilities,
    dependency_count as depends_on_count,
    [r IN core_responsibilities | r.name][..3] as sample_core_responsibilities,
    CASE
        WHEN SIZE(responsibilities) = 0 THEN 'UNDEFINED'
        WHEN SIZE(core_responsibilities) > 3 THEN 'OVERLOADED'
        WHEN SIZE(core_responsibilities) = 0 THEN 'SUPPORT_ONLY'
        ELSE 'BALANCED'
    END as health_status
ORDER BY health_status DESC, total_responsibilities DESC;