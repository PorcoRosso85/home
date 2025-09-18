// KuzuDB要件管理システム スキーマ定義 v3.2
// 作成日: 2024年
// 目的: 実装詳細を含む完全な要件管理
// 原則: このファイルが唯一の正式なスキーマ定義
// 変更履歴:
//   v3.1: priority フィールドを STRING から UINT8 に変更
//   v3.2: HAS_VERSION削除、TRACKS_STATE_OFに統一（migrations/v1参照）

// ========================================
// ノードテーブル（エンティティ）
// ========================================

// 要件エンティティ（拡張版）
CREATE NODE TABLE RequirementEntity (
    id STRING PRIMARY KEY,
    title STRING,
    description STRING,
    priority UINT8 DEFAULT 1,  // 0-255の範囲で優先度を表現（大きいほど高優先度）
    requirement_type STRING DEFAULT 'functional',
    status STRING DEFAULT 'proposed',  // v4で追加: 要件の状態
    verification_required BOOLEAN DEFAULT true,
    // v3で追加: 実装詳細プロパティ
    implementation_details STRING,      // JSON形式の実装詳細
    acceptance_criteria STRING,         // 受け入れ条件
    technical_specifications STRING     // JSON形式の技術仕様
);

// コードエンティティ（既存）
CREATE NODE TABLE CodeEntity (
    persistent_id STRING PRIMARY KEY,
    name STRING,
    type STRING,
    signature STRING,
    complexity INT64 DEFAULT 0,
    start_position INT64,
    end_position INT64
);

// ロケーションURI（既存）
CREATE NODE TABLE LocationURI (
    id STRING PRIMARY KEY
);

// バージョン状態（既存）
CREATE NODE TABLE VersionState (
    id STRING PRIMARY KEY,
    timestamp STRING,
    description STRING,
    change_reason STRING,
    progress_percentage DOUBLE DEFAULT 0.0,
    // v4で追加: バージョン時点の状態追跡
    operation STRING DEFAULT 'UPDATE',  // CREATE, UPDATE, DELETE
    author STRING DEFAULT 'system',
    changed_fields STRING,  // JSON形式の変更フィールドリスト
    previous_state STRING  // JSON形式の変更前の状態
);

// 参照エンティティ（既存）
CREATE NODE TABLE ReferenceEntity (
    id STRING PRIMARY KEY,
    description STRING,
    type STRING,
    source_type STRING DEFAULT 'documentation'
);

// v3で追加: 設定エンティティ
CREATE NODE TABLE ConfigurationEntity (
    id STRING PRIMARY KEY,
    requirement_id STRING,
    config_type STRING,        // 'algorithm_params', 'thresholds', 'environment'等
    config_data STRING,        // JSON形式の設定データ
    version STRING DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true
);

// v3で追加: 実装ガイドエンティティ
CREATE NODE TABLE ImplementationGuideEntity (
    id STRING PRIMARY KEY,
    requirement_id STRING,
    guide_type STRING,         // 'setup', 'implementation', 'testing', 'deployment'等
    content STRING,            // ガイドの内容
    order_index INT64 DEFAULT 0,        // 表示順序
    is_required BOOLEAN DEFAULT true
);

// エンティティ集約ビュー（既存）
CREATE NODE TABLE EntityAggregationView (
    id STRING PRIMARY KEY,
    name STRING,
    type STRING,
    description STRING
);

// ========================================
// エッジテーブル（関係）- 統一形式を採用
// ========================================

// LOCATES関係（統一形式）
CREATE REL TABLE LOCATES (
    FROM LocationURI TO RequirementEntity,
    entity_type STRING DEFAULT 'requirement',
    current BOOLEAN DEFAULT false
);

CREATE REL TABLE LOCATES_CODE (
    FROM LocationURI TO CodeEntity,
    entity_type STRING DEFAULT 'code'
);

// 実装関係（既存）
CREATE REL TABLE IS_IMPLEMENTED_BY (
    FROM RequirementEntity TO CodeEntity,
    confidence_score DOUBLE DEFAULT 1.0
);

// 検証関係（既存）
CREATE REL TABLE IS_VERIFIED_BY (
    FROM RequirementEntity TO CodeEntity,
    test_coverage DOUBLE DEFAULT 0.0
);

// 依存関係（既存）
CREATE REL TABLE DEPENDS_ON (
    FROM RequirementEntity TO RequirementEntity,
    dependency_type STRING DEFAULT 'requires',
    reason STRING
);

// バージョン管理
// HAS_VERSIONは削除（v3.2）- VersionStateはLocationURIのみを管理
// 詳細はmigrations/v1_fix_has_version_to_tracks_state.cypherを参照

CREATE REL TABLE HAS_VERSION_CODE (
    FROM CodeEntity TO VersionState
);

// 階層関係（既存）
CREATE REL TABLE CONTAINS_LOCATION (
    FROM LocationURI TO LocationURI
);

// 参照関係（既存）
CREATE REL TABLE REFERS_TO (
    FROM CodeEntity TO ReferenceEntity,
    relevance_score DOUBLE DEFAULT 1.0
);

CREATE REL TABLE REFERENCES_CODE (
    FROM CodeEntity TO CodeEntity,
    reference_type STRING DEFAULT 'uses'
);

// テスト関係（既存）
CREATE REL TABLE TESTS (
    FROM CodeEntity TO CodeEntity,
    test_type STRING DEFAULT 'unit'
);

// コード包含関係（既存）
CREATE REL TABLE CONTAINS_CODE (
    FROM CodeEntity TO CodeEntity
);

// 状態追跡（既存）
CREATE REL TABLE TRACKS_STATE_OF (
    FROM VersionState TO LocationURI,
    entity_type STRING
);

// バージョン順序（既存）
CREATE REL TABLE FOLLOWS (
    FROM VersionState TO VersionState
);

// v3で追加: 設定関係
CREATE REL TABLE CONFIGURES (
    FROM ConfigurationEntity TO RequirementEntity,
    applied_at STRING,
    applied_by STRING
);

// v3で追加: ガイド関係
CREATE REL TABLE GUIDES (
    FROM ImplementationGuideEntity TO RequirementEntity,
    guide_version STRING DEFAULT '1.0'
);

// 集約ビュー関係（既存）
CREATE REL TABLE USES (
    FROM EntityAggregationView TO LocationURI
);

CREATE REL TABLE AGGREGATES_REQ (
    FROM EntityAggregationView TO RequirementEntity
);

CREATE REL TABLE AGGREGATES_CODE (
    FROM EntityAggregationView TO CodeEntity
);

// ========================================
// インデックス（パフォーマンス最適化）
// ========================================

// KuzuDBは主キーに自動的にインデックスを作成
// 追加のインデックスが必要な場合はここに記述

// ========================================
// サンプルクエリ
// ========================================

// 1. 実装詳細を含む要件の取得
// MATCH (r:RequirementEntity)
// WHERE r.implementation_details IS NOT NULL
// RETURN r.id, r.title, r.implementation_details

// 2. 要件とその設定の取得
// MATCH (r:RequirementEntity {id: 'req_001'})
// OPTIONAL MATCH (c:ConfigurationEntity)-[:CONFIGURES]->(r)
// RETURN r, collect(c) as configurations

// 3. 実装ガイド付き要件の取得
// MATCH (r:RequirementEntity)
// OPTIONAL MATCH (g:ImplementationGuideEntity)-[:GUIDES]->(r)
// WHERE g.is_required = true
// RETURN r.id, r.title, collect(g) as guides
// ORDER BY g.order_index