// 全バージョンを順序付きで取得するDQL
MATCH (v:VersionState)
OPTIONAL MATCH (v)-[:FOLLOWS]->(next:VersionState)
OPTIONAL MATCH (prev:VersionState)-[:FOLLOWS]->(v)

RETURN v.id as version_id,
       v.timestamp as timestamp,
       v.description as description,
       CASE WHEN prev IS NULL THEN true ELSE false END as is_first
ORDER BY v.timestamp ASC
