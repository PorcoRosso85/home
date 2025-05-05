// 階層型トレーサビリティモデル - バージョン状態復元関連クエリ

// 異なるバージョンの状態を作成
// @name: create_version_states
// バージョン1の状態を作成（初期状態）
CREATE (v1:VersionState {
  id: 'v1.0.0',
  timestamp: '2024-01-01T00:00:00Z',
  commit_id: 'commit-001',
  description: '初期バージョン',
  author: 'user1'
})

// 要件を作成
CREATE (req1v1:RequirementEntity {
  id: 'REQ-VS-001',
  title: 'ユーザー認証要件 v1',
  description: 'ユーザー名とパスワードによる認証機能',
  priority: 'high',
  requirement_type: 'functional',
  version: 'v1.0.0'
})

CREATE (req2v1:RequirementEntity {
  id: 'REQ-VS-002',
  title: 'ユーザー管理要件 v1',
  description: 'ユーザー情報の管理機能',
  priority: 'medium',
  requirement_type: 'functional',
  version: 'v1.0.0'
})

// コードを作成
CREATE (code1v1:CodeEntity {
  persistent_id: 'CODE-VS-001',
  name: 'AuthService v1',
  type: 'class',
  signature: 'class AuthService',
  complexity: 5,
  start_position: 100,
  end_position: 1000,
  version: 'v1.0.0'
})

// バージョン状態の関連付け
CREATE (v1)-[:TRACKS_STATE_OF_REQ]->(req1v1)
CREATE (v1)-[:TRACKS_STATE_OF_REQ]->(req2v1)
CREATE (v1)-[:TRACKS_STATE_OF_CODE]->(code1v1)

// 実装関係を作成
CREATE (req1v1)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1v1)

// バージョン2の状態を作成（要件の更新と新規コード追加）
WITH v1
CREATE (v2:VersionState {
  id: 'v1.1.0',
  timestamp: '2024-02-01T00:00:00Z',
  commit_id: 'commit-002',
  description: '要件の更新と新規コード追加',
  author: 'user2'
})

// 前のバージョンと関連付け
CREATE (v1)-[:FOLLOWS]->(v2)

// 更新された要件
CREATE (req1v2:RequirementEntity {
  id: 'REQ-VS-001',
  title: 'ユーザー認証要件 v2',
  description: 'ユーザー名、パスワード、または2FAによる認証機能',
  priority: 'high',
  requirement_type: 'functional',
  version: 'v1.1.0'
})

// 変更なしの要件（前バージョンと同じ）
CREATE (req2v2:RequirementEntity {
  id: 'REQ-VS-002',
  title: 'ユーザー管理要件 v1',
  description: 'ユーザー情報の管理機能',
  priority: 'medium',
  requirement_type: 'functional',
  version: 'v1.1.0'
})

// 新しい要件
CREATE (req3v2:RequirementEntity {
  id: 'REQ-VS-003',
  title: '二要素認証要件',
  description: '二要素認証（2FA）機能の追加',
  priority: 'high',
  requirement_type: 'functional',
  version: 'v1.1.0'
})

// 更新されたコード
CREATE (code1v2:CodeEntity {
  persistent_id: 'CODE-VS-001',
  name: 'AuthService v2',
  type: 'class',
  signature: 'class AuthService',
  complexity: 7,
  start_position: 100,
  end_position: 1200,
  version: 'v1.1.0'
})

// 新しいコード
CREATE (code2v2:CodeEntity {
  persistent_id: 'CODE-VS-002',
  name: 'TwoFactorService',
  type: 'class',
  signature: 'class TwoFactorService',
  complexity: 6,
  start_position: 1300,
  end_position: 2000,
  version: 'v1.1.0'
})

// バージョン状態の関連付け
CREATE (v2)-[:TRACKS_STATE_OF_REQ]->(req1v2)
CREATE (v2)-[:TRACKS_STATE_OF_REQ]->(req2v2)
CREATE (v2)-[:TRACKS_STATE_OF_REQ]->(req3v2)
CREATE (v2)-[:TRACKS_STATE_OF_CODE]->(code1v2)
CREATE (v2)-[:TRACKS_STATE_OF_CODE]->(code2v2)

// 実装関係を作成
CREATE (req1v2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1v2)
CREATE (req3v2)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code2v2)

