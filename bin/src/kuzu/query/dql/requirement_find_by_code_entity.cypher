// コードエンティティと要件の逆引き
// コードから関連する要件を逆引き
MATCH (c:CodeEntity)<-[:IS_IMPLEMENTED_BY]-(r:RequirementEntity)
WHERE c.name CONTAINS $codeName
RETURN c.persistent_id as code_id,
       c.name as code_name,
       collect(r.id) as implementing_requirements;