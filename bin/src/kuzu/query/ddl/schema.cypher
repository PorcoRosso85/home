// 階層型トレーサビリティモデル - スキーマ定義

// ===== ノードテーブル =====

// 1. LocationURIノード - コードや要件の場所情報を保持するノード
// REFACTORED: 最小化（uri_id→id, 7プロパティ→1プロパティ）
// scheme, authority, path, fragment, query, completed は id から派生可能
CREATE NODE TABLE LocationURI (
  id STRING PRIMARY KEY
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
  change_reason STRING,
  progress_percentage FLOAT
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

// 1. LOCATED_WITH: 位置情報とエンティティの関連付け（統一版）
// LocationURIから各種エンティティへの関係を表す
CREATE REL TABLE LOCATED_WITH (
  FROM LocationURI TO CodeEntity,
  entity_type STRING
);

// 2. LOCATED_WITH_REQUIREMENT: 位置情報と要件エンティティの関連付け
CREATE REL TABLE LOCATED_WITH_REQUIREMENT (
  FROM LocationURI TO RequirementEntity,
  entity_type STRING
);

// 3. LOCATED_WITH_REFERENCE: 位置情報と参照エンティティの関連付け
CREATE REL TABLE LOCATED_WITH_REFERENCE (
  FROM LocationURI TO ReferenceEntity,
  entity_type STRING
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

// 13. TRACKS_STATE_OF_LOCATED_ENTITY: バージョンと位置情報の状態追跡
// LocationURIを介してエンティティの状態を追跡する
CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (
  FROM VersionState TO LocationURI
);

// 14. USES: 集計ビューとURI階層の関連付け
CREATE REL TABLE USES (
  FROM EntityAggregationView TO LocationURI
);

// 15. AGGREGATES_REQ: 要件の集計関係
CREATE REL TABLE AGGREGATES_REQ (
  FROM EntityAggregationView TO RequirementEntity,
  aggregation_method STRING
);

// 16. AGGREGATES_CODE: コードの集計関係
CREATE REL TABLE AGGREGATES_CODE (
  FROM EntityAggregationView TO CodeEntity,
  aggregation_method STRING
);