// バージョン3の状態を作成（要件の削除とコードの更新）
WITH v2
CREATE (v3:VersionState {
  id: 'v1.2.0',
  timestamp: '2024-03-01T00:00:00Z',
  commit_id: 'commit-003',
  description: '要件の削除とコードの更新',
  author: 'user1'
})

// 前のバージョンと関連付け
CREATE (v2)-[:FOLLOWS]->(v3)

// 更新された要件
CREATE (req1v3:RequirementEntity {
  id: 'REQ-VS-001',
  title: 'ユーザー認証要件 v3',
  description: 'ユーザー名、パスワード、2FA、またはSSOによる認証機能',
  priority: 'high',
  requirement_type: 'functional',
  version: 'v1.2.0'
})

// 新しい要件
CREATE (req4v3:RequirementEntity {
  id: 'REQ-VS-004',
  title: 'シングルサインオン要件',
  description: 'SSOプロバイダーを使用した認証機能',
  priority: 'medium',
  requirement_type: 'functional',
  version: 'v1.2.0'
})

// 更新されたコード
CREATE (code1v3:CodeEntity {
  persistent_id: 'CODE-VS-001',
  name: 'AuthService v3',
  type: 'class',
  signature: 'class AuthService',
  complexity: 8,
  start_position: 100,
  end_position: 1400,
  version: 'v1.2.0'
})

CREATE (code2v3:CodeEntity {
  persistent_id: 'CODE-VS-002',
  name: 'TwoFactorService v2',
  type: 'class',
  signature: 'class TwoFactorService',
  complexity: 7,
  start_position: 1500,
  end_position: 2200,
  version: 'v1.2.0'
})

// 新しいコード
CREATE (code3v3:CodeEntity {
  persistent_id: 'CODE-VS-003',
  name: 'SSOService',
  type: 'class',
  signature: 'class SSOService',
  complexity: 6,
  start_position: 2300,
  end_position: 3000,
  version: 'v1.2.0'
})

// バージョン状態の関連付け
CREATE (v3)-[:TRACKS_STATE_OF_REQ]->(req1v3)
CREATE (v3)-[:TRACKS_STATE_OF_REQ]->(req4v3)
CREATE (v3)-[:TRACKS_STATE_OF_CODE]->(code1v3)
CREATE (v3)-[:TRACKS_STATE_OF_CODE]->(code2v3)
CREATE (v3)-[:TRACKS_STATE_OF_CODE]->(code3v3)

// 実装関係を作成
CREATE (req1v3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code1v3)
CREATE (req1v3)-[:IS_IMPLEMENTED_BY {implementation_type: 'support'}]->(code2v3)
CREATE (req4v3)-[:IS_IMPLEMENTED_BY {implementation_type: 'direct'}]->(code3v3)

RETURN 3 AS created_versions;

// 特定バージョンの要件を取得
// @name: get_requirements_at_version
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  r.description AS requirement_description,
  r.priority AS requirement_priority,
  r.requirement_type AS requirement_type,
  r.version AS requirement_version
ORDER BY r.id;

// 特定バージョンのコードを取得
// @name: get_code_at_version
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)
RETURN 
  c.persistent_id AS code_id,
  c.name AS code_name,
  c.type AS code_type,
  c.signature AS code_signature,
  c.complexity AS code_complexity,
  c.version AS code_version
ORDER BY c.persistent_id;

// 特定バージョンの要件とコードの関連を取得
// @name: get_relationships_at_version
MATCH (v:VersionState {id: $version})-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
OPTIONAL MATCH (r)-[rel:IS_IMPLEMENTED_BY]->(c:CodeEntity)<-[:TRACKS_STATE_OF_CODE]-(v)
WITH r, rel, c
WHERE c IS NOT NULL
RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  c.persistent_id AS code_id,
  c.name AS code_name,
  rel.implementation_type AS implementation_type
ORDER BY r.id, c.persistent_id;

// 異なるバージョン間の要件の変更を比較
// @name: compare_requirements_between_versions
MATCH (v1:VersionState {id: $version1})-[:TRACKS_STATE_OF_REQ]->(r1:RequirementEntity)
MATCH (v2:VersionState {id: $version2})-[:TRACKS_STATE_OF_REQ]->(r2:RequirementEntity)
WHERE r1.id = r2.id
WITH r1, r2
WHERE
  r1.title <> r2.title OR
  r1.description <> r2.description OR
  r1.priority <> r2.priority OR
  r1.requirement_type <> r2.requirement_type
