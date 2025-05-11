// VersionStateの進捗率を直接更新するクエリ
MATCH (vs:VersionState {id: $version_id})
SET vs.progress_percentage = $progress_percentage
RETURN vs.id as version_id,
       vs.timestamp as timestamp,
       vs.description as description,
       vs.progress_percentage as progress_percentage
