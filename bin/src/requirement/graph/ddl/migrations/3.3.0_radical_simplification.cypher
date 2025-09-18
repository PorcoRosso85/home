// KuzuDB要件管理システム 徹底的簡素化マイグレーション v3.3
// 作成日: 2025-07-09
// 目的: コアエンティティのみを残した最小構成への移行
// 変更内容:
//   - 5つのノードテーブルを削除
//   - RequirementEntityから6つのプロパティを削除
//   - VersionStateから3つのプロパティを削除  
//   - 14のリレーションテーブルを削除
//   - スコアリングシステム完全削除

// ========================================
// ステップ1: 削除されるデータのバックアップ（オプション）
// ========================================

// 削除前にデータをエクスポートする場合は以下を実行:
// COPY (MATCH (n:CodeEntity) RETURN n.*) TO 'backup_code_entities.csv';
// COPY (MATCH (n:ReferenceEntity) RETURN n.*) TO 'backup_reference_entities.csv';
// COPY (MATCH (n:ConfigurationEntity) RETURN n.*) TO 'backup_configuration_entities.csv';
// COPY (MATCH (n:ImplementationGuideEntity) RETURN n.*) TO 'backup_implementation_guide_entities.csv';
// COPY (MATCH (n:EntityAggregationView) RETURN n.*) TO 'backup_entity_aggregation_views.csv';

// ========================================
// ステップ2: リレーションテーブルの削除
// ========================================

DROP TABLE IF EXISTS LOCATES_CODE;
DROP TABLE IF EXISTS IS_IMPLEMENTED_BY;
DROP TABLE IF EXISTS IS_VERIFIED_BY;
DROP TABLE IF EXISTS HAS_VERSION_CODE;
DROP TABLE IF EXISTS REFERS_TO;
DROP TABLE IF EXISTS REFERENCES_CODE;
DROP TABLE IF EXISTS TESTS;
DROP TABLE IF EXISTS CONTAINS_CODE;
DROP TABLE IF EXISTS CONFIGURES;
DROP TABLE IF EXISTS GUIDES;
DROP TABLE IF EXISTS USES;
DROP TABLE IF EXISTS AGGREGATES_REQ;
DROP TABLE IF EXISTS AGGREGATES_CODE;
DROP TABLE IF EXISTS FOLLOWS;

// ========================================
// ステップ3: ノードテーブルの削除
// ========================================

DROP TABLE IF EXISTS CodeEntity;
DROP TABLE IF EXISTS ReferenceEntity;
DROP TABLE IF EXISTS ConfigurationEntity;
DROP TABLE IF EXISTS ImplementationGuideEntity;
DROP TABLE IF EXISTS EntityAggregationView;

// ========================================
// ステップ4: 既存ノードのプロパティ削除
// ========================================

// RequirementEntityの不要プロパティを削除
// 注意: KuzuDBは ALTER TABLE DROP COLUMN をサポートしていない可能性があるため、
// 実際の実装では新しいテーブルを作成して必要なデータのみコピーする方法を推奨

// 以下は概念的な削除操作:
// ALTER TABLE RequirementEntity DROP COLUMN priority;
// ALTER TABLE RequirementEntity DROP COLUMN requirement_type;
// ALTER TABLE RequirementEntity DROP COLUMN verification_required;
// ALTER TABLE RequirementEntity DROP COLUMN implementation_details;
// ALTER TABLE RequirementEntity DROP COLUMN acceptance_criteria;
// ALTER TABLE RequirementEntity DROP COLUMN technical_specifications;

// VersionStateの不要プロパティを削除
// ALTER TABLE VersionState DROP COLUMN progress_percentage;
// ALTER TABLE VersionState DROP COLUMN changed_fields;
// ALTER TABLE VersionState DROP COLUMN previous_state;

// ========================================
// 代替アプローチ: 新しいテーブル構造の作成
// ========================================

// 既存データを保持しつつ新しい構造に移行する場合:

// 1. 新しいRequirementEntityを作成
CREATE NODE TABLE RequirementEntity_v3 (
    id STRING PRIMARY KEY,
    title STRING,
    description STRING,
    status STRING DEFAULT 'proposed'
);

// 2. 必要なデータのみコピー
COPY RequirementEntity_v3
FROM (
    MATCH (r:RequirementEntity)
    RETURN r.id, r.title, r.description, r.status
);

// 3. 新しいVersionStateを作成
CREATE NODE TABLE VersionState_v3 (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);

// 4. 必要なデータのみコピー
COPY VersionState_v3
FROM (
    MATCH (v:VersionState)
    RETURN v.id, v.timestamp, v.description, v.change_reason, v.operation, v.author
);

// 5. 古いテーブルを削除して新しいテーブルをリネーム
DROP TABLE RequirementEntity;
DROP TABLE VersionState;
ALTER TABLE RequirementEntity_v3 RENAME TO RequirementEntity;
ALTER TABLE VersionState_v3 RENAME TO VersionState;

// ========================================
// 結果: 最小構成のスキーマ
// ========================================

// 残存ノード（3個）:
// - RequirementEntity (4プロパティ)
// - LocationURI (1プロパティ)
// - VersionState (6プロパティ)

// 残存リレーション（4個）:
// - LOCATES
// - TRACKS_STATE_OF
// - CONTAINS_LOCATION
// - DEPENDS_ON