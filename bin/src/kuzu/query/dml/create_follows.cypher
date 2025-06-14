// FOLLOWS関係を作成するクエリ（バージョン間の順序）
MATCH (from_version:VersionState {id: $from_version_id})
MATCH (to_version:VersionState {id: $to_version_id})
CREATE (from_version)-[:FOLLOWS]->(to_version)
RETURN from_version.id as from_version, to_version.id as to_version
