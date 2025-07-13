// KuzuDB要件管理システム POC Search完全統合スキーマ v3.4
// 作成日: 2025-07-13
// 目的: POC searchのスキーマに完全準拠したスキーマ

// ========================================
// ノードテーブル（エンティティ）- 3個
// ========================================

// 要件エンティティ（POC Search対応版）
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING,
    description STRING,            -- メインコンテンツフィールド（POC searchで使用）
    embedding DOUBLE[256],         -- POC search必須フィールド
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
// エッジテーブル（関係）- 4個
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