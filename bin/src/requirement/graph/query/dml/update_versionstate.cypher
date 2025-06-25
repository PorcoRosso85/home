// VersionStateノードを更新するクエリ
MATCH (versionstate:VersionState {id: $id})
SET versionstate.timestamp = COALESCE($timestamp, versionstate.timestamp),
    versionstate.description = COALESCE($description, versionstate.description),
    versionstate.change_reason = COALESCE($change_reason, versionstate.change_reason),
    versionstate.progress_percentage = COALESCE($progress_percentage, versionstate.progress_percentage)
RETURN versionstate.id as id,
       versionstate.timestamp as timestamp,
       versionstate.description as description,
       versionstate.change_reason as change_reason,
       versionstate.progress_percentage as progress_percentage
