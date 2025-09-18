// Migration 3.1.0 → 3.2.0: HAS_VERSIONをTRACKS_STATE_OFに統一
// 破壊的変更: RequirementEntity → VersionStateの直接関係を削除
//
// 理由: kuzu/query/ddl準拠 - VersionStateはLocationURIのみを管理すべき

// ========================================
// 既存データのマイグレーション（データがある場合のみ実行）
// ========================================

// HAS_VERSION関係をTRACKS_STATE_OFに変換
MATCH (r:RequirementEntity)-[hv:HAS_VERSION]->(v:VersionState)
MATCH (l:LocationURI)-[:LOCATES]->(r)
CREATE (v)-[:TRACKS_STATE_OF {entity_type: 'requirement'}]->(l);

// 古い関係を削除
MATCH (r:RequirementEntity)-[hv:HAS_VERSION]->(v:VersionState)
DELETE hv;

// ========================================
// DDL変更
// ========================================

// HAS_VERSIONテーブル定義を削除
// （3.2.0_current.cypherでは定義されていない）