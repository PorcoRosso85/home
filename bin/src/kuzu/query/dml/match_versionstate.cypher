// VersionStateノードを検索するクエリ（OPTIONAL MATCHでエラーハンドリング）
OPTIONAL MATCH (versionstate:VersionState {id: $id})
RETURN versionstate.id as id,
       versionstate.timestamp as timestamp,
       versionstate.description as description,
       versionstate.change_reason as change_reason,
       CASE WHEN versionstate IS NULL THEN false ELSE true END as exists
