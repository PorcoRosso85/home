// バージョン履歴を順序付きで取得するDQL（FOLLOWS関係を考慮）
OPTIONAL MATCH (v:VersionState)
OPTIONAL MATCH (v)-[:FOLLOWS]->(next:VersionState)
OPTIONAL MATCH (prev:VersionState)-[:FOLLOWS]->(v)

// 最初のバージョン（他のバージョンから参照されないもの）を特定
WITH v,
     CASE WHEN prev IS NULL THEN 0 ELSE 1 END as has_predecessor,
     collect(next.id) as following_versions
WHERE v IS NOT NULL

// バージョンを順序付きで返す
RETURN v.id as version_id,
       v.timestamp as timestamp,
       v.description as description,
       v.change_reason as change_reason,
       has_predecessor,
       following_versions
ORDER BY v.timestamp ASC
