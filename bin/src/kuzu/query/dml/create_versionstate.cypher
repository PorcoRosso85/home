// VersionStateノードを作成するクエリ
CREATE (versionstate:VersionState {
  id: $id,
  timestamp: $timestamp,
  description: $description
})
RETURN versionstate
