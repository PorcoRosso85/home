// KuzuDB要件管理システム 簡素化スキーマ v3.3
// 作成日: 2025-07-09
// 目的: 最小限のコア機能のみを持つ要件管理
// 原則: このファイルがv3.3以降の正式なスキーマ定義

// ========================================
// ノードテーブル（エンティティ）- 3個のみ
// ========================================

// 要件エンティティ（簡素化版）
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING,
    description STRING,
    status STRING DEFAULT 'proposed'
);

// ロケーションURI（変更なし）
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

// バージョン状態（簡素化版）
CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);

// ========================================
// エッジテーブル（関係）- 4個のみ
// ========================================

// LOCATES関係
CREATE REL TABLE LOCATES (
    FROM LocationURI TO RequirementEntity,
    entity_type STRING DEFAULT 'requirement',
    current BOOLEAN DEFAULT false
);

// バージョン管理
CREATE REL TABLE TRACKS_STATE_OF (
    FROM VersionState TO LocationURI,
    entity_type STRING
);

// 階層関係
CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);

// 依存関係
CREATE REL TABLE DEPENDS_ON (
    FROM RequirementEntity TO RequirementEntity,
    dependency_type STRING DEFAULT 'requires',
    reason STRING
);

// ========================================
// インデックス
// ========================================

// KuzuDBは主キーに自動的にインデックスを作成

// ========================================
// 削除された要素のサマリー
// ========================================

// 削除されたノード:
// - CodeEntity
// - ReferenceEntity 
// - ConfigurationEntity
// - ImplementationGuideEntity
// - EntityAggregationView

// 削除されたリレーション:
// - LOCATES_CODE
// - IS_IMPLEMENTED_BY
// - IS_VERIFIED_BY
// - HAS_VERSION_CODE
// - REFERS_TO
// - REFERENCES_CODE
// - TESTS
// - CONTAINS_CODE
// - CONFIGURES
// - GUIDES
// - USES
// - AGGREGATES_REQ
// - AGGREGATES_CODE
// - FOLLOWS

// 削除されたプロパティ:
// RequirementEntity: priority, requirement_type, verification_required,
//                   implementation_details, acceptance_criteria, technical_specifications
// VersionState: progress_percentage, changed_fields, previous_state