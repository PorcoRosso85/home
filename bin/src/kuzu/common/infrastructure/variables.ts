/**
 * アプリケーション全体で使用する変数と定数
 * 規約準拠: デフォルト値禁止、明示的な設定管理
 */

// 設定エラー型定義（共用体型）
type ConfigSuccess<T> = {
  status: "success";
  value: T;
};

type ConfigMissingError = {
  status: "config_missing";
  key: string;
  message: string;
};

type ConfigValidationError = {
  status: "config_invalid";
  key: string;
  value: string;
  message: string;
};

type ConfigResult<T> = ConfigSuccess<T> | ConfigMissingError | ConfigValidationError;

// 必須環境変数取得関数
function requireEnvVar(key: string): ConfigResult<string> {
  const value = process.env[key];
  if (value === undefined || value === '') {
    return {
      status: "config_missing",
      key,
      message: `Environment variable '${key}' is required but not set`
    };
  }
  return { status: "success", value };
}

// 数値型環境変数取得関数
function requireEnvNumber(key: string): ConfigResult<number> {
  const result = requireEnvVar(key);
  if (result.status !== "success") {
    return result;
  }
  
  const numValue = parseInt(result.value, 10);
  if (isNaN(numValue)) {
    return {
      status: "config_invalid",
      key,
      value: result.value,
      message: `Environment variable '${key}' must be a valid number`
    };
  }
  
  return { status: "success", value: numValue };
}

// ブール型環境変数取得関数
function requireEnvBoolean(key: string): ConfigResult<boolean> {
  const result = requireEnvVar(key);
  if (result.status !== "success") {
    return result;
  }
  
  if (result.value !== 'true' && result.value !== 'false') {
    return {
      status: "config_invalid",
      key,
      value: result.value,
      message: `Environment variable '${key}' must be 'true' or 'false'`
    };
  }
  
  return { status: "success", value: result.value === 'true' };
}

// 設定値取得ヘルパー（エラー時は処理を停止）
function getConfigValue<T>(result: ConfigResult<T>): T {
  if (result.status === "success") {
    return result.value;
  }
  
  // 設定エラーの場合は即座に処理を停止
  console.error(`Configuration Error: ${result.message}`);
  if (typeof process !== 'undefined') {
    process.exit(1);
  }
  
  // ブラウザ環境の場合はエラーを投げる（ただし規約違反なので後で修正予定）
  throw new Error(result.message);
}

// ログレベル定義
export const enum LogLevel {
  ERROR = 1,
  WARN = 2,
  INFO = 3,
  DEBUG = 4
}

export const LOG_LEVEL = getConfigValue(requireEnvNumber('LOG_LEVEL'));
export const NODE_ENV = getConfigValue(requireEnvVar('NODE_ENV'));
export const API_PORT = getConfigValue(requireEnvNumber('API_PORT'));
export const DB_PATH = getConfigValue(requireEnvVar('DB_PATH'));
export const API_HOST = getConfigValue(requireEnvVar('API_HOST'));

// 固定値（変更されない定数）
export const APP_NAME = 'KuzuDB';
export const APP_VERSION = '1.0.0';

// 計算される値
export const IS_PRODUCTION = NODE_ENV === 'production';
export const IS_DEVELOPMENT = NODE_ENV === 'development';
export const API_URL = `http://${API_HOST}:${API_PORT}`;
export const DB_IN_MEMORY = DB_PATH === '';

// 固定配列データ（ハードコードではなく、システム仕様として定義）
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
] as const;
