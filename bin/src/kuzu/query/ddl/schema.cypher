// 階層型トレーサビリティモデル - スキーマ定義

// ===== ノードテーブル =====

// 1. LocationURIノード - コードや要件の場所情報を保持するノード
CREATE NODE TABLE LocationURI (
  uri_id STRING PRIMARY KEY,
  scheme STRING,
  authority STRING,
  path STRING,
  fragment STRING,
  query STRING
);

// 2. CodeEntityノード - コードの構成要素（関数、クラス、メソッド等）
CREATE NODE TABLE CodeEntity (
  persistent_id STRING PRIMARY KEY,
  name STRING,
  type STRING,
  signature STRING,
  complexity INT64,
  start_position INT64,
  end_position INT64
);

// 3. RequirementEntityノード - システム要件
CREATE NODE TABLE RequirementEntity (
  id STRING PRIMARY KEY,
  title STRING,
  description STRING,
  priority STRING,
  requirement_type STRING
);

// 4. VersionStateノード - バージョン管理情報
CREATE NODE TABLE VersionState (
  id STRING PRIMARY KEY,
  timestamp STRING,
  description STRING,
);

// 5. ReferenceEntityノード - 外部参照情報
CREATE NODE TABLE ReferenceEntity (
  id STRING PRIMARY KEY,
  description STRING,
  // DEPRECATED: uriプロパティとurlプロパティは使用禁止となりました
  // uri STRING, -- 削除
  type STRING,
  source_type STRING
);

// 6. RequirementVerificationノード - 要件の検証方法
CREATE NODE TABLE RequirementVerification (
  id STRING PRIMARY KEY,
  name STRING,
  description STRING,
  verification_type STRING
);

// 7. EntityAggregationViewノード - URI階層から上位構造を生成・集計
CREATE NODE TABLE EntityAggregationView (
  id STRING PRIMARY KEY,
  view_type STRING
);

// ===== エッジテーブル =====

// 1. HAS_LOCATION: コードエンティティの位置情報関連付け
CREATE REL TABLE HAS_LOCATION (
  FROM CodeEntity TO LocationURI
);

// 2. REQUIREMENT_HAS_LOCATION: 要件エンティティの位置情報関連付け
CREATE REL TABLE REQUIREMENT_HAS_LOCATION (
  FROM RequirementEntity TO LocationURI
);

// 3. REFERENCE_HAS_LOCATION: 参照エンティティの位置情報関連付け
CREATE REL TABLE REFERENCE_HAS_LOCATION (
  FROM ReferenceEntity TO LocationURI
);

// 4. IS_IMPLEMENTED_BY: 要件の実装関係
CREATE REL TABLE IS_IMPLEMENTED_BY (
  FROM RequirementEntity TO CodeEntity,
  implementation_type STRING
);

// 5. VERIFICATION_IS_IMPLEMENTED_BY: 検証の実装関係
CREATE REL TABLE VERIFICATION_IS_IMPLEMENTED_BY (
  FROM RequirementVerification TO CodeEntity,
  implementation_type STRING
);

// 6. DEPENDS_ON: 要件間の依存関係
CREATE REL TABLE DEPENDS_ON (
  FROM RequirementEntity TO RequirementEntity,
  dependency_type STRING
);

// 7. REFERENCES_CODE: コード間参照関係
CREATE REL TABLE REFERENCES_CODE (
  FROM CodeEntity TO CodeEntity,
  ref_type STRING
);

// 8. REFERS_TO: 外部参照への関係
// FIXME: 旧名称 "REFERENCES_EXTERNAL" から変更。コードエンティティが参照エンティティを参照する関係を表現
CREATE REL TABLE REFERS_TO (
  FROM CodeEntity TO ReferenceEntity,
  ref_type STRING
);

// 9. VERIFIED_BY: 要件と検証の関連付け
CREATE REL TABLE VERIFIED_BY (
  FROM RequirementEntity TO RequirementVerification
);

// 10. CONTAINS_LOCATION: 位置情報間の階層関係
CREATE REL TABLE CONTAINS_LOCATION (
  FROM LocationURI TO LocationURI,
  relation_type STRING
);

// 11. CONTAINS_CODE: コードエンティティ間の階層関係
CREATE REL TABLE CONTAINS_CODE (
  FROM CodeEntity TO CodeEntity
);

// 12. FOLLOWS: バージョン間の順序関係
CREATE REL TABLE FOLLOWS (
  FROM VersionState TO VersionState
);

// 13. TRACKS_STATE_OF_CODE: バージョンとコードの状態追跡
CREATE REL TABLE TRACKS_STATE_OF_CODE (
  FROM VersionState TO CodeEntity
);

// 14. TRACKS_STATE_OF_REQ: バージョンと要件の状態追跡
CREATE REL TABLE TRACKS_STATE_OF_REQ (
  FROM VersionState TO RequirementEntity
);

// 15. TRACKS_STATE_OF_REFERENCE: バージョンと参照の状態追跡
// FIXME: 旧名称 "TRACKS_STATE_OF_REF" から変更。省略形を避け、完全な名前に統一
CREATE REL TABLE TRACKS_STATE_OF_REFERENCE (
  FROM VersionState TO ReferenceEntity
);

// 16. USES: 集計ビューとURI階層の関連付け
CREATE REL TABLE USES (
  FROM EntityAggregationView TO LocationURI
);

// 17. AGGREGATES_REQ: 要件の集計関係
CREATE REL TABLE AGGREGATES_REQ (
  FROM EntityAggregationView TO RequirementEntity,
  aggregation_method STRING
);

// 18. AGGREGATES_CODE: コードの集計関係
CREATE REL TABLE AGGREGATES_CODE (
  FROM EntityAggregationView TO CodeEntity,
  aggregation_method STRING
);
