// 最近のバージョンでの変更影響範囲
// バージョン変更に関連する要件を時系列で取得
MATCH (v:VersionState)-[:VERSION_AFFECTS]->(r:RequirementEntity)
WHERE v.timestamp > $sinceTimestamp
RETURN v.id as version_id,
       v.timestamp,
       v.description as version_description,
       collect(r.id) as affected_requirements
ORDER BY v.timestamp DESC;