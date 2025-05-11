// VersionStateノードを作成するクエリ
CREATE (versionstate:VersionState {
  id: $id,
  timestamp: $timestamp,
  description: $description,
  progress_percentage: COALESCE($progress_percentage, 0.0)
})
RETURN versionstate
