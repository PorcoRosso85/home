// 完了/未完了の統計情報を取得
// 各バージョンの統計情報を収集
OPTIONAL MATCH (vs:VersionState)
OPTIONAL MATCH (vs)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(loc:LocationURI)

WITH vs,
     count(loc) as total_locations,
     count(CASE WHEN loc.completed = true THEN 1 END) as completed_locations,
     count(CASE WHEN loc.completed = false OR loc.completed IS NULL THEN 1 END) as incomplete_locations

// 統計情報の計算 (vsがNULLの場合の考慮)
WITH 
     count(DISTINCT vs) as total_versions,
     sum(total_locations) as overall_total_locations,
     sum(completed_locations) as overall_completed_locations,
     sum(incomplete_locations) as overall_incomplete_locations,
     sum(CASE WHEN vs IS NOT NULL AND COALESCE(vs.progress_percentage, 0.0) = 1.0 THEN 1 ELSE 0 END) as completed_count,
     sum(CASE WHEN vs IS NOT NULL AND COALESCE(vs.progress_percentage, 0.0) > 0.0 AND COALESCE(vs.progress_percentage, 0.0) < 1.0 THEN 1 ELSE 0 END) as in_progress_count,
     sum(CASE WHEN vs IS NOT NULL AND COALESCE(vs.progress_percentage, 0.0) = 0.0 THEN 1 ELSE 0 END) as not_started_count

RETURN 
  COALESCE(total_versions, 0) as total_versions,
  COALESCE(overall_total_locations, 0) as overall_total_locations,
  COALESCE(overall_completed_locations, 0) as overall_completed_locations,
  COALESCE(overall_incomplete_locations, 0) as overall_incomplete_locations,
  COALESCE(completed_count, 0) as completed_count,
  COALESCE(in_progress_count, 0) as in_progress_count,
  COALESCE(not_started_count, 0) as not_started_count
