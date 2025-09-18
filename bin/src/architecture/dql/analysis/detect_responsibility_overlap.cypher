// プロジェクト間の責務重複検出クエリ
// 目的: 複数のプロジェクトが同じ責務を持っていないか確認
// 
// 想定スキーマ:
// - Project: プロジェクトノード (id, name, path, description)
// - Responsibility: 責務ノード (id, name, description)
// - HAS_RESPONSIBILITY: プロジェクトが持つ責務

MATCH (p1:Project)-[:HAS_RESPONSIBILITY]->(r:Responsibility)<-[:HAS_RESPONSIBILITY]-(p2:Project)
WHERE p1.id < p2.id  // 重複を避けるため
WITH p1, p2, r, COUNT(*) as overlap_count
RETURN 
    p1.name as project_1,
    p1.path as project_1_path,
    p2.name as project_2,
    p2.path as project_2_path,
    r.name as overlapping_responsibility,
    r.description as responsibility_description,
    CASE 
        WHEN r.name CONTAINS 'util' OR r.name CONTAINS 'common' THEN 'LOW'
        WHEN overlap_count > 2 THEN 'HIGH'
        ELSE 'MEDIUM'
    END as severity
ORDER BY severity DESC, r.name;