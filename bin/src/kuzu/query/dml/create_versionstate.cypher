// VersionStateノードを作成するクエリ
CREATE (versionstate:VersionState {
  id: $id,
  timestamp: $timestamp,
  description: $description,
  change_reason: $change_reason,
  progress_percentage: COALESCE($progress_percentage, 0.0)
})
RETURN versionstate
