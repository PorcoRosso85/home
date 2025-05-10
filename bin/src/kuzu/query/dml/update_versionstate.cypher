// VersionStateノードを更新するクエリ
MATCH (versionstate:VersionState {id: $id})
SET versionstate.timestamp = COALESCE($timestamp, versionstate.timestamp),
    versionstate.description = COALESCE($description, versionstate.description)
RETURN versionstate.id as id,
       versionstate.timestamp as timestamp,
       versionstate.description as description
