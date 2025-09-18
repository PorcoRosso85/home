// Claude Graph POC - タスク探索用Cypherクエリテンプレート

// ===== 基本的な探索クエリ =====

// 1. 要件の完全な情報取得
// 要件とその実装状態、テスト状態を包括的に取得
MATCH (r:RequirementEntity {id: $requirementId})
OPTIONAL MATCH (r)-[impl:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[ver:IS_VERIFIED_BY]->(t:CodeEntity)
OPTIONAL MATCH (r)-[dep:DEPENDS_ON]->(d:RequirementEntity)
RETURN r, 
       collect(DISTINCT c) as implementations,
       collect(DISTINCT t) as tests,
       collect(DISTINCT d) as dependencies;

// 2. 未実装要件の優先度付き一覧
// 実装が必要な要件を優先度順に取得
MATCH (r:RequirementEntity)
WHERE NOT EXISTS {
  MATCH (r)-[:IS_IMPLEMENTED_BY]->()
}
RETURN r.id, r.title, r.priority, r.description
ORDER BY 
  CASE r.priority 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
    ELSE 4 
  END,
  r.id;

// 3. テストカバレッジ不足の要件
// テストが必要だが未作成の要件を検出
MATCH (r:RequirementEntity)
WHERE r.verification_required = true
  AND NOT EXISTS {
    MATCH (r)-[:IS_VERIFIED_BY]->()
  }
  AND EXISTS {
    MATCH (r)-[:IS_IMPLEMENTED_BY]->()
  }
RETURN r.id, r.title, r.priority
ORDER BY r.priority DESC;

// ===== 依存関係の探索 =====

// 4. 要件の依存関係ツリー
// 特定要件から辿れる全ての依存関係を再帰的に取得
MATCH path = (r:RequirementEntity {id: $requirementId})-[:DEPENDS_ON*]->(d:RequirementEntity)
RETURN r.id as source, 
       [n IN nodes(path) | n.id] as dependency_chain,
       d.id as target,
       length(path) as depth
ORDER BY depth;

// 5. 循環依存の検出
// 要件間の循環依存を検出（問題のある設計を発見）
MATCH (r:RequirementEntity)-[:DEPENDS_ON*]->(r)
RETURN r.id as circular_requirement, 
       r.title,
       'Circular dependency detected' as issue;

// ===== 実装の整合性チェック =====

// 6. 実装されているが依存要件が未実装
// 依存関係の順序が守られていない箇所を検出
MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->()
WHERE EXISTS {
  MATCH (r)-[:DEPENDS_ON]->(d:RequirementEntity)
  WHERE NOT EXISTS {
    MATCH (d)-[:IS_IMPLEMENTED_BY]->()
  }
}
RETURN r.id, r.title, 
       [(r)-[:DEPENDS_ON]->(d) WHERE NOT EXISTS {(d)-[:IS_IMPLEMENTED_BY]->()} | d.id] as unimplemented_dependencies;

// ===== LocationURIベースの探索 =====

// 7. 特定パスの要件と実装状況
// ファイルパスやモジュールパスから関連要件を探索
MATCH (l:LocationURI)-[:LOCATED_WITH_REQUIREMENT]->(r:RequirementEntity)
WHERE l.id CONTAINS $uriPath
OPTIONAL MATCH (r)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
OPTIONAL MATCH (r)-[:IS_VERIFIED_BY]->(t:CodeEntity)
RETURN l.id as location,
       r.id as requirement_id,
       r.title,
       EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) as is_implemented,
       EXISTS((r)-[:IS_VERIFIED_BY]->()) as has_tests;

// 8. コードエンティティと要件の逆引き
// コードから関連する要件を逆引き
MATCH (c:CodeEntity)<-[:IS_IMPLEMENTED_BY]-(r:RequirementEntity)
WHERE c.name CONTAINS $codeName
RETURN c.persistent_id as code_id,
       c.name as code_name,
       collect(r.id) as implementing_requirements;

// ===== 進捗状況の集計 =====

// 9. プロジェクト全体の実装進捗
// 要件タイプ別の実装状況を集計
MATCH (r:RequirementEntity)
RETURN r.requirement_type as type,
       count(*) as total,
       sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) as implemented,
       sum(CASE WHEN EXISTS((r)-[:IS_VERIFIED_BY]->()) THEN 1 ELSE 0 END) as tested,
       round(100.0 * sum(CASE WHEN EXISTS((r)-[:IS_IMPLEMENTED_BY]->()) THEN 1 ELSE 0 END) / count(*), 1) as implementation_rate;

// 10. 最近のバージョンでの変更影響範囲
// バージョン変更に関連する要件を時系列で取得
MATCH (v:VersionState)-[:VERSION_AFFECTS]->(r:RequirementEntity)
WHERE v.timestamp > $sinceTimestamp
RETURN v.id as version_id,
       v.timestamp,
       v.description as version_description,
       collect(r.id) as affected_requirements
ORDER BY v.timestamp DESC;

// ===== 複雑な分析クエリ =====

// 11. 実装の複雑度と要件の関係
// 複雑な実装を持つ要件を特定
MATCH (r:RequirementEntity)-[:IS_IMPLEMENTED_BY]->(c:CodeEntity)
WHERE c.complexity > $complexityThreshold
RETURN r.id, r.title,
       avg(c.complexity) as avg_complexity,
       count(c) as implementation_count,
       collect({name: c.name, complexity: c.complexity}) as complex_implementations
ORDER BY avg_complexity DESC;

// 12. テストカバレッジの詳細分析
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