/**
 * アプリケーション全体で使用する変数と定数
 * 環境変数などのアプリ定数をここで一元管理
 */

// デバッグモード
export const DEBUG = process.env.DEBUG === 'true';

// アプリケーション設定
export const APP_NAME = 'KuzuDB';
export const APP_VERSION = '1.0.0';

// 環境設定
export const NODE_ENV = process.env.NODE_ENV || 'development';
export const IS_PRODUCTION = NODE_ENV === 'production';
export const IS_DEVELOPMENT = NODE_ENV === 'development';

// API設定
export const API_HOST = process.env.API_HOST || 'localhost';
export const API_PORT = parseInt(process.env.API_PORT || '3000', 10);
export const API_URL = process.env.API_URL || `http://${API_HOST}:${API_PORT}`;

// データベース設定
export const DB_HOST = process.env.DB_HOST || 'localhost';
export const DB_PORT = parseInt(process.env.DB_PORT || '5432', 10);
export const DB_PATH = process.env.DB_PATH || '';
export const DB_IN_MEMORY = DB_PATH === '';

// データベース接続（グローバル変数）
export const DB_CONNECTION = null;

// パス設定
export const EXPORT_DATA_PATH = process.env.EXPORT_DATA_PATH || '/export_data';
export const PARQUET_FILES = [
  'EntityAggregationView.parquet',
  'RequirementVerification.parquet',
  'LocationURI.parquet',
  'VersionState.parquet',
  'ReferenceEntity.parquet',
  'CodeEntity.parquet',
  'RequirementEntity.parquet',
  'DEPENDS_ON.parquet',
  'VERIFICATION_IS_IMPLEMENTED_BY.parquet',
  'AGGREGATES_CODE.parquet',
  'IS_IMPLEMENTED_BY.parquet',
  'CONTAINS_LOCATION.parquet',
  'HAS_LOCATION.parquet',
  'REQUIREMENT_HAS_LOCATION.parquet',
  'TRACKS_STATE_OF_REF.parquet',
  'USES.parquet',
  'AGGREGATES_REQ.parquet',
  'TRACKS_STATE_OF_REQ.parquet',
  'FOLLOWS.parquet',
  'TRACKS_STATE_OF_CODE.parquet',
  'CONTAINS_CODE.parquet',
  'REFERENCES_CODE.parquet',
  'VERIFIED_BY.parquet',
  'REFERENCES_EXTERNAL.parquet',
  'REFERENCE_HAS_LOCATION.parquet'
];
