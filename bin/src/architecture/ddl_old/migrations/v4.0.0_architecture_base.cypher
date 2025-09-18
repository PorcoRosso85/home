// Architecture Graph DB ベーススキーマ v4.0.0
// 作成日: 2025-08-03
// 目的: requirement/graphから独立したアーキテクチャ管理用スキーマ
//
// 変更内容:
// - requirement/graph v3.4.0スキーマをベースに独立
// - アーキテクチャ固有の拡張準備
// - DDL完全分離の実現

// ========================================
// ノードテーブル（エンティティ）
// ========================================

// 要件エンティティ
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING,
    description STRING,
    embedding DOUBLE[256],
    status STRING DEFAULT 'proposed'
);

// ロケーションURI
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

// バージョン状態
CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    operation STRING DEFAULT 'UPDATE',
    author STRING DEFAULT 'system'
);

// ========================================
// エッジテーブル（関係）
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