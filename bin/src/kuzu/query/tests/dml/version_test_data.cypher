// 階層型トレーサビリティモデル - バージョンテスト用データ

// v1.3.0のバージョン情報を追加
CREATE (vs4:VersionState {id: 'v1.3.0', timestamp: '2023-04-30T15:45:00Z', commit_id: 'm3n4o5p6', branch_name: 'main'});

// バージョン順序を更新
MATCH (v1:VersionState {id: 'v1.2.0'}), (v2:VersionState {id: 'v1.3.0'}) 
CREATE (v1)-[:FOLLOWS]->(v2);

// 追加のLocationURIデータ
CREATE (loc11:LocationURI {uri_id: 'loc_util', scheme: 'file', authority: 'project', path: '/src/main/java/com/example/util', fragment: '', query: ''});
CREATE (loc12:LocationURI {uri_id: 'loc_integration_req', scheme: 'requirement', authority: 'project', path: '/functional/integration', fragment: '', query: ''});

// 既存階層に追加
MATCH (parent:LocationURI {uri_id: 'loc_example'}), (child:LocationURI {uri_id: 'loc_util'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'file_hierarchy'}]->(child);

MATCH (parent:LocationURI {uri_id: 'loc_functional'}), (child:LocationURI {uri_id: 'loc_integration_req'}) 
CREATE (parent)-[:CONTAINS_LOCATION {relation_type: 'requirement_hierarchy'}]->(child);

// v1.3.0で追加される新しいコードエンティティ
CREATE (code12:CodeEntity {persistent_id: 'CODE-012', name: 'StringUtils', type: 'class', signature: 'public class StringUtils', complexity: 2, start_position: 2200, end_position: 2500});
CREATE (code13:CodeEntity {persistent_id: 'CODE-013', name: 'formatString', type: 'function', signature: 'public static String formatString(String input, Object... args)', complexity: 3, start_position: 2250, end_position: 2350});
CREATE (code14:CodeEntity {persistent_id: 'CODE-014', name: 'validateString', type: 'function', signature: 'public static boolean validateString(String input, String pattern)', complexity: 2, start_position: 2360, end_position: 2450});

// v1.3.0で修正されるコードエンティティ
CREATE (code15:CodeEntity {persistent_id: 'CODE-015', name: 'UserService_v1.3', type: 'class', signature: 'public class UserService', complexity: 6, start_position: 100, end_position: 550});

// 位置情報との関連
MATCH (c:CodeEntity {persistent_id: 'CODE-012'}), (l:LocationURI {uri_id: 'loc_util'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-013'}), (l:LocationURI {uri_id: 'loc_util'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-014'}), (l:LocationURI {uri_id: 'loc_util'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

MATCH (c:CodeEntity {persistent_id: 'CODE-015'}), (l:LocationURI {uri_id: 'loc_service'}) 
CREATE (c)-[:HAS_LOCATION]->(l);

// v1.3.0で追加される新しい要件
CREATE (req9:RequirementEntity {id: 'REQ-009', title: '外部システム連携', description: '外部システムとのデータ連携を行えること', priority: 'HIGH', requirement_type: 'functional'});
CREATE (req10:RequirementEntity {id: 'REQ-010', title: 'ユーティリティ機能', description: '共通ユーティリティを提供すること', priority: 'MEDIUM', requirement_type: 'functional'});

// 位置情報との関連
MATCH (r:RequirementEntity {id: 'REQ-009'}), (l:LocationURI {uri_id: 'loc_integration_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

MATCH (r:RequirementEntity {id: 'REQ-010'}), (l:LocationURI {uri_id: 'loc_maintain_req'}) 
CREATE (r)-[:REQUIREMENT_HAS_LOCATION]->(l);

// 実装関係
MATCH (r:RequirementEntity {id: 'REQ-010'}), (c:CodeEntity {persistent_id: 'CODE-012'}) 
CREATE (r)-[:IS_IMPLEMENTED_BY {implementation_type: 'IMPLEMENTS'}]->(c);

// 親子関係
MATCH (c1:CodeEntity {persistent_id: 'CODE-012'}), (c2:CodeEntity {persistent_id: 'CODE-013'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

MATCH (c1:CodeEntity {persistent_id: 'CODE-012'}), (c2:CodeEntity {persistent_id: 'CODE-014'}) 
CREATE (c1)-[:CONTAINS_CODE]->(c2);

// バージョン管理 - エンティティの関連付け
MATCH (v:VersionState {id: 'v1.3.0'}), (c:CodeEntity {persistent_id: 'CODE-012'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.3.0'}), (c:CodeEntity {persistent_id: 'CODE-013'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.3.0'}), (c:CodeEntity {persistent_id: 'CODE-014'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.3.0'}), (r:RequirementEntity {id: 'REQ-009'}) 
CREATE (v)-[:TRACKS_STATE_OF_REQ]->(r);

MATCH (v:VersionState {id: 'v1.3.0'}), (r:RequirementEntity {id: 'REQ-010'}) 
CREATE (v)-[:TRACKS_STATE_OF_REQ]->(r);

// CODE-001(UserService)がv1.3.0でCODE-015(UserService_v1.3)に更新された
// 注: v1.3.0で両方のエンティティに言及することで変更を表現
MATCH (v:VersionState {id: 'v1.3.0'}), (c:CodeEntity {persistent_id: 'CODE-001'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

MATCH (v:VersionState {id: 'v1.3.0'}), (c:CodeEntity {persistent_id: 'CODE-015'}) 
CREATE (v)-[:TRACKS_STATE_OF_CODE]->(c);

// 修正した要件を追加
MATCH (v:VersionState {id: 'v1.3.0'}), (r:RequirementEntity {id: 'REQ-002'}) 
CREATE (v)-[:TRACKS_STATE_OF_REQ]->(r);