RETURN 
  r1.id AS requirement_id,
  r1.title AS old_title,
  r2.title AS new_title,
  r1.description AS old_description,
  r2.description AS new_description,
  r1.priority AS old_priority,
  r2.priority AS new_priority,
  r1.requirement_type AS old_type,
  r2.requirement_type AS new_type
ORDER BY r1.id;

// 特定バージョンで追加された要件を取得
// @name: get_added_requirements
MATCH (v1:VersionState {id: $older})-[:FOLLOWS]->(v2:VersionState {id: $newer})
MATCH (v2)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
WHERE NOT EXISTS {
  MATCH (v1)-[:TRACKS_STATE_OF_REQ]->(:RequirementEntity {id: r.id})
}
RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  r.description AS requirement_description,
  r.priority AS requirement_priority,
  r.requirement_type AS requirement_type
ORDER BY r.id;

// 特定バージョンで削除された要件を取得
// @name: get_deleted_requirements
MATCH (v1:VersionState {id: $older})-[:FOLLOWS]->(v2:VersionState {id: $newer})
MATCH (v1)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
WHERE NOT EXISTS {
  MATCH (v2)-[:TRACKS_STATE_OF_REQ]->(:RequirementEntity {id: r.id})
}
RETURN 
  r.id AS requirement_id,
  r.title AS requirement_title,
  r.description AS requirement_description,
  r.priority AS requirement_priority,
  r.requirement_type AS requirement_type
ORDER BY r.id;

// 特定バージョンで追加されたコードを取得
// @name: get_added_code
MATCH (v1:VersionState {id: $older})-[:FOLLOWS]->(v2:VersionState {id: $newer})
MATCH (v2)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)
WHERE NOT EXISTS {
  MATCH (v1)-[:TRACKS_STATE_OF_CODE]->(:CodeEntity {persistent_id: c.persistent_id})
}
RETURN 
  c.persistent_id AS code_id,
  c.name AS code_name,
  c.type AS code_type,
  c.signature AS code_signature,
  c.complexity AS code_complexity
ORDER BY c.persistent_id;

// バージョンの履歴を取得
// @name: get_version_history
MATCH path = (v:VersionState)-[:FOLLOWS*0..10]->(latest:VersionState)
WHERE NOT ()-[:FOLLOWS]->(v)
WITH v, latest, path
ORDER BY length(path) DESC
LIMIT 1
MATCH p = (v)-[:FOLLOWS*0..10]->(latest)
WITH [node IN nodes(p) | node.id] AS version_path
UNWIND range(0, size(version_path)-1) AS idx
WITH version_path[idx] AS version_id
MATCH (version:VersionState {id: version_id})
RETURN 
  version.id AS version_id,
  version.timestamp AS timestamp,
  version.description AS description,
  version.author AS author,
  version.commit_id AS commit_id
ORDER BY version.timestamp;

// 完全な状態スナップショットを取得
// @name: get_complete_state_snapshot
MATCH (v:VersionState {id: $version})

// 要件の取得
OPTIONAL MATCH (v)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
WITH v, collect(r) AS requirements

// コードの取得
OPTIONAL MATCH (v)-[:TRACKS_STATE_OF_CODE]->(c:CodeEntity)
WITH v, requirements, collect(c) AS code_entities

// 実装関係の取得
OPTIONAL MATCH (v)-[:TRACKS_STATE_OF_REQ]->(r:RequirementEntity)
OPTIONAL MATCH (r)-[impl:IS_IMPLEMENTED_BY]->(c:CodeEntity)<-[:TRACKS_STATE_OF_CODE]-(v)
WITH v, 
     requirements, 
     code_entities, 
     collect({
       requirement_id: r.id, 
       code_id: c.persistent_id, 
       type: impl.implementation_type
     }) AS implementations

RETURN 
  v.id AS version_id,
  v.timestamp AS timestamp,
  v.description AS description,
  length(requirements) AS requirements_count,
  length(code_entities) AS code_count,
  length(implementations) AS implementation_relationships_count,
  requirements,
  code_entities,
  implementations;