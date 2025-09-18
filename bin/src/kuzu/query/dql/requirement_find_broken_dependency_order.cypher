// 実装されているが依存要件が未実装
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