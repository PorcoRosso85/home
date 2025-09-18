// テストカバレッジ不足の要件
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