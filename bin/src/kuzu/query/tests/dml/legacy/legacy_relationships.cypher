// 階層型トレーサビリティモデル - レガシーリレーションシップデータ

// ===== HAS_LOCATION_URI関係データ =====
MATCH (c:CodeEntity {persistent_id: 'CODE-001'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);
MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);
MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);
MATCH (c:CodeEntity {persistent_id: 'CODE-004'}), (l:LocationURI {uri_id: 'loc2'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);
MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (l:LocationURI {uri_id: 'loc3'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);
MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);
MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (l:LocationURI {uri_id: 'loc1'}) CREATE (c)-[:HAS_LOCATION_URI]->(l);

// ===== REQUIREMENT_HAS_LOCATION_URI関係データ =====
MATCH (r:RequirementEntity {id: 'REQ-001'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l);
MATCH (r:RequirementEntity {id: 'REQ-002'}), (l:LocationURI {uri_id: 'loc4'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l);
MATCH (r:RequirementEntity {id: 'REQ-003'}), (l:LocationURI {uri_id: 'loc5'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l);
MATCH (r:RequirementEntity {id: 'REQ-004'}), (l:LocationURI {uri_id: 'loc5'}) CREATE (r)-[:REQUIREMENT_HAS_LOCATION_URI]->(l);

// ===== IMPLEMENTS関係データ =====
MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r);
MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r);
MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-001'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r);
MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (r:RequirementEntity {id: 'REQ-002'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'TESTS'}]->(r);
MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (r:RequirementEntity {id: 'REQ-003'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r);
MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (r:RequirementEntity {id: 'REQ-004'}) CREATE (c)-[:IMPLEMENTS {implementation_type: 'IMPLEMENTS'}]->(r);

// ===== CONTAINS関係 - 親子関係 =====
MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-002'}) CREATE (c1)-[:CONTAINS]->(c2);
MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-003'}) CREATE (c1)-[:CONTAINS]->(c2);
MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-006'}) CREATE (c1)-[:CONTAINS]->(c2);
MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-007'}) CREATE (c1)-[:CONTAINS]->(c2);
