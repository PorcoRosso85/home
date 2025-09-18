// 要件参照ガードレールシステム スキーマ v3.5.0
// 作成日: 2025-07-28
// 目的: 要件が適切な参照文献に基づいて実装されることを保証するためのスキーマ

// ========================================
// ノードテーブル（エンティティ）
// ========================================

// 参照エンティティ - 要件の根拠となる外部参照文献を管理
// 目的: OWASP ASVS、NISTフレームワーク、業界標準などの参照文献を統一的に管理
CREATE NODE TABLE ReferenceEntity (
    id STRING PRIMARY KEY,           -- 一意識別子（例: "ASVS-V1.1.1", "NIST-AC-2"）
    title STRING,                    -- 参照項目のタイトル
    description STRING,              -- 参照内容の詳細説明
    source STRING,                   -- 出典（例: "OWASP ASVS 5.0", "NIST 800-53"）
    category STRING,                 -- カテゴリー（例: "Authentication", "Access Control"）
    level STRING,                    -- 重要度レベル（例: "L1", "L2", "L3" for ASVS）
    embedding DOUBLE[384],           -- セマンティック検索用の埋め込みベクトル
    version STRING,                  -- 参照文献のバージョン
    url STRING                       -- 参照元URL（オプション）
);

// 例外申請エンティティ - 参照要件からの逸脱を正当化する申請を管理
// 目的: 標準から逸脱する必要がある場合の承認プロセスを追跡
CREATE NODE TABLE ExceptionRequest (
    id STRING PRIMARY KEY,           -- 一意識別子（例: "EXC-2025-001"）
    reason STRING,                   -- 例外申請の理由
    status STRING DEFAULT 'pending', -- 申請ステータス（pending/approved/rejected）
    requested_at STRING,             -- 申請日時
    approved_by STRING,              -- 承認者（オプション）
    approved_at STRING               -- 承認日時（オプション）
);

// ========================================
// エッジテーブル（関係）
// ========================================

// IMPLEMENTS関係 - 要件が参照文献の項目を実装することを示す
// 目的: 各要件がどの標準・ガイドラインに準拠しているかを追跡
CREATE REL TABLE IMPLEMENTS (
    FROM RequirementEntity TO ReferenceEntity,
    implementation_type STRING DEFAULT 'full',  -- 実装タイプ（full/partial/custom）
    notes STRING                                -- 実装に関する補足説明
);

// HAS_EXCEPTION関係 - 要件が参照要件からの例外を持つことを示す
// 目的: 標準からの逸脱とその正当性を文書化
CREATE REL TABLE HAS_EXCEPTION (
    FROM RequirementEntity TO ExceptionRequest,
    exception_type STRING DEFAULT 'deviation',  -- 例外タイプ（deviation/waiver/alternative）
    mitigation STRING                          -- リスク軽減策の説明
);