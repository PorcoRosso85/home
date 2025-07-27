// KuzuDB要件管理システム Reference Entity統合スキーマ v3.5
// 作成日: 2025-07-26
// 目的: ReferenceEntityとIMPLEMENTS関係を追加し、要件と標準文書の関連付けを可能にする
// 前提: v3.4.0スキーマに対する追加マイグレーション

// ========================================
// 変更概要 (v3.4.0からの変更点)
// ========================================
// 追加:
// - ReferenceEntityノードテーブル: 標準文書（ISO、RFCなど）の参照情報を管理
// - IMPLEMENTSリレーション: RequirementEntityからReferenceEntityへの実装関係
//
// 目的:
// - 要件がどの標準文書のどのセクションを実装しているかをトレース可能にする
// - コンプライアンスチェックとギャップ分析の基盤を提供

// ========================================
// 新規ノードテーブル - 1個追加
// ========================================

// 参照エンティティ（標準文書の参照情報）
CREATE NODE TABLE ReferenceEntity (
    id STRING PRIMARY KEY,              // 例: "ISO-14649-10:2003:section-4.2.1"
    standard STRING,                    // 標準文書名（例: "ISO 14649-10"）
    version STRING,                     // バージョン（例: "2003"）
    section STRING,                     // セクション番号（例: "4.2.1"）
    description STRING,                 // セクションの説明
    level INT64 DEFAULT 1,              // 階層レベル（1=章、2=節、3=項など）
    category STRING                     // カテゴリ（例: "data_model", "process"）
);

// ========================================
// 新規エッジテーブル - 1個追加
// ========================================

// IMPLEMENTS関係（要件が標準文書を実装）
CREATE REL TABLE IMPLEMENTS (
    FROM RequirementEntity TO ReferenceEntity,
    implementation_type STRING DEFAULT 'full',    // 'full', 'partial', 'extends'
    compliance_level STRING DEFAULT 'required',   // 'required', 'recommended', 'optional'
    notes STRING,                                 // 実装に関する注記
    verified BOOLEAN DEFAULT false                // 実装が検証済みかどうか
);

// ========================================
// 既存スキーマとの統合
// ========================================
// v3.4.0の以下の要素は変更なし:
// - RequirementEntity（id, title, description, embedding, status）
// - LocationURI（id）
// - VersionState（id, timestamp, description, change_reason, operation, author）
// - LOCATES関係
// - TRACKS_STATE_OF関係
// - CONTAINS_LOCATION関係
// - DEPENDS_ON関係

// ========================================
// 使用例
// ========================================
// 要件を標準文書のセクションに関連付ける:
// MATCH (req:RequirementEntity {id: 'req001'})
// MATCH (ref:ReferenceEntity {id: 'ISO-14649-10:2003:section-4.2.1'})
// CREATE (req)-[:IMPLEMENTS {
//     implementation_type: 'full',
//     compliance_level: 'required',
//     notes: 'Fully implements the data model specification'
// }]->(ref);

// ========================================
// マイグレーション注記
// ========================================
// このマイグレーションは既存のデータに影響を与えません。
// 新しいテーブルとリレーションを追加するのみです。
// 既存のRequirementEntityからReferenceEntityへの関連付けは
// アプリケーション側で必要に応じて行います。