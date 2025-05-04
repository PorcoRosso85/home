// 階層型トレーサビリティモデル - 拡張サンプルデータ

// 追加のLocationURIデータ
CREATE (loc8:LocationURI {uri_id: 'loc_config', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/config', fragment: '', query: ''});
CREATE (loc9:LocationURI {uri_id: 'loc_data_req', scheme: 'requirement', authority: 'project', path: '/functional/data-management', fragment: '', query: ''});
CREATE (loc10:LocationURI {uri_id: 'loc_maintain_req', scheme: 'requirement', authority: 'project', path: '/non-functional/maintainability', fragment: '', query: ''});

// 追加のRequirementEntityデータ
CREATE (req6:RequirementEntity {id: 'REQ-006', title: 'データ永続化', description: 'システムはユーザーデータを永続化できること', priority: 'HIGH', requirement_type: 'functional'});
CREATE (req7:RequirementEntity {id: 'REQ-007', title: 'レスポンスタイム', description: 'ユーザー検索のレスポンスタイムは500ms以下であること', priority: 'MEDIUM', requirement_type: 'performance'});
CREATE (req8:RequirementEntity {id: 'REQ-008', title: '設定管理', description: 'システム設定を外部ファイルで管理できること', priority: 'LOW', requirement_type: 'functional'});

// 追加のCodeEntityデータ
CREATE (code10:CodeEntity {persistent_id: 'CODE-010', name: 'AppConfig', type: 'class', signature: 'public class AppConfig', complexity: 1, start_position: 1900, end_position: 2100});
CREATE (code11:CodeEntity {persistent_id: 'CODE-011', name: 'saveUser', type: 'function', signature: 'public User saveUser(User user)', complexity: 3, start_position: 1450, end_position: 1550});

// 追加のVerificationデータ
CREATE (ver6:RequirementVerification {id: 'TEST-006', name: 'データ永続化テスト', description: 'データ永続化機能の検証', verification_type: 'integration'});
CREATE (ver7:RequirementVerification {id: 'TEST-007', name: '設定管理テスト', description: '設定管理機能の検証', verification_type: 'unit-test'});

// 追加のバージョン情報
CREATE (vs3:VersionState {id: 'v1.2.0', timestamp: '2023-03-25T09:15:00Z', commit_id: 'i9j0k1l2', branch_name: 'main'});

// ===== 追加の関係データ =====

// 階層関係の拡張
MATCH (parent:LocationURI {uri_id: 'loc_example'}), (child:LocationURI {uri_id: 'loc_config'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_functional'}), (child:LocationURI {uri_id: 'loc_data_req'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_non_functional'}), (child:LocationURI {uri_id: 'loc_maintain_req'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

// 位置情報関係の拡張
MATCH (c:CodeEntity {persistent_id: 'CODE-010'}), (l:LocationURI {uri_id: 'loc_config'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-011'}), (l:LocationURI {uri_id: 'loc_repository'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-006'}), (l:LocationURI {uri_id: 'loc_data_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-007'}), (l:LocationURI {uri_id: 'loc_perf_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-008'}), (l:LocationURI {uri_id: 'loc_maintain_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

// 実装関係の拡張
MATCH (r:RequirementEntity {id: 'REQ-006'}), (c:CodeEntity {persistent_id: 'CODE-011'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

MATCH (r:RequirementEntity {id: 'REQ-008'}), (c:CodeEntity {persistent_id: 'CODE-010'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

// 親子関係の拡張
MATCH (c1:CodeEntity {persistent_id: 'CODE-008'}), (c2:CodeEntity {persistent_id: 'CODE-011'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

// 検証関係の拡張
MATCH (r:RequirementEntity {id: 'REQ-006'}), (v:RequirementVerification {id: 'TEST-006'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

MATCH (r:RequirementEntity {id: 'REQ-008'}), (v:RequirementVerification {id: 'TEST-007'}) 
CREATE (r)-[:VERIFIED_BY]->(v);

// バージョン関係の拡張
MATCH (v1:VersionState {id: 'v1.1.0'}), (v2:VersionState {id: 'v1.2.0'}) 
CREATE (v1)-[:FOLLOWS]->(v2);

MATCH (v:VersionState {id: 'v1.2.0'}), (r:RequirementEntity {id: 'REQ-006'}) 
CREATE (v)-[:TRACKS_STATE_OF_REQ {change_type: 'added'}]->(r);

MATCH (v:VersionState {id: 'v1.2.0'}), (r:RequirementEntity {id: 'REQ-008'}) 
CREATE (v)-[:TRACKS_STATE_OF_REQ {change_type: 'added'}]->(r);

MATCH (v:VersionState {id: 'v1.2.0'}), (c:CodeEntity {persistent_id: 'CODE-010'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE {change_type: 'added'}]->(c);

MATCH (v:VersionState {id: 'v1.2.0'}), (c:CodeEntity {persistent_id: 'CODE-011'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE {change_type: 'added'}]->(c);
