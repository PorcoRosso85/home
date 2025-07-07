// テストカバレッジの詳細分析
// 要件に対するテストの種類と数を分析
MATCH (r:RequirementEntity)-[v:IS_VERIFIED_BY]->(t:CodeEntity)
RETURN r.id, r.title,
       count(DISTINCT t) as test_count,
       collect(DISTINCT v.test_type) as test_types,
       CASE 
         WHEN 'unit' IN collect(v.test_type) AND 'integration' IN collect(v.test_type) THEN 'comprehensive'
         WHEN 'unit' IN collect(v.test_type) THEN 'unit_only'
         WHEN 'integration' IN collect(v.test_type) THEN 'integration_only'
         ELSE 'other'
       END as coverage_quality;