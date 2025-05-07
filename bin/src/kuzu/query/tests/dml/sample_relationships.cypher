// 階層型トレーサビリティモデル - サンプルデータの関係

// ===== 位置情報の階層関係 =====

// ファイル階層
MATCH (parent:LocationURI {uri_id: 'loc_root'}), (child:LocationURI {uri_id: 'loc_src'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_src'}), (child:LocationURI {uri_id: 'loc_main'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_src'}), (child:LocationURI {uri_id: 'loc_test_root'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_main'}), (child:LocationURI {uri_id: 'loc_java'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_test_root'}), (child:LocationURI {uri_id: 'loc_test_java'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_java'}), (child:LocationURI {uri_id: 'loc_com'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_test_java'}), (child:LocationURI {uri_id: 'loc_test_com'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_com'}), (child:LocationURI {uri_id: 'loc_example'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_test_com'}), (child:LocationURI {uri_id: 'loc_test_example'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_example'}), (child:LocationURI {uri_id: 'loc_service'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_example'}), (child:LocationURI {uri_id: 'loc_controller'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_example'}), (child:LocationURI {uri_id: 'loc_repository'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_test_example'}), (child:LocationURI {uri_id: 'loc_test'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

// 要件階層
MATCH (parent:LocationURI {uri_id: 'loc_req_root'}), (child:LocationURI {uri_id: 'loc_functional'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_req_root'}), (child:LocationURI {uri_id: 'loc_non_functional'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_functional'}), (child:LocationURI {uri_id: 'loc_func_req'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_non_functional'}), (child:LocationURI {uri_id: 'loc_security_req'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_non_functional'}), (child:LocationURI {uri_id: 'loc_perf_req'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

// ===== エンティティと位置情報の関係 =====

// HAS_LOCATION関係
MATCH (c:CodeEntity {persistent_id: 'CODE-001'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-002'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-004'}), (l:LocationURI {uri_id: 'loc_controller'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-005'}), (l:LocationURI {uri_id: 'loc_test'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-007'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-008'}), (l:LocationURI {uri_id: 'loc_repository'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-009'}), (l:LocationURI {uri_id: 'loc_repository'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

// REQUIREMENT_HAS_LOCATION関係
MATCH (r:RequirementEntity {id: 'REQ-001'}), (l:LocationURI {uri_id: 'loc_func_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-002'}), (l:LocationURI {uri_id: 'loc_func_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-003'}), (l:LocationURI {uri_id: 'loc_security_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-004'}), (l:LocationURI {uri_id: 'loc_security_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-005'}), (l:LocationURI {uri_id: 'loc_perf_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

// REFERENCE_HAS_LOCATION関係
MATCH (ref:ReferenceEntity {id: 'REF-001'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(l);

MATCH (ref:ReferenceEntity {id: 'REF-002'}), (l:LocationURI {uri_id: 'loc_security_req'}) 
CREATE (ref)-[:REFERENCE_HAS_LOCATION]->(l);

// ===== 実装関係 =====

// IS_IMPLEMENTED_BY関係 - 要件の実装
MATCH (r:RequirementEntity {id: 'REQ-001'}), (c:CodeEntity {persistent_id: 'CODE-002'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

MATCH (r:RequirementEntity {id: 'REQ-002'}), (c:CodeEntity {persistent_id: 'CODE-003'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

MATCH (r:RequirementEntity {id: 'REQ-003'}), (c:CodeEntity {persistent_id: 'CODE-006'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

MATCH (r:RequirementEntity {id: 'REQ-004'}), (c:CodeEntity {persistent_id: 'CODE-007'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

MATCH (r:RequirementEntity {id: 'REQ-005'}), (c:CodeEntity {persistent_id: 'CODE-009'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

// VERIFIED_BY関係 - 要件と検証
MATCH (r:RequirementEntity {id: 'REQ-001'}), (v:RequirementVerification {id: 'TEST-001'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

MATCH (r:RequirementEntity {id: 'REQ-002'}), (v:RequirementVerification {id: 'TEST-002'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

MATCH (r:RequirementEntity {id: 'REQ-003'}), (v:RequirementVerification {id: 'TEST-003'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

MATCH (r:RequirementEntity {id: 'REQ-004'}), (v:RequirementVerification {id: 'TEST-004'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

MATCH (r:RequirementEntity {id: 'REQ-005'}), (v:RequirementVerification {id: 'TEST-005'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

// VERIFICATION_IS_IMPLEMENTED_BY関係 - 検証の実装
MATCH (v:RequirementVerification {id: 'TEST-001'}), (c:CodeEntity {persistent_id: 'CODE-005'}) 
CREATE (v)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'TESTS'}]->(c);

MATCH (v:RequirementVerification {id: 'TEST-002'}), (c:CodeEntity {persistent_id: 'CODE-005'}) 
CREATE (v)-[:VERIFICATION_IS_IMPLEMENTED_BY {implementation_type: 'TESTS'}]->(c);

// CONTAINS_CODE関係 - コードの親子関係
MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-002'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-003'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-006'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-001'}), (c2:CodeEntity {persistent_id: 'CODE-007'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-008'}), (c2:CodeEntity {persistent_id: 'CODE-009'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

// ===== その他の関係 =====

// DEPENDS_ON関係 - 要件の依存関係
MATCH (r1:RequirementEntity {id: 'REQ-003'}), (r2:RequirementEntity {id: 'REQ-002'}) 
CREATE (r1)-[:DEPENDS_ON {dependency_type: 'functional'}]->(r2);

MATCH (r1:RequirementEntity {id: 'REQ-004'}), (r2:RequirementEntity {id: 'REQ-002'}) 
CREATE (r1)-[:DEPENDS_ON {dependency_type: 'functional'}]->(r2);

// REFERENCES_CODE関係 - コード間の参照
MATCH (c1:CodeEntity {persistent_id: 'CODE-003'}), (c2:CodeEntity {persistent_id: 'CODE-006'}) 
CREATE (c1)-[:REFERENCES_CODE {ref_type: 'call'}]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-003'}), (c2:CodeEntity {persistent_id: 'CODE-007'}) 
CREATE (c1)-[:REFERENCES_CODE {ref_type: 'call'}]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-002'}), (c2:CodeEntity {persistent_id: 'CODE-009'}) 
CREATE (c1)-[:REFERENCES_CODE {ref_type: 'call'}]->(c2);

// REFERS_TO関係 - 外部参照
// FIXME: 旧名称 "REFERENCES_EXTERNAL" から変更。コードエンティティが参照エンティティを参照することを明確化
MATCH (c:CodeEntity {persistent_id: 'CODE-003'}), (r:ReferenceEntity {id: 'REF-001'}) 
CREATE (c)-[:REFERS_TO {ref_type: 'api'}]->(r);

MATCH (c:CodeEntity {persistent_id: 'CODE-006'}), (r:ReferenceEntity {id: 'REF-002'}) 
CREATE (c)-[:REFERS_TO {ref_type: 'document'}]->(r);

// FOLLOWS関係 - バージョンの順序
MATCH (v1:VersionState {id: 'v1.0.0'}), (v2:VersionState {id: 'v1.1.0'}) 
CREATE (v1)-[:FOLLOWS]->(v2);

// バージョン管理関係
MATCH (v:VersionState {id: 'v1.0.0'}), (c:CodeEntity {persistent_id: 'CODE-001'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.0.0'}), (c:CodeEntity {persistent_id: 'CODE-002'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.0.0'}), (r:RequirementEntity {id: 'REQ-001'}) 
CREATE (v)-[:TRACKS_STATE_OF_REQ]->(r);

MATCH (v:VersionState {id: 'v1.1.0'}), (c:CodeEntity {persistent_id: 'CODE-003'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.1.0'}), (c:CodeEntity {persistent_id: 'CODE-002'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

// 集計関係
MATCH (v:EntityAggregationView {id: 'VIEW-001'}), (l:LocationURI {uri_id: 'loc_func_req'}) 
CREATE (v)-[:USES]->(l);

MATCH (v:EntityAggregationView {id: 'VIEW-002'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (v)-[:USES]->(l);

MATCH (v:EntityAggregationView {id: 'VIEW-001'}), (r:RequirementEntity {id: 'REQ-001'}) 
CREATE (v)-[:AGGREGATES_REQ {aggregation_method: 'coverage'}]->(r);

MATCH (v:EntityAggregationView {id: 'VIEW-002'}), (c:CodeEntity {persistent_id: 'CODE-001'}) 
CREATE (v)-[:AGGREGATES_CODE {aggregation_method: 'progress'}]->(c);
