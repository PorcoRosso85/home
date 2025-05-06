-- KuzuDB Parquetインポートスクリプト
-- エクスポートされたParquetファイルをkuzu-wasmにインポートします

-- スキーマを再作成
-- 注: まずテーブル定義が必要です

-- LocationURIノードテーブル
CREATE NODE TABLE LocationURI (
  uri_id STRING PRIMARY KEY,
  scheme STRING,
  authority STRING,
  path STRING,
  fragment STRING,
  query STRING
);

-- CodeEntityノードテーブル
CREATE NODE TABLE CodeEntity (
  persistent_id STRING PRIMARY KEY,
  name STRING,
  type STRING,
  signature STRING,
  complexity INT64,
  start_position INT64,
  end_position INT64
);

-- RequirementEntityノードテーブル
CREATE NODE TABLE RequirementEntity (
  id STRING PRIMARY KEY,
  title STRING,
  description STRING,
  priority STRING,
  requirement_type STRING
);

-- VersionStateノードテーブル
CREATE NODE TABLE VersionState (
  id STRING PRIMARY KEY,
  timestamp STRING,
  commit_id STRING,
  branch_name STRING
);

-- ReferenceEntityノードテーブル
CREATE NODE TABLE ReferenceEntity (
  id STRING PRIMARY KEY,
  description STRING,
  uri STRING,
  type STRING,
  source_type STRING
);

-- RequirementVerificationノードテーブル
CREATE NODE TABLE RequirementVerification (
  id STRING PRIMARY KEY,
  name STRING,
  description STRING,
  verification_type STRING
);

-- EntityAggregationViewノードテーブル
CREATE NODE TABLE EntityAggregationView (
  id STRING PRIMARY KEY,
  view_type STRING
);

-- エッジテーブル定義
-- HAS_LOCATION: コードエンティティの位置情報関連付け
CREATE REL TABLE HAS_LOCATION (
  FROM CodeEntity TO LocationURI
);

-- REQUIREMENT_HAS_LOCATION: 要件エンティティの位置情報関連付け
CREATE REL TABLE REQUIREMENT_HAS_LOCATION (
  FROM RequirementEntity TO LocationURI
);

-- 他のリレーションシップテーブル定義 (省略)
-- ...

-- Parquetファイルからデータをインポート
LOAD FROM '/db/export.parquet' (
  -- インポートオプション（必要に応じて設定）
  IGNORE_ERRORS=true
);

-- インポート結果の確認
MATCH (n) RETURN count(n) as NodeCount;
MATCH ()-[r]->() RETURN count(r) as RelationshipCount;
